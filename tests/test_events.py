"""Tests for Octoha event firing."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from custom_components.octoha.const import (
    DOMAIN,
    EVENT_DISPATCH_END,
    EVENT_DISPATCH_START,
    EVENT_OFF_PEAK_END,
    EVENT_OFF_PEAK_START,
)
from custom_components.octoha.coordinator import TariffData
from custom_components.octoha.events import (
    DispatchEventManager,
    OffPeakEventManager,
    async_setup_events,
)
from custom_components.octoha.models.dispatch import Dispatch, DispatchSource, DispatchStatus
from custom_components.octoha.models.tariff import CurrentRate, Tariff, TariffType


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.bus = MagicMock()
    hass.bus.async_fire = MagicMock()
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "api_key": "sk_test_key",
        "account": "A-FB05ED6C",
        "mpan": "1234567890123",
    }
    return entry


@pytest.fixture
def sample_off_peak_rate():
    """Create sample off-peak current rate."""
    return CurrentRate(
        rate=7.5,
        is_off_peak=True,
        period_end=datetime(2026, 1, 18, 5, 30, tzinfo=timezone.utc),
        next_rate=24.5,
    )


@pytest.fixture
def sample_peak_rate():
    """Create sample peak current rate."""
    return CurrentRate(
        rate=24.5,
        is_off_peak=False,
        period_end=datetime(2026, 1, 18, 23, 30, tzinfo=timezone.utc),
        next_rate=7.5,
    )


@pytest.fixture
def sample_tariff():
    """Create sample tariff."""
    return Tariff(
        product_code="INTELLI-VAR-22-10-14",
        display_name="Intelligent Octopus Go",
        standing_charge=35.0,
        tariff_type=TariffType.TIME_OF_USE,
    )


@pytest.fixture
def sample_active_dispatch():
    """Create sample active dispatch."""
    return Dispatch(
        start=datetime(2026, 1, 18, 1, 0, tzinfo=timezone.utc),
        end=datetime(2026, 1, 18, 5, 0, tzinfo=timezone.utc),
        source=DispatchSource.SMART_CHARGE,
    )


# ============================================================================
# OffPeakEventManager Tests
# ============================================================================


class TestOffPeakEventManager:
    """Tests for OffPeakEventManager."""

    def test_initial_state_is_none(self, mock_hass, mock_config_entry):
        """Test manager starts with unknown off-peak state."""
        manager = OffPeakEventManager(mock_hass, mock_config_entry)
        assert manager._last_off_peak_state is None

    def test_fires_off_peak_start_on_transition(
        self, mock_hass, mock_config_entry, sample_off_peak_rate, sample_tariff
    ):
        """Test fires off_peak_start event when transitioning to off-peak."""
        manager = OffPeakEventManager(mock_hass, mock_config_entry)
        manager._last_off_peak_state = False  # Was peak

        tariff_data = TariffData(
            electricity_tariff=sample_tariff,
            gas_tariff=None,
            current_rate=sample_off_peak_rate,
        )

        manager.check_and_fire(tariff_data)

        mock_hass.bus.async_fire.assert_called_once()
        call_args = mock_hass.bus.async_fire.call_args
        assert call_args[0][0] == EVENT_OFF_PEAK_START
        assert call_args[0][1]["rate"] == 7.5
        assert call_args[0][1]["tariff_name"] == "Intelligent Octopus Go"

    def test_fires_off_peak_end_on_transition(
        self, mock_hass, mock_config_entry, sample_peak_rate, sample_tariff
    ):
        """Test fires off_peak_end event when transitioning from off-peak."""
        manager = OffPeakEventManager(mock_hass, mock_config_entry)
        manager._last_off_peak_state = True  # Was off-peak

        tariff_data = TariffData(
            electricity_tariff=sample_tariff,
            gas_tariff=None,
            current_rate=sample_peak_rate,
        )

        manager.check_and_fire(tariff_data)

        mock_hass.bus.async_fire.assert_called_once()
        call_args = mock_hass.bus.async_fire.call_args
        assert call_args[0][0] == EVENT_OFF_PEAK_END
        assert call_args[0][1]["rate"] == 24.5

    def test_no_event_when_state_unchanged(
        self, mock_hass, mock_config_entry, sample_off_peak_rate, sample_tariff
    ):
        """Test no event fires when off-peak state is unchanged."""
        manager = OffPeakEventManager(mock_hass, mock_config_entry)
        manager._last_off_peak_state = True  # Was already off-peak

        tariff_data = TariffData(
            electricity_tariff=sample_tariff,
            gas_tariff=None,
            current_rate=sample_off_peak_rate,
        )

        manager.check_and_fire(tariff_data)

        mock_hass.bus.async_fire.assert_not_called()

    def test_no_event_on_first_update(
        self, mock_hass, mock_config_entry, sample_off_peak_rate, sample_tariff
    ):
        """Test no event fires on first update (initial state)."""
        manager = OffPeakEventManager(mock_hass, mock_config_entry)
        # _last_off_peak_state is None (initial)

        tariff_data = TariffData(
            electricity_tariff=sample_tariff,
            gas_tariff=None,
            current_rate=sample_off_peak_rate,
        )

        manager.check_and_fire(tariff_data)

        # Should not fire on first update, just record state
        mock_hass.bus.async_fire.assert_not_called()
        assert manager._last_off_peak_state is True

    def test_handles_missing_rate_data(self, mock_hass, mock_config_entry):
        """Test handles missing current rate gracefully."""
        manager = OffPeakEventManager(mock_hass, mock_config_entry)
        manager._last_off_peak_state = True

        tariff_data = TariffData(
            electricity_tariff=None,
            gas_tariff=None,
            current_rate=None,
        )

        manager.check_and_fire(tariff_data)

        mock_hass.bus.async_fire.assert_not_called()

    def test_event_data_includes_entry_id(
        self, mock_hass, mock_config_entry, sample_off_peak_rate, sample_tariff
    ):
        """Test event data includes config entry ID."""
        manager = OffPeakEventManager(mock_hass, mock_config_entry)
        manager._last_off_peak_state = False

        tariff_data = TariffData(
            electricity_tariff=sample_tariff,
            gas_tariff=None,
            current_rate=sample_off_peak_rate,
        )

        manager.check_and_fire(tariff_data)

        call_args = mock_hass.bus.async_fire.call_args
        assert call_args[0][1]["entry_id"] == "test_entry_id"


# ============================================================================
# DispatchEventManager Tests
# ============================================================================


class TestDispatchEventManager:
    """Tests for DispatchEventManager."""

    def test_initial_state_is_none(self, mock_hass, mock_config_entry):
        """Test manager starts with unknown dispatch state."""
        manager = DispatchEventManager(mock_hass, mock_config_entry)
        assert manager._last_dispatch_state is None

    def test_fires_dispatch_start_on_transition(
        self, mock_hass, mock_config_entry, sample_active_dispatch
    ):
        """Test fires dispatch_start event when dispatch begins."""
        manager = DispatchEventManager(mock_hass, mock_config_entry)
        manager._last_dispatch_state = False  # Was not dispatching

        dispatch_status = DispatchStatus(
            is_dispatching=True,
            current_dispatch=sample_active_dispatch,
            next_dispatch=None,
            planned_dispatches=[],
        )

        manager.check_and_fire(dispatch_status)

        mock_hass.bus.async_fire.assert_called_once()
        call_args = mock_hass.bus.async_fire.call_args
        assert call_args[0][0] == EVENT_DISPATCH_START
        assert "dispatch_start" in call_args[0][1]
        assert "dispatch_end" in call_args[0][1]
        assert call_args[0][1]["source"] == "smart-charge"

    def test_fires_dispatch_end_on_transition(
        self, mock_hass, mock_config_entry
    ):
        """Test fires dispatch_end event when dispatch ends."""
        manager = DispatchEventManager(mock_hass, mock_config_entry)
        manager._last_dispatch_state = True  # Was dispatching

        dispatch_status = DispatchStatus(
            is_dispatching=False,
            current_dispatch=None,
            next_dispatch=None,
            planned_dispatches=[],
        )

        manager.check_and_fire(dispatch_status)

        mock_hass.bus.async_fire.assert_called_once()
        call_args = mock_hass.bus.async_fire.call_args
        assert call_args[0][0] == EVENT_DISPATCH_END

    def test_no_event_when_state_unchanged(
        self, mock_hass, mock_config_entry, sample_active_dispatch
    ):
        """Test no event fires when dispatch state is unchanged."""
        manager = DispatchEventManager(mock_hass, mock_config_entry)
        manager._last_dispatch_state = True  # Was already dispatching

        dispatch_status = DispatchStatus(
            is_dispatching=True,
            current_dispatch=sample_active_dispatch,
            next_dispatch=None,
            planned_dispatches=[],
        )

        manager.check_and_fire(dispatch_status)

        mock_hass.bus.async_fire.assert_not_called()

    def test_no_event_on_first_update(
        self, mock_hass, mock_config_entry, sample_active_dispatch
    ):
        """Test no event fires on first update (initial state)."""
        manager = DispatchEventManager(mock_hass, mock_config_entry)
        # _last_dispatch_state is None (initial)

        dispatch_status = DispatchStatus(
            is_dispatching=True,
            current_dispatch=sample_active_dispatch,
            next_dispatch=None,
            planned_dispatches=[],
        )

        manager.check_and_fire(dispatch_status)

        # Should not fire on first update, just record state
        mock_hass.bus.async_fire.assert_not_called()
        assert manager._last_dispatch_state is True

    def test_event_data_includes_duration(
        self, mock_hass, mock_config_entry, sample_active_dispatch
    ):
        """Test event data includes dispatch duration."""
        manager = DispatchEventManager(mock_hass, mock_config_entry)
        manager._last_dispatch_state = False

        dispatch_status = DispatchStatus(
            is_dispatching=True,
            current_dispatch=sample_active_dispatch,
            next_dispatch=None,
            planned_dispatches=[],
        )

        manager.check_and_fire(dispatch_status)

        call_args = mock_hass.bus.async_fire.call_args
        assert call_args[0][1]["duration_minutes"] == 240  # 4 hours


# ============================================================================
# async_setup_events Tests
# ============================================================================


class TestAsyncSetupEvents:
    """Tests for async_setup_events function."""

    def test_creates_off_peak_manager_with_tariff_coordinator(
        self, mock_hass, mock_config_entry
    ):
        """Test creates off-peak event manager when tariff coordinator exists."""
        mock_tariff_coordinator = MagicMock()
        mock_tariff_coordinator.async_add_listener = MagicMock()

        runtime_data = MagicMock(
            tariff_coordinator=mock_tariff_coordinator,
            dispatch_coordinator=None,
        )

        managers = async_setup_events(mock_hass, mock_config_entry, runtime_data)

        assert "off_peak" in managers
        mock_tariff_coordinator.async_add_listener.assert_called_once()

    def test_creates_dispatch_manager_with_dispatch_coordinator(
        self, mock_hass, mock_config_entry
    ):
        """Test creates dispatch event manager when dispatch coordinator exists."""
        mock_dispatch_coordinator = MagicMock()
        mock_dispatch_coordinator.async_add_listener = MagicMock()

        runtime_data = MagicMock(
            tariff_coordinator=None,
            dispatch_coordinator=mock_dispatch_coordinator,
        )

        managers = async_setup_events(mock_hass, mock_config_entry, runtime_data)

        assert "dispatch" in managers
        mock_dispatch_coordinator.async_add_listener.assert_called_once()

    def test_creates_both_managers(self, mock_hass, mock_config_entry):
        """Test creates both managers when both coordinators exist."""
        mock_tariff_coordinator = MagicMock()
        mock_tariff_coordinator.async_add_listener = MagicMock()
        mock_dispatch_coordinator = MagicMock()
        mock_dispatch_coordinator.async_add_listener = MagicMock()

        runtime_data = MagicMock(
            tariff_coordinator=mock_tariff_coordinator,
            dispatch_coordinator=mock_dispatch_coordinator,
        )

        managers = async_setup_events(mock_hass, mock_config_entry, runtime_data)

        assert "off_peak" in managers
        assert "dispatch" in managers

    def test_returns_empty_dict_with_no_coordinators(
        self, mock_hass, mock_config_entry
    ):
        """Test returns empty dict when no coordinators exist."""
        runtime_data = MagicMock(
            tariff_coordinator=None,
            dispatch_coordinator=None,
        )

        managers = async_setup_events(mock_hass, mock_config_entry, runtime_data)

        assert managers == {}
