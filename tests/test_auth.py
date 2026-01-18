"""Tests for the Octoha API client authentication."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.octoha.api.auth import TokenManager
from custom_components.octoha.api.exceptions import (
    AuthenticationError,
    InvalidResponseError,
)


class TestTokenManager:
    """Tests for TokenManager class."""

    @pytest.fixture
    def token_manager(self, mock_session: MagicMock, api_key: str) -> TokenManager:
        """Create a TokenManager instance for testing."""
        return TokenManager(mock_session, api_key)

    def test_init(self, token_manager: TokenManager, api_key: str) -> None:
        """Test TokenManager initialization."""
        assert token_manager.api_key == api_key
        assert token_manager._token is None
        assert token_manager._token_expires is None

    def test_is_token_valid_no_token(self, token_manager: TokenManager) -> None:
        """Test is_token_valid returns False when no token."""
        assert token_manager.is_token_valid is False

    def test_is_token_valid_expired(self, token_manager: TokenManager) -> None:
        """Test is_token_valid returns False when token is expired."""
        token_manager._token = "test_token"
        # Set expiry in the past
        token_manager._token_expires = datetime(2020, 1, 1, tzinfo=timezone.utc)
        assert token_manager.is_token_valid is False

    def test_is_token_valid_within_buffer(self, token_manager: TokenManager) -> None:
        """Test is_token_valid returns False when within expiry buffer."""
        token_manager._token = "test_token"
        # Set expiry to 3 minutes from now (less than 5 minute buffer)
        from datetime import timedelta

        token_manager._token_expires = datetime.now(timezone.utc) + timedelta(minutes=3)
        assert token_manager.is_token_valid is False

    def test_is_token_valid_fresh(self, token_manager: TokenManager) -> None:
        """Test is_token_valid returns True for fresh token."""
        token_manager._token = "test_token"
        # Set expiry to 30 minutes from now
        from datetime import timedelta

        token_manager._token_expires = datetime.now(timezone.utc) + timedelta(minutes=30)
        assert token_manager.is_token_valid is True

    @pytest.mark.asyncio
    async def test_get_token_cached(
        self,
        token_manager: TokenManager,
    ) -> None:
        """Test get_token returns cached token when valid."""
        from datetime import timedelta

        token_manager._token = "cached_token"
        token_manager._token_expires = datetime.now(timezone.utc) + timedelta(minutes=30)

        result = await token_manager.get_token()

        assert result == "cached_token"
        # Should not have called the session
        token_manager._session.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_token_fetches_new(
        self,
        token_manager: TokenManager,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test get_token fetches new token when expired."""
        auth_response = load_fixture("auth_token_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=auth_response,
        )
        token_manager._session.post.return_value = mock_response

        result = await token_manager.get_token()

        expected_token = auth_response["data"]["obtainKrakenToken"]["token"]
        assert result == expected_token
        assert token_manager._token == expected_token
        assert token_manager._token_expires is not None
        token_manager._session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_token_auth_error_401(
        self,
        token_manager: TokenManager,
        mock_response_factory,
    ) -> None:
        """Test get_token raises AuthenticationError on 401."""
        mock_response = mock_response_factory(status=401)
        token_manager._session.post.return_value = mock_response

        with pytest.raises(AuthenticationError) as exc_info:
            await token_manager.get_token()

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_token_auth_error_429(
        self,
        token_manager: TokenManager,
        mock_response_factory,
    ) -> None:
        """Test get_token raises AuthenticationError on 429 rate limit."""
        mock_response = mock_response_factory(status=429)
        token_manager._session.post.return_value = mock_response

        with pytest.raises(AuthenticationError) as exc_info:
            await token_manager.get_token()

        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_get_token_graphql_error(
        self,
        token_manager: TokenManager,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test get_token raises AuthenticationError on GraphQL error."""
        error_response = load_fixture("auth_error_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=error_response,
        )
        token_manager._session.post.return_value = mock_response

        with pytest.raises(AuthenticationError) as exc_info:
            await token_manager.get_token()

        # Error message is now sanitized - check for generic message
        assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_token_invalid_response(
        self,
        token_manager: TokenManager,
        mock_response_factory,
    ) -> None:
        """Test get_token raises InvalidResponseError on unexpected format."""
        mock_response = mock_response_factory(
            status=200,
            json_data={"data": {"unexpected": "format"}},
        )
        token_manager._session.post.return_value = mock_response

        with pytest.raises(InvalidResponseError):
            await token_manager.get_token()

    def test_invalidate_token(self, token_manager: TokenManager) -> None:
        """Test invalidate_token clears cached token."""
        from datetime import timedelta

        token_manager._token = "test_token"
        token_manager._token_expires = datetime.now(timezone.utc) + timedelta(hours=1)

        token_manager.invalidate_token()

        assert token_manager._token is None
        assert token_manager._token_expires is None
        assert token_manager.is_token_valid is False

    @pytest.mark.asyncio
    async def test_validate_api_key_success(
        self,
        token_manager: TokenManager,
        mock_response_factory,
        load_fixture,
    ) -> None:
        """Test validate_api_key returns True for valid key."""
        auth_response = load_fixture("auth_token_response.json")

        mock_response = mock_response_factory(
            status=200,
            json_data=auth_response,
        )
        token_manager._session.post.return_value = mock_response

        result = await token_manager.validate_api_key()

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_api_key_failure(
        self,
        token_manager: TokenManager,
        mock_response_factory,
    ) -> None:
        """Test validate_api_key raises AuthenticationError for invalid key."""
        mock_response = mock_response_factory(status=401)
        token_manager._session.post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            await token_manager.validate_api_key()
