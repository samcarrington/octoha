"""Diagnostics support for Octoha integration.

Provides sanitized debug data export for troubleshooting, ensuring
sensitive information like API keys and meter identifiers are redacted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .const import DOMAIN, VERSION

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


# Keys that contain sensitive data requiring redaction
SENSITIVE_KEYS = frozenset({"api_key", "token", "password", "secret"})
PARTIAL_REDACT_KEYS = frozenset({"mpan", "mprn", "meter_serial", "gas_meter_serial"})


def redact_api_key(api_key: str | None) -> str | None:
    """Redact an API key, keeping only the prefix visible.

    Args:
        api_key: The API key to redact.

    Returns:
        Redacted API key with only prefix visible, or None if input is None.

    Examples:
        >>> redact_api_key("sk_live_abc123def456")
        'sk_live_***REDACTED***'
        >>> redact_api_key("short")
        '***REDACTED***'
        >>> redact_api_key(None)
        None
    """
    if api_key is None:
        return None

    # If key starts with standard prefix, preserve it
    if api_key.startswith("sk_live_") and len(api_key) > 8:
        return "sk_live_***REDACTED***"

    # Short keys or non-standard format - fully redact
    return "***REDACTED***"


def _partial_redact(value: str, visible_chars: int = 4) -> str:
    """Partially redact a string, showing only the last N characters.

    Args:
        value: The string to redact.
        visible_chars: Number of characters to show at the end.

    Returns:
        Redacted string with only last N characters visible.
    """
    if len(value) <= visible_chars:
        return "****"
    return "****" + value[-visible_chars:]


def redact_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact sensitive data from a dictionary.

    Args:
        data: Dictionary potentially containing sensitive data.

    Returns:
        New dictionary with sensitive values redacted.
    """
    result: dict[str, Any] = {}

    for key, value in data.items():
        if isinstance(value, dict):
            # Recursively redact nested dictionaries
            result[key] = redact_sensitive_data(value)
        elif key in SENSITIVE_KEYS:
            # Fully redact sensitive keys
            if isinstance(value, str):
                result[key] = redact_api_key(value)
            else:
                result[key] = "***REDACTED***"
        elif key in PARTIAL_REDACT_KEYS:
            # Partially redact meter identifiers
            result[key] = _partial_redact(value) if isinstance(value, str) else value
        else:
            result[key] = value

    return result


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to get diagnostics for.

    Returns:
        Dictionary containing sanitized diagnostic data.
    """
    # Check if runtime data exists
    runtime_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    if runtime_data is None:
        return {
            "error": "Runtime data not found for this config entry",
            "config_entry": {
                "entry_id": entry.entry_id,
                "version": entry.version,
            },
        }

    # Build coordinator status
    coordinators: dict[str, Any] = {}

    if runtime_data.electricity_coordinator:
        coord = runtime_data.electricity_coordinator
        coordinators["electricity"] = {
            "available": coord.last_update_success,
            "last_update": (
                coord.last_update_success_time.isoformat()
                if hasattr(coord, "last_update_success_time")
                and coord.last_update_success_time
                else None
            ),
        }

    if runtime_data.gas_coordinator:
        coord = runtime_data.gas_coordinator
        coordinators["gas"] = {
            "available": coord.last_update_success,
            "last_update": (
                coord.last_update_success_time.isoformat()
                if hasattr(coord, "last_update_success_time")
                and coord.last_update_success_time
                else None
            ),
        }

    if runtime_data.tariff_coordinator:
        coord = runtime_data.tariff_coordinator
        coordinators["tariff"] = {
            "available": coord.last_update_success,
        }

    if runtime_data.dispatch_coordinator:
        coord = runtime_data.dispatch_coordinator
        coordinators["dispatch"] = {
            "available": coord.last_update_success,
        }

    # Build data summary (counts only, not raw data)
    data_summary: dict[str, Any] = {}

    elec_coord = runtime_data.electricity_coordinator
    if elec_coord and elec_coord.data:
        elec_data = elec_coord.data
        consumption_count = len(elec_data.consumption) if elec_data.consumption else 0
        daily_count = len(elec_data.daily_usage) if elec_data.daily_usage else 0
        data_summary["electricity"] = {
            "consumption_count": consumption_count,
            "daily_usage_count": daily_count,
        }

    gas_coord = runtime_data.gas_coordinator
    if gas_coord and gas_coord.data:
        gas_data = gas_coord.data
        consumption_count = len(gas_data.consumption) if gas_data.consumption else 0
        daily_count = len(gas_data.daily_usage) if gas_data.daily_usage else 0
        data_summary["gas"] = {
            "consumption_count": consumption_count,
            "daily_usage_count": daily_count,
        }

    tariff_coord = runtime_data.tariff_coordinator
    if tariff_coord and tariff_coord.data:
        tariff_data = tariff_coord.data
        current_rate = tariff_data.current_rate
        data_summary["tariff"] = {
            "name": (
                tariff_data.electricity_tariff.display_name
                if tariff_data.electricity_tariff
                else None
            ),
            "current_rate": current_rate.rate if current_rate else None,
            "is_off_peak": current_rate.is_off_peak if current_rate else None,
        }

    return {
        "integration": {
            "version": VERSION,
            "domain": DOMAIN,
        },
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "minor_version": getattr(entry, "minor_version", 0),
            "data": redact_sensitive_data(dict(entry.data)),
            "options": dict(entry.options),
        },
        "coordinators": coordinators,
        "data": data_summary,
    }
