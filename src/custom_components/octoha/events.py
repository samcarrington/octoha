"""Event management for Octoha integration.

Fires Home Assistant events when:
- Off-peak periods start or end (for time-of-use tariffs)
- Intelligent dispatches start or end
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .const import (
    DOMAIN,
    EVENT_DISPATCH_END,
    EVENT_DISPATCH_START,
    EVENT_OFF_PEAK_END,
    EVENT_OFF_PEAK_START,
)
from .coordinator import TariffData
from .models.dispatch import DispatchStatus

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from . import OctohaRuntimeData

_LOGGER = logging.getLogger(__name__)


def async_setup_events(
    hass: HomeAssistant,
    entry: ConfigEntry,
    runtime_data: OctohaRuntimeData,
) -> list[Callable[[], None]]:
    """Set up event managers for the integration.

    Args:
        hass: Home Assistant instance.
        entry: Config entry.
        runtime_data: Runtime data containing coordinators.

    Returns:
        List of unsubscribe callables to clean up listeners on unload.
    """
    unsubscribers: list[Callable[[], None]] = []

    # Set up off-peak event manager if tariff coordinator exists
    if hasattr(runtime_data, "tariff_coordinator") and runtime_data.tariff_coordinator:
        off_peak_manager = OffPeakEventManager(hass, entry)
        unsub = runtime_data.tariff_coordinator.async_add_listener(
            off_peak_manager._on_coordinator_update
        )
        unsubscribers.append(unsub)
        _LOGGER.debug("Set up off-peak event manager")

    # Set up dispatch event manager if dispatch coordinator exists
    if (
        hasattr(runtime_data, "dispatch_coordinator")
        and runtime_data.dispatch_coordinator
    ):
        dispatch_manager = DispatchEventManager(hass, entry)
        unsub = runtime_data.dispatch_coordinator.async_add_listener(
            dispatch_manager._on_coordinator_update
        )
        unsubscribers.append(unsub)
        _LOGGER.debug("Set up dispatch event manager")

    return unsubscribers


class OffPeakEventManager:
    """Manages off-peak start/end event firing.

    Listens to tariff coordinator updates and fires events when
    the off-peak status transitions.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the off-peak event manager.

        Args:
            hass: Home Assistant instance.
            entry: Config entry.
        """
        self._hass = hass
        self._entry = entry
        self._last_off_peak_state: bool | None = None

    def _on_coordinator_update(self) -> None:
        """Handle coordinator data update.

        Called by the coordinator when new data is available.
        """
        # Get data from the coordinator via hass.data
        runtime_data = self._hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        if runtime_data and runtime_data.tariff_coordinator:
            self.check_and_fire(runtime_data.tariff_coordinator.data)

    def check_and_fire(self, tariff_data: TariffData | None) -> None:
        """Check for off-peak state change and fire events.

        Args:
            tariff_data: Current tariff data from coordinator.
        """
        if not tariff_data or not tariff_data.current_rate:
            return

        current_off_peak = tariff_data.current_rate.is_off_peak

        # On first update, just record the state without firing
        if self._last_off_peak_state is None:
            self._last_off_peak_state = current_off_peak
            _LOGGER.debug("Initial off-peak state: %s", current_off_peak)
            return

        # Check for state transition
        if current_off_peak != self._last_off_peak_state:
            event_data = self._build_event_data(tariff_data)

            if current_off_peak:
                # Transitioned to off-peak
                _LOGGER.info("Off-peak period started, firing event")
                self._hass.bus.async_fire(EVENT_OFF_PEAK_START, event_data)
            else:
                # Transitioned from off-peak
                _LOGGER.info("Off-peak period ended, firing event")
                self._hass.bus.async_fire(EVENT_OFF_PEAK_END, event_data)

            self._last_off_peak_state = current_off_peak

    def _build_event_data(self, tariff_data: TariffData) -> dict[str, Any]:
        """Build event data payload.

        Args:
            tariff_data: Current tariff data.

        Returns:
            Event data dictionary.
        """
        data: dict[str, Any] = {
            "entry_id": self._entry.entry_id,
            "account": self._entry.data.get("account"),
        }

        if tariff_data.current_rate:
            data["rate"] = tariff_data.current_rate.rate
            data["is_off_peak"] = tariff_data.current_rate.is_off_peak
            data["period_end"] = tariff_data.current_rate.period_end.isoformat()
            if tariff_data.current_rate.next_rate is not None:
                data["next_rate"] = tariff_data.current_rate.next_rate

        if tariff_data.electricity_tariff:
            data["tariff_name"] = tariff_data.electricity_tariff.display_name
            data["tariff_code"] = tariff_data.electricity_tariff.product_code

        return data


class DispatchEventManager:
    """Manages dispatch start/end event firing.

    Listens to dispatch coordinator updates and fires events when
    dispatch status transitions.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the dispatch event manager.

        Args:
            hass: Home Assistant instance.
            entry: Config entry.
        """
        self._hass = hass
        self._entry = entry
        self._last_dispatch_state: bool | None = None

    def _on_coordinator_update(self) -> None:
        """Handle coordinator data update.

        Called by the coordinator when new data is available.
        """
        # Get data from the coordinator via hass.data
        runtime_data = self._hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        if runtime_data and runtime_data.dispatch_coordinator:
            self.check_and_fire(runtime_data.dispatch_coordinator.data)

    def check_and_fire(self, dispatch_status: DispatchStatus | None) -> None:
        """Check for dispatch state change and fire events.

        Args:
            dispatch_status: Current dispatch status from coordinator.
        """
        if not dispatch_status:
            return

        current_dispatching = dispatch_status.is_dispatching

        # On first update, just record the state without firing
        if self._last_dispatch_state is None:
            self._last_dispatch_state = current_dispatching
            _LOGGER.debug("Initial dispatch state: %s", current_dispatching)
            return

        # Check for state transition
        if current_dispatching != self._last_dispatch_state:
            event_data = self._build_event_data(dispatch_status)

            if current_dispatching:
                # Dispatch started
                _LOGGER.info("Dispatch started, firing event")
                self._hass.bus.async_fire(EVENT_DISPATCH_START, event_data)
            else:
                # Dispatch ended
                _LOGGER.info("Dispatch ended, firing event")
                self._hass.bus.async_fire(EVENT_DISPATCH_END, event_data)

            self._last_dispatch_state = current_dispatching

    def _build_event_data(self, dispatch_status: DispatchStatus) -> dict[str, Any]:
        """Build event data payload.

        Args:
            dispatch_status: Current dispatch status.

        Returns:
            Event data dictionary.
        """
        data: dict[str, Any] = {
            "entry_id": self._entry.entry_id,
            "account": self._entry.data.get("account"),
            "is_dispatching": dispatch_status.is_dispatching,
        }

        if dispatch_status.current_dispatch:
            dispatch = dispatch_status.current_dispatch
            data["dispatch_start"] = dispatch.start.isoformat()
            data["dispatch_end"] = dispatch.end.isoformat()
            data["source"] = dispatch.source.value
            data["duration_minutes"] = dispatch.duration_minutes

        return data
