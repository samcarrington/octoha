"""Custom exceptions for the Octoha API client.

Exception hierarchy adapted from open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations


class OctopusError(Exception):
    """Base exception for Octopus API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(OctopusError):
    """Exception raised when authentication fails.

    This can occur when:
    - API key is invalid
    - Token has expired and cannot be refreshed
    - Account doesn't have API access enabled
    """


class RateLimitError(OctopusError):
    """Exception raised when API rate limit is exceeded.

    The Octopus API has rate limits. When exceeded, this exception
    is raised with information about when to retry.
    """

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            retry_after: Seconds to wait before retrying.
            status_code: HTTP status code.
        """
        super().__init__(message, status_code)
        self.retry_after = retry_after


class ConnectionError(OctopusError):
    """Exception raised when unable to connect to the API."""


class InvalidResponseError(OctopusError):
    """Exception raised when the API returns an unexpected response format."""
