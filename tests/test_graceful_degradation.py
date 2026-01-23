"""Tests for coordinator graceful degradation on API outages.

These tests verify that coordinators properly handle API failures by:
- Retaining cached data on failure
- Tracking failure counts and timestamps
- Recovering gracefully when API returns
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.octoha.api.client import OctohaApiClient
from custom_components.octoha.api.exceptions import OctopusError
from custom_components.octoha.coordinator import (
    ElectricityCoordinator,
    GasCoordinator,
    TariffCoordinator,
)
from custom_components.octoha.models.consumption import Consumption, DailyUsage

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_api_client() -> AsyncMock:
    """Create a mock OctohaApiClient."""
    return AsyncMock(spec=OctohaApiClient)


@pytest.fixture
def sample_consumption() -> list[Consumption]:
    """Create sample electricity consumption data."""
    now = datetime.now(UTC)
    return [
        Consumption(
            interval_start=now - timedelta(hours=1),
            interval_end=now - timedelta(minutes=30),
            consumption=1.5,
        ),
    ]


@pytest.fixture
def sample_daily_usage() -> list[DailyUsage]:
    """Create sample daily usage data."""
    return [DailyUsage(date="2026-01-18", electricity_kwh=8.5)]


# ============================================================================
# Test: Data Retention on Failure
# ============================================================================


class TestDataRetentionOnFailure:
    """Test that coordinators retain data when API calls fail."""

    @pytest.mark.asyncio
    async def test_coordinator_retains_last_data_on_failure(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_consumption: list[Consumption],
        sample_daily_usage: list[DailyUsage],
    ) -> None:
        """Test that data is retained when update fails after successful fetch."""
        # First call succeeds
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption
        )
        mock_api_client.get_daily_usage = AsyncMock(return_value=sample_daily_usage)

        coordinator = ElectricityCoordinator(hass, mock_api_client)

        # Perform initial successful fetch (use async_refresh, not
        # async_config_entry_first_refresh which requires a config entry)
        await coordinator.async_refresh()
        assert coordinator.data is not None
        assert coordinator.last_update_success is True
        initial_data = coordinator.data

        # Now make API fail
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=OctopusError("API unavailable")
        )

        # Trigger update (should fail but retain data)
        await coordinator.async_refresh()

        # Data should still be available
        assert coordinator.data == initial_data
        assert coordinator.last_update_success is False

    @pytest.mark.asyncio
    async def test_coordinator_tracks_consecutive_failures(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_consumption: list[Consumption],
        sample_daily_usage: list[DailyUsage],
    ) -> None:
        """Test that coordinator tracks number of consecutive failures."""
        # First call succeeds
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption
        )
        mock_api_client.get_daily_usage = AsyncMock(return_value=sample_daily_usage)

        coordinator = ElectricityCoordinator(hass, mock_api_client)
        await coordinator.async_refresh()

        assert coordinator.consecutive_failures == 0

        # Now make API fail multiple times
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=OctopusError("API unavailable")
        )

        await coordinator.async_refresh()
        assert coordinator.consecutive_failures == 1

        await coordinator.async_refresh()
        assert coordinator.consecutive_failures == 2

    @pytest.mark.asyncio
    async def test_coordinator_resets_failure_count_on_success(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_consumption: list[Consumption],
        sample_daily_usage: list[DailyUsage],
    ) -> None:
        """Test that consecutive failure count resets on successful update."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption
        )
        mock_api_client.get_daily_usage = AsyncMock(return_value=sample_daily_usage)

        coordinator = ElectricityCoordinator(hass, mock_api_client)
        await coordinator.async_refresh()

        # Make it fail
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=OctopusError("API unavailable")
        )
        await coordinator.async_refresh()
        await coordinator.async_refresh()
        assert coordinator.consecutive_failures == 2

        # Make it succeed again
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption
        )
        await coordinator.async_refresh()

        assert coordinator.consecutive_failures == 0
        assert coordinator.last_update_success is True


# ============================================================================
# Test: Failure Timestamp Tracking
# ============================================================================


