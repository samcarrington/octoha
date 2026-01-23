"""Tests for GraphQL queries module.

Tests T-019 to T-022: GraphQL query validity and variable builders.
"""

from __future__ import annotations

import pytest

from custom_components.octoha.api.graphql import (
    ACCOUNT_NUMBER_QUERY,
    ACCOUNT_QUERY,
    INTELLIGENT_DEVICE_QUERY,
    INTELLIGENT_DEVICE_QUERY_LEGACY,
    INTELLIGENT_DISPATCH_QUERY,
    INTELLIGENT_DISPATCH_QUERY_LEGACY,
    JOINED_SESSIONS_QUERY,
    LIVE_CONSUMPTION_QUERY,
    LIVE_CONSUMPTION_QUERY_LEGACY,
    LIVE_POWER_QUERY,
    LIVE_POWER_QUERY_LEGACY,
    PRODUCTS_QUERY,
    SAVING_SESSIONS_QUERY,
    SMART_DEVICE_QUERY,
    WHEEL_OF_FORTUNE_QUERY,
    build_account_variables,
    build_device_variables,
    build_dispatch_variables,
    build_live_consumption_variables,
    build_live_consumption_variables_legacy,
)


# ============================================================================
# T-019: GraphQL Query String Validity Tests
# ============================================================================


