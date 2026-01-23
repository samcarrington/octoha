"""Sensor platform for Octoha integration.

Provides sensors for:
- Electricity consumption (current and daily)
- Gas consumption (current and daily)
- Electricity rate (with off-peak detection)
- Gas rate
- Intelligent dispatch information
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, TypeVar

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import (
    DispatchCoordinator,
    ElectricityCoordinator,
    ElectricityData,
    GasCoordinator,
    GasData,
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
    """Set up Octoha sensors from config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry.
        async_add_entities: Callback to add entities.
    """
    runtime_data = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    # Get meter identifiers from config entry
    mpan = entry.data.get("mpan")
    mprn = entry.data.get("mprn")

    # Electricity sensors
    if (
        hasattr(runtime_data, "electricity_coordinator")
        and runtime_data.electricity_coordinator
    ):
        coord = runtime_data.electricity_coordinator
        if mpan:
            entities.append(ElectricityConsumptionSensor(coord, entry, mpan))
            entities.append(ElectricityDailyUsageSensor(coord, entry, mpan))

    # Gas sensors
    if hasattr(runtime_data, "gas_coordinator") and runtime_data.gas_coordinator:
        coord = runtime_data.gas_coordinator
        if mprn:
            entities.append(GasConsumptionSensor(coord, entry, mprn))
            entities.append(GasDailyUsageSensor(coord, entry, mprn))

    # Tariff/Rate sensors
    if hasattr(runtime_data, "tariff_coordinator") and runtime_data.tariff_coordinator:
        coord = runtime_data.tariff_coordinator
        if mpan:
            entities.append(ElectricityRateSensor(coord, entry, mpan))
        if mprn:
            entities.append(GasRateSensor(coord, entry, mprn))

    # Dispatch sensors
    if (
        hasattr(runtime_data, "dispatch_coordinator")
        and runtime_data.dispatch_coordinator
    ):
        coord = runtime_data.dispatch_coordinator
        entities.append(NextDispatchSensor(coord, entry))

    async_add_entities(entities, update_before_add=True)


class OctohaSensorEntity(CoordinatorEntity[T], SensorEntity):
    """Base class for Octoha sensors.

    Provides common functionality for all Octoha sensors including:
    - Device info grouping by account
    - Attribution
    - Availability based on coordinator status and data presence
    - Staleness indication when data is outdated
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: T,
        entry: ConfigEntry,
        sensor_type: str,
        name: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Data coordinator.
            entry: Config entry.
            sensor_type: Unique sensor type identifier.
            name: Human-readable sensor name.
        """
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"

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
        """Return True if entity is available.

        Entity is available if it has data, even if the data is stale.
        This allows users to still see cached values during outages.
        """
        # Available if we have data, regardless of update success
        return self.coordinator.data is not None

    def _get_staleness_attributes(self) -> dict[str, Any]:
        """Return staleness-related attributes.

        Returns:
            Dictionary with staleness information.
        """
        attrs: dict[str, Any] = {}

        # Include update success status
        attrs["last_update_success"] = self.coordinator.last_update_success

        # Include data age if available
        if hasattr(self.coordinator, "data_age_seconds"):
            attrs["data_age_seconds"] = self.coordinator.data_age_seconds

        # Include staleness flag if available
        if hasattr(self.coordinator, "is_data_stale"):
            attrs["is_stale"] = self.coordinator.is_data_stale

        return attrs


# ============================================================================
# Electricity Sensors
# ============================================================================


class ElectricityConsumptionSensor(OctohaSensorEntity[ElectricityCoordinator]):
    """Sensor for current electricity consumption reading.

    Reports the most recent half-hourly consumption reading in kWh.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: ElectricityCoordinator,
        entry: ConfigEntry,
        mpan: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Electricity coordinator.
            entry: Config entry.
            mpan: Meter Point Administration Number.
        """
        super().__init__(
            coordinator=coordinator,
            entry=entry,
            sensor_type="electricity_consumption",
            name="Electricity Consumption",
        )
        self._mpan = mpan

    @property
    def native_value(self) -> float | None:
        """Return the most recent consumption reading."""
        data: ElectricityData = self.coordinator.data
        if not data or not data.consumption:
            return None
        # Return the latest (most recent) reading
        latest = data.consumption[-1]
        return latest.consumption

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {"mpan": self._mpan}
        attrs.update(self._get_staleness_attributes())
        data: ElectricityData = self.coordinator.data
        if data and data.consumption:
            latest = data.consumption[-1]
            attrs["last_reading_start"] = latest.interval_start.isoformat()
            attrs["last_reading_end"] = latest.interval_end.isoformat()
        return attrs


class ElectricityDailyUsageSensor(OctohaSensorEntity[ElectricityCoordinator]):
    """Sensor for today's total electricity usage.

    Reports the cumulative electricity consumption for today in kWh.
    Compatible with Home Assistant Energy Dashboard.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "kWh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: ElectricityCoordinator,
        entry: ConfigEntry,
        mpan: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Electricity coordinator.
            entry: Config entry.
            mpan: Meter Point Administration Number.
        """
        super().__init__(
            coordinator=coordinator,
            entry=entry,
            sensor_type="electricity_daily_usage",
            name="Electricity Daily Usage",
        )
        self._mpan = mpan

    @property
    def native_value(self) -> float | None:
        """Return today's total electricity usage."""
        data: ElectricityData = self.coordinator.data
        if not data or not data.daily_usage:
            return None

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        for usage in data.daily_usage:
            if usage.date == today:
                return usage.electricity_kwh
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {"mpan": self._mpan}
        attrs.update(self._get_staleness_attributes())
        return attrs


