"""Tests for Octoha diagnostics."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from custom_components.octoha.const import DOMAIN
from custom_components.octoha.coordinator import (
    ElectricityData,
    TariffData,
)
from custom_components.octoha.diagnostics import (
    async_get_config_entry_diagnostics,
    redact_api_key,
    redact_sensitive_data,
)
from custom_components.octoha.models.consumption import Consumption, DailyUsage
from custom_components.octoha.models.tariff import CurrentRate, Tariff, TariffType

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry with sensitive data."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "api_key": "sk_live_abc123def456ghi789",
        "account": "A-FB05ED6C",
        "mpan": "1234567890123",
        "mprn": "1234567890",
        "meter_serial": "20P1234567",
        "gas_meter_serial": "G4P12345678",
    }
    entry.options = {
        "electricity_interval": 300,
        "gas_interval": 300,
    }
    entry.version = 1
    entry.minor_version = 0
    return entry


@pytest.fixture
def sample_electricity_data():
    """Create sample electricity data."""
    return ElectricityData(
        consumption=[
            Consumption(
                interval_start=datetime(2026, 1, 18, 0, 0, tzinfo=UTC),
                interval_end=datetime(2026, 1, 18, 0, 30, tzinfo=UTC),
                consumption=0.5,
            ),
        ],
        daily_usage=[
            DailyUsage(date="2026-01-18", electricity_kwh=7.2),
        ],
    )


@pytest.fixture
def sample_tariff_data():
    """Create sample tariff data."""
    return TariffData(
        electricity_tariff=Tariff(
            product_code="INTELLI-VAR-22-10-14",
            display_name="Intelligent Octopus Go",
            standing_charge=35.0,
            tariff_type=TariffType.TIME_OF_USE,
        ),
        gas_tariff=None,
        current_rate=CurrentRate(
            rate=7.5,
            is_off_peak=True,
            period_end=datetime(2026, 1, 18, 5, 30, tzinfo=UTC),
        ),
    )


@pytest.fixture
def mock_runtime_data(sample_electricity_data, sample_tariff_data):
    """Create mock runtime data."""
    electricity_coordinator = MagicMock()
    electricity_coordinator.data = sample_electricity_data
    electricity_coordinator.last_update_success = True
    electricity_coordinator.last_update_success_time = datetime(
        2026, 1, 18, 12, 0, tzinfo=UTC
    )

    tariff_coordinator = MagicMock()
    tariff_coordinator.data = sample_tariff_data
    tariff_coordinator.last_update_success = True

    client = MagicMock()
    client._account_number = "A-FB05ED6C"

    return MagicMock(
        client=client,
        electricity_coordinator=electricity_coordinator,
        gas_coordinator=None,
        tariff_coordinator=tariff_coordinator,
        dispatch_coordinator=None,
    )


# ============================================================================
# Redaction Tests
# ============================================================================


class TestRedaction:
    """Tests for data redaction functions."""

    def test_redact_api_key_hides_most_characters(self):
        """Test API key is redacted with only prefix visible."""
        api_key = "sk_live_abc123def456ghi789"
        redacted = redact_api_key(api_key)
        assert redacted == "sk_live_***REDACTED***"

    def test_redact_api_key_short_key(self):
        """Test short API keys are fully redacted."""
        api_key = "short"
        redacted = redact_api_key(api_key)
        assert redacted == "***REDACTED***"

    def test_redact_api_key_none(self):
        """Test None API key returns None."""
        assert redact_api_key(None) is None

    def test_redact_sensitive_data_entry_data(self):
        """Test sensitive fields in entry data are redacted."""
        data = {
            "api_key": "sk_live_secret123",
            "account": "A-FB05ED6C",
            "mpan": "1234567890123",
            "mprn": "1234567890",
        }
        redacted = redact_sensitive_data(data)

        assert redacted["api_key"] == "sk_live_***REDACTED***"
        # Account should NOT be redacted (useful for debugging)
        assert redacted["account"] == "A-FB05ED6C"
        # MPAN/MPRN should be partially redacted
        assert "****" in redacted["mpan"]
        assert "****" in redacted["mprn"]

    def test_redact_sensitive_data_nested(self):
        """Test redaction works on nested dictionaries."""
        data = {
            "config": {
                "api_key": "sk_live_secret123",
            },
            "other": "value",
        }
        redacted = redact_sensitive_data(data)
        assert redacted["config"]["api_key"] == "sk_live_***REDACTED***"
        assert redacted["other"] == "value"


# ============================================================================
# Diagnostics Tests
# ============================================================================


class TestAsyncGetConfigEntryDiagnostics:
    """Tests for async_get_config_entry_diagnostics."""

    @pytest.mark.asyncio
    async def test_returns_redacted_config_entry(
        self, mock_hass, mock_config_entry, mock_runtime_data
    ):
        """Test diagnostics includes redacted config entry data."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = mock_runtime_data

        diagnostics = await async_get_config_entry_diagnostics(
            mock_hass, mock_config_entry
        )

        assert "config_entry" in diagnostics
        assert "api_key" in diagnostics["config_entry"]["data"]
        # API key should be redacted
        assert "REDACTED" in diagnostics["config_entry"]["data"]["api_key"]

    @pytest.mark.asyncio
    async def test_includes_coordinator_status(
        self, mock_hass, mock_config_entry, mock_runtime_data
    ):
        """Test diagnostics includes coordinator status."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = mock_runtime_data

        diagnostics = await async_get_config_entry_diagnostics(
            mock_hass, mock_config_entry
        )

        assert "coordinators" in diagnostics
        assert "electricity" in diagnostics["coordinators"]
        assert diagnostics["coordinators"]["electricity"]["available"] is True

    @pytest.mark.asyncio
    async def test_includes_consumption_summary(
        self, mock_hass, mock_config_entry, mock_runtime_data
    ):
        """Test diagnostics includes consumption data summary."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = mock_runtime_data

        diagnostics = await async_get_config_entry_diagnostics(
            mock_hass, mock_config_entry
        )

        assert "data" in diagnostics
        assert "electricity" in diagnostics["data"]
        assert "consumption_count" in diagnostics["data"]["electricity"]

    @pytest.mark.asyncio
    async def test_includes_tariff_info(
        self, mock_hass, mock_config_entry, mock_runtime_data
    ):
        """Test diagnostics includes tariff information."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = mock_runtime_data

        diagnostics = await async_get_config_entry_diagnostics(
            mock_hass, mock_config_entry
        )

        assert "tariff" in diagnostics["data"]
        assert diagnostics["data"]["tariff"]["name"] == "Intelligent Octopus Go"
        assert diagnostics["data"]["tariff"]["current_rate"] == 7.5

    @pytest.mark.asyncio
    async def test_handles_missing_runtime_data(self, mock_hass, mock_config_entry):
        """Test diagnostics handles missing runtime data gracefully."""
        # No runtime data set
        mock_hass.data[DOMAIN] = {}

        diagnostics = await async_get_config_entry_diagnostics(
            mock_hass, mock_config_entry
        )

        assert "error" in diagnostics
        assert "not found" in diagnostics["error"].lower()

    @pytest.mark.asyncio
    async def test_includes_version_info(
        self, mock_hass, mock_config_entry, mock_runtime_data
    ):
        """Test diagnostics includes integration version."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = mock_runtime_data

        diagnostics = await async_get_config_entry_diagnostics(
            mock_hass, mock_config_entry
        )

        assert "integration" in diagnostics
        assert "version" in diagnostics["integration"]
