"""Pytest configuration for Octoha tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio as the async backend."""
    return "asyncio"


@pytest.fixture
def fixtures_path() -> Path:
    """Return the path to test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture(fixtures_path: Path):
    """Load a JSON fixture file."""

    def _load(filename: str) -> dict[str, Any]:
        filepath = fixtures_path / filename
        with open(filepath) as f:
            return json.load(f)

    return _load


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock aiohttp ClientSession.
    
    The session methods (post, get, request) return async context managers
    to match aiohttp's behavior with `async with session.post(...) as resp:`.
    """
    session = MagicMock()
    
    # Create methods that return async context managers
    # These need to be set up per-test using mock_response_factory
    session.post = MagicMock()
    session.get = MagicMock()
    session.request = MagicMock()
    
    return session


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
def api_key() -> str:
    """Return a test API key."""
    return "sk_test_abc123def456"


@pytest.fixture
def account_number() -> str:
    """Return a test account number."""
    return "A-FB05ED6C"


@pytest.fixture
def mpan() -> str:
    """Return a test MPAN."""
    return "1234567890123"


@pytest.fixture
def mprn() -> str:
    """Return a test MPRN."""
    return "1234567890"


@pytest.fixture
def meter_serial() -> str:
    """Return a test electricity meter serial."""
    return "20P1234567"


@pytest.fixture
def gas_meter_serial() -> str:
    """Return a test gas meter serial."""
    return "G4P12345678"
