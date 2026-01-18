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
    CONF_API_KEY,
    CONF_ACCOUNT,
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


class OctohaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
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

                    # Fetch account data to discover meters
                    self._account = await self._client.get_account()

                    # Check if already configured
                    await self.async_set_unique_id(self._account.account_number)
                    self._abort_if_unique_id_configured()

                    # Check for available meters
                    elec_meter = self._account.primary_electricity
                    gas_meter = self._account.primary_gas

                    if elec_meter is None and gas_meter is None:
                        # No meters found
                        errors["base"] = "no_meters"
                    elif elec_meter is not None and gas_meter is not None:
                        # Multiple meter types - show meter selection step
                        return await self.async_step_meters()
                    else:
                        # Single meter type - create entry directly
                        return self._create_entry()

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

        This step is shown when the account has multiple meter types
        (electricity and gas) and allows the user to select which
        meters to monitor.

        Args:
            user_input: User input from the form, or None on initial load.

        Returns:
            ConfigFlowResult indicating next step or entry creation.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # User selected meters, create entry
            return self._create_entry()

        # Build schema based on available meters
        schema_dict: dict[Any, Any] = {}

        if self._account is not None:
            elec_meter = self._account.primary_electricity
            gas_meter = self._account.primary_gas

            if elec_meter is not None:
                schema_dict[vol.Optional(CONF_MPAN, default=elec_meter.mpan)] = str

            if gas_meter is not None:
                schema_dict[vol.Optional(CONF_MPRN, default=gas_meter.mprn)] = str

        return self.async_show_form(
            step_id="meters",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    def _create_entry(self) -> FlowResult:
        """Create the config entry with collected data.

        Returns:
            ConfigFlowResult for entry creation.
        """
        if self._account is None or self._api_key is None:
            # This should not happen in normal flow
            return self.async_abort(reason="unknown")

        elec_meter = self._account.primary_electricity
        gas_meter = self._account.primary_gas

        data: dict[str, Any] = {
            CONF_API_KEY: self._api_key,
            CONF_ACCOUNT: self._account.account_number,
        }

        # Add electricity meter data if available
        if elec_meter is not None:
            data[CONF_MPAN] = elec_meter.mpan
            data[CONF_METER_SERIAL] = elec_meter.meter_serial

        # Add gas meter data if available
        if gas_meter is not None:
            data[CONF_MPRN] = gas_meter.mprn
            data[CONF_GAS_METER_SERIAL] = gas_meter.meter_serial

        # Format title as "Octoha (account_number)"
        title = f"Octoha ({self._account.account_number})"

        return self.async_create_entry(
            title=title,
            data=data,
        )

    @staticmethod
    @config_entries.HANDLERS.register(DOMAIN)
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
