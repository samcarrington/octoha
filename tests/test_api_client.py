"""Tests for the main Octoha API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.octoha.api.client import OctohaApiClient
from custom_components.octoha.api.exceptions import (
    AuthenticationError,
    OctopusError,
)
from custom_components.octoha.models.account import Account
from custom_components.octoha.models.dispatch import DispatchStatus


class TestOctohaApiClient:
    """Tests for OctohaApiClient class."""

    @pytest.fixture
    def client(
        self,
        mock_session: MagicMock,
        api_key: str,
        account_number: str,
    ) -> OctohaApiClient:
        """Create an OctohaApiClient instance for testing."""
        return OctohaApiClient(mock_session, api_key, account_number)

    def test_init(
        self,
        client: OctohaApiClient,
        api_key: str,
        account_number: str,
    ) -> None:
        """Test OctohaApiClient initialization."""
        assert client.account_number == account_number
        assert client.account is None
        assert client._token_manager is not None
        assert client._rest_client is not None

    @pytest.mark.asyncio
    async def test_validate_credentials_success(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test validate_credentials returns True for valid key."""
        auth_response = load_fixture("auth_token_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=auth_response,
        )
        client._session.post.return_value = mock_response

        result = await client.validate_credentials()

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_credentials_failure(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test validate_credentials raises AuthenticationError for invalid key."""
        mock_response = mock_response_factory(status=401)
        client._session.post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            await client.validate_credentials()

    @pytest.mark.asyncio
    async def test_get_account_success(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test successful account retrieval."""
        auth_response = load_fixture("auth_token_response.json")
        account_response = load_fixture("account_response.json")

        # Mock token request
        auth_mock = mock_response_factory(status=200, json_data=auth_response)
        # Mock account request
        account_mock = mock_response_factory(status=200, json_data=account_response)

        client._session.post.side_effect = [auth_mock, account_mock]

        result = await client.get_account()

        assert isinstance(result, Account)
        assert result.account_number == "A-FB05ED6C"
        assert result.balance == -12.50
        assert len(result.properties) == 1

        # Check electricity meter
        elec_meter = result.primary_electricity
        assert elec_meter is not None
        assert elec_meter.mpan == "1234567890123"
        assert elec_meter.meter_serial == "20P1234567"

        # Check gas meter
        gas_meter = result.primary_gas
        assert gas_meter is not None
        assert gas_meter.mprn == "1234567890"
        assert gas_meter.meter_serial == "G4P12345678"

    @pytest.mark.asyncio
    async def test_get_account_cached(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test that account is cached after first fetch."""
        auth_response = load_fixture("auth_token_response.json")
        account_response = load_fixture("account_response.json")

        auth_mock = mock_response_factory(status=200, json_data=auth_response)
        account_mock = mock_response_factory(status=200, json_data=account_response)

        client._session.post.side_effect = [auth_mock, account_mock]

        # First call
        result1 = await client.get_account()
        # Second call (should use cache)
        result2 = await client.get_account()

        assert result1 is result2
        # Should only have called API twice (auth + account), not three times
        assert client._session.post.call_count == 2

    @pytest.mark.asyncio
    async def test_get_account_force_refresh(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test force_refresh bypasses cache."""
        auth_response = load_fixture("auth_token_response.json")
        account_response = load_fixture("account_response.json")

        # Set up mock to return auth and account responses
        auth_mock = mock_response_factory(status=200, json_data=auth_response)
        account_mock = mock_response_factory(status=200, json_data=account_response)

        client._session.post.return_value = auth_mock

        # Pre-populate cache by setting _token to avoid auth call
        from datetime import datetime, timedelta, timezone

        client._token_manager._token = "cached_token"
        client._token_manager._token_expires = datetime.now(timezone.utc) + timedelta(
            hours=1
        )
        client._session.post.return_value = account_mock

        # First call
        await client.get_account()
        # Second call with force_refresh
        await client.get_account(force_refresh=True)

        # Should have called API twice for account (not using cache)
        assert client._session.post.call_count == 2

    @pytest.mark.asyncio
    async def test_get_account_no_account_number(
        self,
        mock_session: MagicMock,
        api_key: str,
    ) -> None:
        """Test get_account raises error when no account number set."""
        client = OctohaApiClient(mock_session, api_key, account_number=None)

        with pytest.raises(OctopusError) as exc_info:
            await client.get_account()

        assert "Account number not set" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_dispatches_success(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test successful dispatch retrieval."""
        auth_response = load_fixture("auth_token_response.json")
        dispatches_response = load_fixture("dispatches_response.json")

        auth_mock = mock_response_factory(status=200, json_data=auth_response)
        dispatches_mock = mock_response_factory(
            status=200, json_data=dispatches_response
        )

        client._session.post.side_effect = [auth_mock, dispatches_mock]

        result = await client.get_dispatches()

        assert isinstance(result, DispatchStatus)
        assert len(result.planned_dispatches) == 2
        assert len(result.completed_dispatches) == 2
        assert result.completed_dispatches[0].charge_kwh == 45.2

    @pytest.mark.asyncio
    async def test_get_saving_sessions_success(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test successful saving sessions retrieval."""
        auth_response = load_fixture("auth_token_response.json")
        sessions_response = load_fixture("saving_sessions_response.json")

        auth_mock = mock_response_factory(status=200, json_data=auth_response)
        sessions_mock = mock_response_factory(status=200, json_data=sessions_response)

        client._session.post.side_effect = [auth_mock, sessions_mock]

        result = await client.get_saving_sessions()

        assert len(result) == 2
        assert result[0].code == "SS-2024-01-18"
        assert result[0].reward_per_kwh == 800
        assert result[1].reward_per_kwh == 1200

    @pytest.mark.asyncio
    async def test_close(self, client: OctohaApiClient) -> None:
        """Test close clears cached data."""
        from datetime import datetime, timedelta, timezone

        # Set some cached data
        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(timezone.utc) + timedelta(
            hours=1
        )
        client._account = Account(account_number="A-123")

        await client.close()

        assert client._token_manager._token is None
        assert client._account is None


class TestOctohaApiClientConsumption:
    """Tests for OctohaApiClient consumption methods."""

    @pytest.fixture
    def client(
        self,
        mock_session: MagicMock,
        api_key: str,
        account_number: str,
    ) -> OctohaApiClient:
        """Create an OctohaApiClient instance for testing."""
        return OctohaApiClient(mock_session, api_key, account_number)

    @pytest.mark.asyncio
    async def test_get_electricity_consumption_with_meters(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
        mpan: str,
        meter_serial: str,
    ) -> None:
        """Test electricity consumption with explicit meter params."""
        consumption_response = load_fixture("electricity_consumption_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=consumption_response,
        )
        client._rest_client._session.request.return_value = mock_response

        result = await client.get_electricity_consumption(
            mpan=mpan,
            meter_serial=meter_serial,
        )

        assert len(result) == 5
        assert result[0].consumption == 0.234

    @pytest.mark.asyncio
    async def test_get_gas_consumption_with_meters(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
        mprn: str,
        gas_meter_serial: str,
    ) -> None:
        """Test gas consumption with explicit meter params."""
        consumption_response = load_fixture("gas_consumption_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=consumption_response,
        )
        client._rest_client._session.request.return_value = mock_response

        result = await client.get_gas_consumption(
            mprn=mprn,
            meter_serial=gas_meter_serial,
        )

        assert len(result) == 5
        assert result[0].consumption == 1.234


class TestOctohaApiClientTariff:
    """Tests for OctohaApiClient tariff methods."""

    @pytest.fixture
    def client(
        self,
        mock_session: MagicMock,
        api_key: str,
        account_number: str,
    ) -> OctohaApiClient:
        """Create an OctohaApiClient instance for testing."""
        return OctohaApiClient(mock_session, api_key, account_number)

    def test_format_tariff_name_intelligent(self, client: OctohaApiClient) -> None:
        """Test tariff name formatting for Intelligent Go."""
        result = client._format_tariff_name("INTELLI-VAR-22-10-14")
        assert result == "Intelligent Octopus Go"

    def test_format_tariff_name_agile(self, client: OctohaApiClient) -> None:
        """Test tariff name formatting for Agile."""
        result = client._format_tariff_name("AGILE-FLEX-22-11-25")
        assert result == "Agile Octopus"

    def test_format_tariff_name_go(self, client: OctohaApiClient) -> None:
        """Test tariff name formatting for Octopus Go."""
        result = client._format_tariff_name("GO-VAR-22-10-14")
        assert result == "Octopus Go"

    def test_format_tariff_name_tracker(self, client: OctohaApiClient) -> None:
        """Test tariff name formatting for Tracker."""
        result = client._format_tariff_name("TRACKER-22-11-25")
        assert result == "Octopus Tracker"

    def test_format_tariff_name_flex(self, client: OctohaApiClient) -> None:
        """Test tariff name formatting for Flexible."""
        result = client._format_tariff_name("FLEX-VAR-22-11-25")
        assert result == "Flexible Octopus"

    def test_format_tariff_name_unknown(self, client: OctohaApiClient) -> None:
        """Test tariff name formatting for unknown tariff."""
        result = client._format_tariff_name("SPECIAL-TARIFF-22")
        assert result == "Special Tariff 22"
