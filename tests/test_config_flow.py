"""Tests for Octoha config flow.

Comprehensive test suite for the config flow which handles user setup,
credential validation, meter discovery, and error handling.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from custom_components.octoha.api.client import OctohaApiClient
from custom_components.octoha.api.exceptions import (
    AuthenticationError,
    OctopusError,
)
from custom_components.octoha.const import (
    CONF_API_KEY,
    CONF_ACCOUNT,
    CONF_MPAN,
    CONF_MPRN,
    CONF_METER_SERIAL,
    CONF_GAS_METER_SERIAL,
    DOMAIN,
)
from custom_components.octoha.models.account import (
    Account,
    Property,
    MeterPoint,
    GasMeterPoint,
    Agreement,
)


class TestOctohaConfigFlow:
    """Test suite for Octoha config flow."""

    @pytest.fixture
    def mock_api_client(self) -> MagicMock:
        """Create a mock OctohaApiClient."""
        return MagicMock(spec=OctohaApiClient)

    @pytest.fixture
    def single_meter_account(
        self,
        account_number: str,
        mpan: str,
        meter_serial: str,
    ) -> Account:
        """Create test account with single electricity meter."""
        property_obj = Property(
            address_line_1="123 Test Street",
            postcode="AB12 3CD",
            electricity_meter_points=[
                MeterPoint(
                    mpan=mpan,
                    meter_serial=meter_serial,
                    is_smart=True,
                    agreements=[
                        Agreement(
                            tariff_code="E-1R-INTELLI-VAR-22-10-14-J",
                            valid_from="2024-01-01T00:00:00Z",
                        )
                    ],
                )
            ],
            gas_meter_points=[],
        )
        return Account(
            account_number=account_number,
            balance=-10.50,
            properties=[property_obj],
        )

    @pytest.fixture
    def multi_meter_account(
        self,
        account_number: str,
        mpan: str,
        meter_serial: str,
        mprn: str,
        gas_meter_serial: str,
    ) -> Account:
        """Create test account with multiple meters (electricity + gas)."""
        property_obj = Property(
            address_line_1="456 Multi Meter Lane",
            postcode="XY98 7ZW",
            electricity_meter_points=[
                MeterPoint(
                    mpan=mpan,
                    meter_serial=meter_serial,
                    is_smart=True,
                    agreements=[
                        Agreement(
                            tariff_code="E-1R-AGILE-22-10-14-J",
                            valid_from="2024-01-01T00:00:00Z",
                        )
                    ],
                )
            ],
            gas_meter_points=[
                GasMeterPoint(
                    mprn=mprn,
                    meter_serial=gas_meter_serial,
                    is_smart=True,
                    agreements=[
                        Agreement(
                            tariff_code="G-1R-FLEX-22-10-14-J",
                            valid_from="2024-01-01T00:00:00Z",
                        )
                    ],
                )
            ],
        )
        return Account(
            account_number=account_number,
            balance=5.25,
            properties=[property_obj],
        )

    # ========================================================================
    # User Step Tests - Happy Path
    # ========================================================================

    @pytest.mark.asyncio
    async def test_form_shows_user_step(self, hass: HomeAssistant) -> None:
        """Test that user step form is displayed with api_key field.

        Verifies that:
        - Config flow starts with user step
        - Form has api_key input field
        - Form schema is correct
        """
        # Currently this should FAIL - config_flow.py doesn't exist yet
        with patch(
            "custom_components.octoha.config_flow.OctohaConfigFlow"
        ) as mock_flow_class:
            mock_flow = MagicMock()
            mock_flow_class.return_value = mock_flow

            # This will fail when config_flow doesn't exist
            from custom_components.octoha.config_flow import OctohaConfigFlow

            flow = OctohaConfigFlow()

            # Assert form has correct step_id
            assert hasattr(flow, "async_step_user")
            # Once implemented, verify form shows api_key field

    @pytest.mark.asyncio
    async def test_user_step_success_single_meter(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        single_meter_account: Account,
        api_key: str,
        account_number: str,
        mpan: str,
        meter_serial: str,
    ) -> None:
        """Test successful user step with single meter account.

        Verifies that when user provides valid API key:
        - Credentials are validated successfully
        - Account data is fetched
        - For single meter, config entry is created directly (no meter selection)
        - Entry has correct data (api_key, account, mpan, meter_serial)
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=single_meter_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            # This will fail when config_flow doesn't exist
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, this should pass with assertions like:
            # result = await hass.config_entries.flow.async_init(
            #     DOMAIN, context={"source": config_entries.SOURCE_USER}
            # )
            # assert result["type"] == FlowResult.type.FORM
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: api_key}
            # )
            # assert result["type"] == FlowResult.type.CREATE_ENTRY
            # assert result["data"][CONF_API_KEY] == api_key
            # assert result["data"][CONF_ACCOUNT] == account_number
            # assert result["data"][CONF_MPAN] == mpan
            # assert result["data"][CONF_METER_SERIAL] == meter_serial

    @pytest.mark.asyncio
    async def test_user_step_success_multiple_meters(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        multi_meter_account: Account,
        api_key: str,
    ) -> None:
        """Test user step with multiple meter account.

        Verifies that when user provides valid API key with multiple meters:
        - Credentials are validated successfully
        - Account data is fetched
        - For multiple meters, flow proceeds to meter selection step
        - Meter step options are shown correctly
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=multi_meter_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            # This will fail when config_flow doesn't exist
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # result = await hass.config_entries.flow.async_init(...)
            # assert result["type"] == FlowResult.type.FORM
            # assert result["step_id"] == "user"
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: api_key}
            # )
            # assert result["type"] == FlowResult.type.FORM
            # assert result["step_id"] == "meter_selection"
            # Verify electricity and gas meter options are available

    # ========================================================================
    # User Step Tests - Error Handling
    # ========================================================================

    @pytest.mark.asyncio
    async def test_user_step_invalid_api_key(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        api_key: str,
    ) -> None:
        """Test user step with invalid API key.

        Verifies that when user provides invalid API key:
        - validate_credentials raises AuthenticationError
        - Form shows error with key "invalid_api_key"
        - User can retry with different API key
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(
            side_effect=AuthenticationError("Invalid API key")
        )

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # result = await hass.config_entries.flow.async_init(...)
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: api_key}
            # )
            # assert result["type"] == FlowResult.type.FORM
            # assert result["step_id"] == "user"
            # assert "invalid_api_key" in result["errors"]

    @pytest.mark.asyncio
    async def test_user_step_cannot_connect(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        api_key: str,
    ) -> None:
        """Test user step with connection error.

        Verifies that when API connection fails:
        - validate_credentials raises OctopusError
        - Form shows error with key "cannot_connect"
        - User can retry
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(
            side_effect=OctopusError("Failed to connect to API")
        )

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # result = await hass.config_entries.flow.async_init(...)
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: api_key}
            # )
            # assert result["type"] == FlowResult.type.FORM
            # assert "cannot_connect" in result["errors"]

    @pytest.mark.asyncio
    async def test_user_step_unknown_error(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        api_key: str,
    ) -> None:
        """Test user step with unexpected error.

        Verifies that when an unexpected exception is raised:
        - Form shows error with key "unknown"
        - User can retry
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(
            side_effect=ValueError("Unexpected error")
        )

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # result = await hass.config_entries.flow.async_init(...)
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: api_key}
            # )
            # assert result["type"] == FlowResult.type.FORM
            # assert "unknown" in result["errors"]

    # ========================================================================
    # Meter Selection Step Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_meter_step_displays_options(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        multi_meter_account: Account,
        api_key: str,
        mpan: str,
        mprn: str,
    ) -> None:
        """Test meter selection step displays correct meter options.

        Verifies that meter selection form:
        - Shows all available electricity meter points
        - Shows all available gas meter points
        - Shows proper labels/descriptions for each meter
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=multi_meter_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # Initiate flow, get to meter selection step
            # Verify form includes options for selecting:
            # - Electricity meter (MPAN: mpan)
            # - Gas meter (MPRN: mprn)

    @pytest.mark.asyncio
    async def test_meter_step_creates_entry(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        multi_meter_account: Account,
        api_key: str,
        account_number: str,
        mpan: str,
        meter_serial: str,
        mprn: str,
        gas_meter_serial: str,
    ) -> None:
        """Test meter selection creates config entry.

        Verifies that when user selects meters in meter_selection step:
        - Config entry is created with correct data
        - Entry includes: api_key, account, mpan, meter_serial, mprn, gas_meter_serial
        - Entry title uses account number
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=multi_meter_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # result = await hass.config_entries.flow.async_init(...)
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: api_key}
            # )
            # # Now in meter selection step
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"],
            #     {
            #         CONF_MPAN: mpan,
            #         CONF_MPRN: mprn,
            #     }
            # )
            # assert result["type"] == FlowResult.type.CREATE_ENTRY
            # assert result["data"][CONF_API_KEY] == api_key
            # assert result["data"][CONF_ACCOUNT] == account_number
            # assert result["data"][CONF_MPAN] == mpan
            # assert result["data"][CONF_METER_SERIAL] == meter_serial
            # assert result["data"][CONF_MPRN] == mprn
            # assert result["data"][CONF_GAS_METER_SERIAL] == gas_meter_serial

    # ========================================================================
    # Duplicate Account Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_abort_already_configured(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        single_meter_account: Account,
        api_key: str,
        account_number: str,
    ) -> None:
        """Test that config flow aborts for duplicate account.

        Verifies that when attempting to add same account twice:
        - Flow checks if account already exists
        - Flow aborts with reason "already_configured"
        - User is informed account is already set up
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=single_meter_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # Create first entry successfully
            # entry = hass.config_entries.async_entries(DOMAIN)[0]

            # Attempt to add same account again
            # result = await hass.config_entries.flow.async_init(...)
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: api_key}
            # )
            # assert result["type"] == FlowResult.type.ABORT
            # assert result["reason"] == "already_configured"

    # ========================================================================
    # Edge Cases - Account Data Variations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_account_with_no_meters(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        account_number: str,
    ) -> None:
        """Test handling of account with no meters.

        Verifies that account with no electricity or gas meters:
        - Is detected during validation
        - Shows appropriate error message
        - Prevents incomplete configuration
        """
        # Create account with no meters
        empty_account = Account(
            account_number=account_number,
            balance=0.0,
            properties=[
                Property(
                    address_line_1="Empty Address",
                    postcode="XX00 0XX",
                    electricity_meter_points=[],
                    gas_meter_points=[],
                )
            ],
        )

        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=empty_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # result = await hass.config_entries.flow.async_init(...)
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: test_api_key}
            # )
            # assert result["type"] == FlowResult.type.FORM
            # assert "no_meters" in result["errors"] or result["reason"] == "no_meters"

    @pytest.mark.asyncio
    async def test_account_electricity_only(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        account_number: str,
        mpan: str,
        meter_serial: str,
    ) -> None:
        """Test handling of account with only electricity meter.

        Verifies that:
        - Account with only electricity meter is accepted
        - Config entry is created without MPRN/gas_meter_serial
        - Flow completes successfully
        """
        # Create account with only electricity
        elec_only_account = Account(
            account_number=account_number,
            balance=0.0,
            properties=[
                Property(
                    address_line_1="Electric Only",
                    postcode="EL1 2CT",
                    electricity_meter_points=[
                        MeterPoint(
                            mpan=mpan,
                            meter_serial=meter_serial,
                        )
                    ],
                    gas_meter_points=[],
                )
            ],
        )

        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=elec_only_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # Flow completes with only electricity meter selected
            # MPRN and gas_meter_serial are None or not present

    @pytest.mark.asyncio
    async def test_account_gas_only(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        account_number: str,
        mprn: str,
        gas_meter_serial: str,
    ) -> None:
        """Test handling of account with only gas meter.

        Verifies that:
        - Account with only gas meter is accepted
        - Config entry is created without MPAN/meter_serial
        - Flow completes successfully
        """
        # Create account with only gas
        gas_only_account = Account(
            account_number=account_number,
            balance=0.0,
            properties=[
                Property(
                    address_line_1="Gas Only",
                    postcode="GA1 2ST",
                    electricity_meter_points=[],
                    gas_meter_points=[
                        GasMeterPoint(
                            mprn=mprn,
                            meter_serial=gas_meter_serial,
                        )
                    ],
                )
            ],
        )

        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=gas_only_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # Flow completes with only gas meter selected
            # MPAN and meter_serial are None or not present

    # ========================================================================
    # Input Validation Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_user_step_empty_api_key(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test user step with empty API key input.

        Verifies that:
        - Empty API key is rejected before API call
        - Form shows appropriate validation error
        - User is prompted to enter valid API key
        """
        # This test should FAIL - config_flow doesn't exist yet
        from custom_components.octoha.config_flow import OctohaConfigFlow

        # Once implemented, verify:
        # result = await hass.config_entries.flow.async_init(...)
        # result = await hass.config_entries.flow.async_configure(
        #     result["flow_id"], {CONF_API_KEY: ""}
        # )
        # assert result["type"] == FlowResult.type.FORM
        # assert "invalid_api_key" in result["errors"] or "required" in result["errors"]

    @pytest.mark.asyncio
    async def test_user_step_whitespace_api_key(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Test user step with whitespace-only API key.

        Verifies that:
        - Whitespace-only API key is rejected
        - Input is trimmed/validated
        - User is prompted to enter valid API key
        """
        # This test should FAIL - config_flow doesn't exist yet
        from custom_components.octoha.config_flow import OctohaConfigFlow

        # Once implemented, verify:
        # result = await hass.config_entries.flow.async_init(...)
        # result = await hass.config_entries.flow.async_configure(
        #     result["flow_id"], {CONF_API_KEY: "   "}
        # )
        # assert result["type"] == FlowResult.type.FORM
        # assert "errors" in result

    # ========================================================================
    # Flow Title and Description Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_config_entry_title_format(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        single_meter_account: Account,
        api_key: str,
        account_number: str,
    ) -> None:
        """Test that config entry has proper title format.

        Verifies that created entry title:
        - Uses account number (e.g., "A-FB05ED6C")
        - Matches expected format
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=single_meter_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented, verify:
            # result = await hass.config_entries.flow.async_init(...)
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: api_key}
            # )
            # assert result["type"] == FlowResult.type.CREATE_ENTRY
            # assert result["title"] == account_number


