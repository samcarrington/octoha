"""Integration tests for Octopus Energy API onboarding.

These tests use a real API key from the OCTOPUS_API_KEY environment variable
to test actual integration with the Octopus Energy API.

IMPORTANT: These tests make real API calls and require a valid API key.
They are skipped if OCTOPUS_API_KEY is not set.

To run these tests:
    pytest tests/test_integration_onboarding.py -v -p no:socket -p no:homeassistant

Or with API key:
    OCTOPUS_API_KEY=your_key pytest tests/test_integration_onboarding.py -v \
        -p no:socket -p no:homeassistant
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator

import aiohttp
import pytest

from custom_components.octoha.api.client import OctohaApiClient
from custom_components.octoha.api.exceptions import (
    AuthenticationError,
    OctopusError,
    RateLimitError,
)
from custom_components.octoha.models.account import Account

# Get API key from environment
OCTOPUS_API_KEY = os.environ.get("OCTOPUS_API_KEY")

# Marker to enable sockets and allow all hosts for integration tests
# pytest-socket blocks by default, these markers allow real network access
enable_socket = pytest.mark.enable_socket
allow_hosts = pytest.mark.allow_hosts(
    ["api.octopus.energy", "127.0.0.1"], allow_unix_socket=True
)

# Skip marker for tests requiring real API key
requires_api_key = pytest.mark.skipif(
    OCTOPUS_API_KEY is None,
    reason="OCTOPUS_API_KEY environment variable not set",
)

# Rate limit handling constants
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


async def with_retry(coro_func, *args, **kwargs):
    """Execute an async function with retry on rate limit.

    Args:
        coro_func: Async function to call.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        Result of the function call.

    Raises:
        The last exception if all retries fail.
    """
    last_exception: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return await coro_func(*args, **kwargs)
        except RateLimitError as e:
            # Explicit rate limit error
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY_SECONDS * (attempt + 1)
                retry_msg = f"{attempt + 2}/{MAX_RETRIES}"
                print(
                    f"\nRate limited (RateLimitError), "
                    f"waiting {wait_time}s before retry {retry_msg}..."
                )
                await asyncio.sleep(wait_time)
        except AuthenticationError as e:
            # Check if it's actually a rate limit error disguised as auth error
            error_str = str(e).lower()
            if "too many requests" in error_str or "rate limit" in error_str:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY_SECONDS * (attempt + 1)
                    retry_msg = f"{attempt + 2}/{MAX_RETRIES}"
                    print(
                        f"\nRate limited (AuthError), "
                        f"waiting {wait_time}s before retry {retry_msg}..."
                    )
                    await asyncio.sleep(wait_time)
            else:
                # Real authentication error, don't retry
                raise
    if last_exception is not None:
        raise last_exception
    raise OctopusError("Unknown error occurred after retries")


@pytest.fixture
async def real_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Create a real aiohttp ClientSession for integration tests.

    Yields:
        aiohttp.ClientSession: A real HTTP client session.
    """
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def real_api_key() -> str:
    """Return the real API key from environment.

    Returns:
        str: The Octopus Energy API key.

    Raises:
        ValueError: If API key is not set.
    """
    if OCTOPUS_API_KEY is None:
        raise ValueError("OCTOPUS_API_KEY environment variable not set")
    return OCTOPUS_API_KEY


@pytest.fixture
async def real_client(
    real_session: aiohttp.ClientSession, real_api_key: str
) -> OctohaApiClient:
    """Create a real API client for integration tests.

    Args:
        real_session: Real aiohttp client session.
        real_api_key: Real Octopus Energy API key.

    Returns:
        OctohaApiClient: Configured API client.
    """
    return OctohaApiClient(
        session=real_session,
        api_key=real_api_key,
    )


