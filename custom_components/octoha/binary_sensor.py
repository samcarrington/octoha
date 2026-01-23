"""Binary sensor platform for Octoha integration.

Provides binary sensors for:
- Off-peak rate detection (for time-of-use tariffs)
- Intelligent dispatch active status
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypeVar

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import (
    DispatchCoordinator,
    TariffCoordinator,
    TariffData,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Octoha binary sensors from config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry.
        async_add_entities: Callback to add entities.
    """
    runtime_data = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = []

    # Get meter identifier for electricity sensors
    mpan = entry.data.get("mpan")

    # Off-peak sensor (requires tariff coordinator and MPAN)
    tariff_coord = getattr(runtime_data, "tariff_coordinator", None)
    if tariff_coord and mpan:
        entities.append(OffPeakBinarySensor(tariff_coord, entry, mpan))

    # Dispatch active sensor (requires dispatch coordinator)
    if (
        hasattr(runtime_data, "dispatch_coordinator")
        and runtime_data.dispatch_coordinator
    ):
        entities.append(
            DispatchActiveBinarySensor(runtime_data.dispatch_coordinator, entry)
        )

    async_add_entities(entities, update_before_add=False)


class OctohaBinarySensorEntity(CoordinatorEntity[T], BinarySensorEntity):
    """Base class for Octoha binary sensors.

    Provides common functionality for all Octoha binary sensors including:
    - Device info grouping by account
    - Attribution
    - Availability based on coordinator status
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: T,
        entry: ConfigEntry,
        sensor_type: str,
        name: str,
        meter_id: str | None = None,
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: Data coordinator.
            entry: Config entry.
            sensor_type: Unique sensor type identifier.
            name: Human-readable sensor name.
            meter_id: Stable meter identifier (MPAN/MPRN/account) for unique ID.
        """
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type
        self._attr_name = name
        # Use stable meter ID for unique_id when available, fallback to entry_id
        stable_id = meter_id if meter_id else entry.entry_id
        self._attr_unique_id = f"{stable_id}_{sensor_type}"

    @property
    def attribution(self) -> str:
        """Return attribution."""
        return ATTRIBUTION

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to group sensors by account."""
        account = self._entry.data.get("account", "unknown")
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Octopus Energy {account}",
            manufacturer="Octopus Energy",
            model="Smart Meter",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self.coordinator.last_update_success)


class OffPeakBinarySensor(OctohaBinarySensorEntity[TariffCoordinator]):
    """Binary sensor for off-peak rate detection.

    Returns ON when the current electricity rate is off-peak,
    useful for automating appliances during cheap rate periods.
    """

    _attr_device_class = BinarySensorDeviceClass.POWER

    def __init__(
        self,
        coordinator: TariffCoordinator,
        entry: ConfigEntry,
        mpan: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Tariff coordinator.
            entry: Config entry.
            mpan: Meter Point Administration Number.
        """
        super().__init__(
            coordinator=coordinator,
            entry=entry,
            sensor_type="off_peak",
            name="Off-Peak Rate",
            meter_id=mpan,
        )
        self._mpan = mpan

    @property
    def is_on(self) -> bool:
        """Return True if currently in off-peak period."""
        data: TariffData = self.coordinator.data
        if not data or not data.current_rate:
            return False
        return data.current_rate.is_off_peak

    @property
    def icon(self) -> str:
        """Return icon based on off-peak status."""
        return "mdi:flash" if self.is_on else "mdi:flash-off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {"mpan": self._mpan}
        data: TariffData = self.coordinator.data
        if data and data.current_rate:
            attrs["current_rate"] = data.current_rate.rate
            attrs["period_end"] = data.current_rate.period_end.isoformat()
            attrs["next_rate"] = data.current_rate.next_rate
        if data and data.electricity_tariff:
            attrs["tariff_name"] = data.electricity_tariff.display_name
            attrs["is_intelligent"] = data.electricity_tariff.is_intelligent
        return attrs


class DispatchActiveBinarySensor(OctohaBinarySensorEntity[DispatchCoordinator]):
    """Binary sensor for Intelligent Octopus dispatch status.

    Returns ON when a smart charge dispatch is currently active,
    useful for automating around Intelligent charging sessions.
    """

    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(
        self,
        coordinator: DispatchCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Dispatch coordinator.
            entry: Config entry.
        """
        super().__init__(
            coordinator=coordinator,
            entry=entry,
            sensor_type="dispatch_active",
            name="Dispatch Active",
            meter_id=entry.data.get("account"),
        )

    @property
    def is_on(self) -> bool:
        """Return True if a dispatch is currently active."""
        data = self.coordinator.data
        if not data:
            return False
        return bool(data.is_dispatching)

    @property
    def icon(self) -> str:
        """Return icon based on dispatch status."""
        return "mdi:battery-charging" if self.is_on else "mdi:battery"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {}
        data = self.coordinator.data
        if data and data.current_dispatch:
            dispatch = data.current_dispatch
            attrs["dispatch_start"] = dispatch.start.isoformat()
            attrs["dispatch_end"] = dispatch.end.isoformat()
            attrs["dispatch_source"] = dispatch.source.value
            attrs["duration_minutes"] = dispatch.duration_minutes
        return attrs