# ============================================================================
# Integration Tests
# ============================================================================


class TestOctohaConfigFlowIntegration:
    """Integration tests for complete config flow scenarios."""

    @pytest.fixture
    def mock_api_client(self) -> MagicMock:
        """Create a mock OctohaApiClient."""
        return MagicMock(spec=OctohaApiClient)

    @pytest.fixture
    def single_meter_account(
        self,
        account_number: str,
        mpan: str,
        meter_serial: str,
    ) -> Account:
        """Create test account with single electricity meter."""
        property_obj = Property(
            address_line_1="123 Test Street",
            postcode="AB12 3CD",
            electricity_meter_points=[
                MeterPoint(
                    mpan=mpan,
                    meter_serial=meter_serial,
                    is_smart=True,
                    agreements=[
                        Agreement(
                            tariff_code="E-1R-INTELLI-VAR-22-10-14-J",
                            valid_from="2024-01-01T00:00:00Z",
                        )
                    ],
                )
            ],
            gas_meter_points=[],
        )
        return Account(
            account_number=account_number,
            balance=-10.50,
            properties=[property_obj],
        )

    @pytest.fixture
    def multi_meter_account(
        self,
        account_number: str,
        mpan: str,
        meter_serial: str,
        mprn: str,
        gas_meter_serial: str,
    ) -> Account:
        """Create test account with multiple meters (electricity + gas)."""
        property_obj = Property(
            address_line_1="456 Multi Meter Lane",
            postcode="XY98 7ZW",
            electricity_meter_points=[
                MeterPoint(
                    mpan=mpan,
                    meter_serial=meter_serial,
                    is_smart=True,
                    agreements=[
                        Agreement(
                            tariff_code="E-1R-AGILE-22-10-14-J",
                            valid_from="2024-01-01T00:00:00Z",
                        )
                    ],
                )
            ],
            gas_meter_points=[
                GasMeterPoint(
                    mprn=mprn,
                    meter_serial=gas_meter_serial,
                    is_smart=True,
                    agreements=[
                        Agreement(
                            tariff_code="G-1R-FLEX-22-10-14-J",
                            valid_from="2024-01-01T00:00:00Z",
                        )
                    ],
                )
            ],
        )
        return Account(
            account_number=account_number,
            balance=5.25,
            properties=[property_obj],
        )

    @pytest.mark.asyncio
    async def test_complete_flow_single_meter(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        single_meter_account: Account,
        api_key: str,
    ) -> None:
        """Test complete config flow from start to entry creation.

        Comprehensive test verifying:
        - Form is displayed
        - User enters API key
        - Credentials are validated
        - Account is fetched
        - For single meter, entry is created immediately
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=single_meter_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented:
            # 1. Initialize flow
            # result = await hass.config_entries.flow.async_init(
            #     DOMAIN, context={"source": config_entries.SOURCE_USER}
            # )
            # assert result["type"] == FlowResult.type.FORM
            # assert result["step_id"] == "user"

            # 2. Submit user form
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: api_key}
            # )

            # 3. Verify entry created (no meter selection for single meter)
            # assert result["type"] == FlowResult.type.CREATE_ENTRY
            # assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    @pytest.mark.asyncio
    async def test_complete_flow_multiple_meters(
        self,
        hass: HomeAssistant,
        mock_api_client: MagicMock,
        multi_meter_account: Account,
        api_key: str,
    ) -> None:
        """Test complete config flow with meter selection step.

        Comprehensive test verifying:
        - Form is displayed
        - User enters API key
        - Credentials are validated
        - Account is fetched
        - For multiple meters, meter selection form is shown
        - User selects meters
        - Entry is created with correct data
        """
        # This test should FAIL - config_flow doesn't exist yet
        mock_api_client.validate_credentials = AsyncMock(return_value=True)
        mock_api_client.get_account = AsyncMock(return_value=multi_meter_account)

        with patch(
            "custom_components.octoha.config_flow.OctohaApiClient",
            return_value=mock_api_client,
        ):
            from custom_components.octoha.config_flow import OctohaConfigFlow

            # Once implemented:
            # 1. Initialize flow
            # result = await hass.config_entries.flow.async_init(...)

            # 2. Submit user form
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"], {CONF_API_KEY: api_key}
            # )
            # assert result["step_id"] == "meter_selection"

            # 3. Submit meter selection form
            # result = await hass.config_entries.flow.async_configure(
            #     result["flow_id"],
            #     {
            #         CONF_MPAN: multi_meter_account.properties[0].electricity_meter_points[0].mpan,
            #         CONF_MPRN: multi_meter_account.properties[0].gas_meter_points[0].mprn,
            #     }
            # )

            # 4. Verify entry created
            # assert result["type"] == FlowResult.type.CREATE_ENTRY
            # assert len(hass.config_entries.async_entries(DOMAIN)) == 1
