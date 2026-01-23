"""Config flow for Octoha integration.

Handles user setup, credential validation, meter discovery, and error handling.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.client import OctohaApiClient
from .api.exceptions import AuthenticationError, OctopusError
from .const import (
    CONF_ACCOUNT,
    CONF_API_KEY,
    CONF_DISPATCH_INTERVAL,
    CONF_ELECTRICITY_INTERVAL,
    CONF_GAS_INTERVAL,
    CONF_GAS_METER_SERIAL,
    CONF_METER_SERIAL,
    CONF_MPAN,
    CONF_MPRN,
    CONF_TARIFF_INTERVAL,
    DEFAULT_DISPATCH_INTERVAL,
    DEFAULT_ELECTRICITY_INTERVAL,
    DEFAULT_GAS_INTERVAL,
    DEFAULT_TARIFF_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Schema for user step form
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


class OctohaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Octoha.

    The config flow handles:
    1. User step: Accept API key input
    2. Validate credentials by calling validate_credentials()
    3. Fetch account data with get_account()
    4. Show meter discovery step if account has multiple meter points
    5. Handle errors: invalid_api_key, cannot_connect, unknown
    6. Abort if account already configured
    """

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_key: str | None = None
        self._account: Any = None
        self._client: OctohaApiClient | None = None
        # Meter selection state
        self._selected_mpan: str | None = None
        self._selected_mprn: str | None = None
        self._selected_meter_serial: str | None = None
        self._selected_gas_meter_serial: str | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step.

        This step prompts the user for their Octopus Energy API key
        and validates the credentials.

        Args:
            user_input: User input from the form, or None on initial load.

        Returns:
            ConfigFlowResult indicating next step or errors.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY, "").strip()

            # Validate non-empty API key
            if not api_key:
                errors["base"] = "invalid_api_key"
            else:
                # Store API key for later steps
                self._api_key = api_key

                try:
                    # Create client and validate credentials
                    session = async_get_clientsession(self.hass)
                    self._client = OctohaApiClient(
                        session=session,
                        api_key=api_key,
                    )

                    await self._client.validate_credentials()

                    # Discover account number from API key
                    await self._client.discover_account_number()

                    # Fetch account data to discover meters
                    self._account = await self._client.get_account()

                    # Check if already configured
                    await self.async_set_unique_id(self._account.account_number)
                    self._abort_if_unique_id_configured()

                    # Check for available meters using meter point lists
                    elec_meters = self._account.electricity_meter_points
                    gas_meters = self._account.gas_meter_points
                    total_meters = len(elec_meters) + len(gas_meters)

                    if total_meters == 0:
                        # No meters found
                        errors["base"] = "no_meters"
                    elif total_meters == 1:
                        # Only one meter, no selection needed
                        return self._create_entry()
                    else:
                        # Multiple meters - show meter selection step
                        return await self.async_step_meters()

                except AuthenticationError:
                    _LOGGER.debug("Authentication failed for API key")
                    errors["base"] = "invalid_api_key"
                except OctopusError as err:
                    _LOGGER.debug("API connection error: %s", err)
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected error during config flow")
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_meters(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the meter selection step.

        This step is shown when the account has multiple meter points
        and allows the user to select which meters to monitor.

        Args:
            user_input: User input from the form, or None on initial load.

        Returns:
            ConfigFlowResult indicating next step or entry creation.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Persist user selections
            self._selected_mpan = user_input.get(CONF_MPAN)
            self._selected_mprn = user_input.get(CONF_MPRN)

            # Look up serial numbers for selected meters
            if self._selected_mpan and self._account:
                for mp in self._account.electricity_meter_points:
                    if mp.mpan == self._selected_mpan:
                        self._selected_meter_serial = mp.meter_serial
                        break

            if self._selected_mprn and self._account:
                for mp in self._account.gas_meter_points:
                    if mp.mprn == self._selected_mprn:
                        self._selected_gas_meter_serial = mp.meter_serial
                        break

            return self._create_entry()

        # Build schema based on available meters
        schema_dict: dict[Any, Any] = {}

        if self._account is not None:
            elec_meters = self._account.electricity_meter_points
            gas_meters = self._account.gas_meter_points

            # Build electricity meter selector
            if elec_meters:
                mpan_options = [mp.mpan for mp in elec_meters]
                default_mpan = elec_meters[0].mpan
                schema_dict[vol.Optional(CONF_MPAN, default=default_mpan)] = vol.In(
                    mpan_options
                )

            # Build gas meter selector
            if gas_meters:
                mprn_options = [mp.mprn for mp in gas_meters]
                default_mprn = gas_meters[0].mprn
                schema_dict[vol.Optional(CONF_MPRN, default=default_mprn)] = vol.In(
                    mprn_options
                )

        return self.async_show_form(
            step_id="meters",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    def _create_entry(self) -> FlowResult:
        """Create the config entry with collected data.

        Uses selected meters if available from async_step_meters(),
        otherwise falls back to primary meters.

        Returns:
            ConfigFlowResult for entry creation.
        """
        if self._account is None or self._api_key is None:
            # This should not happen in normal flow
            return self.async_abort(reason="unknown")

        # Use selected meters if available, otherwise fall back to primary
        mpan = self._selected_mpan
        meter_serial = self._selected_meter_serial
        mprn = self._selected_mprn
        gas_meter_serial = self._selected_gas_meter_serial

        # Fallback to primary if no selection was made
        if mpan is None and self._account.primary_electricity:
            mpan = self._account.primary_electricity.mpan
            meter_serial = self._account.primary_electricity.meter_serial

        if mprn is None and self._account.primary_gas:
            mprn = self._account.primary_gas.mprn
            gas_meter_serial = self._account.primary_gas.meter_serial

        data: dict[str, Any] = {
            CONF_API_KEY: self._api_key,
            CONF_ACCOUNT: self._account.account_number,
        }

        # Add electricity meter data if available
        if mpan is not None and meter_serial is not None:
            data[CONF_MPAN] = mpan
            data[CONF_METER_SERIAL] = meter_serial

        # Add gas meter data if available
        if mprn is not None and gas_meter_serial is not None:
            data[CONF_MPRN] = mprn
            data[CONF_GAS_METER_SERIAL] = gas_meter_serial

        # Use account number as entry title
        title = self._account.account_number

        return self.async_create_entry(
            title=title,
            data=data,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OctohaOptionsFlow:
        """Create the options flow handler.

        Args:
            config_entry: The config entry to configure options for.

        Returns:
            Options flow handler instance.
        """
        return OctohaOptionsFlow(config_entry)


class OctohaOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Octoha.

    Allows users to reconfigure update intervals for:
    - Electricity consumption
    - Gas consumption
    - Tariff rates
    - Dispatch schedules
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow.

        Args:
            config_entry: The config entry being configured.
        """
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the options flow initial step.

        Args:
            user_input: User input from the form, or None on initial load.

        Returns:
            FlowResult indicating completion or form display.
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values or defaults
        options = self._config_entry.options

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ELECTRICITY_INTERVAL,
                    default=options.get(
                        CONF_ELECTRICITY_INTERVAL, DEFAULT_ELECTRICITY_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                vol.Optional(
                    CONF_GAS_INTERVAL,
                    default=options.get(CONF_GAS_INTERVAL, DEFAULT_GAS_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                vol.Optional(
                    CONF_TARIFF_INTERVAL,
                    default=options.get(CONF_TARIFF_INTERVAL, DEFAULT_TARIFF_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=300, max=7200)),
                vol.Optional(
                    CONF_DISPATCH_INTERVAL,
                    default=options.get(
                        CONF_DISPATCH_INTERVAL, DEFAULT_DISPATCH_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
