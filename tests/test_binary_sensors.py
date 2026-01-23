"""Tests for Octoha binary sensors."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from custom_components.octoha.binary_sensor import (
    DispatchActiveBinarySensor,
    OffPeakBinarySensor,
    async_setup_entry,
)
from custom_components.octoha.const import DOMAIN
from custom_components.octoha.coordinator import (
    DispatchCoordinator,
    TariffCoordinator,
    TariffData,
)
from custom_components.octoha.models.dispatch import (
    Dispatch,
    DispatchSource,
    DispatchStatus,
)
from custom_components.octoha.models.tariff import CurrentRate, Tariff, TariffType

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
    }
    return entry


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
def sample_current_rate_off_peak():
    """Create sample current rate in off-peak period."""
    return CurrentRate(
        rate=7.5,
        is_off_peak=True,
        period_end=datetime(2026, 1, 18, 5, 30, tzinfo=UTC),
        next_rate=24.5,
    )


@pytest.fixture
def sample_current_rate_peak():
    """Create sample current rate in peak period."""
    return CurrentRate(
        rate=24.5,
        is_off_peak=False,
        period_end=datetime(2026, 1, 18, 23, 30, tzinfo=UTC),
        next_rate=7.5,
    )


@pytest.fixture
def sample_active_dispatch():
    """Create sample active dispatch."""
    return Dispatch(
        start=datetime(2026, 1, 18, 1, 0, tzinfo=UTC),
        end=datetime(2026, 1, 18, 5, 0, tzinfo=UTC),
        source=DispatchSource.SMART_CHARGE,
    )


@pytest.fixture
def mock_tariff_coordinator_off_peak(sample_tariff, sample_current_rate_off_peak):
    """Create mock tariff coordinator with off-peak rate."""
    coordinator = MagicMock(spec=TariffCoordinator)
    coordinator.data = TariffData(
        electricity_tariff=sample_tariff,
        gas_tariff=None,
        current_rate=sample_current_rate_off_peak,
    )
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_tariff_coordinator_peak(sample_tariff, sample_current_rate_peak):
    """Create mock tariff coordinator with peak rate."""
    coordinator = MagicMock(spec=TariffCoordinator)
    coordinator.data = TariffData(
        electricity_tariff=sample_tariff,
        gas_tariff=None,
        current_rate=sample_current_rate_peak,
    )
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_dispatch_coordinator_active(sample_active_dispatch):
    """Create mock dispatch coordinator with active dispatch."""
    coordinator = MagicMock(spec=DispatchCoordinator)
    coordinator.data = DispatchStatus(
        is_dispatching=True,
        current_dispatch=sample_active_dispatch,
        next_dispatch=None,
        planned_dispatches=[],
    )
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_dispatch_coordinator_inactive():
    """Create mock dispatch coordinator without active dispatch."""
    coordinator = MagicMock(spec=DispatchCoordinator)
    coordinator.data = DispatchStatus(
        is_dispatching=False,
        current_dispatch=None,
        next_dispatch=None,
        planned_dispatches=[],
    )
    coordinator.last_update_success = True
    return coordinator


# ============================================================================
# Off-Peak Binary Sensor Tests
# ============================================================================


class TestOffPeakBinarySensor:
    """Tests for OffPeakBinarySensor."""

    def test_is_on_during_off_peak(
        self, mock_tariff_coordinator_off_peak, mock_config_entry
    ):
        """Test sensor is ON during off-peak period."""
        sensor = OffPeakBinarySensor(
            coordinator=mock_tariff_coordinator_off_peak,
            entry=mock_config_entry,
        )
        assert sensor.is_on is True

    def test_is_off_during_peak(
        self, mock_tariff_coordinator_peak, mock_config_entry
    ):
        """Test sensor is OFF during peak period."""
        sensor = OffPeakBinarySensor(
            coordinator=mock_tariff_coordinator_peak,
            entry=mock_config_entry,
        )
        assert sensor.is_on is False

    def test_is_off_when_no_rate_data(
        self, mock_tariff_coordinator_peak, mock_config_entry
    ):
        """Test sensor is OFF when no rate data available."""
        mock_tariff_coordinator_peak.data = TariffData(
            electricity_tariff=None,
            gas_tariff=None,
            current_rate=None,
        )
        sensor = OffPeakBinarySensor(
            coordinator=mock_tariff_coordinator_peak,
            entry=mock_config_entry,
        )
        assert sensor.is_on is False

    def test_unique_id(self, mock_tariff_coordinator_off_peak, mock_config_entry):
        """Test unique ID format."""
        sensor = OffPeakBinarySensor(
            coordinator=mock_tariff_coordinator_off_peak,
            entry=mock_config_entry,
        )
        assert "test_entry_id" in sensor.unique_id
        assert "off_peak" in sensor.unique_id

    def test_extra_state_attributes(
        self, mock_tariff_coordinator_off_peak, mock_config_entry
    ):
        """Test extra state attributes include rate info."""
        sensor = OffPeakBinarySensor(
            coordinator=mock_tariff_coordinator_off_peak,
            entry=mock_config_entry,
        )
        attrs = sensor.extra_state_attributes
        assert attrs["current_rate"] == 7.5
        assert "period_end" in attrs
        assert attrs["next_rate"] == 24.5

    def test_icon_when_off_peak(
        self, mock_tariff_coordinator_off_peak, mock_config_entry
    ):
        """Test icon shows flash when off-peak."""
        sensor = OffPeakBinarySensor(
            coordinator=mock_tariff_coordinator_off_peak,
            entry=mock_config_entry,
        )
        assert sensor.icon == "mdi:flash"

    def test_icon_when_peak(
        self, mock_tariff_coordinator_peak, mock_config_entry
    ):
        """Test icon shows flash-off when peak."""
        sensor = OffPeakBinarySensor(
            coordinator=mock_tariff_coordinator_peak,
            entry=mock_config_entry,
        )
        assert sensor.icon == "mdi:flash-off"


# ============================================================================
# Dispatch Active Binary Sensor Tests
# ============================================================================


class TestDispatchActiveBinarySensor:
    """Tests for DispatchActiveBinarySensor."""

    def test_is_on_when_dispatch_active(
        self, mock_dispatch_coordinator_active, mock_config_entry
    ):
        """Test sensor is ON when dispatch is active."""
        sensor = DispatchActiveBinarySensor(
            coordinator=mock_dispatch_coordinator_active,
            entry=mock_config_entry,
        )
        assert sensor.is_on is True

    def test_is_off_when_no_dispatch(
        self, mock_dispatch_coordinator_inactive, mock_config_entry
    ):
        """Test sensor is OFF when no dispatch active."""
        sensor = DispatchActiveBinarySensor(
            coordinator=mock_dispatch_coordinator_inactive,
            entry=mock_config_entry,
        )
        assert sensor.is_on is False

    def test_unique_id(self, mock_dispatch_coordinator_active, mock_config_entry):
        """Test unique ID format."""
        sensor = DispatchActiveBinarySensor(
            coordinator=mock_dispatch_coordinator_active,
            entry=mock_config_entry,
        )
        assert "test_entry_id" in sensor.unique_id
        assert "dispatch_active" in sensor.unique_id

    def test_extra_state_attributes_when_active(
        self,
        mock_dispatch_coordinator_active,
        mock_config_entry,
        sample_active_dispatch,
    ):
        """Test extra state attributes when dispatch is active."""
        sensor = DispatchActiveBinarySensor(
            coordinator=mock_dispatch_coordinator_active,
            entry=mock_config_entry,
        )
        attrs = sensor.extra_state_attributes
        assert "dispatch_start" in attrs
        assert "dispatch_end" in attrs
        assert attrs["dispatch_source"] == "smart-charge"
        assert "duration_minutes" in attrs

    def test_extra_state_attributes_when_inactive(
        self, mock_dispatch_coordinator_inactive, mock_config_entry
    ):
        """Test extra state attributes when no dispatch."""
        sensor = DispatchActiveBinarySensor(
            coordinator=mock_dispatch_coordinator_inactive,
            entry=mock_config_entry,
        )
        attrs = sensor.extra_state_attributes
        assert attrs == {}

    def test_icon_when_dispatching(
        self, mock_dispatch_coordinator_active, mock_config_entry
    ):
        """Test icon shows battery-charging when dispatching."""
        sensor = DispatchActiveBinarySensor(
            coordinator=mock_dispatch_coordinator_active,
            entry=mock_config_entry,
        )
        assert sensor.icon == "mdi:battery-charging"

    def test_icon_when_not_dispatching(
        self, mock_dispatch_coordinator_inactive, mock_config_entry
    ):
        """Test icon shows battery when not dispatching."""
        sensor = DispatchActiveBinarySensor(
            coordinator=mock_dispatch_coordinator_inactive,
            entry=mock_config_entry,
        )
        assert sensor.icon == "mdi:battery"


# ============================================================================
# async_setup_entry Tests
# ============================================================================


class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_setup_creates_off_peak_sensor(
        self, mock_hass, mock_config_entry, mock_tariff_coordinator_off_peak
    ):
        """Test setup creates off-peak sensor when tariff coordinator exists."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock(
            tariff_coordinator=mock_tariff_coordinator_off_peak,
            dispatch_coordinator=None,
        )

        entities = []

        def mock_add_entities(new_entities, update_before_add=False):
            entities.extend(new_entities)

        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        entity_types = [type(e).__name__ for e in entities]
        assert "OffPeakBinarySensor" in entity_types

    @pytest.mark.asyncio
    async def test_setup_creates_dispatch_sensor(
        self, mock_hass, mock_config_entry, mock_dispatch_coordinator_active
    ):
        """Test setup creates dispatch sensor when dispatch coordinator exists."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock(
            tariff_coordinator=None,
            dispatch_coordinator=mock_dispatch_coordinator_active,
        )

        entities = []

        def mock_add_entities(new_entities, update_before_add=False):
            entities.extend(new_entities)

        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        entity_types = [type(e).__name__ for e in entities]
        assert "DispatchActiveBinarySensor" in entity_types

    @pytest.mark.asyncio
    async def test_setup_creates_both_sensors(
        self,
        mock_hass,
        mock_config_entry,
        mock_tariff_coordinator_off_peak,
        mock_dispatch_coordinator_active,
    ):
        """Test setup creates both sensors when both coordinators exist."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock(
            tariff_coordinator=mock_tariff_coordinator_off_peak,
            dispatch_coordinator=mock_dispatch_coordinator_active,
        )

        entities = []

        def mock_add_entities(new_entities, update_before_add=False):
            entities.extend(new_entities)

        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

        entity_types = [type(e).__name__ for e in entities]
        assert "OffPeakBinarySensor" in entity_types
        assert "DispatchActiveBinarySensor" in entity_types
        assert len(entities) == 2
