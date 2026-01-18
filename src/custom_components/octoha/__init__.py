"""Octoha - Home Assistant integration for Octopus Energy.

This integration provides accurate gas and electricity consumption data
from Octopus Energy's APIs, replacing broken Bright/SMETS integration.

For more information, see:
https://github.com/samcarrington/octoha
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.client import OctohaApiClient
from .api.exceptions import AuthenticationError, OctopusError
from .const import CONF_ACCOUNT, CONF_API_KEY, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


@dataclass
class OctohaRuntimeData:
    """Runtime data for the Octoha integration.

    Stores the API client and any other runtime data needed by platforms.
    """

    client: OctohaApiClient


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
        await client.get_account()
    except OctopusError as err:
        _LOGGER.error("Failed to fetch account data: %s", err)
        raise ConfigEntryNotReady("Cannot fetch account data") from err

    # Store runtime data
    entry.runtime_data = OctohaRuntimeData(client=client)

    # Also store in hass.data for backwards compatibility
    hass.data[DOMAIN][entry.entry_id] = entry.runtime_data

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
        # Clean up API client
        if entry.runtime_data:
            await entry.runtime_data.client.close()

        # Remove from hass.data
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


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