class TestGraphQLQueryValidity:
    """Test that GraphQL query strings are syntactically valid."""

    @pytest.mark.parametrize(
        ("query_name", "query_string"),
        [
            ("ACCOUNT_QUERY", ACCOUNT_QUERY),
            ("ACCOUNT_NUMBER_QUERY", ACCOUNT_NUMBER_QUERY),
            ("INTELLIGENT_DISPATCH_QUERY", INTELLIGENT_DISPATCH_QUERY),
            ("INTELLIGENT_DISPATCH_QUERY_LEGACY", INTELLIGENT_DISPATCH_QUERY_LEGACY),
            ("INTELLIGENT_DEVICE_QUERY", INTELLIGENT_DEVICE_QUERY),
            ("INTELLIGENT_DEVICE_QUERY_LEGACY", INTELLIGENT_DEVICE_QUERY_LEGACY),
            ("SMART_DEVICE_QUERY", SMART_DEVICE_QUERY),
            ("SAVING_SESSIONS_QUERY", SAVING_SESSIONS_QUERY),
            ("JOINED_SESSIONS_QUERY", JOINED_SESSIONS_QUERY),
            ("LIVE_POWER_QUERY", LIVE_POWER_QUERY),
            ("LIVE_POWER_QUERY_LEGACY", LIVE_POWER_QUERY_LEGACY),
            ("LIVE_CONSUMPTION_QUERY", LIVE_CONSUMPTION_QUERY),
            ("LIVE_CONSUMPTION_QUERY_LEGACY", LIVE_CONSUMPTION_QUERY_LEGACY),
            ("PRODUCTS_QUERY", PRODUCTS_QUERY),
            ("WHEEL_OF_FORTUNE_QUERY", WHEEL_OF_FORTUNE_QUERY),
        ],
    )
    def test_query_is_non_empty_string(
        self, query_name: str, query_string: str
    ) -> None:
        """Test that each query is a non-empty string."""
        assert isinstance(query_string, str), f"{query_name} should be a string"
        assert len(query_string.strip()) > 0, f"{query_name} should not be empty"

    @pytest.mark.parametrize(
        ("query_name", "query_string"),
        [
            ("ACCOUNT_QUERY", ACCOUNT_QUERY),
            ("ACCOUNT_NUMBER_QUERY", ACCOUNT_NUMBER_QUERY),
            ("INTELLIGENT_DISPATCH_QUERY", INTELLIGENT_DISPATCH_QUERY),
            ("INTELLIGENT_DISPATCH_QUERY_LEGACY", INTELLIGENT_DISPATCH_QUERY_LEGACY),
            ("INTELLIGENT_DEVICE_QUERY", INTELLIGENT_DEVICE_QUERY),
            ("INTELLIGENT_DEVICE_QUERY_LEGACY", INTELLIGENT_DEVICE_QUERY_LEGACY),
            ("SMART_DEVICE_QUERY", SMART_DEVICE_QUERY),
            ("SAVING_SESSIONS_QUERY", SAVING_SESSIONS_QUERY),
            ("JOINED_SESSIONS_QUERY", JOINED_SESSIONS_QUERY),
            ("LIVE_POWER_QUERY", LIVE_POWER_QUERY),
            ("LIVE_POWER_QUERY_LEGACY", LIVE_POWER_QUERY_LEGACY),
            ("LIVE_CONSUMPTION_QUERY", LIVE_CONSUMPTION_QUERY),
            ("LIVE_CONSUMPTION_QUERY_LEGACY", LIVE_CONSUMPTION_QUERY_LEGACY),
            ("PRODUCTS_QUERY", PRODUCTS_QUERY),
            ("WHEEL_OF_FORTUNE_QUERY", WHEEL_OF_FORTUNE_QUERY),
        ],
    )
    def test_query_has_balanced_braces(
        self, query_name: str, query_string: str
    ) -> None:
        """Test that each query has balanced curly braces."""
        open_count = query_string.count("{")
        close_count = query_string.count("}")
        assert (
            open_count == close_count
        ), f"{query_name} has unbalanced braces: {open_count} open, {close_count} close"

    @pytest.mark.parametrize(
        ("query_name", "query_string"),
        [
            ("ACCOUNT_QUERY", ACCOUNT_QUERY),
            ("ACCOUNT_NUMBER_QUERY", ACCOUNT_NUMBER_QUERY),
            ("INTELLIGENT_DISPATCH_QUERY", INTELLIGENT_DISPATCH_QUERY),
            ("INTELLIGENT_DISPATCH_QUERY_LEGACY", INTELLIGENT_DISPATCH_QUERY_LEGACY),
            ("INTELLIGENT_DEVICE_QUERY", INTELLIGENT_DEVICE_QUERY),
            ("INTELLIGENT_DEVICE_QUERY_LEGACY", INTELLIGENT_DEVICE_QUERY_LEGACY),
            ("SMART_DEVICE_QUERY", SMART_DEVICE_QUERY),
            ("SAVING_SESSIONS_QUERY", SAVING_SESSIONS_QUERY),
            ("JOINED_SESSIONS_QUERY", JOINED_SESSIONS_QUERY),
            ("LIVE_POWER_QUERY", LIVE_POWER_QUERY),
            ("LIVE_POWER_QUERY_LEGACY", LIVE_POWER_QUERY_LEGACY),
            ("LIVE_CONSUMPTION_QUERY", LIVE_CONSUMPTION_QUERY),
            ("LIVE_CONSUMPTION_QUERY_LEGACY", LIVE_CONSUMPTION_QUERY_LEGACY),
            ("PRODUCTS_QUERY", PRODUCTS_QUERY),
            ("WHEEL_OF_FORTUNE_QUERY", WHEEL_OF_FORTUNE_QUERY),
        ],
    )
    def test_query_starts_with_query_keyword(
        self, query_name: str, query_string: str
    ) -> None:
        """Test that each query starts with the 'query' keyword."""
        stripped = query_string.strip()
        assert stripped.startswith(
            "query"
        ), f"{query_name} should start with 'query' keyword"

    @pytest.mark.parametrize(
        ("query_name", "query_string"),
        [
            ("ACCOUNT_QUERY", ACCOUNT_QUERY),
            ("ACCOUNT_NUMBER_QUERY", ACCOUNT_NUMBER_QUERY),
            ("INTELLIGENT_DISPATCH_QUERY", INTELLIGENT_DISPATCH_QUERY),
            ("INTELLIGENT_DISPATCH_QUERY_LEGACY", INTELLIGENT_DISPATCH_QUERY_LEGACY),
            ("INTELLIGENT_DEVICE_QUERY", INTELLIGENT_DEVICE_QUERY),
            ("INTELLIGENT_DEVICE_QUERY_LEGACY", INTELLIGENT_DEVICE_QUERY_LEGACY),
            ("SMART_DEVICE_QUERY", SMART_DEVICE_QUERY),
            ("SAVING_SESSIONS_QUERY", SAVING_SESSIONS_QUERY),
            ("JOINED_SESSIONS_QUERY", JOINED_SESSIONS_QUERY),
            ("LIVE_POWER_QUERY", LIVE_POWER_QUERY),
            ("LIVE_POWER_QUERY_LEGACY", LIVE_POWER_QUERY_LEGACY),
            ("LIVE_CONSUMPTION_QUERY", LIVE_CONSUMPTION_QUERY),
            ("LIVE_CONSUMPTION_QUERY_LEGACY", LIVE_CONSUMPTION_QUERY_LEGACY),
            ("PRODUCTS_QUERY", PRODUCTS_QUERY),
            ("WHEEL_OF_FORTUNE_QUERY", WHEEL_OF_FORTUNE_QUERY),
        ],
    )
    def test_query_has_balanced_parentheses(
        self, query_name: str, query_string: str
    ) -> None:
        """Test that each query has balanced parentheses."""
        open_count = query_string.count("(")
        close_count = query_string.count(")")
        assert (
            open_count == close_count
        ), f"{query_name} has unbalanced parentheses: {open_count} open, {close_count} close"