@requires_api_key
@enable_socket
@allow_hosts
class TestCredentialValidation:
    """Integration tests for API credential validation.

    These tests verify that the API key validation works correctly
    with the real Octopus Energy API.
    """

    @pytest.mark.asyncio
    async def test_validate_credentials_with_valid_key(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that validate_credentials succeeds with a valid API key.

        This verifies the first step of the onboarding process where
        the user's API key is validated.
        """
        result = await with_retry(real_client.validate_credentials)

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_credentials_with_invalid_key(
        self,
        real_session: aiohttp.ClientSession,
    ) -> None:
        """Test that validate_credentials fails with an invalid API key.

        This verifies that authentication errors are properly raised
        when the API key is incorrect.
        """
        client = OctohaApiClient(
            session=real_session,
            api_key="sk_invalid_key_12345",
        )

        with pytest.raises(AuthenticationError):
            await client.validate_credentials()

    @pytest.mark.asyncio
    async def test_validate_credentials_with_empty_key(
        self,
        real_session: aiohttp.ClientSession,
    ) -> None:
        """Test that validate_credentials fails with an empty API key.

        This verifies edge case handling for empty/blank API keys.
        """
        client = OctohaApiClient(
            session=real_session,
            api_key="",
        )

        with pytest.raises((AuthenticationError, OctopusError)):
            await client.validate_credentials()

    @pytest.mark.asyncio
    async def test_validate_credentials_with_malformed_key(
        self,
        real_session: aiohttp.ClientSession,
    ) -> None:
        """Test that validate_credentials fails with a malformed API key.

        This verifies handling of API keys that don't match expected format.
        """
        client = OctohaApiClient(
            session=real_session,
            api_key="not-a-valid-api-key-format",
        )

        with pytest.raises((AuthenticationError, OctopusError)):
            await client.validate_credentials()


@requires_api_key
@enable_socket
@allow_hosts
class TestAccountDiscovery:
    """Integration tests for account number discovery.

    These tests verify that the account discovery process works correctly
    with the real Octopus Energy API.
    """

    @pytest.mark.asyncio
    async def test_discover_account_number_success(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that discover_account_number returns a valid account number.

        This verifies the second step of the onboarding process where
        the account number is auto-discovered from the API key.
        """
        account_number = await with_retry(real_client.discover_account_number)

        # Account numbers follow the format A-XXXXXXXX (letter-8chars)
        assert account_number is not None
        assert len(account_number) > 0
        assert account_number.startswith("A-")

    @pytest.mark.asyncio
    async def test_discover_account_number_caches_result(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that the discovered account number is cached on the client.

        This verifies that after discovery, the account_number property
        is set correctly for subsequent operations.
        """
        # Initially, account number should be None
        assert real_client.account_number is None

        # Discover account number
        account_number = await with_retry(real_client.discover_account_number)

        # After discovery, it should be cached
        assert real_client.account_number == account_number

    @pytest.mark.asyncio
    async def test_discover_account_number_with_invalid_key(
        self,
        real_session: aiohttp.ClientSession,
    ) -> None:
        """Test that discover_account_number fails with an invalid API key.

        This verifies proper error handling during account discovery
        when authentication fails.
        """
        client = OctohaApiClient(
            session=real_session,
            api_key="sk_invalid_key_12345",
        )

        with pytest.raises((AuthenticationError, OctopusError)):
            await client.discover_account_number()


@requires_api_key
@enable_socket
@allow_hosts
class TestAccountFetching:
    """Integration tests for fetching account data.

    These tests verify that account data retrieval works correctly
    with the real Octopus Energy API.
    """

    @pytest.mark.asyncio
    async def test_get_account_success(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that get_account returns valid account data.

        This verifies the third step of the onboarding process where
        account details including meters are fetched.
        """
        # First discover account number (required for get_account)
        await with_retry(real_client.discover_account_number)

        # Then fetch account data
        account = await with_retry(real_client.get_account)

        assert account is not None
        assert isinstance(account, Account)
        assert account.account_number is not None
        assert len(account.account_number) > 0

    @pytest.mark.asyncio
    async def test_get_account_has_properties(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that the account has at least one property.

        This verifies that the account data includes property information
        which is required for meter discovery during onboarding.
        """
        await with_retry(real_client.discover_account_number)
        account = await with_retry(real_client.get_account)

        # A valid account should have at least one property
        assert account.properties is not None
        assert len(account.properties) >= 1

    @pytest.mark.asyncio
    async def test_get_account_has_meters(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that the account has at least one meter point.

        This verifies that the account has electricity and/or gas meters
        which are required for the integration to function.
        """
        await with_retry(real_client.discover_account_number)
        account = await with_retry(real_client.get_account)

        # Should have at least one meter type
        has_electricity = account.primary_electricity is not None
        has_gas = account.primary_gas is not None

        assert has_electricity or has_gas, (
            "Account must have at least one electricity or gas meter. "
            "If your account genuinely has no meters, this test is expected to fail."
        )

    @pytest.mark.asyncio
    async def test_get_account_electricity_meter_details(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that electricity meter has required details.

        This verifies that electricity meter data includes MPAN and
        serial number which are required for consumption queries.
        """
        await with_retry(real_client.discover_account_number)
        account = await with_retry(real_client.get_account)

        elec_meter = account.primary_electricity
        if elec_meter is None:
            pytest.skip("Account does not have an electricity meter")

        # Verify meter has required fields
        assert elec_meter.mpan is not None
        assert len(elec_meter.mpan) > 0
        assert elec_meter.meter_serial is not None
        # Serial might be empty for non-smart meters

    @pytest.mark.asyncio
    async def test_get_account_gas_meter_details(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that gas meter has required details.

        This verifies that gas meter data includes MPRN and
        serial number which are required for consumption queries.
        """
        await with_retry(real_client.discover_account_number)
        account = await with_retry(real_client.get_account)

        gas_meter = account.primary_gas
        if gas_meter is None:
            pytest.skip("Account does not have a gas meter")

        # Verify meter has required fields
        assert gas_meter.mprn is not None
        assert len(gas_meter.mprn) > 0
        assert gas_meter.meter_serial is not None
        # Serial might be empty for non-smart meters

    @pytest.mark.asyncio
    async def test_get_account_balance(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that account balance is returned.

        This verifies that the balance field is populated in the account data.
        Balance can be positive (credit) or negative (owed).
        """
        await with_retry(real_client.discover_account_number)
        account = await with_retry(real_client.get_account)

        # Balance should be a float (can be positive, negative, or zero)
        assert isinstance(account.balance, float)

    @pytest.mark.asyncio
    async def test_get_account_caching(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that account data is cached after first fetch.

        This verifies that subsequent calls return the cached data
        without making additional API requests.
        """
        await with_retry(real_client.discover_account_number)

        # First call
        account1 = await with_retry(real_client.get_account)

        # Second call (should use cache)
        account2 = await real_client.get_account()

        # Should be the same object (cached)
        assert account1 is account2

    @pytest.mark.asyncio
    async def test_get_account_force_refresh(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that force_refresh bypasses the cache.

        This verifies that force_refresh=True fetches fresh data
        from the API instead of using cached data.
        """
        await with_retry(real_client.discover_account_number)

        # First call
        account1 = await with_retry(real_client.get_account)

        # Second call with force_refresh
        account2 = await with_retry(real_client.get_account, force_refresh=True)

        # Should NOT be the same object (new fetch)
        assert account1 is not account2
        # But should have same account number
        assert account1.account_number == account2.account_number


@requires_api_key
@enable_socket
@allow_hosts
class TestFullOnboardingFlow:
    """Integration tests for the complete onboarding flow.

    These tests simulate the full onboarding process as it would
    happen in the Home Assistant config flow.
    """

    @pytest.mark.asyncio
    async def test_full_onboarding_flow(
        self,
        real_session: aiohttp.ClientSession,
        real_api_key: str,
    ) -> None:
        """Test the complete onboarding flow end-to-end.

        This simulates the entire config flow process:
        1. Create client with API key
        2. Validate credentials
        3. Discover account number
        4. Fetch account data
        5. Verify meter discovery
        """
        # Step 1: Create client with API key (simulating user input)
        client = OctohaApiClient(
            session=real_session,
            api_key=real_api_key,
        )

        # Step 2: Validate credentials (simulating async_step_user validation)
        is_valid = await with_retry(client.validate_credentials)
        assert is_valid is True, "Credential validation should succeed"

        # Step 3: Discover account number
        account_number = await with_retry(client.discover_account_number)
        assert account_number is not None
        assert account_number.startswith("A-")
        assert client.account_number == account_number

        # Step 4: Fetch account data
        account = await with_retry(client.get_account)
        assert account is not None
        assert account.account_number == account_number

        # Step 5: Verify meter discovery
        has_electricity = account.primary_electricity is not None
        has_gas = account.primary_gas is not None
        total_meters = len(account.electricity_meter_points) + len(
            account.gas_meter_points
        )

        assert total_meters > 0, "Account must have at least one meter"

        # Log discovered configuration for debugging
        print("\n=== Onboarding Flow Successful ===")
        print(f"Account Number: {account_number}")
        print(f"Balance: {account.balance}")
        print(f"Properties: {len(account.properties)}")
        print(f"Electricity Meters: {len(account.electricity_meter_points)}")
        print(f"Gas Meters: {len(account.gas_meter_points)}")

        if has_electricity:
            elec = account.primary_electricity
            assert elec is not None  # for type checker
            print(f"Primary Electricity MPAN: {elec.mpan}")
            print(f"Primary Electricity Serial: {elec.meter_serial}")
            if elec.agreements:
                print(f"Tariff: {elec.agreements[0].tariff_code}")

        if has_gas:
            gas = account.primary_gas
            assert gas is not None  # for type checker
            print(f"Primary Gas MPRN: {gas.mprn}")
            print(f"Primary Gas Serial: {gas.meter_serial}")

    @pytest.mark.asyncio
    async def test_onboarding_creates_config_data(
        self,
        real_session: aiohttp.ClientSession,
        real_api_key: str,
    ) -> None:
        """Test that onboarding produces valid config entry data.

        This verifies that all data required for creating a config entry
        is available after the onboarding flow completes.
        """
        client = OctohaApiClient(
            session=real_session,
            api_key=real_api_key,
        )

        await with_retry(client.validate_credentials)
        await with_retry(client.discover_account_number)
        account = await with_retry(client.get_account)

        # Build config data as config_flow._create_entry would
        config_data: dict[str, str] = {
            "api_key": real_api_key,
            "account": account.account_number,
        }

        # Add electricity meter data if available
        if account.primary_electricity:
            config_data["mpan"] = account.primary_electricity.mpan
            config_data["meter_serial"] = account.primary_electricity.meter_serial

        # Add gas meter data if available
        if account.primary_gas:
            config_data["mprn"] = account.primary_gas.mprn
            config_data["gas_meter_serial"] = account.primary_gas.meter_serial

        # Verify required fields are present
        assert "api_key" in config_data
        assert "account" in config_data
        assert config_data["account"] is not None

        # At least one meter type should be configured
        has_elec_config = "mpan" in config_data and "meter_serial" in config_data
        has_gas_config = "mprn" in config_data and "gas_meter_serial" in config_data
        assert has_elec_config or has_gas_config


@requires_api_key
@enable_socket
@allow_hosts
class TestAgreementsAndTariffs:
    """Integration tests for tariff agreement discovery.

    These tests verify that tariff information is correctly discovered
    during onboarding, which is important for rate sensors.
    """

    @pytest.mark.asyncio
    async def test_electricity_agreements_discovered(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that electricity tariff agreements are discovered.

        This verifies that the current tariff code is available
        for creating tariff-related sensors.
        """
        await with_retry(real_client.discover_account_number)
        account = await with_retry(real_client.get_account)

        elec_meter = account.primary_electricity
        if elec_meter is None:
            pytest.skip("Account does not have an electricity meter")

        # Most meters should have at least one agreement
        if len(elec_meter.agreements) == 0:
            pytest.skip("Electricity meter has no active agreements")

        agreement = elec_meter.agreements[0]
        assert agreement.tariff_code is not None
        assert len(agreement.tariff_code) > 0
        assert agreement.valid_from is not None

    @pytest.mark.asyncio
    async def test_gas_agreements_discovered(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that gas tariff agreements are discovered.

        This verifies that the current gas tariff code is available
        for creating tariff-related sensors.
        """
        await with_retry(real_client.discover_account_number)
        account = await with_retry(real_client.get_account)

        gas_meter = account.primary_gas
        if gas_meter is None:
            pytest.skip("Account does not have a gas meter")

        # Most meters should have at least one agreement
        if len(gas_meter.agreements) == 0:
            pytest.skip("Gas meter has no active agreements")

        agreement = gas_meter.agreements[0]
        assert agreement.tariff_code is not None
        assert len(agreement.tariff_code) > 0
        assert agreement.valid_from is not None


@requires_api_key
@enable_socket
@allow_hosts
class TestTokenManagement:
    """Integration tests for token management during onboarding.

    These tests verify that token acquisition and caching work correctly
    with the real API.
    """

    @pytest.mark.asyncio
    async def test_token_obtained_on_first_request(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that a token is obtained on the first API request.

        This verifies that the token manager correctly authenticates
        when making the first request.
        """
        # Token should be None initially
        assert real_client._token_manager._token is None

        # Make a request that requires authentication
        await with_retry(real_client.discover_account_number)

        # Token should now be set
        assert real_client._token_manager._token is not None
        assert real_client._token_manager.is_token_valid

    @pytest.mark.asyncio
    async def test_token_reused_for_subsequent_requests(
        self,
        real_client: OctohaApiClient,
    ) -> None:
        """Test that the token is reused for subsequent requests.

        This verifies that the token manager doesn't re-authenticate
        unnecessarily, improving performance.
        """
        # First request - obtain token
        await with_retry(real_client.discover_account_number)
        token_after_first = real_client._token_manager._token

        # Second request - should reuse token
        await with_retry(real_client.get_account)
        token_after_second = real_client._token_manager._token

        # Same token should be used
        assert token_after_first == token_after_second


@requires_api_key
@enable_socket
@allow_hosts
class TestErrorRecovery:
    """Integration tests for error handling during onboarding.

    These tests verify that errors are properly handled and meaningful
    error messages are provided to users.
    """

    @pytest.mark.asyncio
    async def test_authentication_error_is_clear(
        self,
        real_session: aiohttp.ClientSession,
    ) -> None:
        """Test that authentication errors provide clear feedback.

        This verifies that when a user enters an invalid API key,
        they receive a clear error message.
        """
        client = OctohaApiClient(
            session=real_session,
            api_key="sk_totally_invalid_key",
        )

        with pytest.raises(AuthenticationError) as exc_info:
            await client.validate_credentials()

        # Error should be meaningful
        error = exc_info.value
        assert str(error) is not None
        assert len(str(error)) > 0

    @pytest.mark.asyncio
    async def test_client_cleanup_on_close(
        self,
        real_session: aiohttp.ClientSession,
        real_api_key: str,
    ) -> None:
        """Test that client properly cleans up resources on close.

        This verifies that cached data is cleared when the client
        is closed, which is important for cleanup on error.
        """
        client = OctohaApiClient(
            session=real_session,
            api_key=real_api_key,
        )

        # Populate cache
        await with_retry(client.discover_account_number)
        await with_retry(client.get_account)

        assert client._token_manager._token is not None
        assert client._account is not None

        # Close client
        await client.close()

        # Cache should be cleared
        assert client._token_manager._token is None
        assert client._account is None
