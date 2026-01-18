"""Octoha API client package.

This package contains the API client for communicating with Octopus Energy's
GraphQL and REST APIs. The implementation is adapted from the open-octopus
project (https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

from .auth import TokenManager
from .client import OctohaApiClient
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    InvalidResponseError,
    OctopusError,
    RateLimitError,
    ValidationError,
    sanitize_error_message,
    sanitize_log_message,
    validate_mpan,
    validate_mprn,
    validate_meter_serial,
)
from .rest import RestClient

__all__ = [
    # Main client
    "OctohaApiClient",
    # Sub-clients
    "RestClient",
    "TokenManager",
    # Exceptions
    "AuthenticationError",
    "ConnectionError",
    "InvalidResponseError",
    "OctopusError",
    "RateLimitError",
    "ValidationError",
    # Utilities
    "sanitize_error_message",
    "sanitize_log_message",
    "validate_mpan",
    "validate_mprn",
    "validate_meter_serial",
]
