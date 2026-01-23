"""Comprehensive test suite for Octoha data coordinators.

Tests the coordinator implementations that handle periodic data fetching from
the Octopus Energy API with proper error handling, update intervals, and
listener notifications.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from custom_components.octoha.api.client import OctohaApiClient
from custom_components.octoha.api.exceptions import (
    AuthenticationError,
    OctopusError,
)
from custom_components.octoha.const import (
    DOMAIN,
    UPDATE_INTERVAL_DISPATCH,
    UPDATE_INTERVAL_ELECTRICITY,
    UPDATE_INTERVAL_GAS,
    UPDATE_INTERVAL_TARIFF,
)
from custom_components.octoha.coordinator import (
    DispatchCoordinator,
    ElectricityCoordinator,
    ElectricityData,
    GasCoordinator,
    GasData,
    OctohaBaseCoordinator,
    TariffCoordinator,
    TariffData,
)
from custom_components.octoha.models.consumption import (
    Consumption,
    DailyUsage,
    GasConsumption,
)
from custom_components.octoha.models.dispatch import (
    Dispatch,
    DispatchSource,
    DispatchStatus,
)
from custom_components.octoha.models.tariff import (
    CurrentRate,
    GasTariff,
    Tariff,
    TariffType,
)


class TestOctohaBaseCoordinator:
    """Tests for the base OctohaBaseCoordinator class."""

    @pytest.fixture
    def mock_api_client(self) -> AsyncMock:
        """Create a mock OctohaApiClient."""
        return AsyncMock(spec=OctohaApiClient)

    def test_base_coordinator_extends_data_update_coordinator(self) -> None:
        """Test that OctohaBaseCoordinator extends DataUpdateCoordinator."""
        assert issubclass(OctohaBaseCoordinator, DataUpdateCoordinator)

    @pytest.mark.asyncio
    async def test_base_coordinator_has_client_attribute(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that base coordinator stores the API client."""
        coordinator = ElectricityCoordinator(hass, mock_api_client)
        assert coordinator.client is mock_api_client


