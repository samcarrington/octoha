"""Test suite for Octoha REST API client.

Tests the RestClient class that handles consumption and tariff data
fetching from the Octopus Energy REST API.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.octoha.api.exceptions import (
    AuthenticationError,
    OctopusError,
    RateLimitError,
    ValidationError,
)
from custom_components.octoha.api.rest import (
    EndpointSuffix,
    MeterType,
    RestClient,
)


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock aiohttp ClientSession."""
    return MagicMock()


@pytest.fixture
def mock_response_factory():
    """Factory for creating mock aiohttp responses."""

    def _create(
        status: int = 200,
        json_data: dict | None = None,
        text: str = "",
        headers: dict | None = None,
    ) -> MagicMock:
        response = MagicMock()
        response.status = status
        response.json = AsyncMock(return_value=json_data or {})
        response.text = AsyncMock(return_value=text)
        response.headers = headers or {}

        # Make it work as async context manager
        response.__aenter__ = AsyncMock(return_value=response)
        response.__aexit__ = AsyncMock(return_value=None)

        return response

    return _create


@pytest.fixture
def rest_client(mock_session: MagicMock) -> RestClient:
    """Create a RestClient instance with mock session."""
    return RestClient(session=mock_session, api_key="sk_test_abc123")


class TestRestClientInit:
    """Tests for RestClient initialization."""

    def test_client_stores_api_key(self, mock_session: MagicMock) -> None:
        """Test that client stores the API key."""
        client = RestClient(session=mock_session, api_key="sk_test_key")
        assert client._api_key == "sk_test_key"

    def test_client_stores_session(self, mock_session: MagicMock) -> None:
        """Test that client stores the session."""
        client = RestClient(session=mock_session, api_key="sk_test_key")
        assert client._session is mock_session

    def test_client_sets_base_url(self, mock_session: MagicMock) -> None:
        """Test that client sets the base URL."""
        client = RestClient(session=mock_session, api_key="sk_test_key")
        assert client._base_url == "https://api.octopus.energy/v1"


