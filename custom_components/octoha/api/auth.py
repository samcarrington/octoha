"""Authentication and token management for Octopus Energy GraphQL API.

Token management adapted from the open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import aiohttp

from ..const import GRAPHQL_URL, REQUEST_TIMEOUT, TOKEN_EXPIRY_BUFFER, TOKEN_LIFETIME
from .exceptions import (
    AuthenticationError,
    InvalidResponseError,
    RateLimitError,
    sanitize_log_message,
)

_LOGGER = logging.getLogger(__name__)

# GraphQL mutation for obtaining authentication token
OBTAIN_TOKEN_MUTATION = """
mutation krakenTokenAuthentication($apiKey: String!) {
  obtainKrakenToken(input: { APIKey: $apiKey }) {
    token
  }
}
"""


class TokenManager:
    """Manages authentication tokens for the Octopus Energy GraphQL API.

    Tokens are valid for approximately 55 minutes. This manager handles
    automatic refresh with a configurable buffer before expiry.

    Attributes:
        api_key: The Octopus Energy API key.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
    ) -> None:
        """Initialize the token manager.

        Args:
            session: aiohttp client session for HTTP requests.
            api_key: Octopus Energy API key.
        """
        self._session = session
        self._api_key = api_key
        self._token: str | None = None
        self._token_expires: datetime | None = None

    @property
    def api_key(self) -> str:
        """Return the API key."""
        return self._api_key

    @property
    def is_token_valid(self) -> bool:
        """Check if the current token is valid.

        Returns:
            True if token exists and hasn't expired (with buffer).
        """
        if self._token is None or self._token_expires is None:
            return False

        now = datetime.now(UTC)
        expires_with_buffer = self._token_expires - TOKEN_EXPIRY_BUFFER
        return now < expires_with_buffer

    async def get_token(self) -> str:
        """Get a valid authentication token.

        If the current token is expired or about to expire, a new token
        is obtained from the API.

        Returns:
            Valid authentication token.

        Raises:
            AuthenticationError: If authentication fails.
        """
        if self.is_token_valid and self._token is not None:
            _LOGGER.debug("Using cached token")
            return self._token

        _LOGGER.debug("Token expired or missing, obtaining new token")
        return await self._obtain_new_token()

    async def _obtain_new_token(self) -> str:
        """Obtain a new token from the GraphQL API.

        Returns:
            New authentication token.

        Raises:
            AuthenticationError: If authentication fails.
            InvalidResponseError: If response format is unexpected.
        """
        payload = {
            "query": OBTAIN_TOKEN_MUTATION,
            "variables": {"apiKey": self._api_key},
        }

        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

        try:
            async with self._session.post(
                GRAPHQL_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            ) as response:
                if response.status == 401:
                    raise AuthenticationError(
                        "Invalid API key",
                        status_code=401,
                    )

                if response.status == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_seconds: int | None = None
                    if retry_after:
                        try:
                            retry_seconds = int(retry_after)
                        except ValueError:
                            _LOGGER.warning(
                                "Invalid Retry-After header value: %s", retry_after
                            )
                    raise RateLimitError(
                        "Rate limited during authentication",
                        retry_after=retry_seconds,
                        status_code=429,
                    )

                if response.status != 200:
                    text = await response.text()
                    # Log full details for debugging, but sanitize user-facing message
                    _LOGGER.error(
                        "Authentication failed: HTTP %s: %s",
                        response.status,
                        sanitize_log_message(text),
                    )
                    raise AuthenticationError(
                        f"Authentication failed (HTTP {response.status})",
                        status_code=response.status,
                    )

                data = await response.json()

        except (AuthenticationError, RateLimitError):
            raise
        except Exception as err:
            _LOGGER.exception("Failed to obtain authentication token")
            raise AuthenticationError("Failed to connect to Octopus API") from err

        return self._extract_token(data)

    def _extract_token(self, data: dict) -> str:
        """Extract and store token from API response.

        Args:
            data: GraphQL response data.

        Returns:
            Authentication token.

        Raises:
            AuthenticationError: If token is not present in response.
            RateLimitError: If rate limited.
            InvalidResponseError: If response format is unexpected.
        """
        # Check for GraphQL errors
        if "errors" in data:
            errors = data["errors"]
            error_messages = [e.get("message", str(e)) for e in errors]
            
            # Check for rate limiting errors
            for error in errors:
                msg = error.get("message", "").lower()
                extensions = error.get("extensions", {})
                error_code = extensions.get("errorCode", "")
                
                if "too many requests" in msg or error_code == "KT-CT-1199":
                    _LOGGER.warning(
                        "Rate limited during authentication: %s",
                        [sanitize_log_message(m) for m in error_messages],
                    )
                    raise RateLimitError(
                        "Rate limited: too many authentication requests"
                    )
            
            _LOGGER.error(
                "GraphQL errors during authentication: %s",
                [sanitize_log_message(msg) for msg in error_messages],
            )
            # Provide generic message to user, details are in logs
            raise AuthenticationError(
                "Authentication failed: invalid credentials or API error"
            )

        # Extract token from response
        try:
            token = data["data"]["obtainKrakenToken"]["token"]
        except (KeyError, TypeError) as err:
            _LOGGER.error("Unexpected authentication response: %s", data)
            raise InvalidResponseError(
                "Unexpected authentication response format"
            ) from err

        if not token:
            raise AuthenticationError("No token returned from authentication")

        # Store token with expiry time
        self._token = token
        self._token_expires = datetime.now(UTC) + TOKEN_LIFETIME

        _LOGGER.debug("Obtained new authentication token")
        return str(token)

    def invalidate_token(self) -> None:
        """Invalidate the current token.

        Call this when a request fails with 401 to force re-authentication
        on the next request.
        """
        _LOGGER.debug("Invalidating cached token")
        self._token = None
        self._token_expires = None

    async def validate_api_key(self) -> bool:
        """Validate that the API key is valid.

        This attempts to obtain a token and returns True if successful.
        Useful for config flow validation.

        Returns:
            True if API key is valid.

        Raises:
            AuthenticationError: If API key is invalid.
        """
        await self._obtain_new_token()
        return True
