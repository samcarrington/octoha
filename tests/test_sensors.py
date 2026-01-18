"""Tests for Octoha sensors."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.octoha.const import ATTRIBUTION, DOMAIN
from custom_components.octoha.coordinator import (
    ElectricityCoordinator,
    ElectricityData,
    GasCoordinator,
    GasData,
    TariffCoordinator,
    TariffData,
    DispatchCoordinator,
)
from custom_components.octoha.models.consumption import Consumption, DailyUsage, GasConsumption
from custom_components.octoha.models.tariff import CurrentRate, GasTariff, Tariff, TariffType
from custom_components.octoha.models.dispatch import Dispatch, DispatchSource, DispatchStatus
from custom_components.octoha.sensor import (
    OctohaSensorEntity,
    ElectricityConsumptionSensor,
    ElectricityDailyUsageSensor,
    ElectricityRateSensor,
    GasConsumptionSensor,
    GasDailyUsageSensor,
    GasRateSensor,
    NextDispatchSensor,
    async_setup_entry,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "api_key": "sk_test_key",
        "account": "A-FB05ED6C",
        "mpan": "1234567890123",
        "mprn": "1234567890",
        "meter_serial": "20P1234567",
        "gas_meter_serial": "G4P12345678",
    }
    return entry


@pytest.fixture
def sample_consumption():
    """Create sample electricity consumption data."""
    return [
        Consumption(
            interval_start=datetime(2026, 1, 18, 0, 0, tzinfo=timezone.utc),
            interval_end=datetime(2026, 1, 18, 0, 30, tzinfo=timezone.utc),
            consumption=0.5,
        ),
        Consumption(
            interval_start=datetime(2026, 1, 18, 0, 30, tzinfo=timezone.utc),
            interval_end=datetime(2026, 1, 18, 1, 0, tzinfo=timezone.utc),
            consumption=0.75,
        ),
    ]


@pytest.fixture
def sample_gas_consumption():
    """Create sample gas consumption data."""
    return [
        GasConsumption(
            interval_start=datetime(2026, 1, 18, 0, 0, tzinfo=timezone.utc),
            interval_end=datetime(2026, 1, 18, 0, 30, tzinfo=timezone.utc),
            consumption=0.3,
            consumption_m3=0.028,
        ),
        GasConsumption(
            interval_start=datetime(2026, 1, 18, 0, 30, tzinfo=timezone.utc),
            interval_end=datetime(2026, 1, 18, 1, 0, tzinfo=timezone.utc),
            consumption=0.4,
            consumption_m3=0.037,
        ),
    ]


@pytest.fixture
def sample_daily_usage():
    """Create sample daily usage data."""
    return [
        DailyUsage(date="2026-01-17", electricity_kwh=8.5, gas_kwh=12.0),
        DailyUsage(date="2026-01-18", electricity_kwh=7.2, gas_kwh=10.5),
    ]


@pytest.fixture
def sample_tariff():
    """Create sample electricity tariff."""
    return Tariff(
        product_code="INTELLI-VAR-22-10-14",
        display_name="Intelligent Octopus Go",
        standing_charge=35.0,
        tariff_type=TariffType.TIME_OF_USE,
        off_peak_rate=7.5,
        peak_rate=24.5,
    )


@pytest.fixture
def sample_gas_tariff():
    """Create sample gas tariff."""
    return GasTariff(
        product_code="VAR-22-10-14",
        display_name="Flexible Octopus",
        standing_charge=28.0,
        unit_rate=6.5,
    )


@pytest.fixture
def sample_current_rate():
    """Create sample current rate."""
    return CurrentRate(
        rate=7.5,
        is_off_peak=True,
        period_end=datetime(2026, 1, 18, 5, 30, tzinfo=timezone.utc),
        next_rate=24.5,
    )


@pytest.fixture
def sample_dispatch():
    """Create sample dispatch."""
    return Dispatch(
        start=datetime(2026, 1, 18, 1, 0, tzinfo=timezone.utc),
        end=datetime(2026, 1, 18, 5, 0, tzinfo=timezone.utc),
        source=DispatchSource.SMART_CHARGE,
    )


@pytest.fixture
def sample_dispatch_status(sample_dispatch):
    """Create sample dispatch status."""
    return DispatchStatus(
        is_dispatching=False,
        current_dispatch=None,
        next_dispatch=sample_dispatch,
        planned_dispatches=[sample_dispatch],
    )


@pytest.fixture
def mock_electricity_coordinator(sample_consumption, sample_daily_usage):
    """Create mock electricity coordinator."""
    coordinator = MagicMock(spec=ElectricityCoordinator)
    coordinator.data = ElectricityData(
        consumption=sample_consumption,
        daily_usage=sample_daily_usage,
    )
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_gas_coordinator(sample_gas_consumption, sample_daily_usage):
    """Create mock gas coordinator."""
    coordinator = MagicMock(spec=GasCoordinator)
    coordinator.data = GasData(
        consumption=sample_gas_consumption,
        daily_usage=sample_daily_usage,
    )
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_tariff_coordinator(sample_tariff, sample_gas_tariff, sample_current_rate):
    """Create mock tariff coordinator."""
    coordinator = MagicMock(spec=TariffCoordinator)
    coordinator.data = TariffData(
        electricity_tariff=sample_tariff,
        gas_tariff=sample_gas_tariff,
        current_rate=sample_current_rate,
    )
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_dispatch_coordinator(sample_dispatch_status):
    """Create mock dispatch coordinator."""
    coordinator = MagicMock(spec=DispatchCoordinator)
    coordinator.data = sample_dispatch_status
    coordinator.last_update_success = True
    return coordinator


# ============================================================================
# Base Entity Tests
# ============================================================================


class TestOctohaSensorEntityBase:
    """Tests for OctohaSensorEntity base class."""

    def test_attribution(self, mock_electricity_coordinator, mock_config_entry):
        """Test that attribution is set correctly."""
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        assert sensor.attribution == ATTRIBUTION

    def test_unique_id_format(self, mock_electricity_coordinator, mock_config_entry):
        """Test unique ID includes entry_id and sensor type."""
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        assert "test_entry_id" in sensor.unique_id
        assert "electricity_consumption" in sensor.unique_id

    def test_device_info(self, mock_electricity_coordinator, mock_config_entry):
        """Test device info groups sensors by account."""
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        device_info = sensor.device_info
        assert device_info is not None
        assert DOMAIN in str(device_info["identifiers"])

    def test_available_when_coordinator_has_data(
        self, mock_electricity_coordinator, mock_config_entry
    ):
        """Test sensor is available when coordinator has data."""
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        assert sensor.available is True

    def test_unavailable_when_coordinator_failed(
        self, mock_electricity_coordinator, mock_config_entry
    ):
        """Test sensor is still available with cached data when coordinator update failed.

        Sensors remain available during outages to show cached data.
        Only unavailable when there is no data at all.
        """
        mock_electricity_coordinator.last_update_success = False
        # Sensor has data (from previous successful update)
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        # Should still be available because data exists
        assert sensor.available is True

    def test_unavailable_when_no_data(
        self, mock_electricity_coordinator, mock_config_entry
    ):
        """Test sensor is unavailable when there is no data."""
        mock_electricity_coordinator.last_update_success = False
        mock_electricity_coordinator.data = None  # No data at all
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        assert sensor.available is False


# ============================================================================
# Electricity Consumption Sensor Tests
# ============================================================================


class TestElectricityConsumptionSensor:
    """Tests for ElectricityConsumptionSensor."""

    def test_native_value_returns_latest_consumption(
        self, mock_electricity_coordinator, mock_config_entry
    ):
        """Test native_value returns the most recent consumption reading."""
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        # Latest reading is 0.75 kWh
        assert sensor.native_value == 0.75

    def test_native_value_none_when_no_data(
        self, mock_electricity_coordinator, mock_config_entry
    ):
        """Test native_value is None when no consumption data."""
        mock_electricity_coordinator.data = ElectricityData(
            consumption=[],
            daily_usage=[],
        )
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        assert sensor.native_value is None

    def test_unit_of_measurement(self, mock_electricity_coordinator, mock_config_entry):
        """Test unit of measurement is kWh."""
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        assert sensor.native_unit_of_measurement == "kWh"

    def test_device_class(self, mock_electricity_coordinator, mock_config_entry):
        """Test device class is energy."""
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        from homeassistant.components.sensor import SensorDeviceClass
        assert sensor.device_class == SensorDeviceClass.ENERGY

    def test_state_class_measurement(self, mock_electricity_coordinator, mock_config_entry):
        """Test state class is measurement for consumption."""
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        from homeassistant.components.sensor import SensorStateClass
        assert sensor.state_class == SensorStateClass.MEASUREMENT

    def test_extra_state_attributes(self, mock_electricity_coordinator, mock_config_entry):
        """Test extra state attributes include MPAN and timestamp."""
        sensor = ElectricityConsumptionSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        attrs = sensor.extra_state_attributes
        assert attrs["mpan"] == "1234567890123"
        assert "last_reading_start" in attrs
        assert "last_reading_end" in attrs


# ============================================================================
# Electricity Daily Usage Sensor Tests
# ============================================================================


class TestElectricityDailyUsageSensor:
    """Tests for ElectricityDailyUsageSensor."""

    def test_native_value_returns_today_usage(
        self, mock_electricity_coordinator, mock_config_entry
    ):
        """Test native_value returns today's usage."""
        with patch("custom_components.octoha.sensor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 18, 12, 0, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            sensor = ElectricityDailyUsageSensor(
                coordinator=mock_electricity_coordinator,
                entry=mock_config_entry,
                mpan="1234567890123",
            )
            # Today (2026-01-18) usage is 7.2 kWh
            assert sensor.native_value == 7.2

    def test_native_value_none_when_no_today_data(
        self, mock_electricity_coordinator, mock_config_entry
    ):
        """Test native_value is None when no data for today."""
        mock_electricity_coordinator.data = ElectricityData(
            consumption=[],
            daily_usage=[DailyUsage(date="2026-01-17", electricity_kwh=8.5)],
        )
        with patch("custom_components.octoha.sensor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 18, 12, 0, tzinfo=timezone.utc)
            sensor = ElectricityDailyUsageSensor(
                coordinator=mock_electricity_coordinator,
                entry=mock_config_entry,
                mpan="1234567890123",
            )
            assert sensor.native_value is None

    def test_state_class_total_increasing(
        self, mock_electricity_coordinator, mock_config_entry
    ):
        """Test state class is total_increasing for daily usage."""
        sensor = ElectricityDailyUsageSensor(
            coordinator=mock_electricity_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        from homeassistant.components.sensor import SensorStateClass
        assert sensor.state_class == SensorStateClass.TOTAL_INCREASING


# ============================================================================
# Electricity Rate Sensor Tests
# ============================================================================


class TestElectricityRateSensor:
    """Tests for ElectricityRateSensor."""

    def test_native_value_returns_current_rate(
        self, mock_tariff_coordinator, mock_config_entry
    ):
        """Test native_value returns current electricity rate."""
        sensor = ElectricityRateSensor(
            coordinator=mock_tariff_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        # Current rate is 7.5 pence/kWh
        assert sensor.native_value == 7.5

    def test_native_value_none_when_no_rate(
        self, mock_tariff_coordinator, mock_config_entry
    ):
        """Test native_value is None when no current rate."""
        mock_tariff_coordinator.data = TariffData(
            electricity_tariff=None,
            gas_tariff=None,
            current_rate=None,
        )
        sensor = ElectricityRateSensor(
            coordinator=mock_tariff_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        assert sensor.native_value is None

    def test_unit_of_measurement_pence_per_kwh(
        self, mock_tariff_coordinator, mock_config_entry
    ):
        """Test unit is p/kWh."""
        sensor = ElectricityRateSensor(
            coordinator=mock_tariff_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        assert sensor.native_unit_of_measurement == "p/kWh"

    def test_device_class_monetary(self, mock_tariff_coordinator, mock_config_entry):
        """Test device class is monetary."""
        sensor = ElectricityRateSensor(
            coordinator=mock_tariff_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        from homeassistant.components.sensor import SensorDeviceClass
        assert sensor.device_class == SensorDeviceClass.MONETARY

    def test_extra_state_attributes_include_off_peak(
        self, mock_tariff_coordinator, mock_config_entry
    ):
        """Test extra attributes include off_peak status."""
        sensor = ElectricityRateSensor(
            coordinator=mock_tariff_coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )
        attrs = sensor.extra_state_attributes
        assert attrs["is_off_peak"] is True
        assert "period_end" in attrs
        assert "next_rate" in attrs
        assert attrs["next_rate"] == 24.5


# ============================================================================
# Gas Consumption Sensor Tests
# ============================================================================


class TestGasConsumptionSensor:
    """Tests for GasConsumptionSensor."""

    def test_native_value_returns_latest_consumption(
        self, mock_gas_coordinator, mock_config_entry
    ):
        """Test native_value returns the most recent gas consumption."""
        sensor = GasConsumptionSensor(
            coordinator=mock_gas_coordinator,
            entry=mock_config_entry,
            mprn="1234567890",
        )
        # Latest reading is 0.4 kWh
        assert sensor.native_value == 0.4

    def test_extra_state_attributes_include_m3(
        self, mock_gas_coordinator, mock_config_entry
    ):
        """Test extra attributes include m3 value."""
        sensor = GasConsumptionSensor(
            coordinator=mock_gas_coordinator,
            entry=mock_config_entry,
            mprn="1234567890",
        )
        attrs = sensor.extra_state_attributes
        assert attrs["mprn"] == "1234567890"
        assert attrs["consumption_m3"] == 0.037


# ============================================================================
# Gas Daily Usage Sensor Tests
# ============================================================================


class TestGasDailyUsageSensor:
    """Tests for GasDailyUsageSensor."""

    def test_native_value_returns_today_usage(
        self, mock_gas_coordinator, mock_config_entry
    ):
        """Test native_value returns today's gas usage."""
        with patch("custom_components.octoha.sensor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 18, 12, 0, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            sensor = GasDailyUsageSensor(
                coordinator=mock_gas_coordinator,
                entry=mock_config_entry,
                mprn="1234567890",
            )
            # Today (2026-01-18) gas usage is 10.5 kWh
            assert sensor.native_value == 10.5


# ============================================================================
# Gas Rate Sensor Tests
# ============================================================================


class TestGasRateSensor:
    """Tests for GasRateSensor."""

    def test_native_value_returns_gas_rate(
        self, mock_tariff_coordinator, mock_config_entry
    ):
        """Test native_value returns gas unit rate."""
        sensor = GasRateSensor(
            coordinator=mock_tariff_coordinator,
            entry=mock_config_entry,
            mprn="1234567890",
        )
        # Gas rate is 6.5 pence/kWh
        assert sensor.native_value == 6.5

    def test_extra_state_attributes_include_standing_charge(
        self, mock_tariff_coordinator, mock_config_entry
    ):
        """Test extra attributes include standing charge."""
        sensor = GasRateSensor(
            coordinator=mock_tariff_coordinator,
            entry=mock_config_entry,
            mprn="1234567890",
        )
        attrs = sensor.extra_state_attributes
        assert attrs["standing_charge"] == 28.0
        assert attrs["tariff_name"] == "Flexible Octopus"


# ============================================================================
# Dispatch Sensor Tests
# ============================================================================


class TestNextDispatchSensor:
    """Tests for NextDispatchSensor."""

    def test_native_value_returns_next_dispatch_start(
        self, mock_dispatch_coordinator, mock_config_entry
    ):
        """Test native_value returns next dispatch start time."""
        sensor = NextDispatchSensor(
            coordinator=mock_dispatch_coordinator,
            entry=mock_config_entry,
        )
        expected = datetime(2026, 1, 18, 1, 0, tzinfo=timezone.utc)
        assert sensor.native_value == expected

    def test_native_value_none_when_no_dispatches(
        self, mock_dispatch_coordinator, mock_config_entry
    ):
        """Test native_value is None when no upcoming dispatches."""
        mock_dispatch_coordinator.data = DispatchStatus(
            is_dispatching=False,
            current_dispatch=None,
            next_dispatch=None,
            planned_dispatches=[],
        )
        sensor = NextDispatchSensor(
            coordinator=mock_dispatch_coordinator,
            entry=mock_config_entry,
        )
        assert sensor.native_value is None

    def test_device_class_timestamp(self, mock_dispatch_coordinator, mock_config_entry):
        """Test device class is timestamp."""
        sensor = NextDispatchSensor(
            coordinator=mock_dispatch_coordinator,
            entry=mock_config_entry,
        )
        from homeassistant.components.sensor import SensorDeviceClass
        assert sensor.device_class == SensorDeviceClass.TIMESTAMP

    def test_extra_state_attributes(
        self, mock_dispatch_coordinator, mock_config_entry, sample_dispatch
    ):
        """Test extra attributes include dispatch details."""
        sensor = NextDispatchSensor(
            coordinator=mock_dispatch_coordinator,
            entry=mock_config_entry,
        )
        attrs = sensor.extra_state_attributes
        assert "dispatch_end" in attrs
        assert attrs["dispatch_source"] == "smart-charge"
        assert "duration_minutes" in attrs
        assert attrs["duration_minutes"] == 240  # 4 hours


# ============================================================================
# async_setup_entry Tests
# ============================================================================


class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_setup_creates_sensors_for_electricity(
        self, mock_hass, mock_config_entry, mock_electricity_coordinator, mock_tariff_coordinator
    ):
        """Test setup creates electricity sensors when data available."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock(
            electricity_coordinator=mock_electricity_coordinator,
            gas_coordinator=None,
            tariff_coordinator=mock_tariff_coordinator,
            dispatch_coordinator=None,
        )

        entities = []

        def mock_add_entities(new_entities, update_before_add=False):
            entities.extend(new_entities)

        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        # Should have electricity consumption, daily usage, and rate sensors
        assert len(entities) >= 3
        entity_types = [type(e).__name__ for e in entities]
        assert "ElectricityConsumptionSensor" in entity_types
        assert "ElectricityDailyUsageSensor" in entity_types
        assert "ElectricityRateSensor" in entity_types

    @pytest.mark.asyncio
    async def test_setup_creates_sensors_for_gas(
        self, mock_hass, mock_config_entry, mock_gas_coordinator, mock_tariff_coordinator
    ):
        """Test setup creates gas sensors when data available."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock(
            electricity_coordinator=None,
            gas_coordinator=mock_gas_coordinator,
            tariff_coordinator=mock_tariff_coordinator,
            dispatch_coordinator=None,
        )

        entities = []

        def mock_add_entities(new_entities, update_before_add=False):
            entities.extend(new_entities)

        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        entity_types = [type(e).__name__ for e in entities]
        assert "GasConsumptionSensor" in entity_types
        assert "GasDailyUsageSensor" in entity_types
        assert "GasRateSensor" in entity_types

    @pytest.mark.asyncio
    async def test_setup_creates_dispatch_sensor_when_coordinator_exists(
        self, mock_hass, mock_config_entry, mock_dispatch_coordinator
    ):
        """Test setup creates dispatch sensor when coordinator exists."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock(
            electricity_coordinator=None,
            gas_coordinator=None,
            tariff_coordinator=None,
            dispatch_coordinator=mock_dispatch_coordinator,
        )

        entities = []

        def mock_add_entities(new_entities, update_before_add=False):
            entities.extend(new_entities)

        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        entity_types = [type(e).__name__ for e in entities]
        assert "NextDispatchSensor" in entity_types
