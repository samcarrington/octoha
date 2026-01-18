"""Tests for the Octoha API client tariff methods."""

from __future__ import annotations

from datetime import time
from unittest.mock import MagicMock

import pytest

from custom_components.octoha.api.rest import RestClient
from custom_components.octoha.api.exceptions import OctopusError
from custom_components.octoha.models.tariff import (
    Rate,
    Tariff,
    TariffType,
    TimeWindow,
    parse_rate,
)


class TestRestClientTariff:
    """Tests for RestClient tariff methods."""

    @pytest.fixture
    def rest_client(self, mock_session: MagicMock, api_key: str) -> RestClient:
        """Create a RestClient instance for testing."""
        return RestClient(mock_session, api_key)

    @pytest.mark.asyncio
    async def test_get_electricity_unit_rates_success(
        self,
        rest_client: RestClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test successful electricity unit rates retrieval."""
        rates_response = load_fixture("electricity_rates_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=rates_response,
        )
        rest_client._session.request.return_value = mock_response

        result = await rest_client.get_electricity_standard_unit_rates(
            product_code="INTELLI-VAR-22-10-14",
            tariff_code="E-1R-INTELLI-VAR-22-10-14-J",
        )

        assert len(result) == 2
        assert all(isinstance(r, Rate) for r in result)
        # Off-peak rate
        assert result[0].value_inc_vat == 6.5625
        # Peak rate
        assert result[1].value_inc_vat == 29.9985

    @pytest.mark.asyncio
    async def test_get_electricity_standing_charge_success(
        self,
        rest_client: RestClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test successful electricity standing charge retrieval."""
        standing_charge_response = load_fixture("standing_charge_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=standing_charge_response,
        )
        rest_client._session.request.return_value = mock_response

        result = await rest_client.get_electricity_standing_charge(
            product_code="INTELLI-VAR-22-10-14",
            tariff_code="E-1R-INTELLI-VAR-22-10-14-J",
        )

        assert result == 47.4915

    @pytest.mark.asyncio
    async def test_get_electricity_standing_charge_empty(
        self,
        rest_client: RestClient,
        mock_response_factory,
    ) -> None:
        """Test standing charge returns None when no results."""
        mock_response = mock_response_factory(
            status=200,
            json_data={"results": []},
        )
        rest_client._session.request.return_value = mock_response

        result = await rest_client.get_electricity_standing_charge(
            product_code="INTELLI-VAR-22-10-14",
            tariff_code="E-1R-INTELLI-VAR-22-10-14-J",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_gas_unit_rates_success(
        self,
        rest_client: RestClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test successful gas unit rates retrieval."""
        standing_charge_response = load_fixture("standing_charge_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=standing_charge_response,
        )
        rest_client._session.request.return_value = mock_response

        result = await rest_client.get_gas_standard_unit_rates(
            product_code="FLEX-VAR-22-11-25",
            tariff_code="G-1R-FLEX-VAR-22-11-25-J",
        )

        assert len(result) == 1
        assert isinstance(result[0], Rate)


class TestExtractProductCode:
    """Tests for extract_product_code helper."""

    @pytest.fixture
    def rest_client(self, mock_session: MagicMock, api_key: str) -> RestClient:
        """Create a RestClient instance for testing."""
        return RestClient(mock_session, api_key)

    def test_extract_from_electricity_tariff(self, rest_client: RestClient) -> None:
        """Test extracting product code from electricity tariff."""
        tariff_code = "E-1R-INTELLI-VAR-22-10-14-J"
        result = rest_client.extract_product_code(tariff_code)
        assert result == "INTELLI-VAR-22-10-14"

    def test_extract_from_gas_tariff(self, rest_client: RestClient) -> None:
        """Test extracting product code from gas tariff."""
        tariff_code = "G-1R-FLEX-VAR-22-11-25-J"
        result = rest_client.extract_product_code(tariff_code)
        assert result == "FLEX-VAR-22-11-25"

    def test_extract_from_agile_tariff(self, rest_client: RestClient) -> None:
        """Test extracting product code from Agile tariff."""
        tariff_code = "E-1R-AGILE-FLEX-22-11-25-J"
        result = rest_client.extract_product_code(tariff_code)
        assert result == "AGILE-FLEX-22-11-25"

    def test_extract_short_code(self, rest_client: RestClient) -> None:
        """Test extracting from short/malformed tariff code."""
        tariff_code = "SIMPLE"
        result = rest_client.extract_product_code(tariff_code)
        assert result == "SIMPLE"


class TestRateParsing:
    """Tests for rate data parsing."""

    def test_parse_rate_with_valid_to(self) -> None:
        """Test parsing rate with valid_to date."""
        data = {
            "value_inc_vat": 29.5,
            "value_exc_vat": 28.095,
            "valid_from": "2024-01-18T05:30:00Z",
            "valid_to": "2024-01-18T23:30:00Z",
        }

        result = parse_rate(data)

        assert result.value_inc_vat == 29.5
        assert result.value_exc_vat == 28.095
        assert result.valid_from.hour == 5
        assert result.valid_to is not None
        assert result.valid_to.hour == 23

    def test_parse_rate_without_valid_to(self) -> None:
        """Test parsing rate without valid_to date (ongoing)."""
        data = {
            "value_inc_vat": 29.5,
            "valid_from": "2024-01-18T05:30:00Z",
            "valid_to": None,
        }

        result = parse_rate(data)

        assert result.valid_to is None

    def test_rate_value_gbp(self) -> None:
        """Test rate value_gbp conversion."""
        from datetime import datetime, timezone

        rate = Rate(
            valid_from=datetime.now(timezone.utc),
            valid_to=None,
            value_inc_vat=29.5,
        )

        assert rate.value_gbp == 0.295  # 29.5p = £0.295


class TestTimeWindow:
    """Tests for TimeWindow off-peak detection."""

    def test_normal_window_active(self) -> None:
        """Test time window detection for normal hours."""
        window = TimeWindow(
            start_time=time(1, 0),
            end_time=time(5, 0),
            rate=7.5,
        )

        assert window.is_active(time(2, 0)) is True
        assert window.is_active(time(3, 30)) is True
        assert window.is_active(time(1, 0)) is True  # Start is inclusive

    def test_normal_window_inactive(self) -> None:
        """Test time window detection outside normal hours."""
        window = TimeWindow(
            start_time=time(1, 0),
            end_time=time(5, 0),
            rate=7.5,
        )

        assert window.is_active(time(0, 30)) is False
        assert window.is_active(time(5, 0)) is False  # End is exclusive
        assert window.is_active(time(12, 0)) is False

    def test_midnight_crossing_window_active(self) -> None:
        """Test time window that crosses midnight (Intelligent Go)."""
        # Intelligent Go: 23:30 - 05:30
        window = TimeWindow(
            start_time=time(23, 30),
            end_time=time(5, 30),
            rate=7.5,
        )

        # Before midnight
        assert window.is_active(time(23, 30)) is True
        assert window.is_active(time(23, 59)) is True

        # After midnight
        assert window.is_active(time(0, 0)) is True
        assert window.is_active(time(3, 0)) is True
        assert window.is_active(time(5, 0)) is True

    def test_midnight_crossing_window_inactive(self) -> None:
        """Test time window that crosses midnight - inactive hours."""
        # Intelligent Go: 23:30 - 05:30
        window = TimeWindow(
            start_time=time(23, 30),
            end_time=time(5, 30),
            rate=7.5,
        )

        assert window.is_active(time(5, 30)) is False  # End is exclusive
        assert window.is_active(time(12, 0)) is False
        assert window.is_active(time(23, 0)) is False


class TestTariffModel:
    """Tests for Tariff model."""

    def test_is_time_of_use_tou(self) -> None:
        """Test is_time_of_use for time-of-use tariff."""
        tariff = Tariff(
            product_code="INTELLI-VAR-22-10-14",
            display_name="Intelligent Go",
            standing_charge=47.0,
            tariff_type=TariffType.TIME_OF_USE,
        )

        assert tariff.is_time_of_use is True

    def test_is_time_of_use_agile(self) -> None:
        """Test is_time_of_use for Agile tariff."""
        tariff = Tariff(
            product_code="AGILE-FLEX-22-11-25",
            display_name="Agile Octopus",
            standing_charge=47.0,
            tariff_type=TariffType.AGILE,
        )

        assert tariff.is_time_of_use is True

    def test_is_time_of_use_standard(self) -> None:
        """Test is_time_of_use for standard tariff."""
        tariff = Tariff(
            product_code="FLEX-22-11-25",
            display_name="Flexible Octopus",
            standing_charge=47.0,
            tariff_type=TariffType.STANDARD,
        )

        assert tariff.is_time_of_use is False

    def test_is_intelligent(self) -> None:
        """Test is_intelligent detection."""
        intelligent = Tariff(
            product_code="INTELLI-VAR-22-10-14",
            display_name="Intelligent Go",
            standing_charge=47.0,
        )

        regular = Tariff(
            product_code="GO-VAR-22-10-14",
            display_name="Octopus Go",
            standing_charge=47.0,
        )

        assert intelligent.is_intelligent is True
        assert regular.is_intelligent is False
