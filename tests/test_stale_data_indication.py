"""Tests for stale data indication in entity states.

These tests verify that entities properly indicate when their data
is stale due to API outages or update failures.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.octoha.const import DOMAIN
from custom_components.octoha.coordinator import (
    ElectricityCoordinator,
    ElectricityData,
    TariffCoordinator,
    TariffData,
)
from custom_components.octoha.models.consumption import Consumption, DailyUsage
from custom_components.octoha.models.tariff import CurrentRate, Tariff, TariffType
from custom_components.octoha.sensor import (
    ElectricityConsumptionSensor,
    ElectricityDailyUsageSensor,
    ElectricityRateSensor,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {
        "api_key": "sk_live_test",
        "account": "A-12345678",
        "mpan": "1234567890123",
    }
    return entry


@pytest.fixture
def sample_electricity_data() -> ElectricityData:
    """Create sample electricity data."""
    now = datetime.now(timezone.utc)
    return ElectricityData(
        consumption=[
            Consumption(
                interval_start=now - timedelta(hours=1),
                interval_end=now - timedelta(minutes=30),
                consumption=1.5,
            ),
        ],
        daily_usage=[DailyUsage(date="2026-01-18", electricity_kwh=8.5)],
    )


@pytest.fixture
def sample_tariff_data() -> TariffData:
    """Create sample tariff data."""
    return TariffData(
        electricity_tariff=Tariff(
            product_code="AGILE-24-04-03",
            display_name="Agile Octopus",
            standing_charge=47.18,
            tariff_type=TariffType.AGILE,
        ),
        gas_tariff=None,
        current_rate=CurrentRate(
            rate=15.5,
            is_off_peak=False,
            period_end=datetime.now(timezone.utc) + timedelta(minutes=30),
        ),
    )


# ============================================================================
# Test: Stale Data Attributes
# ============================================================================


class TestStaleDataAttributes:
    """Test that entities expose stale data information in attributes."""

    def test_sensor_includes_data_age_in_attributes(
        self,
        mock_config_entry,
        sample_electricity_data: ElectricityData,
    ) -> None:
        """Test that sensor includes data_age_seconds in extra attributes."""
        coordinator = MagicMock(spec=ElectricityCoordinator)
        coordinator.data = sample_electricity_data
        coordinator.last_update_success = True
        coordinator.data_age_seconds = 120.0
        coordinator.is_data_stale = False

        sensor = ElectricityConsumptionSensor(
            coordinator=coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )

        attrs = sensor.extra_state_attributes
        assert "data_age_seconds" in attrs
        assert attrs["data_age_seconds"] == 120.0

    def test_sensor_includes_is_stale_in_attributes(
        self,
        mock_config_entry,
        sample_electricity_data: ElectricityData,
    ) -> None:
        """Test that sensor includes is_stale in extra attributes."""
        coordinator = MagicMock(spec=ElectricityCoordinator)
        coordinator.data = sample_electricity_data
        coordinator.last_update_success = True
        coordinator.data_age_seconds = 120.0
        coordinator.is_data_stale = False

        sensor = ElectricityConsumptionSensor(
            coordinator=coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )

        attrs = sensor.extra_state_attributes
        assert "is_stale" in attrs
        assert attrs["is_stale"] is False

    def test_sensor_shows_stale_when_data_is_old(
        self,
        mock_config_entry,
        sample_electricity_data: ElectricityData,
    ) -> None:
        """Test that sensor shows is_stale=True when data is old."""
        coordinator = MagicMock(spec=ElectricityCoordinator)
        coordinator.data = sample_electricity_data
        coordinator.last_update_success = False
        coordinator.data_age_seconds = 1200.0  # 20 minutes old
        coordinator.is_data_stale = True

        sensor = ElectricityConsumptionSensor(
            coordinator=coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )

        attrs = sensor.extra_state_attributes
        assert attrs["is_stale"] is True

    def test_sensor_includes_last_update_success(
        self,
        mock_config_entry,
        sample_electricity_data: ElectricityData,
    ) -> None:
        """Test that sensor includes last update success in attributes."""
        coordinator = MagicMock(spec=ElectricityCoordinator)
        coordinator.data = sample_electricity_data
        coordinator.last_update_success = False
        coordinator.data_age_seconds = 600.0
        coordinator.is_data_stale = True
        coordinator.consecutive_failures = 3

        sensor = ElectricityConsumptionSensor(
            coordinator=coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )

        attrs = sensor.extra_state_attributes
        assert "last_update_success" in attrs
        assert attrs["last_update_success"] is False


# ============================================================================
# Test: Availability During Outages
# ============================================================================


class TestAvailabilityDuringOutages:
    """Test entity availability behavior during API outages."""

    def test_sensor_still_available_with_stale_data(
        self,
        mock_config_entry,
        sample_electricity_data: ElectricityData,
    ) -> None:
        """Test that sensor remains available when data is stale but exists."""
        coordinator = MagicMock(spec=ElectricityCoordinator)
        coordinator.data = sample_electricity_data
        coordinator.last_update_success = False  # Last update failed
        coordinator.data_age_seconds = 600.0
        coordinator.is_data_stale = True

        sensor = ElectricityConsumptionSensor(
            coordinator=coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )

        # Sensor should still be available (shows cached data)
        assert sensor.available is True

    def test_sensor_unavailable_when_no_data_at_all(
        self,
        mock_config_entry,
    ) -> None:
        """Test that sensor is unavailable when there's no data."""
        coordinator = MagicMock(spec=ElectricityCoordinator)
        coordinator.data = None
        coordinator.last_update_success = False
        coordinator.data_age_seconds = None
        coordinator.is_data_stale = True

        sensor = ElectricityConsumptionSensor(
            coordinator=coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )

        # Sensor should be unavailable with no data
        assert sensor.available is False


# ============================================================================
# Test: Rate Sensor Stale Indication
# ============================================================================


class TestRateSensorStaleIndication:
    """Test stale indication for rate sensors."""

    def test_rate_sensor_includes_stale_attributes(
        self,
        mock_config_entry,
        sample_tariff_data: TariffData,
    ) -> None:
        """Test that rate sensor includes staleness attributes."""
        coordinator = MagicMock(spec=TariffCoordinator)
        coordinator.data = sample_tariff_data
        coordinator.last_update_success = True
        coordinator.data_age_seconds = 60.0
        coordinator.is_data_stale = False

        sensor = ElectricityRateSensor(
            coordinator=coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )

        attrs = sensor.extra_state_attributes
        assert "is_stale" in attrs
        assert "data_age_seconds" in attrs


# ============================================================================
# Test: Daily Usage Sensor
# ============================================================================


class TestDailyUsageSensorStaleIndication:
    """Test stale indication for daily usage sensors."""

    def test_daily_sensor_includes_stale_attributes(
        self,
        mock_config_entry,
        sample_electricity_data: ElectricityData,
    ) -> None:
        """Test that daily usage sensor includes staleness attributes."""
        coordinator = MagicMock(spec=ElectricityCoordinator)
        coordinator.data = sample_electricity_data
        coordinator.last_update_success = True
        coordinator.data_age_seconds = 300.0
        coordinator.is_data_stale = False

        sensor = ElectricityDailyUsageSensor(
            coordinator=coordinator,
            entry=mock_config_entry,
            mpan="1234567890123",
        )

        attrs = sensor.extra_state_attributes
        assert "is_stale" in attrs
        assert "data_age_seconds" in attrs