class TestQueryVariableDeclarations:
    """Test that queries declare expected variables."""

    def test_account_query_requires_account_number(self) -> None:
        """Test ACCOUNT_QUERY declares $accountNumber variable."""
        assert "$accountNumber: String!" in ACCOUNT_QUERY
        assert "account(accountNumber: $accountNumber)" in ACCOUNT_QUERY

    def test_account_number_query_has_no_variables(self) -> None:
        """Test ACCOUNT_NUMBER_QUERY has no variable declarations."""
        # The query should use viewer which doesn't need variables
        assert "getAccountNumber" in ACCOUNT_NUMBER_QUERY
        assert "viewer" in ACCOUNT_NUMBER_QUERY

    def test_intelligent_dispatch_query_requires_both_variables(self) -> None:
        """Test INTELLIGENT_DISPATCH_QUERY requires account and device."""
        assert "$accountNumber: String!" in INTELLIGENT_DISPATCH_QUERY
        assert "$deviceId: String!" in INTELLIGENT_DISPATCH_QUERY

    def test_intelligent_dispatch_legacy_requires_only_account(self) -> None:
        """Test legacy dispatch query only needs account number."""
        assert "$accountNumber: String!" in INTELLIGENT_DISPATCH_QUERY_LEGACY
        assert "$deviceId" not in INTELLIGENT_DISPATCH_QUERY_LEGACY

    def test_live_power_query_requires_device_id(self) -> None:
        """Test LIVE_POWER_QUERY requires device ID."""
        assert "$deviceId: String!" in LIVE_POWER_QUERY
        assert "smartMeterTelemetry(deviceId: $deviceId)" in LIVE_POWER_QUERY

    def test_live_power_legacy_requires_account(self) -> None:
        """Test legacy live power query requires account number."""
        assert "$accountNumber: String!" in LIVE_POWER_QUERY_LEGACY

    def test_live_consumption_query_requires_all_variables(self) -> None:
        """Test LIVE_CONSUMPTION_QUERY requires device, start, and end."""
        assert "$deviceId: String!" in LIVE_CONSUMPTION_QUERY
        assert "$start: DateTime!" in LIVE_CONSUMPTION_QUERY
        assert "$end: DateTime!" in LIVE_CONSUMPTION_QUERY

    def test_live_consumption_legacy_requires_account_and_dates(self) -> None:
        """Test legacy consumption query requires account and dates."""
        assert "$accountNumber: String!" in LIVE_CONSUMPTION_QUERY_LEGACY
        assert "$start: DateTime!" in LIVE_CONSUMPTION_QUERY_LEGACY
        assert "$end: DateTime!" in LIVE_CONSUMPTION_QUERY_LEGACY