class ElectricityRateSensor(OctohaSensorEntity[TariffCoordinator]):
    """Sensor for current electricity rate.

    Reports the current electricity rate in p/kWh, including
    off-peak detection for time-of-use tariffs.
    """

    _attr_native_unit_of_measurement = "p/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:currency-gbp"

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
            sensor_type="electricity_rate",
            name="Electricity Rate",
        )
        self._mpan = mpan

    @property
    def native_value(self) -> float | None:
        """Return current electricity rate in p/kWh."""
        data: TariffData = self.coordinator.data
        if not data or not data.current_rate:
            return None
        return data.current_rate.rate

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {"mpan": self._mpan}
        attrs.update(self._get_staleness_attributes())
        data: TariffData = self.coordinator.data
        if data and data.current_rate:
            attrs["is_off_peak"] = data.current_rate.is_off_peak
            attrs["period_end"] = data.current_rate.period_end.isoformat()
            attrs["next_rate"] = data.current_rate.next_rate
        if data and data.electricity_tariff:
            attrs["tariff_name"] = data.electricity_tariff.display_name
            attrs["standing_charge"] = data.electricity_tariff.standing_charge
        return attrs


# ============================================================================
# Gas Sensors
# ============================================================================


class GasConsumptionSensor(OctohaSensorEntity[GasCoordinator]):
    """Sensor for current gas consumption reading.

    Reports the most recent half-hourly gas consumption reading in kWh.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: GasCoordinator,
        entry: ConfigEntry,
        mprn: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Gas coordinator.
            entry: Config entry.
            mprn: Meter Point Reference Number.
        """
        super().__init__(
            coordinator=coordinator,
            entry=entry,
            sensor_type="gas_consumption",
            name="Gas Consumption",
        )
        self._mprn = mprn

    @property
    def native_value(self) -> float | None:
        """Return the most recent gas consumption reading."""
        data: GasData = self.coordinator.data
        if not data or not data.consumption:
            return None
        latest = data.consumption[-1]
        return latest.consumption

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {"mprn": self._mprn}
        attrs.update(self._get_staleness_attributes())
        data: GasData = self.coordinator.data
        if data and data.consumption:
            latest = data.consumption[-1]
            attrs["last_reading_start"] = latest.interval_start.isoformat()
            attrs["last_reading_end"] = latest.interval_end.isoformat()
            if latest.consumption_m3 is not None:
                attrs["consumption_m3"] = latest.consumption_m3
        return attrs


class GasDailyUsageSensor(OctohaSensorEntity[GasCoordinator]):
    """Sensor for today's total gas usage.

    Reports the cumulative gas consumption for today in kWh.
    Compatible with Home Assistant Energy Dashboard.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "kWh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: GasCoordinator,
        entry: ConfigEntry,
        mprn: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Gas coordinator.
            entry: Config entry.
            mprn: Meter Point Reference Number.
        """
        super().__init__(
            coordinator=coordinator,
            entry=entry,
            sensor_type="gas_daily_usage",
            name="Gas Daily Usage",
        )
        self._mprn = mprn

    @property
    def native_value(self) -> float | None:
        """Return today's total gas usage."""
        data: GasData = self.coordinator.data
        if not data or not data.daily_usage:
            return None

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        for usage in data.daily_usage:
            if usage.date == today:
                return usage.gas_kwh
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {"mprn": self._mprn}
        attrs.update(self._get_staleness_attributes())
        return attrs


class GasRateSensor(OctohaSensorEntity[TariffCoordinator]):
    """Sensor for current gas rate.

    Reports the gas unit rate in p/kWh.
    """

    _attr_native_unit_of_measurement = "p/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:currency-gbp"

    def __init__(
        self,
        coordinator: TariffCoordinator,
        entry: ConfigEntry,
        mprn: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Tariff coordinator.
            entry: Config entry.
            mprn: Meter Point Reference Number.
        """
        super().__init__(
            coordinator=coordinator,
            entry=entry,
            sensor_type="gas_rate",
            name="Gas Rate",
        )
        self._mprn = mprn

    @property
    def native_value(self) -> float | None:
        """Return current gas rate in p/kWh."""
        data: TariffData = self.coordinator.data
        if not data or not data.gas_tariff:
            return None
        return data.gas_tariff.unit_rate

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {"mprn": self._mprn}
        attrs.update(self._get_staleness_attributes())
        data: TariffData = self.coordinator.data
        if data and data.gas_tariff:
            attrs["tariff_name"] = data.gas_tariff.display_name
            attrs["standing_charge"] = data.gas_tariff.standing_charge
        return attrs


# ============================================================================
# Dispatch Sensors
# ============================================================================


class NextDispatchSensor(OctohaSensorEntity[DispatchCoordinator]):
    """Sensor for next Intelligent Octopus dispatch.

    Reports the start time of the next scheduled dispatch.
    """

    _attr_device_class = SensorDeviceClass.TIMESTAMP

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
            sensor_type="next_dispatch",
            name="Next Dispatch",
        )

    @property
    def native_value(self) -> datetime | None:
        """Return start time of next dispatch."""
        data = self.coordinator.data
        if not data or not data.next_dispatch:
            return None
        # Cast to satisfy mypy - Dispatch.start is typed as datetime
        start: datetime = data.next_dispatch.start
        return start

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {}
        attrs.update(self._get_staleness_attributes())
        data = self.coordinator.data
        if data and data.next_dispatch:
            dispatch = data.next_dispatch
            attrs["dispatch_end"] = dispatch.end.isoformat()
            attrs["dispatch_source"] = dispatch.source.value
            attrs["duration_minutes"] = dispatch.duration_minutes
        return attrs
