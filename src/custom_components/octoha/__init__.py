"""Octoha - Home Assistant integration for Octopus Energy.

This integration provides accurate gas and electricity consumption data
from Octopus Energy's APIs, replacing broken Bright/SMETS integration.

For more information, see:
https://github.com/samcarrington/octoha
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


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

    # TODO: Initialize API client
    # TODO: Validate credentials
    # TODO: Create coordinators
    # TODO: Store runtime data

    _LOGGER.debug("Setting up Octoha integration for entry %s", entry.entry_id)

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


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
