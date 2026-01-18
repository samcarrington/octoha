"""Tests for the Octoha API client consumption methods."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.octoha.api.rest import RestClient
from custom_components.octoha.api.exceptions import (
    AuthenticationError,
    OctopusError,
    RateLimitError,
)
from custom_components.octoha.models.consumption import Consumption, GasConsumption


class TestRestClientConsumption:
    """Tests for RestClient consumption methods."""

    @pytest.fixture
    def rest_client(self, mock_session: MagicMock, api_key: str) -> RestClient:
        """Create a RestClient instance for testing."""
        return RestClient(mock_session, api_key)

    @pytest.mark.asyncio
    async def test_get_electricity_consumption_success(
        self,
        rest_client: RestClient,
        mock_response_factory,
        load_fixture,
        mpan: str,
        meter_serial: str,
    ) -> None:
        """Test successful electricity consumption retrieval."""
        consumption_response = load_fixture("electricity_consumption_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=consumption_response,
        )
        rest_client._session.request.return_value = mock_response

        result = await rest_client.get_electricity_consumption(
            mpan=mpan,
            meter_serial=meter_serial,
        )

        assert len(result) == 5
        assert all(isinstance(c, Consumption) for c in result)
        assert result[0].consumption == 0.234
        assert result[0].kwh == 0.234

        # Verify the request was made correctly
        rest_client._session.request.assert_called_once()
        call_args = rest_client._session.request.call_args
        assert call_args[0][0] == "GET"
        assert mpan in call_args[0][1]
        assert meter_serial in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_gas_consumption_success(
        self,
        rest_client: RestClient,
        mock_response_factory,
        load_fixture,
        mprn: str,
        gas_meter_serial: str,
    ) -> None:
        """Test successful gas consumption retrieval."""
        consumption_response = load_fixture("gas_consumption_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=consumption_response,
        )
        rest_client._session.request.return_value = mock_response

        result = await rest_client.get_gas_consumption(
            mprn=mprn,
            meter_serial=gas_meter_serial,
        )

        assert len(result) == 5
        assert all(isinstance(c, GasConsumption) for c in result)
        assert result[0].consumption == 1.234
        assert result[0].kwh == 1.234

    @pytest.mark.asyncio
    async def test_get_consumption_auth_error(
        self,
        rest_client: RestClient,
        mock_response_factory,
        mpan: str,
        meter_serial: str,
    ) -> None:
        """Test consumption retrieval raises AuthenticationError on 401."""
        mock_response = mock_response_factory(status=401)
        rest_client._session.request.return_value = mock_response

        with pytest.raises(AuthenticationError) as exc_info:
            await rest_client.get_electricity_consumption(
                mpan=mpan,
                meter_serial=meter_serial,
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_consumption_rate_limit(
        self,
        rest_client: RestClient,
        mock_response_factory,
        mpan: str,
        meter_serial: str,
    ) -> None:
        """Test consumption retrieval raises RateLimitError on 429."""
        mock_response = mock_response_factory(
            status=429,
            headers={"Retry-After": "60"},
        )
        rest_client._session.request.return_value = mock_response

        with pytest.raises(RateLimitError) as exc_info:
            await rest_client.get_electricity_consumption(
                mpan=mpan,
                meter_serial=meter_serial,
            )

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_get_consumption_not_found(
        self,
        rest_client: RestClient,
        mock_response_factory,
        mpan: str,
        meter_serial: str,
    ) -> None:
        """Test consumption retrieval raises OctopusError on 404."""
        mock_response = mock_response_factory(status=404)
        rest_client._session.request.return_value = mock_response

        with pytest.raises(OctopusError) as exc_info:
            await rest_client.get_electricity_consumption(
                mpan=mpan,
                meter_serial=meter_serial,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_consumption_empty_results(
        self,
        rest_client: RestClient,
        mock_response_factory,
        mpan: str,
        meter_serial: str,
    ) -> None:
        """Test consumption retrieval with empty results."""
        mock_response = mock_response_factory(
            status=200,
            json_data={"results": []},
        )
        rest_client._session.request.return_value = mock_response

        result = await rest_client.get_electricity_consumption(
            mpan=mpan,
            meter_serial=meter_serial,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_recent_consumption(
        self,
        rest_client: RestClient,
        mock_response_factory,
        load_fixture,
        mpan: str,
        meter_serial: str,
    ) -> None:
        """Test get_recent_consumption helper method."""
        consumption_response = load_fixture("electricity_consumption_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=consumption_response,
        )
        rest_client._session.request.return_value = mock_response

        result = await rest_client.get_recent_consumption(
            mpan=mpan,
            meter_serial=meter_serial,
            periods=48,
        )

        assert len(result) == 5  # From fixture

        # Verify ordering param was set
        call_args = rest_client._session.request.call_args
        assert call_args[1]["params"]["order_by"] == "-period"  # Newest first

    @pytest.mark.asyncio
    async def test_get_recent_gas_consumption(
        self,
        rest_client: RestClient,
        mock_response_factory,
        load_fixture,
        mprn: str,
        gas_meter_serial: str,
    ) -> None:
        """Test get_recent_gas_consumption helper method."""
        consumption_response = load_fixture("gas_consumption_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=consumption_response,
        )
        rest_client._session.request.return_value = mock_response

        result = await rest_client.get_recent_gas_consumption(
            mprn=mprn,
            meter_serial=gas_meter_serial,
            periods=48,
        )

        assert len(result) == 5  # From fixture


class TestConsumptionParsing:
    """Tests for consumption data parsing."""

    def test_parse_consumption_iso_date(self) -> None:
        """Test parsing consumption with ISO format dates."""
        from custom_components.octoha.models.consumption import parse_consumption

        data = {
            "consumption": 0.5,
            "interval_start": "2024-01-18T12:00:00Z",
            "interval_end": "2024-01-18T12:30:00Z",
        }

        result = parse_consumption(data)

        assert result.consumption == 0.5
        assert result.interval_start.hour == 12
        assert result.interval_end.hour == 12
        assert result.interval_end.minute == 30

    def test_parse_gas_consumption_with_m3(self) -> None:
        """Test parsing gas consumption with m³ value."""
        from custom_components.octoha.models.consumption import parse_gas_consumption

        data = {
            "consumption": 11.1868,  # 1 m³ in kWh
            "interval_start": "2024-01-18T12:00:00Z",
            "interval_end": "2024-01-18T12:30:00Z",
            "consumption_m3": 1.0,
        }

        result = parse_gas_consumption(data)

        assert result.consumption == 11.1868
        assert result.consumption_m3 == 1.0
        assert result.m3 == 1.0

    def test_consumption_kwh_alias(self) -> None:
        """Test that kwh property returns consumption."""
        from custom_components.octoha.models.consumption import Consumption
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        consumption = Consumption(
            interval_start=now,
            interval_end=now,
            consumption=1.234,
        )

        assert consumption.kwh == consumption.consumption