class TestBuildMeterEndpoint:
    """Tests for _build_meter_endpoint method."""

    def test_electricity_consumption_endpoint(self, rest_client: RestClient) -> None:
        """Test building electricity consumption endpoint."""
        endpoint = rest_client._build_meter_endpoint(
            meter_type=MeterType.ELECTRICITY,
            meter_id="1234567890123",
            meter_serial="20P1234567",
            endpoint_suffix=EndpointSuffix.CONSUMPTION,
        )
        expected = (
            "/electricity-meter-points/1234567890123/meters/20P1234567/consumption/"
        )
        assert endpoint == expected

    def test_gas_consumption_endpoint(self, rest_client: RestClient) -> None:
        """Test building gas consumption endpoint."""
        endpoint = rest_client._build_meter_endpoint(
            meter_type=MeterType.GAS,
            meter_id="1234567890",
            meter_serial="G4P12345678",
            endpoint_suffix=EndpointSuffix.CONSUMPTION,
        )
        expected = "/gas-meter-points/1234567890/meters/G4P12345678/consumption/"
        assert endpoint == expected

    def test_empty_meter_id_raises(self, rest_client: RestClient) -> None:
        """Test that empty meter ID raises ValueError."""
        with pytest.raises(ValueError, match="meter_id cannot be empty"):
            rest_client._build_meter_endpoint(
                meter_type=MeterType.ELECTRICITY,
                meter_id="",
                meter_serial="20P1234567",
            )

    def test_empty_meter_serial_raises(self, rest_client: RestClient) -> None:
        """Test that empty meter serial raises ValueError."""
        with pytest.raises(ValueError, match="meter_serial cannot be empty"):
            rest_client._build_meter_endpoint(
                meter_type=MeterType.ELECTRICITY,
                meter_id="1234567890123",
                meter_serial="",
            )

    def test_invalid_meter_type_raises(self, rest_client: RestClient) -> None:
        """Test that invalid meter type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid meter_type"):
            rest_client._build_meter_endpoint(
                meter_type="invalid",  # type: ignore
                meter_id="1234567890123",
                meter_serial="20P1234567",
            )

    def test_string_suffix(self, rest_client: RestClient) -> None:
        """Test building endpoint with string suffix."""
        endpoint = rest_client._build_meter_endpoint(
            meter_type=MeterType.ELECTRICITY,
            meter_id="1234567890123",
            meter_serial="20P1234567",
            endpoint_suffix="custom/",
        )
        expected = "/electricity-meter-points/1234567890123/meters/20P1234567/custom/"
        assert endpoint == expected


class TestRequest:
    """Tests for _request method."""

    @pytest.mark.asyncio
    async def test_request_success_returns_json(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test successful request returns JSON data."""
        response = mock_response_factory(
            status=200,
            json_data={"results": [{"value": 1.23}]},
        )
        mock_session.request.return_value = response

        result = await rest_client._request("GET", "/test/endpoint")

        assert result == {"results": [{"value": 1.23}]}
        mock_session.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_401_raises_authentication_error(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test 401 response raises AuthenticationError."""
        response = mock_response_factory(status=401)
        mock_session.request.return_value = response

        with pytest.raises(AuthenticationError) as exc_info:
            await rest_client._request("GET", "/test/endpoint")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_request_429_raises_rate_limit_error(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test 429 response raises RateLimitError."""
        response = mock_response_factory(
            status=429,
            headers={"Retry-After": "60"},
        )
        mock_session.request.return_value = response

        with pytest.raises(RateLimitError) as exc_info:
            await rest_client._request("GET", "/test/endpoint")

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_request_429_without_retry_after(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test 429 response without Retry-After header."""
        response = mock_response_factory(status=429)
        mock_session.request.return_value = response

        with pytest.raises(RateLimitError) as exc_info:
            await rest_client._request("GET", "/test/endpoint")

        assert exc_info.value.retry_after is None

    @pytest.mark.asyncio
    async def test_request_404_raises_octopus_error(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test 404 response raises OctopusError."""
        response = mock_response_factory(status=404)
        mock_session.request.return_value = response

        with pytest.raises(OctopusError) as exc_info:
            await rest_client._request("GET", "/test/endpoint")

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_request_500_raises_octopus_error(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test 500 response raises OctopusError."""
        response = mock_response_factory(
            status=500,
            text="Internal Server Error",
        )
        mock_session.request.return_value = response

        with pytest.raises(OctopusError) as exc_info:
            await rest_client._request("GET", "/test/endpoint")

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_request_exception_raises_octopus_error(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
    ) -> None:
        """Test network exception raises OctopusError."""
        mock_session.request.side_effect = Exception("Network error")

        with pytest.raises(OctopusError):
            await rest_client._request("GET", "/test/endpoint")


class TestGetElectricityConsumption:
    """Tests for get_electricity_consumption method."""

    @pytest.mark.asyncio
    async def test_get_electricity_consumption_success(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test successful electricity consumption fetch."""
        response = mock_response_factory(
            status=200,
            json_data={
                "results": [
                    {
                        "consumption": 1.234,
                        "interval_start": "2024-01-01T00:00:00Z",
                        "interval_end": "2024-01-01T00:30:00Z",
                    }
                ]
            },
        )
        mock_session.request.return_value = response

        result = await rest_client.get_electricity_consumption(
            mpan="1234567890123",
            meter_serial="20P1234567",
        )

        assert len(result) == 1
        assert result[0].consumption == 1.234

    @pytest.mark.asyncio
    async def test_get_electricity_consumption_with_period(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test electricity consumption with date filters."""
        response = mock_response_factory(
            status=200,
            json_data={"results": []},
        )
        mock_session.request.return_value = response

        period_from = datetime(2024, 1, 1, tzinfo=UTC)
        period_to = datetime(2024, 1, 2, tzinfo=UTC)

        await rest_client.get_electricity_consumption(
            mpan="1234567890123",
            meter_serial="20P1234567",
            period_from=period_from,
            period_to=period_to,
        )

        # Verify params were passed
        call_args = mock_session.request.call_args
        params = call_args[1]["params"]
        assert "period_from" in params
        assert "period_to" in params

    @pytest.mark.asyncio
    async def test_get_electricity_consumption_invalid_mpan(
        self,
        rest_client: RestClient,
    ) -> None:
        """Test invalid MPAN raises ValidationError."""
        with pytest.raises(ValidationError):
            await rest_client.get_electricity_consumption(
                mpan="invalid",
                meter_serial="20P1234567",
            )


class TestGetGasConsumption:
    """Tests for get_gas_consumption method."""

    @pytest.mark.asyncio
    async def test_get_gas_consumption_success(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test successful gas consumption fetch."""
        response = mock_response_factory(
            status=200,
            json_data={
                "results": [
                    {
                        "consumption": 5.678,
                        "interval_start": "2024-01-01T00:00:00Z",
                        "interval_end": "2024-01-01T00:30:00Z",
                    }
                ]
            },
        )
        mock_session.request.return_value = response

        result = await rest_client.get_gas_consumption(
            mprn="1234567890",
            meter_serial="G4P12345678",
        )

        assert len(result) == 1
        assert result[0].consumption == 5.678

    @pytest.mark.asyncio
    async def test_get_gas_consumption_invalid_mprn(
        self,
        rest_client: RestClient,
    ) -> None:
        """Test invalid MPRN raises ValidationError."""
        with pytest.raises(ValidationError):
            await rest_client.get_gas_consumption(
                mprn="short",
                meter_serial="G4P12345678",
            )


class TestGetTariffRates:
    """Tests for tariff rate methods."""

    @pytest.mark.asyncio
    async def test_get_electricity_standard_unit_rates(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test fetching electricity unit rates."""
        response = mock_response_factory(
            status=200,
            json_data={
                "results": [
                    {
                        "value_exc_vat": 20.0,
                        "value_inc_vat": 21.0,
                        "valid_from": "2024-01-01T00:00:00Z",
                        "valid_to": "2024-01-01T00:30:00Z",
                    }
                ]
            },
        )
        mock_session.request.return_value = response

        result = await rest_client.get_electricity_standard_unit_rates(
            product_code="AGILE-FLEX-22-11-25",
            tariff_code="E-1R-AGILE-FLEX-22-11-25-J",
        )

        assert len(result) == 1
        assert result[0].value_inc_vat == 21.0

    @pytest.mark.asyncio
    async def test_get_electricity_standing_charge(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test fetching electricity standing charge."""
        response = mock_response_factory(
            status=200,
            json_data={
                "results": [
                    {
                        "value_exc_vat": 45.0,
                        "value_inc_vat": 47.25,
                        "valid_from": "2024-01-01T00:00:00Z",
                    }
                ]
            },
        )
        mock_session.request.return_value = response

        result = await rest_client.get_electricity_standing_charge(
            product_code="FLEX-22-11-25",
            tariff_code="E-1R-FLEX-22-11-25-J",
        )

        assert result == 47.25

    @pytest.mark.asyncio
    async def test_get_electricity_standing_charge_no_results(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test standing charge returns None when no results."""
        response = mock_response_factory(
            status=200,
            json_data={"results": []},
        )
        mock_session.request.return_value = response

        result = await rest_client.get_electricity_standing_charge(
            product_code="FLEX-22-11-25",
            tariff_code="E-1R-FLEX-22-11-25-J",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_gas_standard_unit_rates(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test fetching gas unit rates."""
        response = mock_response_factory(
            status=200,
            json_data={
                "results": [
                    {
                        "value_exc_vat": 6.0,
                        "value_inc_vat": 6.3,
                        "valid_from": "2024-01-01T00:00:00Z",
                    }
                ]
            },
        )
        mock_session.request.return_value = response

        result = await rest_client.get_gas_standard_unit_rates(
            product_code="FLEX-22-11-25",
            tariff_code="G-1R-FLEX-22-11-25-J",
        )

        assert len(result) == 1
        assert result[0].value_inc_vat == 6.3


class TestExtractProductCode:
    """Tests for extract_product_code method."""

    def test_extract_electricity_product_code(self, rest_client: RestClient) -> None:
        """Test extracting product code from electricity tariff."""
        result = rest_client.extract_product_code("E-1R-INTELLI-VAR-22-10-14-J")
        assert result == "INTELLI-VAR-22-10-14"

    def test_extract_gas_product_code(self, rest_client: RestClient) -> None:
        """Test extracting product code from gas tariff."""
        result = rest_client.extract_product_code("G-1R-FLEX-22-11-25-J")
        assert result == "FLEX-22-11-25"

    def test_extract_agile_product_code(self, rest_client: RestClient) -> None:
        """Test extracting Agile product code."""
        result = rest_client.extract_product_code("E-1R-AGILE-FLEX-22-11-25-A")
        assert result == "AGILE-FLEX-22-11-25"

    def test_extract_short_tariff_code(self, rest_client: RestClient) -> None:
        """Test short tariff code returns as-is."""
        result = rest_client.extract_product_code("SHORT")
        assert result == "SHORT"


class TestGetProducts:
    """Tests for product-related methods."""

    @pytest.mark.asyncio
    async def test_get_products_success(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test fetching products list."""
        response = mock_response_factory(
            status=200,
            json_data={
                "results": [
                    {"code": "AGILE-FLEX-22-11-25"},
                    {"code": "GO-VAR-22-10-14"},
                ]
            },
        )
        mock_session.request.return_value = response

        result = await rest_client.get_products()

        assert len(result) == 2
        assert result[0]["code"] == "AGILE-FLEX-22-11-25"

    @pytest.mark.asyncio
    async def test_get_product_success(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test fetching single product."""
        response = mock_response_factory(
            status=200,
            json_data={"code": "AGILE-FLEX-22-11-25", "full_name": "Agile Octopus"},
        )
        mock_session.request.return_value = response

        result = await rest_client.get_product("AGILE-FLEX-22-11-25")

        assert result is not None
        assert result["code"] == "AGILE-FLEX-22-11-25"

    @pytest.mark.asyncio
    async def test_get_product_not_found(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test fetching non-existent product returns None."""
        response = mock_response_factory(status=404)
        mock_session.request.return_value = response

        result = await rest_client.get_product("NONEXISTENT")

        assert result is None


class TestRecentConsumption:
    """Tests for recent consumption helper methods."""

    @pytest.mark.asyncio
    async def test_get_recent_consumption_uses_newest_first(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test get_recent_consumption orders by newest first."""
        response = mock_response_factory(
            status=200,
            json_data={"results": []},
        )
        mock_session.request.return_value = response

        await rest_client.get_recent_consumption(
            mpan="1234567890123",
            meter_serial="20P1234567",
            periods=24,
        )

        call_args = mock_session.request.call_args
        params = call_args[1]["params"]
        assert params["order_by"] == "-period"
        assert params["page_size"] == 24

    @pytest.mark.asyncio
    async def test_get_recent_gas_consumption_uses_newest_first(
        self,
        rest_client: RestClient,
        mock_session: MagicMock,
        mock_response_factory,
    ) -> None:
        """Test get_recent_gas_consumption orders by newest first."""
        response = mock_response_factory(
            status=200,
            json_data={"results": []},
        )
        mock_session.request.return_value = response

        await rest_client.get_recent_gas_consumption(
            mprn="1234567890",
            meter_serial="G4P12345678",
            periods=48,
        )

        call_args = mock_session.request.call_args
        params = call_args[1]["params"]
        assert params["order_by"] == "-period"
        assert params["page_size"] == 48
