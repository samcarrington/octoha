"""Octoha API client package.

This package contains the API client for communicating with Octopus Energy's
GraphQL and REST APIs. The implementation is adapted from the open-octopus
project (https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

from .exceptions import (
    AuthenticationError,
    OctopusError,
    RateLimitError,
)

__all__ = [
    "AuthenticationError",
    "OctopusError",
    "RateLimitError",
]
