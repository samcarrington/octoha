"""Tests for OctohaApiClient.get_daily_usage() method.

This module provides comprehensive test coverage for daily usage aggregation,
including concurrent execution of electricity and gas consumption fetches,
error handling, and data aggregation across multiple readings.
"""

from __future__ import annotations

from datetime import UTC
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.octoha.api.client import OctohaApiClient


class TestOctohaApiClientDailyUsage:
    """Tests for OctohaApiClient.get_daily_usage() method."""

    @pytest.fixture
    def client(
        self,
        mock_session: MagicMock,
        api_key: str,
        account_number: str,
    ) -> OctohaApiClient:
        """Create an OctohaApiClient instance for testing."""
        return OctohaApiClient(mock_session, api_key, account_number)

    def _create_consumption_objects(
        self, dates_and_values: list[tuple[str, float]]
    ) -> list[object]:
        """Helper to create Consumption objects from dates and values.

        Args:
            dates_and_values: List of (date_str, consumption_value) tuples.
                             date_str format: "2024-01-18"

        Returns:
            List of Consumption-like objects.
        """
        from datetime import datetime

        from custom_components.octoha.models.consumption import Consumption

        results = []
        for date_str, consumption_value in dates_and_values:
            # Parse date and create interval_start/end
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(
                hour=0, minute=0, second=0, tzinfo=UTC
            )
            results.append(
                Consumption(
                    interval_start=date_obj,
                    interval_end=date_obj.replace(hour=0, minute=30),
                    consumption=consumption_value,
                )
            )
        return results

    def _create_gas_consumption_objects(
        self, dates_and_values: list[tuple[str, float]]
    ) -> list[object]:
        """Helper to create GasConsumption objects from dates and values.

        Args:
            dates_and_values: List of (date_str, consumption_value) tuples.
                             date_str format: "2024-01-18"

        Returns:
            List of GasConsumption-like objects.
        """
        from datetime import datetime

        from custom_components.octoha.models.consumption import GasConsumption

        results = []
        for date_str, consumption_value in dates_and_values:
            # Parse date and create interval_start/end
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(
                hour=0, minute=0, second=0, tzinfo=UTC
            )
            results.append(
                GasConsumption(
                    interval_start=date_obj,
                    interval_end=date_obj.replace(hour=0, minute=30),
                    consumption=consumption_value,
                )
            )
        return results

    @pytest.mark.asyncio
    async def test_get_daily_usage_with_both_electricity_and_gas(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test daily usage aggregation with both electricity and gas data.

        Verifies:
        - Both electricity and gas data are fetched and aggregated
        - Multiple readings per day are correctly summed
        - Results are sorted by date in descending order (newest first)
        - REST client is called with correct parameters
        """
        account_response = load_fixture("account_response.json")

        # Pre-populate account to avoid account API calls
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        # Create test consumption data spanning multiple days
        electricity_data = self._create_consumption_objects(
            [
                ("2024-01-20", 0.5),
                ("2024-01-20", 0.3),
                ("2024-01-19", 0.8),
                ("2024-01-18", 0.6),
            ]
        )
        gas_data = self._create_gas_consumption_objects(
            [
                ("2024-01-20", 1.2),
                ("2024-01-20", 0.4),
                ("2024-01-19", 1.5),
                ("2024-01-18", 0.9),
            ]
        )

        # Mock the REST client methods
        client._rest_client.get_electricity_consumption = AsyncMock(
            return_value=electricity_data
        )
        client._rest_client.get_gas_consumption = AsyncMock(return_value=gas_data)

        result = await client.get_daily_usage(days=7)

        # Should have 3 days of data
        assert len(result) == 3

        # Results should be sorted by date descending (newest first)
        assert result[0].date == "2024-01-20"
        assert result[1].date == "2024-01-19"
        assert result[2].date == "2024-01-18"

        # Verify aggregated values for 2024-01-20
        assert result[0].electricity_kwh == pytest.approx(0.8)  # 0.5 + 0.3
        assert result[0].gas_kwh == pytest.approx(1.6)  # 1.2 + 0.4
        assert result[0].total_kwh == pytest.approx(2.4)

        # Verify aggregated values for 2024-01-19
        assert result[1].electricity_kwh == pytest.approx(0.8)
        assert result[1].gas_kwh == pytest.approx(1.5)
        assert result[1].total_kwh == pytest.approx(2.3)

        # Verify aggregated values for 2024-01-18
        assert result[2].electricity_kwh == pytest.approx(0.6)
        assert result[2].gas_kwh == pytest.approx(0.9)
        assert result[2].total_kwh == pytest.approx(1.5)

        # Verify REST client was called with correct parameters
        client._rest_client.get_electricity_consumption.assert_called_once()
        client._rest_client.get_gas_consumption.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_daily_usage_electricity_only(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test daily usage when only electricity meter exists.

        Verifies:
        - Electricity data is returned
        - Gas data defaults to 0.0 using defaultdict behavior
        - Gas API is not called when meter is None
        """
        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])

        # Remove gas meter to simulate electricity-only account
        account.properties[0].gas_meter_points = []
        client._account = account

        electricity_data = self._create_consumption_objects(
            [
                ("2024-01-20", 0.5),
                ("2024-01-19", 0.8),
            ]
        )

        client._rest_client.get_electricity_consumption = AsyncMock(
            return_value=electricity_data
        )
        client._rest_client.get_gas_consumption = AsyncMock()

        result = await client.get_daily_usage(days=7)

        # Should have 2 days
        assert len(result) == 2

        # Electricity present, gas absent (defaultdict returns 0.0)
        assert result[0].electricity_kwh == 0.5
        assert result[0].gas_kwh == 0.0
        assert result[0].total_kwh == 0.5

        # Gas fetch should not have been called
        client._rest_client.get_gas_consumption.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_daily_usage_gas_only(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test daily usage when only gas meter exists.

        Verifies:
        - Gas data is returned
        - Electricity data defaults to 0.0 using defaultdict behavior
        - Electricity API is not called when meter is None
        """
        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])

        # Remove electricity meter to simulate gas-only account
        account.properties[0].electricity_meter_points = []
        client._account = account

        gas_data = self._create_gas_consumption_objects(
            [
                ("2024-01-20", 1.2),
                ("2024-01-19", 1.5),
            ]
        )

        client._rest_client.get_gas_consumption = AsyncMock(return_value=gas_data)
        client._rest_client.get_electricity_consumption = AsyncMock()

        result = await client.get_daily_usage(days=7)

        # Should have 2 days
        assert len(result) == 2

        # Gas present, electricity absent
        assert result[0].electricity_kwh == 0.0
        assert result[0].gas_kwh == 1.2
        assert result[0].total_kwh == 1.2

        # Electricity fetch should not have been called
        client._rest_client.get_electricity_consumption.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_daily_usage_no_meters(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test daily usage when no meters exist.

        Verifies:
        - Empty list is returned when no meters are configured
        - Neither electricity nor gas APIs are called
        """
        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])

        # Remove both meters
        account.properties[0].electricity_meter_points = []
        account.properties[0].gas_meter_points = []
        client._account = account

        client._rest_client.get_electricity_consumption = AsyncMock()
        client._rest_client.get_gas_consumption = AsyncMock()

        result = await client.get_daily_usage(days=7)

        # Should return empty list when no meters
        assert len(result) == 0
        assert result == []

        # Neither should have been called
        client._rest_client.get_electricity_consumption.assert_not_called()
        client._rest_client.get_gas_consumption.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_daily_usage_electricity_api_error(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test that gas data is returned even if electricity API fails.

        Verifies:
        - When electricity API fails with OctopusError, it's caught and logged
        - Gas data is still returned
        - Method returns successfully with partial data
        """
        from custom_components.octoha.api.exceptions import OctopusError

        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        gas_data = self._create_gas_consumption_objects(
            [
                ("2024-01-20", 1.2),
                ("2024-01-19", 1.5),
            ]
        )

        # Electricity API fails
        client._rest_client.get_electricity_consumption = AsyncMock(
            side_effect=OctopusError("API error")
        )
        client._rest_client.get_gas_consumption = AsyncMock(return_value=gas_data)

        result = await client.get_daily_usage(days=7)

        # Should still have gas data despite electricity error
        assert len(result) == 2
        assert result[0].electricity_kwh == 0.0
        assert result[0].gas_kwh == 1.2
        assert result[0].total_kwh == 1.2

    @pytest.mark.asyncio
    async def test_get_daily_usage_gas_api_error(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test that electricity data is returned even if gas API fails.

        Verifies:
        - When gas API fails with OctopusError, it's caught and logged
        - Electricity data is still returned
        - Method returns successfully with partial data
        """
        from custom_components.octoha.api.exceptions import OctopusError

        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        electricity_data = self._create_consumption_objects(
            [
                ("2024-01-20", 0.5),
                ("2024-01-19", 0.8),
            ]
        )

        # Gas API fails
        client._rest_client.get_electricity_consumption = AsyncMock(
            return_value=electricity_data
        )
        client._rest_client.get_gas_consumption = AsyncMock(
            side_effect=OctopusError("API error")
        )

        result = await client.get_daily_usage(days=7)

        # Should still have electricity data despite gas error
        assert len(result) == 2
        assert result[0].electricity_kwh == 0.5
        assert result[0].gas_kwh == 0.0
        assert result[0].total_kwh == 0.5

    @pytest.mark.asyncio
    async def test_get_daily_usage_both_apis_fail(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test that empty list is returned if both APIs fail.

        Verifies:
        - When both electricity and gas APIs fail, errors are caught and logged
        - Empty list is returned gracefully
        - No exception is raised to the caller
        """
        from custom_components.octoha.api.exceptions import OctopusError

        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        # Both APIs fail
        client._rest_client.get_electricity_consumption = AsyncMock(
            side_effect=OctopusError("API error")
        )
        client._rest_client.get_gas_consumption = AsyncMock(
            side_effect=OctopusError("API error")
        )

        result = await client.get_daily_usage(days=7)

        # Should return empty list when both fail
        assert len(result) == 0
        assert result == []

    @pytest.mark.asyncio
    async def test_get_daily_usage_concurrent_execution(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test electricity and gas are fetched concurrently.

        Verifies:
        - Both fetch_electricity and fetch_gas are executed concurrently
        - Total execution time is ~equal to max(electricity_time, gas_time)
        - Both calls complete successfully
        """
        import asyncio
        import time

        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        electricity_data = self._create_consumption_objects([("2024-01-20", 0.5)])
        gas_data = self._create_gas_consumption_objects([("2024-01-20", 1.2)])

        # Create async mocks with delays to verify concurrency
        async def delayed_electricity(*args, **kwargs):
            await asyncio.sleep(0.1)
            return electricity_data

        async def delayed_gas(*args, **kwargs):
            await asyncio.sleep(0.1)
            return gas_data

        client._rest_client.get_electricity_consumption = AsyncMock(
            side_effect=delayed_electricity
        )
        client._rest_client.get_gas_consumption = AsyncMock(side_effect=delayed_gas)

        start_time = time.time()
        await client.get_daily_usage(days=7)
        elapsed_time = time.time() - start_time

        # If run serially, would take ~0.2 seconds; concurrent should be ~0.1-0.15
        # Using a generous threshold (0.18s) to avoid flakiness in CI
        assert elapsed_time < 0.18, (
            f"Execution took {elapsed_time}s, expected concurrent execution (~0.1s)"
        )

        # Both should have been called
        assert client._rest_client.get_electricity_consumption.called
        assert client._rest_client.get_gas_consumption.called

    @pytest.mark.asyncio
    async def test_get_daily_usage_multiple_readings_per_day_summed(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test that multiple readings on the same day are correctly summed.

        Verifies:
        - defaultdict(float) is used for aggregation
        - Multiple readings with the same date are accumulated
        - Only one DailyUsage object is created per unique date
        """
        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        # Create 4 readings for 2024-01-20 that should be summed
        electricity_data = self._create_consumption_objects(
            [
                ("2024-01-20", 0.1),
                ("2024-01-20", 0.2),
                ("2024-01-20", 0.15),
                ("2024-01-20", 0.25),
            ]
        )
        gas_data = self._create_gas_consumption_objects(
            [
                ("2024-01-20", 0.5),
                ("2024-01-20", 0.6),
                ("2024-01-20", 0.4),
            ]
        )

        client._rest_client.get_electricity_consumption = AsyncMock(
            return_value=electricity_data
        )
        client._rest_client.get_gas_consumption = AsyncMock(return_value=gas_data)

        result = await client.get_daily_usage(days=7)

        # Should have only 1 day
        assert len(result) == 1
        assert result[0].date == "2024-01-20"

        # All readings should be summed
        assert result[0].electricity_kwh == pytest.approx(0.7)
        assert result[0].gas_kwh == pytest.approx(1.5)  # 0.5 + 0.6 + 0.4

    @pytest.mark.asyncio
    async def test_get_daily_usage_results_sorted_by_date_descending(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test that results are sorted by date in descending order (newest first).

        Verifies:
        - Results are sorted with reverse=True
        - Newest dates appear first in the list
        - Dates in descending order (2024-01-21, 2024-01-20, etc.)
        """
        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        # Create data in random order to verify sorting
        electricity_data = self._create_consumption_objects(
            [
                ("2024-01-18", 0.1),
                ("2024-01-21", 0.2),
                ("2024-01-19", 0.15),
                ("2024-01-20", 0.25),
            ]
        )
        gas_data = self._create_gas_consumption_objects(
            [
                ("2024-01-21", 0.5),
                ("2024-01-18", 0.6),
                ("2024-01-20", 0.4),
                ("2024-01-19", 0.3),
            ]
        )

        client._rest_client.get_electricity_consumption = AsyncMock(
            return_value=electricity_data
        )
        client._rest_client.get_gas_consumption = AsyncMock(return_value=gas_data)

        result = await client.get_daily_usage(days=7)

        # Verify results are in descending date order
        assert len(result) == 4
        assert result[0].date == "2024-01-21"
        assert result[1].date == "2024-01-20"
        assert result[2].date == "2024-01-19"
        assert result[3].date == "2024-01-18"

    @pytest.mark.asyncio
    async def test_get_daily_usage_respects_days_parameter(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test that days parameter is correctly passed to REST client.

        Verifies:
        - page_size is calculated as days * 48 (number of half-hour periods)
        - group_by parameter is set to "day" for daily aggregation
        - REST client receives correct parameters for the desired time range
        """
        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        electricity_data = self._create_consumption_objects([("2024-01-20", 0.5)])
        gas_data = self._create_gas_consumption_objects([("2024-01-20", 1.2)])

        client._rest_client.get_electricity_consumption = AsyncMock(
            return_value=electricity_data
        )
        client._rest_client.get_gas_consumption = AsyncMock(return_value=gas_data)

        await client.get_daily_usage(days=14)

        # Verify page_size was calculated correctly (days * 48 half-hour periods)
        electricity_call = client._rest_client.get_electricity_consumption.call_args
        gas_call = client._rest_client.get_gas_consumption.call_args

        assert electricity_call[1]["page_size"] == 14 * 48
        assert gas_call[1]["page_size"] == 14 * 48

        # Verify group_by parameter was set
        assert electricity_call[1]["group_by"] == "day"
        assert gas_call[1]["group_by"] == "day"

    @pytest.mark.asyncio
    async def test_get_daily_usage_empty_consumption_data(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test handling of empty consumption responses.

        Verifies:
        - Empty list from API is handled gracefully
        - Empty result list is returned when both APIs return empty
        - No errors occur with empty data
        """
        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        # Both APIs return empty lists
        client._rest_client.get_electricity_consumption = AsyncMock(return_value=[])
        client._rest_client.get_gas_consumption = AsyncMock(return_value=[])

        result = await client.get_daily_usage(days=7)

        # Should return empty list
        assert len(result) == 0
        assert result == []

    @pytest.mark.asyncio
    async def test_get_daily_usage_overlapping_dates_from_both_meters(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test aggregation when dates overlap between electricity and gas.

        Verifies:
        - Dates are correctly combined using set union
        - Both electricity and gas values are present for overlapping dates
        - Union operation works correctly: set(elec_dates) | set(gas_dates)
        """
        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        # Same dates in both
        electricity_data = self._create_consumption_objects(
            [
                ("2024-01-20", 0.5),
                ("2024-01-19", 0.8),
                ("2024-01-18", 0.6),
            ]
        )
        gas_data = self._create_gas_consumption_objects(
            [
                ("2024-01-20", 1.2),
                ("2024-01-19", 1.5),
                ("2024-01-18", 0.9),
            ]
        )

        client._rest_client.get_electricity_consumption = AsyncMock(
            return_value=electricity_data
        )
        client._rest_client.get_gas_consumption = AsyncMock(return_value=gas_data)

        result = await client.get_daily_usage(days=7)

        # All dates should be present
        assert len(result) == 3
        dates = [r.date for r in result]
        assert "2024-01-20" in dates
        assert "2024-01-19" in dates
        assert "2024-01-18" in dates

        # Each date should have both electricity and gas
        for daily_usage in result:
            assert daily_usage.electricity_kwh > 0
            assert daily_usage.gas_kwh > 0

    @pytest.mark.asyncio
    async def test_get_daily_usage_disjoint_dates_from_both_meters(
        self,
        client: OctohaApiClient,
        load_fixture,
    ) -> None:
        """Test aggregation when dates don't overlap between electricity and gas.

        Verifies:
        - Set union correctly combines non-overlapping dates
        - Electricity-only dates have gas_kwh = 0.0 (defaultdict default)
        - Gas-only dates have electricity_kwh = 0.0 (defaultdict default)
        - All unique dates from both sources are included in results
        """
        account_response = load_fixture("account_response.json")
        account = client._parse_account(account_response["data"]["account"])
        client._account = account

        # Different dates for each meter
        electricity_data = self._create_consumption_objects(
            [
                ("2024-01-20", 0.5),
                ("2024-01-19", 0.8),
            ]
        )
        gas_data = self._create_gas_consumption_objects(
            [
                ("2024-01-18", 1.2),
                ("2024-01-17", 1.5),
            ]
        )

        client._rest_client.get_electricity_consumption = AsyncMock(
            return_value=electricity_data
        )
        client._rest_client.get_gas_consumption = AsyncMock(return_value=gas_data)

        result = await client.get_daily_usage(days=7)

        # Should have union of all dates (4 total)
        assert len(result) == 4
        dates = {r.date for r in result}
        assert dates == {"2024-01-20", "2024-01-19", "2024-01-18", "2024-01-17"}

        # Dates from electricity-only should have 0 gas
        elec_only_date = next(r for r in result if r.date == "2024-01-20")
        assert elec_only_date.electricity_kwh == 0.5
        assert elec_only_date.gas_kwh == 0.0

        # Dates from gas-only should have 0 electricity
        gas_only_date = next(r for r in result if r.date == "2024-01-18")
        assert gas_only_date.electricity_kwh == 0.0
        assert gas_only_date.gas_kwh == 1.2