class TestFailureTimestampTracking:
    """Test that coordinators track when failures started."""

    @pytest.mark.asyncio
    async def test_coordinator_tracks_first_failure_time(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_consumption: list[Consumption],
        sample_daily_usage: list[DailyUsage],
    ) -> None:
        """Test that coordinator records when failures started."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption
        )
        mock_api_client.get_daily_usage = AsyncMock(return_value=sample_daily_usage)

        coordinator = ElectricityCoordinator(hass, mock_api_client)
        await coordinator.async_refresh()

        assert coordinator.first_failure_time is None

        # Make it fail
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=OctopusError("API unavailable")
        )
        await coordinator.async_refresh()

        assert coordinator.first_failure_time is not None
        first_failure = coordinator.first_failure_time

        # Second failure should not update the timestamp
        await coordinator.async_refresh()
        assert coordinator.first_failure_time == first_failure

    @pytest.mark.asyncio
    async def test_coordinator_clears_first_failure_time_on_success(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_consumption: list[Consumption],
        sample_daily_usage: list[DailyUsage],
    ) -> None:
        """Test that first failure time clears on successful update."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption
        )
        mock_api_client.get_daily_usage = AsyncMock(return_value=sample_daily_usage)

        coordinator = ElectricityCoordinator(hass, mock_api_client)
        await coordinator.async_refresh()

        # Make it fail
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=OctopusError("API unavailable")
        )
        await coordinator.async_refresh()
        assert coordinator.first_failure_time is not None

        # Make it succeed
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption
        )
        await coordinator.async_refresh()
        assert coordinator.first_failure_time is None


# ============================================================================
# Test: Data Staleness Detection
# ============================================================================


class TestDataStalenessDetection:
    """Test that coordinators can indicate data staleness."""

    @pytest.mark.asyncio
    async def test_coordinator_reports_data_age(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_consumption: list[Consumption],
        sample_daily_usage: list[DailyUsage],
    ) -> None:
        """Test that coordinator can report how old the data is."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption
        )
        mock_api_client.get_daily_usage = AsyncMock(return_value=sample_daily_usage)

        coordinator = ElectricityCoordinator(hass, mock_api_client)
        await coordinator.async_refresh()

        # Data should be fresh (age close to 0)
        assert coordinator.data_age_seconds is not None
        assert coordinator.data_age_seconds < 5  # Should be very fresh

    @pytest.mark.asyncio
    async def test_coordinator_is_data_stale_property(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_consumption: list[Consumption],
        sample_daily_usage: list[DailyUsage],
    ) -> None:
        """Test that coordinator has is_data_stale property."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption
        )
        mock_api_client.get_daily_usage = AsyncMock(return_value=sample_daily_usage)

        coordinator = ElectricityCoordinator(hass, mock_api_client)
        await coordinator.async_refresh()

        # Data should not be stale immediately after fetch
        assert coordinator.is_data_stale is False


# ============================================================================
# Test: Recovery Behavior
# ============================================================================


class TestRecoveryBehavior:
    """Test coordinator recovery after API outages."""

    @pytest.mark.asyncio
    async def test_coordinator_recovers_after_multiple_failures(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_consumption: list[Consumption],
        sample_daily_usage: list[DailyUsage],
    ) -> None:
        """Test that coordinator properly recovers after multiple failures."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption
        )
        mock_api_client.get_daily_usage = AsyncMock(return_value=sample_daily_usage)

        coordinator = ElectricityCoordinator(hass, mock_api_client)
        await coordinator.async_refresh()

        # Simulate outage
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=OctopusError("API down")
        )
        for _ in range(5):
            await coordinator.async_refresh()

        assert coordinator.consecutive_failures == 5
        assert coordinator.last_update_success is False

        # Recovery
        new_consumption = [
            Consumption(
                interval_start=datetime.now(UTC) - timedelta(minutes=30),
                interval_end=datetime.now(UTC),
                consumption=2.0,
            )
        ]
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=new_consumption
        )

        await coordinator.async_refresh()

        assert coordinator.last_update_success is True
        assert coordinator.consecutive_failures == 0
        assert coordinator.first_failure_time is None
        assert coordinator.data.consumption == new_consumption


# ============================================================================
# Test: All Coordinator Types
# ============================================================================


class TestAllCoordinatorTypes:
    """Ensure all coordinator types support graceful degradation."""

    @pytest.mark.asyncio
    async def test_gas_coordinator_has_failure_tracking(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that GasCoordinator has failure tracking attributes."""
        coordinator = GasCoordinator(hass, mock_api_client)

        assert hasattr(coordinator, "consecutive_failures")
        assert hasattr(coordinator, "first_failure_time")
        assert hasattr(coordinator, "data_age_seconds")
        assert hasattr(coordinator, "is_data_stale")

    @pytest.mark.asyncio
    async def test_tariff_coordinator_has_failure_tracking(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that TariffCoordinator has failure tracking attributes."""
        coordinator = TariffCoordinator(hass, mock_api_client)

        assert hasattr(coordinator, "consecutive_failures")
        assert hasattr(coordinator, "first_failure_time")
        assert hasattr(coordinator, "data_age_seconds")
        assert hasattr(coordinator, "is_data_stale")
