"""Tests for the main Octoha API client."""

from __future__ import annotations

from datetime import UTC
from unittest.mock import AsyncMock, MagicMock

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
        from datetime import datetime, timedelta

        client._token_manager._token = "cached_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)
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
        """Test successful dispatch retrieval with device ID (new API)."""
        auth_response = load_fixture("auth_token_response.json")
        account_response = load_fixture("account_with_device_id_response.json")
        dispatches_response = load_fixture("dispatches_new_api_response.json")

        auth_mock = mock_response_factory(status=200, json_data=auth_response)
        account_mock = mock_response_factory(status=200, json_data=account_response)
        dispatches_mock = mock_response_factory(
            status=200, json_data=dispatches_response
        )

        client._session.post.side_effect = [auth_mock, account_mock, dispatches_mock]

        result = await client.get_dispatches()

        assert isinstance(result, DispatchStatus)
        assert len(result.planned_dispatches) == 2
        assert len(result.completed_dispatches) == 2
        assert result.completed_dispatches[0].charge_kwh == 45.2

    @pytest.mark.asyncio
    async def test_get_dispatches_success_legacy(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test successful dispatch retrieval without device ID (legacy API)."""
        auth_response = load_fixture("auth_token_response.json")
        account_response = load_fixture("account_response.json")  # No device ID
        dispatches_response = load_fixture("dispatches_response.json")

        auth_mock = mock_response_factory(status=200, json_data=auth_response)
        account_mock = mock_response_factory(status=200, json_data=account_response)
        dispatches_mock = mock_response_factory(
            status=200, json_data=dispatches_response
        )

        client._session.post.side_effect = [auth_mock, account_mock, dispatches_mock]

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
        from datetime import datetime, timedelta

        # Set some cached data
        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)
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


class TestGraphQLClient:
    """Tests for OctohaApiClient GraphQL functionality."""

    @pytest.fixture
    def client(
        self,
        mock_session: MagicMock,
        api_key: str,
        account_number: str,
    ) -> OctohaApiClient:
        """Create an OctohaApiClient instance for testing."""
        return OctohaApiClient(mock_session, api_key, account_number)

    # ========================================================================
    # Successful GraphQL Request Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_graphql_successful_request_with_data(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test successful GraphQL request returns data."""
        # Arrange
        expected_data = {
            "data": {
                "account": {
                    "number": "A-FB05ED6C",
                    "balance": -12.50,
                }
            }
        }
        mock_response = mock_response_factory(status=200, json_data=expected_data)
        client._session.post.return_value = mock_response

        # Pre-populate token to avoid auth call
        from datetime import datetime, timedelta

        client._token_manager._token = "test_token_123"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act
        result = await client._graphql(
            "query { account { number balance } }",
            variables={"accountNumber": "A-FB05ED6C"},
        )

        # Assert
        assert result == expected_data["data"]
        assert result["account"]["number"] == "A-FB05ED6C"
        assert result["account"]["balance"] == -12.50

    @pytest.mark.asyncio
    async def test_graphql_successful_request_without_variables(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test successful GraphQL request with no variables."""
        # Arrange
        expected_data = {
            "data": {
                "viewer": {
                    "id": "user-123",
                }
            }
        }
        mock_response = mock_response_factory(status=200, json_data=expected_data)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token_123"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act
        result = await client._graphql("query { viewer { id } }")

        # Assert
        assert result == expected_data["data"]
        assert result["viewer"]["id"] == "user-123"

    @pytest.mark.asyncio
    async def test_graphql_successful_request_empty_data(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test GraphQL request that returns empty data object."""
        # Arrange
        expected_data = {"data": {}}
        mock_response = mock_response_factory(status=200, json_data=expected_data)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token_123"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act
        result = await client._graphql("query { empty }")

        # Assert
        assert result == {}

    # ========================================================================
    # 401 Authentication Error Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_graphql_401_raises_authentication_error(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test 401 response raises AuthenticationError."""
        # Arrange
        mock_response = mock_response_factory(status=401, text="Unauthorized")
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "expired_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await client._graphql("query { account { number } }")

        assert "authentication failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_graphql_401_invalidates_token(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test 401 response invalidates cached token."""
        # Arrange
        mock_response = mock_response_factory(status=401)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        token_before = "test_token_123"
        client._token_manager._token = token_before
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act
        with pytest.raises(AuthenticationError):
            await client._graphql("query { account { number } }")

        # Assert
        assert client._token_manager._token is None

    @pytest.mark.asyncio
    async def test_graphql_401_status_code_in_error(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test AuthenticationError includes status code."""
        # Arrange
        mock_response = mock_response_factory(status=401)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await client._graphql("query { account { number } }")

        assert exc_info.value.status_code == 401

    # ========================================================================
    # Non-401 HTTP Error Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_graphql_500_error_raises_octopus_error(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test 500 HTTP error raises OctopusError."""
        # Arrange
        mock_response = mock_response_factory(status=500, text="Internal Server Error")
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError) as exc_info:
            await client._graphql("query { account { number } }")

        assert "HTTP 500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_graphql_503_error_includes_status_code(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test 503 error includes status code in exception."""
        # Arrange
        mock_response = mock_response_factory(status=503, text="Service Unavailable")
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError) as exc_info:
            await client._graphql("query { test }")

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_graphql_400_error_with_sanitized_message(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test 400 error with potentially sensitive error text."""
        # Arrange
        sensitive_text = "Invalid query: sk_live_secret_key_12345"
        mock_response = mock_response_factory(status=400, text=sensitive_text)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError) as exc_info:
            await client._graphql("query { test }")

        # Message should be generic, not exposing the sensitive error text
        assert "HTTP 400" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_graphql_429_rate_limit_error(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test 429 rate limit error."""
        # Arrange
        mock_response = mock_response_factory(status=429, text="Too Many Requests")
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError) as exc_info:
            await client._graphql("query { test }")

        assert "HTTP 429" in str(exc_info.value)

    # ========================================================================
    # GraphQL-Level Error Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_graphql_graphql_errors_in_response(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test GraphQL-level errors raise OctopusError."""
        # Arrange
        graphql_error_response = {
            "data": None,
            "errors": [
                {
                    "message": "Field 'unknown' doesn't exist on type 'Query'",
                    "locations": [{"line": 1, "column": 10}],
                }
            ],
        }
        mock_response = mock_response_factory(
            status=200, json_data=graphql_error_response
        )
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError) as exc_info:
            await client._graphql("query { unknown }")

        assert "GraphQL request returned errors" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_graphql_multiple_graphql_errors(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test multiple GraphQL errors in response."""
        # Arrange
        graphql_error_response = {
            "data": None,
            "errors": [
                {"message": "Validation error: account required"},
                {"message": "Validation error: invalid variable type"},
            ],
        }
        mock_response = mock_response_factory(
            status=200, json_data=graphql_error_response
        )
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError):
            await client._graphql("query { invalid }")

    @pytest.mark.asyncio
    async def test_graphql_error_without_message_field(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test GraphQL error object without message field."""
        # Arrange
        graphql_error_response = {
            "data": None,
            "errors": [
                {"code": "INVALID_QUERY"},  # No message field
            ],
        }
        mock_response = mock_response_factory(
            status=200, json_data=graphql_error_response
        )
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError):
            await client._graphql("query { test }")

    # ========================================================================
    # Auth-Related GraphQL Error Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_graphql_authentication_error_message_invalidates_token(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test auth-related GraphQL error invalidates token."""
        # Arrange
        graphql_error_response = {
            "data": None,
            "errors": [
                {"message": "Authentication required"},
            ],
        }
        mock_response = mock_response_factory(
            status=200, json_data=graphql_error_response
        )
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "expired_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(AuthenticationError):
            await client._graphql("query { account { number } }")

        assert client._token_manager._token is None

    @pytest.mark.asyncio
    async def test_graphql_unauthorized_error_message_invalidates_token(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test 'unauthorized' in error message invalidates token."""
        # Arrange
        graphql_error_response = {
            "data": None,
            "errors": [
                {"message": "User is unauthorized to access this field"},
            ],
        }
        mock_response = mock_response_factory(
            status=200, json_data=graphql_error_response
        )
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        token_before = "test_token"
        client._token_manager._token = token_before
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await client._graphql("query { secret }")

        # Verify token was invalidated
        assert client._token_manager._token is None
        assert "GraphQL authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_graphql_case_insensitive_auth_error_detection(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test auth error detection is case-insensitive."""
        # Arrange
        graphql_error_response = {
            "data": None,
            "errors": [
                {"message": "UNAUTHORIZED ACCESS DENIED"},
            ],
        }
        mock_response = mock_response_factory(
            status=200, json_data=graphql_error_response
        )
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(AuthenticationError):
            await client._graphql("query { test }")

    @pytest.mark.asyncio
    async def test_graphql_non_auth_error_preserves_token(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test non-auth GraphQL errors don't invalidate token."""
        # Arrange
        graphql_error_response = {
            "data": None,
            "errors": [
                {"message": "Rate limit exceeded"},
            ],
        }
        mock_response = mock_response_factory(
            status=200, json_data=graphql_error_response
        )
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        token_before = "test_token"
        client._token_manager._token = token_before
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError):
            await client._graphql("query { test }")

        # Token should still be present
        assert client._token_manager._token == token_before

    # ========================================================================
    # Network/Connection Error Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_graphql_network_error_raises_octopus_error(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test network error raises OctopusError."""
        # Arrange
        client._session.post.side_effect = TimeoutError("Connection timeout")

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError) as exc_info:
            await client._graphql("query { test }")

        assert "GraphQL request failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_graphql_json_decode_error_raises_octopus_error(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test invalid JSON response raises OctopusError."""
        # Arrange
        mock_response = mock_response_factory(status=200)
        # Make json() raise an exception
        import json

        mock_response.json = AsyncMock(
            side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
        )
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError) as exc_info:
            await client._graphql("query { test }")

        assert "GraphQL request failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_graphql_connection_error_raises_octopus_error(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test connection error raises OctopusError."""
        # Arrange
        client._session.post.side_effect = ConnectionError("Failed to connect")

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError):
            await client._graphql("query { test }")

    @pytest.mark.asyncio
    async def test_graphql_network_error_preserves_token(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test network errors don't invalidate token."""
        # Arrange
        client._session.post.side_effect = TimeoutError("Timeout")

        from datetime import datetime, timedelta

        token_before = "test_token"
        client._token_manager._token = token_before
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(OctopusError):
            await client._graphql("query { test }")

        # Token should still be present
        assert client._token_manager._token == token_before

    # ========================================================================
    # Request Construction Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_graphql_sends_correct_headers(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test GraphQL request includes correct headers."""
        # Arrange
        expected_data = {"data": {"result": "ok"}}
        mock_response = mock_response_factory(status=200, json_data=expected_data)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        test_token = "Bearer test_token_xyz"
        client._token_manager._token = test_token
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        query = "query { test }"

        # Act
        await client._graphql(query)

        # Assert
        assert client._session.post.called
        call_args = client._session.post.call_args
        assert call_args.kwargs["headers"]["Authorization"] == test_token
        assert call_args.kwargs["headers"]["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_graphql_sends_correct_payload(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test GraphQL request sends correct payload structure."""
        # Arrange
        expected_data = {"data": {"result": "ok"}}
        mock_response = mock_response_factory(status=200, json_data=expected_data)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        query = "query { test }"
        variables = {"var1": "value1", "var2": 123}

        # Act
        await client._graphql(query, variables)

        # Assert
        assert client._session.post.called
        call_args = client._session.post.call_args
        payload = call_args.kwargs["json"]
        assert payload["query"] == query
        assert payload["variables"] == variables

    @pytest.mark.asyncio
    async def test_graphql_sends_empty_variables_when_not_provided(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test GraphQL request sends empty variables dict when not provided."""
        # Arrange
        expected_data = {"data": {"result": "ok"}}
        mock_response = mock_response_factory(status=200, json_data=expected_data)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        query = "query { test }"

        # Act
        await client._graphql(query)

        # Assert
        call_args = client._session.post.call_args
        payload = call_args.kwargs["json"]
        assert payload["variables"] == {}

    # ========================================================================
    # Edge Cases
    # ========================================================================

    @pytest.mark.asyncio
    async def test_graphql_response_with_data_and_errors(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test response with both data and errors raises OctopusError."""
        # Arrange
        response_with_both = {
            "data": {"account": {"number": "A-123"}},
            "errors": [{"message": "Field 'unknown' is invalid"}],
        }
        mock_response = mock_response_factory(status=200, json_data=response_with_both)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act & Assert
        # Errors take precedence over data
        with pytest.raises(OctopusError):
            await client._graphql("query { account { number } }")

    @pytest.mark.asyncio
    async def test_graphql_response_missing_data_key(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test response without 'data' key returns empty dict."""
        # Arrange
        response_no_data = {"result": "ok"}
        mock_response = mock_response_factory(status=200, json_data=response_no_data)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act
        result = await client._graphql("query { test }")

        # Assert
        assert result == {}

    @pytest.mark.asyncio
    async def test_graphql_complex_nested_response(
        self,
        client: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test complex nested GraphQL response is returned correctly."""
        # Arrange
        complex_response = {
            "data": {
                "account": {
                    "number": "A-123",
                    "properties": [
                        {
                            "address": "123 Main St",
                            "meters": [
                                {
                                    "type": "electricity",
                                    "readings": [
                                        {"date": "2024-01-01", "value": 123.45}
                                    ],
                                }
                            ],
                        }
                    ],
                }
            }
        }
        mock_response = mock_response_factory(status=200, json_data=complex_response)
        client._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client._token_manager._token = "test_token"
        client._token_manager._token_expires = datetime.now(UTC) + timedelta(hours=1)

        # Act
        result = await client._graphql("query { account { ... } }")

        # Assert
        assert result == complex_response["data"]
        readings = result["account"]["properties"][0]["meters"][0]["readings"]
        assert readings[0]["value"] == 123.45


class TestAccountDiscovery:
    """Tests for OctohaApiClient.discover_account_number() method."""

    @pytest.fixture
    def client_no_account(
        self,
        mock_session: MagicMock,
        api_key: str,
    ) -> OctohaApiClient:
        """Create an OctohaApiClient instance without account number."""
        return OctohaApiClient(mock_session, api_key, account_number=None)

    # ========================================================================
    # Successful Discovery Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_discover_account_number_success(
        self,
        client_no_account: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test successful account number discovery from API."""
        # Arrange
        discovery_response = load_fixture("account_discovery_response.json")
        mock_response = mock_response_factory(status=200, json_data=discovery_response)
        client_no_account._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client_no_account._token_manager._token = "test_token"
        client_no_account._token_manager._token_expires = datetime.now(UTC) + timedelta(
            hours=1
        )

        # Act
        result = await client_no_account.discover_account_number()

        # Assert
        assert result == "A-FB05ED6C"

    @pytest.mark.asyncio
    async def test_discover_account_number_caches_result(
        self,
        client_no_account: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test that discovered account number is cached in _account_number."""
        # Arrange
        discovery_response = load_fixture("account_discovery_response.json")
        mock_response = mock_response_factory(status=200, json_data=discovery_response)
        client_no_account._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client_no_account._token_manager._token = "test_token"
        client_no_account._token_manager._token_expires = datetime.now(UTC) + timedelta(
            hours=1
        )

        # Verify initial state
        assert client_no_account._account_number is None

        # Act
        await client_no_account.discover_account_number()

        # Assert - account number should be cached
        assert client_no_account._account_number == "A-FB05ED6C"
        assert client_no_account.account_number == "A-FB05ED6C"

    # ========================================================================
    # Error Condition Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_discover_account_number_no_accounts(
        self,
        client_no_account: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test error when no accounts found for API key."""
        # Arrange
        empty_response = {"data": {"viewer": {"accounts": {"edges": []}}}}
        mock_response = mock_response_factory(status=200, json_data=empty_response)
        client_no_account._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client_no_account._token_manager._token = "test_token"
        client_no_account._token_manager._token_expires = datetime.now(UTC) + timedelta(
            hours=1
        )

        # Act & Assert
        with pytest.raises(OctopusError) as exc_info:
            await client_no_account.discover_account_number()

        assert "No accounts found for this API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_discover_account_number_missing_number_field(
        self,
        client_no_account: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test error when node exists but number field is missing."""
        # Arrange
        response_no_number = {
            "data": {
                "viewer": {
                    "accounts": {
                        "edges": [
                            {
                                "node": {}  # No number field
                            }
                        ]
                    }
                }
            }
        }
        mock_response = mock_response_factory(status=200, json_data=response_no_number)
        client_no_account._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client_no_account._token_manager._token = "test_token"
        client_no_account._token_manager._token_expires = datetime.now(UTC) + timedelta(
            hours=1
        )

        # Act & Assert
        with pytest.raises(OctopusError) as exc_info:
            await client_no_account.discover_account_number()

        assert "Could not extract account number" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_discover_account_number_empty_viewer(
        self,
        client_no_account: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test error when viewer object is empty."""
        # Arrange
        empty_viewer_response = {"data": {"viewer": {}}}
        mock_response = mock_response_factory(
            status=200, json_data=empty_viewer_response
        )
        client_no_account._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client_no_account._token_manager._token = "test_token"
        client_no_account._token_manager._token_expires = datetime.now(UTC) + timedelta(
            hours=1
        )

        # Act & Assert
        with pytest.raises(OctopusError) as exc_info:
            await client_no_account.discover_account_number()

        assert "No accounts found" in str(exc_info.value)

    # ========================================================================
    # Multiple Accounts Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_discover_account_number_multiple_accounts_uses_first(
        self,
        client_no_account: OctohaApiClient,
        mock_response_factory,
    ) -> None:
        """Test that when multiple accounts exist, the first one is used."""
        # Arrange
        multi_account_response = {
            "data": {
                "viewer": {
                    "accounts": {
                        "edges": [
                            {"node": {"number": "A-FIRST123"}},
                            {"node": {"number": "A-SECOND456"}},
                            {"node": {"number": "A-THIRD789"}},
                        ]
                    }
                }
            }
        }
        mock_response = mock_response_factory(
            status=200, json_data=multi_account_response
        )
        client_no_account._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client_no_account._token_manager._token = "test_token"
        client_no_account._token_manager._token_expires = datetime.now(UTC) + timedelta(
            hours=1
        )

        # Act
        result = await client_no_account.discover_account_number()

        # Assert - should use the first account
        assert result == "A-FIRST123"
        assert client_no_account._account_number == "A-FIRST123"

    @pytest.mark.asyncio
    async def test_discover_account_number_multiple_accounts_logs_warning(
        self,
        client_no_account: OctohaApiClient,
        mock_response_factory,
        caplog,
    ) -> None:
        """Test that a warning is logged when multiple accounts are found."""
        import logging

        # Arrange
        multi_account_response = {
            "data": {
                "viewer": {
                    "accounts": {
                        "edges": [
                            {"node": {"number": "A-FIRST123"}},
                            {"node": {"number": "A-SECOND456"}},
                        ]
                    }
                }
            }
        }
        mock_response = mock_response_factory(
            status=200, json_data=multi_account_response
        )
        client_no_account._session.post.return_value = mock_response

        from datetime import datetime, timedelta

        client_no_account._token_manager._token = "test_token"
        client_no_account._token_manager._token_expires = datetime.now(UTC) + timedelta(
            hours=1
        )

        # Act
        with caplog.at_level(logging.WARNING):
            await client_no_account.discover_account_number()

        # Assert - warning should be logged
        assert "Multiple accounts found" in caplog.text
        assert "2" in caplog.text  # Number of accounts
        assert "A-FIRST123" in caplog.text  # Account being used


class TestAccountParsing:
    """Tests for OctohaApiClient._parse_account() edge cases."""

    @pytest.fixture
    def client(
        self,
        mock_session: MagicMock,
        api_key: str,
        account_number: str,
    ) -> OctohaApiClient:
        """Create an OctohaApiClient instance for testing."""
        return OctohaApiClient(mock_session, api_key, account_number)

    # ========================================================================
    # Missing Data Edge Cases
    # ========================================================================

    def test_parse_account_empty_properties(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing account with no properties."""
        data = {
            "number": "A-123456",
            "balance": -10.50,
            "properties": [],
        }

        result = client._parse_account(data)

        assert result.account_number == "A-123456"
        assert result.balance == -10.50
        assert result.properties == []
        assert result.primary_electricity is None
        assert result.primary_gas is None

    def test_parse_account_missing_properties_key(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing account without properties key."""
        data = {
            "number": "A-123456",
            "balance": 0,
        }

        result = client._parse_account(data)

        assert result.account_number == "A-123456"
        assert result.properties == []

    def test_parse_account_no_electricity_meters(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing account with property but no electricity meters."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [],
                    "gasMeterPoints": [
                        {
                            "mprn": "1234567890",
                            "meters": [{"serialNumber": "G4P12345678"}],
                            "agreements": [],
                        }
                    ],
                }
            ],
        }

        result = client._parse_account(data)

        assert result.primary_electricity is None
        assert result.primary_gas is not None
        assert result.primary_gas.mprn == "1234567890"

    def test_parse_account_no_gas_meters(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing account with property but no gas meters."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1234567890123",
                            "meters": [{"serialNumber": "20P1234567"}],
                            "agreements": [],
                        }
                    ],
                    "gasMeterPoints": [],
                }
            ],
        }

        result = client._parse_account(data)

        assert result.primary_electricity is not None
        assert result.primary_electricity.mpan == "1234567890123"
        assert result.primary_gas is None

    def test_parse_account_empty_meters_list(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing meter point with empty meters array."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1234567890123",
                            "meters": [],  # No meters registered
                            "agreements": [],
                        }
                    ],
                    "gasMeterPoints": [],
                }
            ],
        }

        result = client._parse_account(data)

        elec = result.primary_electricity
        assert elec is not None
        assert elec.meter_serial == ""  # Should be empty, not error
        assert elec.is_smart is False  # No meters means not smart

    def test_parse_account_missing_serial_number(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing meter without serialNumber field."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1234567890123",
                            "meters": [{}],  # Meter without serialNumber
                            "agreements": [],
                        }
                    ],
                    "gasMeterPoints": [],
                }
            ],
        }

        # This should raise KeyError - test the current behavior
        with pytest.raises(KeyError):
            client._parse_account(data)

    # ========================================================================
    # Agreement Edge Cases
    # ========================================================================

    def test_parse_account_empty_agreements(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing meter point with no agreements."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1234567890123",
                            "meters": [{"serialNumber": "20P1234567"}],
                            "agreements": [],
                        }
                    ],
                    "gasMeterPoints": [],
                }
            ],
        }

        result = client._parse_account(data)

        elec = result.primary_electricity
        assert elec is not None
        assert elec.agreements == []

    def test_parse_account_agreement_without_tariff_code(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing agreement with missing tariff code."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1234567890123",
                            "meters": [{"serialNumber": "20P1234567"}],
                            "agreements": [
                                {
                                    "validFrom": "2024-01-01T00:00:00Z",
                                    "validTo": None,
                                    "tariff": {},  # No tariffCode
                                }
                            ],
                        }
                    ],
                    "gasMeterPoints": [],
                }
            ],
        }

        result = client._parse_account(data)

        elec = result.primary_electricity
        assert elec is not None
        # Agreement without tariff_code should be skipped
        assert len(elec.agreements) == 0

    def test_parse_account_agreement_missing_tariff_object(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing agreement without tariff object."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1234567890123",
                            "meters": [{"serialNumber": "20P1234567"}],
                            "agreements": [
                                {
                                    "validFrom": "2024-01-01T00:00:00Z",
                                    "validTo": None,
                                    # No tariff field at all
                                }
                            ],
                        }
                    ],
                    "gasMeterPoints": [],
                }
            ],
        }

        result = client._parse_account(data)

        elec = result.primary_electricity
        assert elec is not None
        # Agreement without tariff should be skipped
        assert len(elec.agreements) == 0

    def test_parse_account_multiple_agreements(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing meter with multiple agreements."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1234567890123",
                            "meters": [{"serialNumber": "20P1234567"}],
                            "agreements": [
                                {
                                    "validFrom": "2024-01-01T00:00:00Z",
                                    "validTo": "2024-06-30T00:00:00Z",
                                    "tariff": {
                                        "tariffCode": "E-1R-OLD-TARIFF-22-J",
                                    },
                                },
                                {
                                    "validFrom": "2024-07-01T00:00:00Z",
                                    "validTo": None,
                                    "tariff": {
                                        "tariffCode": "E-1R-INTELLI-VAR-22-10-14-J",
                                    },
                                },
                            ],
                        }
                    ],
                    "gasMeterPoints": [],
                }
            ],
        }

        result = client._parse_account(data)

        elec = result.primary_electricity
        assert elec is not None
        assert len(elec.agreements) == 2
        assert elec.agreements[0].tariff_code == "E-1R-OLD-TARIFF-22-J"
        assert elec.agreements[1].tariff_code == "E-1R-INTELLI-VAR-22-10-14-J"

    # ========================================================================
    # Balance Edge Cases
    # ========================================================================

    def test_parse_account_missing_balance(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing account without balance field."""
        data = {
            "number": "A-123456",
            # No balance field
            "properties": [],
        }

        result = client._parse_account(data)

        assert result.balance == 0.0

    def test_parse_account_null_balance(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing account with null balance."""
        data = {
            "number": "A-123456",
            "balance": None,
            "properties": [],
        }

        # float(None) raises TypeError - test current behavior
        with pytest.raises(TypeError):
            client._parse_account(data)

    def test_parse_account_string_balance(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing account with string balance (API quirk)."""
        data = {
            "number": "A-123456",
            "balance": "-15.75",  # String instead of number
            "properties": [],
        }

        result = client._parse_account(data)

        assert result.balance == -15.75

    # ========================================================================
    # Multiple Properties Edge Cases
    # ========================================================================

    def test_parse_account_multiple_properties(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test parsing account with multiple properties."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Home St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1111111111111",
                            "meters": [{"serialNumber": "ELEC1"}],
                            "agreements": [],
                        }
                    ],
                    "gasMeterPoints": [],
                },
                {
                    "addressLine1": "456 Holiday Cottage",
                    "postcode": "SW1A 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "2222222222222",
                            "meters": [{"serialNumber": "ELEC2"}],
                            "agreements": [],
                        }
                    ],
                    "gasMeterPoints": [],
                },
            ],
        }

        result = client._parse_account(data)

        assert len(result.properties) == 2
        assert result.properties[0].address_line_1 == "123 Home St"
        assert result.properties[1].address_line_1 == "456 Holiday Cottage"
        # Primary meter should be from first property
        assert result.primary_electricity.mpan == "1111111111111"


class TestDeviceIdDiscovery:
    """Tests for device ID discovery and extraction from account data."""

    @pytest.fixture
    def client(
        self,
        mock_session: MagicMock,
        api_key: str,
        account_number: str,
    ) -> OctohaApiClient:
        """Create an OctohaApiClient instance for testing."""
        return OctohaApiClient(mock_session, api_key, account_number)

    # ========================================================================
    # Device ID Parsing Tests
    # ========================================================================

    def test_parse_account_extracts_device_id(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test that device ID is extracted from smartDevices."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1234567890123",
                            "meters": [
                                {
                                    "serialNumber": "20P1234567",
                                    "smartDevices": [
                                        {"deviceId": "smart-meter-device-001"}
                                    ],
                                }
                            ],
                            "agreements": [],
                        }
                    ],
                    "gasMeterPoints": [],
                }
            ],
        }

        result = client._parse_account(data)

        elec = result.primary_electricity
        assert elec is not None
        assert elec.device_id == "smart-meter-device-001"

    def test_parse_account_device_id_none_when_no_smart_devices(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test that device ID is None when smartDevices is empty."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1234567890123",
                            "meters": [
                                {
                                    "serialNumber": "20P1234567",
                                    "smartDevices": [],
                                }
                            ],
                            "agreements": [],
                        }
                    ],
                    "gasMeterPoints": [],
                }
            ],
        }

        result = client._parse_account(data)

        elec = result.primary_electricity
        assert elec is not None
        assert elec.device_id is None

    def test_parse_account_device_id_none_when_missing_smart_devices(
        self,
        client: OctohaApiClient,
    ) -> None:
        """Test that device ID is None when smartDevices key is missing."""
        data = {
            "number": "A-123456",
            "balance": 0,
            "properties": [
                {
                    "addressLine1": "123 Test St",
                    "postcode": "EH1 1AA",
                    "electricityMeterPoints": [
                        {
                            "mpan": "1234567890123",
                            "meters": [
                                {
                                    "serialNumber": "20P1234567",
                                    # No smartDevices key
                                }
                            ],
                            "agreements": [],
                        }
                    ],
                    "gasMeterPoints": [],
                }
            ],
        }

        result = client._parse_account(data)

        elec = result.primary_electricity
        assert elec is not None
        assert elec.device_id is None

    # ========================================================================
    # Device Discovery Method Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_electricity_device_id_returns_device_id(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test get_electricity_device_id returns device ID when available."""
        # Use a fixture with device ID
        auth_response = load_fixture("auth_token_response.json")
        account_response = load_fixture("account_with_device_id_response.json")

        auth_mock = mock_response_factory(status=200, json_data=auth_response)
        account_mock = mock_response_factory(status=200, json_data=account_response)

        client._session.post.side_effect = [auth_mock, account_mock]

        result = await client.get_electricity_device_id()

        assert result == "smart-meter-device-001"

    @pytest.mark.asyncio
    async def test_get_electricity_device_id_returns_none_when_no_device(
        self,
        client: OctohaApiClient,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test get_electricity_device_id returns None when no device available."""
        auth_response = load_fixture("auth_token_response.json")
        account_response = load_fixture("account_response.json")  # No device ID

        auth_mock = mock_response_factory(status=200, json_data=auth_response)
        account_mock = mock_response_factory(status=200, json_data=account_response)

        client._session.post.side_effect = [auth_mock, account_mock]

        result = await client.get_electricity_device_id()

        assert result is None