class TestElectricityCoordinator:
    """Tests for ElectricityCoordinator - fetches electricity consumption."""

    @pytest.fixture
    def mock_api_client(self) -> AsyncMock:
        """Create a mock OctohaApiClient."""
        return AsyncMock(spec=OctohaApiClient)

    @pytest.fixture
    def sample_consumption_data(self) -> list[Consumption]:
        """Create sample electricity consumption data."""
        now = datetime.now(UTC)
        return [
            Consumption(
                interval_start=now - timedelta(hours=1),
                interval_end=now - timedelta(minutes=30),
                consumption=1.23,
            ),
            Consumption(
                interval_start=now - timedelta(minutes=30),
                interval_end=now,
                consumption=1.45,
            ),
        ]

    @pytest.fixture
    def sample_daily_usage(self) -> list[DailyUsage]:
        """Create sample daily usage data."""
        return [
            DailyUsage(date="2024-01-15", electricity_kwh=12.5, gas_kwh=25.0),
            DailyUsage(date="2024-01-14", electricity_kwh=11.8, gas_kwh=24.2),
        ]

    @pytest.mark.asyncio
    async def test_electricity_coordinator_successful_fetch(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_consumption_data: list[Consumption],
        sample_daily_usage: list[DailyUsage],
    ) -> None:
        """Test successful electricity consumption data fetch."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            return_value=sample_consumption_data
        )
        mock_api_client.get_daily_usage = AsyncMock(return_value=sample_daily_usage)

        coordinator = ElectricityCoordinator(hass, mock_api_client)
        data = await coordinator._async_update_data()

        assert isinstance(data, ElectricityData)
        assert data.consumption == sample_consumption_data
        assert data.daily_usage == sample_daily_usage

    @pytest.mark.asyncio
    async def test_electricity_coordinator_respects_update_interval(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that ElectricityCoordinator uses correct update interval."""
        coordinator = ElectricityCoordinator(hass, mock_api_client)
        assert coordinator.update_interval == UPDATE_INTERVAL_ELECTRICITY
        assert coordinator.update_interval == timedelta(seconds=300)

    @pytest.mark.asyncio
    async def test_electricity_coordinator_handles_api_failure(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that OctopusError is wrapped in UpdateFailed."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=OctopusError("API error")
        )

        coordinator = ElectricityCoordinator(hass, mock_api_client)

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "Error fetching electricity data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_electricity_coordinator_handles_auth_error(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that AuthenticationError is wrapped in UpdateFailed."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        coordinator = ElectricityCoordinator(hass, mock_api_client)

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_electricity_coordinator_has_descriptive_name(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that coordinator has a descriptive name."""
        coordinator = ElectricityCoordinator(hass, mock_api_client)
        assert DOMAIN in coordinator.name
        assert "electricity" in coordinator.name


class TestGasCoordinator:
    """Tests for GasCoordinator - fetches gas consumption."""

    @pytest.fixture
    def mock_api_client(self) -> AsyncMock:
        """Create a mock OctohaApiClient."""
        return AsyncMock(spec=OctohaApiClient)

    @pytest.fixture
    def sample_gas_consumption(self) -> list[GasConsumption]:
        """Create sample gas consumption data."""
        now = datetime.now(UTC)
        return [
            GasConsumption(
                interval_start=now - timedelta(hours=1),
                interval_end=now - timedelta(minutes=30),
                consumption=27.5,
                consumption_m3=2.5,
            ),
            GasConsumption(
                interval_start=now - timedelta(minutes=30),
                interval_end=now,
                consumption=30.8,
                consumption_m3=2.8,
            ),
        ]

    @pytest.fixture
    def sample_daily_usage(self) -> list[DailyUsage]:
        """Create sample daily usage data."""
        return [
            DailyUsage(date="2024-01-15", electricity_kwh=12.5, gas_kwh=25.0),
        ]

    @pytest.mark.asyncio
    async def test_gas_coordinator_successful_fetch(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_gas_consumption: list[GasConsumption],
        sample_daily_usage: list[DailyUsage],
    ) -> None:
        """Test successful gas consumption data fetch."""
        mock_api_client.get_gas_consumption = AsyncMock(
            return_value=sample_gas_consumption
        )
        mock_api_client.get_daily_usage = AsyncMock(return_value=sample_daily_usage)

        coordinator = GasCoordinator(hass, mock_api_client)
        data = await coordinator._async_update_data()

        assert isinstance(data, GasData)
        assert data.consumption == sample_gas_consumption
        assert data.daily_usage == sample_daily_usage

    @pytest.mark.asyncio
    async def test_gas_coordinator_respects_update_interval(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that GasCoordinator uses correct update interval."""
        coordinator = GasCoordinator(hass, mock_api_client)
        assert coordinator.update_interval == UPDATE_INTERVAL_GAS
        assert coordinator.update_interval == timedelta(seconds=300)

    @pytest.mark.asyncio
    async def test_gas_coordinator_handles_api_failure(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that OctopusError is wrapped in UpdateFailed."""
        mock_api_client.get_gas_consumption = AsyncMock(
            side_effect=OctopusError("No gas meter found")
        )

        coordinator = GasCoordinator(hass, mock_api_client)

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "Error fetching gas data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_gas_coordinator_has_descriptive_name(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that coordinator has a descriptive name."""
        coordinator = GasCoordinator(hass, mock_api_client)
        assert DOMAIN in coordinator.name
        assert "gas" in coordinator.name


class TestTariffCoordinator:
    """Tests for TariffCoordinator - fetches tariff and rate data."""

    @pytest.fixture
    def mock_api_client(self) -> AsyncMock:
        """Create a mock OctohaApiClient."""
        return AsyncMock(spec=OctohaApiClient)

    @pytest.fixture
    def sample_tariff(self) -> Tariff:
        """Create sample electricity tariff."""
        return Tariff(
            product_code="AGILE-24-04-03",
            display_name="Agile Octopus",
            standing_charge=47.18,
            tariff_type=TariffType.AGILE,
            unit_rate=15.5,
        )

    @pytest.fixture
    def sample_gas_tariff(self) -> GasTariff:
        """Create sample gas tariff."""
        return GasTariff(
            product_code="SILVER-24-04-03",
            display_name="Flexible Octopus",
            standing_charge=29.85,
            unit_rate=5.48,
        )

    @pytest.fixture
    def sample_current_rate(self) -> CurrentRate:
        """Create sample current rate."""
        return CurrentRate(
            rate=12.5,
            is_off_peak=False,
            period_end=datetime.now(UTC) + timedelta(minutes=30),
        )

    @pytest.mark.asyncio
    async def test_tariff_coordinator_successful_fetch(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_tariff: Tariff,
        sample_gas_tariff: GasTariff,
        sample_current_rate: CurrentRate,
    ) -> None:
        """Test successful tariff data fetch."""
        mock_api_client.get_electricity_tariff = AsyncMock(return_value=sample_tariff)
        mock_api_client.get_gas_tariff = AsyncMock(return_value=sample_gas_tariff)
        mock_api_client.get_current_rate = AsyncMock(return_value=sample_current_rate)

        coordinator = TariffCoordinator(hass, mock_api_client)
        data = await coordinator._async_update_data()

        assert isinstance(data, TariffData)
        assert data.electricity_tariff == sample_tariff
        assert data.gas_tariff == sample_gas_tariff
        assert data.current_rate == sample_current_rate

    @pytest.mark.asyncio
    async def test_tariff_coordinator_respects_30min_interval(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that TariffCoordinator uses 30-minute update interval."""
        coordinator = TariffCoordinator(hass, mock_api_client)
        assert coordinator.update_interval == UPDATE_INTERVAL_TARIFF
        assert coordinator.update_interval == timedelta(seconds=1800)

    @pytest.mark.asyncio
    async def test_tariff_coordinator_handles_missing_tariff(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that coordinator handles None tariff gracefully."""
        mock_api_client.get_electricity_tariff = AsyncMock(return_value=None)
        mock_api_client.get_gas_tariff = AsyncMock(return_value=None)
        mock_api_client.get_current_rate = AsyncMock(return_value=None)

        coordinator = TariffCoordinator(hass, mock_api_client)
        data = await coordinator._async_update_data()

        assert data.electricity_tariff is None
        assert data.gas_tariff is None
        assert data.current_rate is None

    @pytest.mark.asyncio
    async def test_tariff_coordinator_handles_api_failure(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that OctopusError is wrapped in UpdateFailed."""
        mock_api_client.get_electricity_tariff = AsyncMock(
            side_effect=OctopusError("Tariff not found")
        )

        coordinator = TariffCoordinator(hass, mock_api_client)

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "Error fetching tariff data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tariff_coordinator_has_descriptive_name(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that coordinator has a descriptive name."""
        coordinator = TariffCoordinator(hass, mock_api_client)
        assert DOMAIN in coordinator.name
        assert "tariff" in coordinator.name


class TestDispatchCoordinator:
    """Tests for DispatchCoordinator - fetches Intelligent Octopus dispatches."""

    @pytest.fixture
    def mock_api_client(self) -> AsyncMock:
        """Create a mock OctohaApiClient."""
        return AsyncMock(spec=OctohaApiClient)

    @pytest.fixture
    def sample_dispatch_status(self) -> DispatchStatus:
        """Create sample dispatch status."""
        now = datetime.now(UTC)
        return DispatchStatus(
            is_dispatching=True,
            current_dispatch=Dispatch(
                start=now - timedelta(minutes=15),
                end=now + timedelta(minutes=45),
                source=DispatchSource.SMART_CHARGE,
            ),
            next_dispatch=Dispatch(
                start=now + timedelta(hours=2),
                end=now + timedelta(hours=4),
                source=DispatchSource.SMART_CHARGE,
            ),
            planned_dispatches=[],
            completed_dispatches=[],
        )

    @pytest.mark.asyncio
    async def test_dispatch_coordinator_successful_fetch(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
        sample_dispatch_status: DispatchStatus,
    ) -> None:
        """Test successful dispatch data fetch."""
        mock_api_client.get_dispatches = AsyncMock(return_value=sample_dispatch_status)

        coordinator = DispatchCoordinator(hass, mock_api_client)
        data = await coordinator._async_update_data()

        assert isinstance(data, DispatchStatus)
        assert data.is_dispatching is True
        assert data.current_dispatch is not None

    @pytest.mark.asyncio
    async def test_dispatch_coordinator_respects_update_interval(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that DispatchCoordinator uses correct update interval."""
        coordinator = DispatchCoordinator(hass, mock_api_client)
        assert coordinator.update_interval == UPDATE_INTERVAL_DISPATCH
        assert coordinator.update_interval == timedelta(seconds=300)

    @pytest.mark.asyncio
    async def test_dispatch_coordinator_handles_no_dispatches(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that coordinator handles empty dispatch list."""
        empty_status = DispatchStatus(
            is_dispatching=False,
            current_dispatch=None,
            next_dispatch=None,
            planned_dispatches=[],
            completed_dispatches=[],
        )
        mock_api_client.get_dispatches = AsyncMock(return_value=empty_status)

        coordinator = DispatchCoordinator(hass, mock_api_client)
        data = await coordinator._async_update_data()

        assert data.is_dispatching is False
        assert data.current_dispatch is None
        assert data.next_dispatch is None

    @pytest.mark.asyncio
    async def test_dispatch_coordinator_handles_api_failure(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that OctopusError is wrapped in UpdateFailed."""
        mock_api_client.get_dispatches = AsyncMock(
            side_effect=OctopusError("Account number not set")
        )

        coordinator = DispatchCoordinator(hass, mock_api_client)

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "Error fetching dispatch data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_dispatch_coordinator_has_descriptive_name(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that coordinator has a descriptive name."""
        coordinator = DispatchCoordinator(hass, mock_api_client)
        assert DOMAIN in coordinator.name
        assert "dispatch" in coordinator.name


class TestCoordinatorErrorHandling:
    """Tests for coordinator error handling behavior."""

    @pytest.fixture
    def mock_api_client(self) -> AsyncMock:
        """Create a mock OctohaApiClient."""
        return AsyncMock(spec=OctohaApiClient)

    @pytest.mark.asyncio
    async def test_coordinator_wraps_octopus_error_in_update_failed(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that OctopusError is properly wrapped in UpdateFailed."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=OctopusError("Test error")
        )

        coordinator = ElectricityCoordinator(hass, mock_api_client)

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_coordinator_wraps_authentication_error_in_update_failed(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that AuthenticationError is properly wrapped in UpdateFailed."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        coordinator = ElectricityCoordinator(hass, mock_api_client)

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_coordinator_handles_unexpected_error(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that unexpected errors are wrapped in UpdateFailed."""
        mock_api_client.get_electricity_consumption = AsyncMock(
            side_effect=ValueError("Unexpected error")
        )

        coordinator = ElectricityCoordinator(hass, mock_api_client)

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "Unexpected error" in str(exc_info.value)


class TestCoordinatorConfiguration:
    """Tests for coordinator configuration and initialization."""

    @pytest.fixture
    def mock_api_client(self) -> AsyncMock:
        """Create a mock OctohaApiClient."""
        return AsyncMock(spec=OctohaApiClient)

    @pytest.mark.asyncio
    async def test_all_coordinators_have_correct_intervals(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that all coordinators have correct update intervals."""
        elec = ElectricityCoordinator(hass, mock_api_client)
        gas = GasCoordinator(hass, mock_api_client)
        tariff = TariffCoordinator(hass, mock_api_client)
        dispatch = DispatchCoordinator(hass, mock_api_client)

        assert elec.update_interval == timedelta(seconds=300)
        assert gas.update_interval == timedelta(seconds=300)
        assert tariff.update_interval == timedelta(seconds=1800)
        assert dispatch.update_interval == timedelta(seconds=300)

    @pytest.mark.asyncio
    async def test_coordinators_have_descriptive_names(
        self,
        hass: HomeAssistant,
        mock_api_client: AsyncMock,
    ) -> None:
        """Test that all coordinators have descriptive names."""
        elec = ElectricityCoordinator(hass, mock_api_client)
        gas = GasCoordinator(hass, mock_api_client)
        tariff = TariffCoordinator(hass, mock_api_client)
        dispatch = DispatchCoordinator(hass, mock_api_client)

        assert "octoha" in elec.name and "electricity" in elec.name
        assert "octoha" in gas.name and "gas" in gas.name
        assert "octoha" in tariff.name and "tariff" in tariff.name
        assert "octoha" in dispatch.name and "dispatch" in dispatch.name
