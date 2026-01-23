"""Test suite for Octoha integration lifecycle.

Tests the main integration setup, unload, migration, and options update
functions in __init__.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.octoha import (
    OctohaRuntimeData,
    async_migrate_entry,
    async_setup_entry,
    async_unload_entry,
    async_update_options,
)
from custom_components.octoha.api.exceptions import AuthenticationError, OctopusError
from custom_components.octoha.const import (
    CONF_ACCOUNT,
    CONF_API_KEY,
    CONF_MPAN,
    CONF_MPRN,
    DOMAIN,
)
from custom_components.octoha.models.account import Account, Agreement, MeterPoint

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_API_KEY: "sk_test_abc123",
        CONF_ACCOUNT: "A-TEST1234",
        CONF_MPAN: "1234567890123",
        CONF_MPRN: "1234567890",
    }
    entry.options = {}
    entry.runtime_data = None
    entry.add_update_listener = MagicMock(return_value=MagicMock())
    entry.async_on_unload = MagicMock()
    entry.version = 1
    entry.minor_version = 0
    return entry


@pytest.fixture
def mock_config_entry_electricity_only() -> MagicMock:
    """Create a mock config entry with electricity only."""
    entry = MagicMock()
    entry.entry_id = "test_entry_elec"
    entry.data = {
        CONF_API_KEY: "sk_test_abc123",
        CONF_ACCOUNT: "A-TEST1234",
        CONF_MPAN: "1234567890123",
    }
    entry.options = {}
    entry.runtime_data = None
    entry.add_update_listener = MagicMock(return_value=MagicMock())
    entry.async_on_unload = MagicMock()
    return entry


@pytest.fixture
def mock_config_entry_gas_only() -> MagicMock:
    """Create a mock config entry with gas only."""
    entry = MagicMock()
    entry.entry_id = "test_entry_gas"
    entry.data = {
        CONF_API_KEY: "sk_test_abc123",
        CONF_ACCOUNT: "A-TEST1234",
        CONF_MPRN: "1234567890",
    }
    entry.options = {}
    entry.runtime_data = None
    entry.add_update_listener = MagicMock(return_value=MagicMock())
    entry.async_on_unload = MagicMock()
    return entry


@pytest.fixture
def mock_account() -> Account:
    """Create a mock account with standard tariff."""
    return Account(
        account_number="A-TEST1234",
        balance=0.0,
        properties=[],
    )


@pytest.fixture
def mock_account_intelligent() -> Account:
    """Create a mock account with Intelligent tariff."""
    return Account(
        account_number="A-TEST1234",
        balance=0.0,
        properties=[
            MagicMock(
                electricity_meter_points=[
                    MeterPoint(
                        mpan="1234567890123",
                        meter_serial="20P1234567",
                        is_smart=True,
                        agreements=[
                            Agreement(
                                tariff_code="E-1R-INTELLI-VAR-22-10-14-J",
                                valid_from="2024-01-01",
                                valid_to=None,
                            )
                        ],
                        device_id="device123",
                    )
                ],
                gas_meter_points=[],
            )
        ],
    )


@pytest.fixture
def mock_api_client() -> AsyncMock:
    """Create a mock API client."""
    client = AsyncMock()
    client.validate_credentials = AsyncMock(return_value=True)
    client.get_account = AsyncMock()
    client.close = AsyncMock()
    return client


class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_setup_entry_success_both_meters(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
        mock_account: Account,
    ) -> None:
        """Test successful setup with both electricity and gas meters."""
        with (
            patch(
                "custom_components.octoha.async_get_clientsession"
            ) as mock_get_session,
            patch("custom_components.octoha.OctohaApiClient") as mock_client_class,
            patch(
                "custom_components.octoha.ElectricityCoordinator"
            ) as mock_elec_coord,
            patch("custom_components.octoha.GasCoordinator") as mock_gas_coord,
            patch("custom_components.octoha.TariffCoordinator") as mock_tariff_coord,
            patch("custom_components.octoha.async_setup_events") as mock_setup_events,
        ):
            mock_get_session.return_value = MagicMock()

            mock_client = AsyncMock()
            mock_client.validate_credentials = AsyncMock(return_value=True)
            mock_client.get_account = AsyncMock(return_value=mock_account)
            mock_client_class.return_value = mock_client

            mock_elec_coord.return_value.async_config_entry_first_refresh = AsyncMock()
            mock_gas_coord.return_value.async_config_entry_first_refresh = AsyncMock()
            mock_tariff_coord.return_value.async_config_entry_first_refresh = (
                AsyncMock()
            )

            hass.config_entries.async_forward_entry_setups = AsyncMock()

            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            assert DOMAIN in hass.data
            assert mock_config_entry.entry_id in hass.data[DOMAIN]
            mock_client.validate_credentials.assert_called_once()
            mock_client.get_account.assert_called_once()
            mock_elec_coord.return_value.async_config_entry_first_refresh.assert_called_once()
            mock_gas_coord.return_value.async_config_entry_first_refresh.assert_called_once()
            mock_tariff_coord.return_value.async_config_entry_first_refresh.assert_called_once()
            mock_setup_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_entry_success_electricity_only(
        self,
        hass: HomeAssistant,
        mock_config_entry_electricity_only: MagicMock,
        mock_account: Account,
    ) -> None:
        """Test successful setup with electricity meter only."""
        with (
            patch(
                "custom_components.octoha.async_get_clientsession"
            ) as mock_get_session,
            patch("custom_components.octoha.OctohaApiClient") as mock_client_class,
            patch(
                "custom_components.octoha.ElectricityCoordinator"
            ) as mock_elec_coord,
            patch("custom_components.octoha.GasCoordinator") as mock_gas_coord,
            patch("custom_components.octoha.TariffCoordinator") as mock_tariff_coord,
            patch("custom_components.octoha.async_setup_events"),
        ):
            mock_get_session.return_value = MagicMock()

            mock_client = AsyncMock()
            mock_client.validate_credentials = AsyncMock(return_value=True)
            mock_client.get_account = AsyncMock(return_value=mock_account)
            mock_client_class.return_value = mock_client

            mock_elec_coord.return_value.async_config_entry_first_refresh = AsyncMock()
            mock_tariff_coord.return_value.async_config_entry_first_refresh = (
                AsyncMock()
            )

            hass.config_entries.async_forward_entry_setups = AsyncMock()

            result = await async_setup_entry(hass, mock_config_entry_electricity_only)

            assert result is True
            mock_elec_coord.return_value.async_config_entry_first_refresh.assert_called_once()
            # Gas coordinator should not be created
            mock_gas_coord.return_value.async_config_entry_first_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_entry_success_gas_only(
        self,
        hass: HomeAssistant,
        mock_config_entry_gas_only: MagicMock,
        mock_account: Account,
    ) -> None:
        """Test successful setup with gas meter only."""
        with (
            patch(
                "custom_components.octoha.async_get_clientsession"
            ) as mock_get_session,
            patch("custom_components.octoha.OctohaApiClient") as mock_client_class,
            patch(
                "custom_components.octoha.ElectricityCoordinator"
            ) as mock_elec_coord,
            patch("custom_components.octoha.GasCoordinator") as mock_gas_coord,
            patch("custom_components.octoha.TariffCoordinator") as mock_tariff_coord,
            patch("custom_components.octoha.async_setup_events"),
        ):
            mock_get_session.return_value = MagicMock()

            mock_client = AsyncMock()
            mock_client.validate_credentials = AsyncMock(return_value=True)
            mock_client.get_account = AsyncMock(return_value=mock_account)
            mock_client_class.return_value = mock_client

            mock_gas_coord.return_value.async_config_entry_first_refresh = AsyncMock()
            mock_tariff_coord.return_value.async_config_entry_first_refresh = (
                AsyncMock()
            )

            hass.config_entries.async_forward_entry_setups = AsyncMock()

            result = await async_setup_entry(hass, mock_config_entry_gas_only)

            assert result is True
            mock_gas_coord.return_value.async_config_entry_first_refresh.assert_called_once()
            # Electricity coordinator should not be created
            mock_elec_coord.return_value.async_config_entry_first_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_entry_with_intelligent_tariff(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
        mock_account_intelligent: Account,
    ) -> None:
        """Test setup creates dispatch coordinator for Intelligent tariff."""
        with (
            patch(
                "custom_components.octoha.async_get_clientsession"
            ) as mock_get_session,
            patch("custom_components.octoha.OctohaApiClient") as mock_client_class,
            patch("custom_components.octoha.ElectricityCoordinator") as mock_elec_coord,
            patch("custom_components.octoha.GasCoordinator") as mock_gas_coord,
            patch("custom_components.octoha.TariffCoordinator") as mock_tariff_coord,
            patch(
                "custom_components.octoha.DispatchCoordinator"
            ) as mock_dispatch_coord,
            patch("custom_components.octoha.async_setup_events"),
        ):
            mock_get_session.return_value = MagicMock()

            mock_client = AsyncMock()
            mock_client.validate_credentials = AsyncMock(return_value=True)
            mock_client.get_account = AsyncMock(return_value=mock_account_intelligent)
            mock_client_class.return_value = mock_client

            mock_elec_coord.return_value.async_config_entry_first_refresh = AsyncMock()
            mock_gas_coord.return_value.async_config_entry_first_refresh = AsyncMock()
            mock_tariff_coord.return_value.async_config_entry_first_refresh = (
                AsyncMock()
            )
            mock_dispatch_coord.return_value.async_config_entry_first_refresh = (
                AsyncMock()
            )

            hass.config_entries.async_forward_entry_setups = AsyncMock()

            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            mock_dispatch_coord.return_value.async_config_entry_first_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_entry_authentication_failure(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test setup raises ConfigEntryAuthFailed on authentication failure."""
        with (
            patch("custom_components.octoha.async_get_clientsession"),
            patch("custom_components.octoha.OctohaApiClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.validate_credentials = AsyncMock(
                side_effect=AuthenticationError("Invalid API key")
            )
            mock_client_class.return_value = mock_client

            with pytest.raises(ConfigEntryAuthFailed):
                await async_setup_entry(hass, mock_config_entry)

    @pytest.mark.asyncio
    async def test_setup_entry_connection_failure(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test setup raises ConfigEntryNotReady on connection failure."""
        with (
            patch("custom_components.octoha.async_get_clientsession"),
            patch("custom_components.octoha.OctohaApiClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.validate_credentials = AsyncMock(
                side_effect=OctopusError("Connection failed")
            )
            mock_client_class.return_value = mock_client

            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(hass, mock_config_entry)

    @pytest.mark.asyncio
    async def test_setup_entry_account_fetch_failure(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test setup raises ConfigEntryNotReady when account fetch fails."""
        with (
            patch("custom_components.octoha.async_get_clientsession"),
            patch("custom_components.octoha.OctohaApiClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.validate_credentials = AsyncMock(return_value=True)
            mock_client.get_account = AsyncMock(
                side_effect=OctopusError("Account fetch failed")
            )
            mock_client_class.return_value = mock_client

            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(hass, mock_config_entry)


class TestAsyncUnloadEntry:
    """Tests for async_unload_entry function."""

    @pytest.mark.asyncio
    async def test_unload_entry_success(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test successful unload cleans up resources."""
        # Set up runtime data
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        runtime_data = OctohaRuntimeData(client=mock_client)
        mock_config_entry.runtime_data = runtime_data

        hass.data[DOMAIN] = {mock_config_entry.entry_id: runtime_data}
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        mock_client.close.assert_called_once()
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unload_entry_removes_from_hass_data(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test unload removes entry from hass.data."""
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        runtime_data = OctohaRuntimeData(client=mock_client)
        mock_config_entry.runtime_data = runtime_data

        hass.data[DOMAIN] = {mock_config_entry.entry_id: runtime_data}
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        await async_unload_entry(hass, mock_config_entry)

        assert mock_config_entry.entry_id not in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unload_entry_platform_unload_failure(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test unload returns False when platform unload fails."""
        mock_client = AsyncMock()
        runtime_data = OctohaRuntimeData(client=mock_client)
        mock_config_entry.runtime_data = runtime_data

        hass.data[DOMAIN] = {mock_config_entry.entry_id: runtime_data}
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

        result = await async_unload_entry(hass, mock_config_entry)

        assert result is False
        # Client should NOT be closed if unload failed
        mock_client.close.assert_not_called()


class TestAsyncUpdateOptions:
    """Tests for async_update_options function."""

    @pytest.mark.asyncio
    async def test_update_options_triggers_reload(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test options update triggers config entry reload."""
        hass.config_entries.async_reload = AsyncMock()

        await async_update_options(hass, mock_config_entry)

        hass.config_entries.async_reload.assert_called_once_with(
            mock_config_entry.entry_id
        )


class TestAsyncMigrateEntry:
    """Tests for async_migrate_entry function."""

    @pytest.mark.asyncio
    async def test_migrate_entry_returns_true(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
    ) -> None:
        """Test migration returns True (no migrations needed yet)."""
        result = await async_migrate_entry(hass, mock_config_entry)
        assert result is True


class TestOctohaRuntimeData:
    """Tests for OctohaRuntimeData dataclass."""

    def test_runtime_data_creation(self) -> None:
        """Test runtime data can be created with just client."""
        mock_client = AsyncMock()
        runtime_data = OctohaRuntimeData(client=mock_client)

        assert runtime_data.client is mock_client
        assert runtime_data.electricity_coordinator is None
        assert runtime_data.gas_coordinator is None
        assert runtime_data.tariff_coordinator is None
        assert runtime_data.dispatch_coordinator is None

    def test_runtime_data_with_coordinators(self) -> None:
        """Test runtime data with all coordinators set."""
        mock_client = AsyncMock()
        mock_elec = MagicMock()
        mock_gas = MagicMock()
        mock_tariff = MagicMock()
        mock_dispatch = MagicMock()

        runtime_data = OctohaRuntimeData(
            client=mock_client,
            electricity_coordinator=mock_elec,
            gas_coordinator=mock_gas,
            tariff_coordinator=mock_tariff,
            dispatch_coordinator=mock_dispatch,
        )

        assert runtime_data.electricity_coordinator is mock_elec
        assert runtime_data.gas_coordinator is mock_gas
        assert runtime_data.tariff_coordinator is mock_tariff
        assert runtime_data.dispatch_coordinator is mock_dispatch
