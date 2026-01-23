"""Octoha - Home Assistant integration for Octopus Energy.

This integration provides accurate gas and electricity consumption data
from Octopus Energy's APIs, replacing broken Bright/SMETS integration.

For more information, see:
https://github.com/samcarrington/octoha
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.client import OctohaApiClient
from .api.exceptions import AuthenticationError, OctopusError
from .const import (
    CONF_ACCOUNT,
    CONF_API_KEY,
    CONF_DISPATCH_INTERVAL,
    CONF_ELECTRICITY_INTERVAL,
    CONF_GAS_INTERVAL,
    CONF_MPAN,
    CONF_MPRN,
    CONF_TARIFF_INTERVAL,
    DEFAULT_DISPATCH_INTERVAL,
    DEFAULT_ELECTRICITY_INTERVAL,
    DEFAULT_GAS_INTERVAL,
    DEFAULT_TARIFF_INTERVAL,
    DOMAIN,
)
from .coordinator import (
    DispatchCoordinator,
    ElectricityCoordinator,
    GasCoordinator,
    TariffCoordinator,
)
from .events import async_setup_events

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


def _log_refresh_errors(results: list[BaseException | None]) -> int:
    """Log any errors from coordinator refresh tasks.

    Args:
        results: List of results from asyncio.gather with return_exceptions=True.

    Returns:
        Number of failed tasks.
    """
    failure_count = 0
    for result in results:
        if isinstance(result, BaseException):
            failure_count += 1
            _LOGGER.error(
                "Coordinator initial refresh failed: %s: %s",
                type(result).__name__,
                result,
            )
    return failure_count


def _check_critical_failures(
    results: list[BaseException | None],
    tariff_idx: int,
    failure_count: int,
) -> None:
    """Check for critical coordinator failures and raise if setup should fail.

    Args:
        results: List of results from asyncio.gather with return_exceptions=True.
        tariff_idx: Index of the tariff coordinator result (required coordinator).
        failure_count: Total number of failed coordinators.

    Raises:
        ConfigEntryNotReady: If a critical coordinator failed or all failed.
    """
    # Check if the required tariff coordinator failed
    if isinstance(results[tariff_idx], BaseException):
        raise ConfigEntryNotReady(
            "Tariff coordinator failed to initialize"
        ) from results[tariff_idx]

    # If all coordinators failed, the integration is broken
    if failure_count == len(results):
        raise ConfigEntryNotReady("All coordinators failed to initialize")


@dataclass
class OctohaRuntimeData:
    """Runtime data for the Octoha integration.

    Stores the API client and coordinators needed by platforms.
    """

    client: OctohaApiClient
    electricity_coordinator: ElectricityCoordinator | None = None
    gas_coordinator: GasCoordinator | None = None
    tariff_coordinator: TariffCoordinator | None = None
    dispatch_coordinator: DispatchCoordinator | None = None
    event_unsubscribers: list[Callable[[], None]] = field(default_factory=list)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Octoha from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to set up.

    Returns:
        True if setup was successful.

    Raises:
        ConfigEntryAuthFailed: If authentication fails.
        ConfigEntryNotReady: If the integration cannot connect.
    """
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("Setting up Octoha integration for entry %s", entry.entry_id)

    # Get configuration from entry
    api_key = entry.data[CONF_API_KEY]
    account_number = entry.data.get(CONF_ACCOUNT)

    # Initialize API client
    session = async_get_clientsession(hass)
    client = OctohaApiClient(
        session=session,
        api_key=api_key,
        account_number=account_number,
    )

    # Validate credentials
    try:
        await client.validate_credentials()
    except AuthenticationError as err:
        _LOGGER.error("Authentication failed: %s", err)
        raise ConfigEntryAuthFailed("Invalid API key") from err
    except OctopusError as err:
        _LOGGER.error("Failed to connect to Octopus Energy API: %s", err)
        raise ConfigEntryNotReady("Cannot connect to Octopus Energy API") from err

    # Fetch account data to verify configuration
    try:
        account = await client.get_account()
    except OctopusError as err:
        _LOGGER.error("Failed to fetch account data: %s", err)
        raise ConfigEntryNotReady("Cannot fetch account data") from err

    # Determine which meters are configured
    mpan = entry.data.get(CONF_MPAN)
    mprn = entry.data.get(CONF_MPRN)

    # Read user-configured intervals from options (with defaults)
    elec_seconds = entry.options.get(
        CONF_ELECTRICITY_INTERVAL, DEFAULT_ELECTRICITY_INTERVAL
    )
    elec_interval = timedelta(seconds=elec_seconds)
    gas_interval = timedelta(
        seconds=entry.options.get(CONF_GAS_INTERVAL, DEFAULT_GAS_INTERVAL)
    )
    tariff_interval = timedelta(
        seconds=entry.options.get(CONF_TARIFF_INTERVAL, DEFAULT_TARIFF_INTERVAL)
    )
    dispatch_interval = timedelta(
        seconds=entry.options.get(CONF_DISPATCH_INTERVAL, DEFAULT_DISPATCH_INTERVAL)
    )

    # Create coordinators based on available meters
    electricity_coordinator = None
    gas_coordinator = None
    tariff_coordinator = None
    dispatch_coordinator = None

    # Electricity coordinator (if MPAN configured)
    if mpan:
        electricity_coordinator = ElectricityCoordinator(
            hass, client, update_interval=elec_interval
        )
        _LOGGER.debug("Created electricity coordinator for MPAN %s", mpan)

    # Gas coordinator (if MPRN configured)
    if mprn:
        gas_coordinator = GasCoordinator(hass, client, update_interval=gas_interval)
        _LOGGER.debug("Created gas coordinator for MPRN %s", mprn)

    # Tariff coordinator (always create for rate info)
    tariff_coordinator = TariffCoordinator(
        hass, client, update_interval=tariff_interval
    )
    _LOGGER.debug("Created tariff coordinator")

    # Dispatch coordinator (only for Intelligent tariffs)
    if account and account.primary_electricity:
        agreements = account.primary_electricity.agreements
        if agreements and any("INTELLI" in a.tariff_code.upper() for a in agreements):
            dispatch_coordinator = DispatchCoordinator(
                hass, client, update_interval=dispatch_interval
            )
            _LOGGER.debug("Created dispatch coordinator for Intelligent tariff")

    # Perform initial data refresh concurrently for all coordinators
    # Track tariff coordinator index since it's always required
    refresh_tasks = []
    tariff_idx = -1
    if electricity_coordinator:
        refresh_tasks.append(electricity_coordinator.async_config_entry_first_refresh())
    if gas_coordinator:
        refresh_tasks.append(gas_coordinator.async_config_entry_first_refresh())
    tariff_idx = len(refresh_tasks)
    refresh_tasks.append(tariff_coordinator.async_config_entry_first_refresh())
    if dispatch_coordinator:
        refresh_tasks.append(dispatch_coordinator.async_config_entry_first_refresh())

    if refresh_tasks:
        results = await asyncio.gather(*refresh_tasks, return_exceptions=True)
        task_count = len(refresh_tasks)
        failure_count = _log_refresh_errors(results)
        _LOGGER.debug("Completed initial refresh for %d coordinators", task_count)
        _check_critical_failures(results, tariff_idx, failure_count)

    # Store runtime data
    runtime_data = OctohaRuntimeData(
        client=client,
        electricity_coordinator=electricity_coordinator,
        gas_coordinator=gas_coordinator,
        tariff_coordinator=tariff_coordinator,
        dispatch_coordinator=dispatch_coordinator,
    )
    entry.runtime_data = runtime_data

    # Also store in hass.data for platforms to access
    hass.data[DOMAIN][entry.entry_id] = runtime_data

    # Set up event managers for automation triggers
    event_unsubscribers = async_setup_events(hass, entry, runtime_data)
    runtime_data.event_unsubscribers = event_unsubscribers

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update.

    Args:
        hass: Home Assistant instance.
        entry: Config entry with updated options.
    """
    _LOGGER.debug("Options updated for entry %s, reloading", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to unload.

    Returns:
        True if unload was successful.
    """
    _LOGGER.debug("Unloading Octoha integration for entry %s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up event listeners
        if entry.runtime_data and entry.runtime_data.event_unsubscribers:
            for unsub in entry.runtime_data.event_unsubscribers:
                unsub()
            listener_count = len(entry.runtime_data.event_unsubscribers)
            _LOGGER.debug("Cleaned up %d event listeners", listener_count)

        # Clean up API client
        if entry.runtime_data:
            await entry.runtime_data.client.close()

        # Remove from hass.data
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return bool(unload_ok)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry to new version.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to migrate.

    Returns:
        True if migration was successful.
    """
    _LOGGER.debug(
        "Migrating Octoha config entry from version %s.%s",
        entry.version,
        entry.minor_version,
    )

    # No migrations needed yet
    return True