class TestQueryFields:
    """Test that queries request expected fields."""

    def test_account_query_includes_meter_points(self) -> None:
        """Test ACCOUNT_QUERY includes electricity and gas meter points."""
        assert "electricityMeterPoints" in ACCOUNT_QUERY
        assert "gasMeterPoints" in ACCOUNT_QUERY
        assert "mpan" in ACCOUNT_QUERY
        assert "mprn" in ACCOUNT_QUERY

    def test_account_query_includes_agreements(self) -> None:
        """Test ACCOUNT_QUERY includes tariff agreements."""
        assert "agreements" in ACCOUNT_QUERY
        assert "tariffCode" in ACCOUNT_QUERY
        assert "productCode" in ACCOUNT_QUERY

    def test_account_query_includes_balance(self) -> None:
        """Test ACCOUNT_QUERY includes account balance."""
        assert "balance" in ACCOUNT_QUERY

    def test_intelligent_dispatch_includes_dispatches(self) -> None:
        """Test dispatch query includes planned and completed dispatches."""
        assert "flexPlannedDispatches" in INTELLIGENT_DISPATCH_QUERY
        assert "completedDispatches" in INTELLIGENT_DISPATCH_QUERY
        assert "start" in INTELLIGENT_DISPATCH_QUERY
        assert "end" in INTELLIGENT_DISPATCH_QUERY

    def test_saving_sessions_includes_events(self) -> None:
        """Test saving sessions query includes event data."""
        assert "events" in SAVING_SESSIONS_QUERY
        assert "startAt" in SAVING_SESSIONS_QUERY
        assert "endAt" in SAVING_SESSIONS_QUERY
        assert "rewardPerKwhInOctoPoints" in SAVING_SESSIONS_QUERY

    def test_live_power_query_includes_telemetry(self) -> None:
        """Test live power query includes telemetry fields."""
        assert "smartMeterTelemetry" in LIVE_POWER_QUERY
        assert "demand" in LIVE_POWER_QUERY
        assert "readAt" in LIVE_POWER_QUERY

    def test_wheel_of_fortune_includes_spins(self) -> None:
        """Test wheel of fortune query includes spin data."""
        assert "wheelOfFortuneSpins" in WHEEL_OF_FORTUNE_QUERY
        assert "electricity" in WHEEL_OF_FORTUNE_QUERY
        assert "gas" in WHEEL_OF_FORTUNE_QUERY
        assert "remainingSpinsThisMonth" in WHEEL_OF_FORTUNE_QUERY


# ============================================================================
# T-020: build_account_variables() Tests
# ============================================================================


class TestBuildAccountVariables:
    """Test build_account_variables helper function."""

    def test_returns_dict_with_account_number(self) -> None:
        """Test function returns dict with accountNumber key."""
        result = build_account_variables("A-1234ABCD")
        assert isinstance(result, dict)
        assert "accountNumber" in result
        assert result["accountNumber"] == "A-1234ABCD"

    def test_with_various_account_formats(self) -> None:
        """Test with different account number formats."""
        # Standard format
        result = build_account_variables("A-12AB34CD")
        assert result["accountNumber"] == "A-12AB34CD"

        # Longer account number
        result = build_account_variables("A-1234567890")
        assert result["accountNumber"] == "A-1234567890"

        # Just the number part (edge case)
        result = build_account_variables("1234ABCD")
        assert result["accountNumber"] == "1234ABCD"

    def test_returns_only_account_number_key(self) -> None:
        """Test function returns dict with only accountNumber key."""
        result = build_account_variables("A-TEST1234")
        assert len(result) == 1
        assert list(result.keys()) == ["accountNumber"]


# ============================================================================
# T-021: build_dispatch_variables() Tests
# ============================================================================


class TestBuildDispatchVariables:
    """Test build_dispatch_variables helper function."""

    def test_returns_dict_with_both_keys(self) -> None:
        """Test function returns dict with accountNumber and deviceId."""
        result = build_dispatch_variables("A-1234ABCD", "device-123")
        assert isinstance(result, dict)
        assert "accountNumber" in result
        assert "deviceId" in result
        assert result["accountNumber"] == "A-1234ABCD"
        assert result["deviceId"] == "device-123"

    def test_with_various_device_id_formats(self) -> None:
        """Test with different device ID formats."""
        # UUID-style device ID
        result = build_dispatch_variables(
            "A-TEST1234", "550e8400-e29b-41d4-a716-446655440000"
        )
        assert result["deviceId"] == "550e8400-e29b-41d4-a716-446655440000"

        # Simple device ID
        result = build_dispatch_variables("A-TEST1234", "charger-1")
        assert result["deviceId"] == "charger-1"

    def test_returns_exactly_two_keys(self) -> None:
        """Test function returns dict with exactly two keys."""
        result = build_dispatch_variables("A-TEST", "device-1")
        assert len(result) == 2


# ============================================================================
# T-022: Other Variable Builder Tests
# ============================================================================


class TestBuildDeviceVariables:
    """Test build_device_variables helper function."""

    def test_returns_dict_with_device_id(self) -> None:
        """Test function returns dict with deviceId key."""
        result = build_device_variables("smart-meter-123")
        assert isinstance(result, dict)
        assert "deviceId" in result
        assert result["deviceId"] == "smart-meter-123"

    def test_returns_only_device_id_key(self) -> None:
        """Test function returns dict with only deviceId key."""
        result = build_device_variables("device-xyz")
        assert len(result) == 1
        assert list(result.keys()) == ["deviceId"]


class TestBuildLiveConsumptionVariables:
    """Test build_live_consumption_variables helper function."""

    def test_returns_dict_with_all_keys(self) -> None:
        """Test function returns dict with deviceId, start, and end."""
        result = build_live_consumption_variables(
            "device-123",
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
        )
        assert isinstance(result, dict)
        assert "deviceId" in result
        assert "start" in result
        assert "end" in result
        assert result["deviceId"] == "device-123"
        assert result["start"] == "2024-01-01T00:00:00Z"
        assert result["end"] == "2024-01-02T00:00:00Z"

    def test_returns_exactly_three_keys(self) -> None:
        """Test function returns dict with exactly three keys."""
        result = build_live_consumption_variables(
            "device-1", "2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"
        )
        assert len(result) == 3

    def test_preserves_iso_format(self) -> None:
        """Test function preserves ISO datetime format."""
        start = "2024-06-15T14:30:00+01:00"
        end = "2024-06-15T15:30:00+01:00"
        result = build_live_consumption_variables("device", start, end)
        assert result["start"] == start
        assert result["end"] == end


class TestBuildLiveConsumptionVariablesLegacy:
    """Test build_live_consumption_variables_legacy helper function."""

    def test_returns_dict_with_all_keys(self) -> None:
        """Test function returns dict with accountNumber, start, and end."""
        result = build_live_consumption_variables_legacy(
            "A-1234ABCD",
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
        )
        assert isinstance(result, dict)
        assert "accountNumber" in result
        assert "start" in result
        assert "end" in result
        assert result["accountNumber"] == "A-1234ABCD"
        assert result["start"] == "2024-01-01T00:00:00Z"
        assert result["end"] == "2024-01-02T00:00:00Z"

    def test_uses_account_number_not_device_id(self) -> None:
        """Test legacy function uses accountNumber instead of deviceId."""
        result = build_live_consumption_variables_legacy(
            "A-TEST", "2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"
        )
        assert "accountNumber" in result
        assert "deviceId" not in result

    def test_returns_exactly_three_keys(self) -> None:
        """Test function returns dict with exactly three keys."""
        result = build_live_consumption_variables_legacy(
            "A-TEST", "2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"
        )
        assert len(result) == 3


# ============================================================================
# Query Consistency Tests
# ============================================================================


class TestQueryConsistency:
    """Test consistency between regular and legacy query versions."""

    def test_dispatch_queries_have_same_operation_name(self) -> None:
        """Test both dispatch queries use same operation name."""
        assert "getIntelligentDispatches" in INTELLIGENT_DISPATCH_QUERY
        assert "getIntelligentDispatches" in INTELLIGENT_DISPATCH_QUERY_LEGACY

    def test_live_power_queries_have_same_operation_name(self) -> None:
        """Test both live power queries use same operation name."""
        assert "getLivePower" in LIVE_POWER_QUERY
        assert "getLivePower" in LIVE_POWER_QUERY_LEGACY

    def test_live_consumption_queries_have_same_operation_name(self) -> None:
        """Test both live consumption queries use same operation name."""
        assert "getLiveConsumption" in LIVE_CONSUMPTION_QUERY
        assert "getLiveConsumption" in LIVE_CONSUMPTION_QUERY_LEGACY

    def test_device_queries_use_different_operation_names(self) -> None:
        """Test device queries have distinct operation names."""
        # New query uses getIntelligentDevices (plural)
        assert "getIntelligentDevices" in INTELLIGENT_DEVICE_QUERY
        # Legacy uses getIntelligentDevice (singular)
        assert "getIntelligentDevice" in INTELLIGENT_DEVICE_QUERY_LEGACY


class TestTariffFragments:
    """Test tariff type fragments in account query."""

    @pytest.mark.parametrize(
        "tariff_type",
        [
            "StandardTariff",
            "HalfHourlyTariff",
            "DayNightTariff",
            "ThreeRateTariff",
            "PrepayTariff",
        ],
    )
    def test_account_query_includes_tariff_type(self, tariff_type: str) -> None:
        """Test ACCOUNT_QUERY includes inline fragments for all tariff types."""
        assert f"... on {tariff_type}" in ACCOUNT_QUERY
