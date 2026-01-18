"""Main Octoha API client facade.

Provides a unified interface to both GraphQL and REST Octopus Energy APIs.
Client architecture adapted from the open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, time, timezone
from typing import TYPE_CHECKING, Any

from ..const import GRAPHQL_URL
from ..models.account import Account, Agreement, GasMeterPoint, MeterPoint, Property
from ..models.consumption import Consumption, DailyUsage, GasConsumption
from ..models.dispatch import (
    Dispatch,
    DispatchSource,
    DispatchStatus,
    SavingSession,
    parse_completed_dispatch,
    parse_dispatch,
)
from ..models.tariff import CurrentRate, GasTariff, Rate, Tariff, TariffType, TimeWindow
from .auth import TokenManager
from .exceptions import (
    AuthenticationError,
    InvalidResponseError,
    OctopusError,
    sanitize_log_message,
)
from .graphql import (
    ACCOUNT_QUERY,
    INTELLIGENT_DISPATCH_QUERY,
    SAVING_SESSIONS_QUERY,
    build_account_variables,
)
from .rest import RestClient

if TYPE_CHECKING:
    import aiohttp

_LOGGER = logging.getLogger(__name__)


class OctohaApiClient:
    """Main API client for Octopus Energy data.

    This client provides a high-level interface for fetching:
    - Account information and meter details
    - Electricity and gas consumption data
    - Tariff rates and standing charges
    - Intelligent Octopus dispatch schedules
    - Saving Sessions and events

    The client uses GraphQL for account/dispatch data and REST for
    consumption/tariff data.

    Attributes:
        account_number: The Octopus Energy account number.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        account_number: str | None = None,
    ) -> None:
        """Initialize the API client.

        Args:
            session: aiohttp client session for HTTP requests.
            api_key: Octopus Energy API key.
            account_number: Optional account number (auto-discovered if not provided).
        """
        self._session = session
        self._api_key = api_key
        self._account_number = account_number
        self._account: Account | None = None

        # Initialize sub-clients
        self._token_manager = TokenManager(session, api_key)
        self._rest_client = RestClient(session, api_key)

    @property
    def account_number(self) -> str | None:
        """Return the account number."""
        return self._account_number

    @property
    def account(self) -> Account | None:
        """Return the cached account data."""
        return self._account

    # ========================================================================
    # GraphQL Methods
    # ========================================================================

    async def _graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict:
        """Execute an authenticated GraphQL query.

        Args:
            query: GraphQL query string.
            variables: Optional query variables.

        Returns:
            GraphQL response data.

        Raises:
            AuthenticationError: If authentication fails.
            InvalidResponseError: If response format is unexpected.
            OctopusError: For other API errors.
        """
        token = await self._token_manager.get_token()

        payload = {
            "query": query,
            "variables": variables or {},
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": token,
        }

        try:
            async with self._session.post(
                GRAPHQL_URL,
                json=payload,
                headers=headers,
            ) as response:
                if response.status == 401:
                    self._token_manager.invalidate_token()
                    raise AuthenticationError(
                        "GraphQL authentication failed",
                        status_code=401,
                    )

                if response.status != 200:
                    text = await response.text()
                    # Log full details, sanitize user-facing message
                    _LOGGER.error(
                        "GraphQL error: HTTP %s: %s",
                        response.status,
                        sanitize_log_message(text),
                    )
                    raise OctopusError(
                        f"GraphQL request failed (HTTP {response.status})",
                        status_code=response.status,
                    )

                data = await response.json()

        except (AuthenticationError, OctopusError):
            raise
        except Exception as err:
            _LOGGER.exception("GraphQL request failed")
            raise OctopusError("GraphQL request failed") from err

        # Check for GraphQL errors
        if "errors" in data:
            errors = data["errors"]
            error_messages = [e.get("message", str(e)) for e in errors]
            _LOGGER.error(
                "GraphQL errors: %s",
                [sanitize_log_message(msg) for msg in error_messages],
            )

            # Check if this is an auth error
            for msg in error_messages:
                if "unauthorized" in msg.lower() or "authentication" in msg.lower():
                    self._token_manager.invalidate_token()
                    raise AuthenticationError("GraphQL authentication failed")

            raise OctopusError("GraphQL request returned errors")

        return data.get("data", {})

    # ========================================================================
    # Account Methods
    # ========================================================================

    async def get_account(self, force_refresh: bool = False) -> Account:
        """Get account information including meter points.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            Account object with properties and meter points.

        Raises:
            AuthenticationError: If authentication fails.
            OctopusError: If request fails.
        """
        if self._account is not None and not force_refresh:
            return self._account

        if self._account_number is None:
            raise OctopusError("Account number not set")

        data = await self._graphql(
            ACCOUNT_QUERY,
            build_account_variables(self._account_number),
        )

        account_data = data.get("account")
        if not account_data:
            raise OctopusError(f"Account not found: {self._account_number}")

        self._account = self._parse_account(account_data)
        return self._account

    def _parse_account(self, data: dict) -> Account:
        """Parse account data from GraphQL response.

        Args:
            data: Account data dictionary.

        Returns:
            Account object.
        """
        properties = []

        for prop_data in data.get("properties", []):
            # Parse electricity meter points
            electricity_meters = []
            for mp_data in prop_data.get("electricityMeterPoints", []):
                meters = mp_data.get("meters", [])
                meter_serial = meters[0]["serialNumber"] if meters else ""

                # Parse agreements
                agreements = []
                for agr in mp_data.get("agreements", []):
                    tariff = agr.get("tariff", {})
                    tariff_code = tariff.get("tariffCode", "")
                    if tariff_code:
                        agreements.append(
                            Agreement(
                                tariff_code=tariff_code,
                                valid_from=agr.get("validFrom", ""),
                                valid_to=agr.get("validTo"),
                            )
                        )

                electricity_meters.append(
                    MeterPoint(
                        mpan=mp_data.get("mpan", ""),
                        meter_serial=meter_serial,
                        is_smart=bool(meters),
                        agreements=agreements,
                    )
                )

            # Parse gas meter points
            gas_meters = []
            for mp_data in prop_data.get("gasMeterPoints", []):
                meters = mp_data.get("meters", [])
                meter_serial = meters[0]["serialNumber"] if meters else ""

                # Parse agreements
                agreements = []
                for agr in mp_data.get("agreements", []):
                    tariff = agr.get("tariff", {})
                    tariff_code = tariff.get("tariffCode", "")
                    if tariff_code:
                        agreements.append(
                            Agreement(
                                tariff_code=tariff_code,
                                valid_from=agr.get("validFrom", ""),
                                valid_to=agr.get("validTo"),
                            )
                        )

                gas_meters.append(
                    GasMeterPoint(
                        mprn=mp_data.get("mprn", ""),
                        meter_serial=meter_serial,
                        is_smart=bool(meters),
                        agreements=agreements,
                    )
                )

            properties.append(
                Property(
                    address_line_1=prop_data.get("addressLine1", ""),
                    postcode=prop_data.get("postcode", ""),
                    electricity_meter_points=electricity_meters,
                    gas_meter_points=gas_meters,
                )
            )

        return Account(
            account_number=data.get("number", ""),
            balance=float(data.get("balance", 0)),
            properties=properties,
        )

    async def validate_credentials(self) -> bool:
        """Validate API credentials by fetching account data.

        Returns:
            True if credentials are valid.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        await self._token_manager.validate_api_key()
        return True

    # ========================================================================
    # Consumption Methods
    # ========================================================================

    async def get_electricity_consumption(
        self,
        mpan: str | None = None,
        meter_serial: str | None = None,
        periods: int = 48,
    ) -> list[Consumption]:
        """Get electricity consumption data.

        If mpan/meter_serial not provided, uses primary meter from account.

        Args:
            mpan: Meter Point Administration Number.
            meter_serial: Meter serial number.
            periods: Number of half-hour periods to retrieve.

        Returns:
            List of Consumption objects, newest first.

        Raises:
            OctopusError: If request fails or no meter configured.
        """
        if mpan is None or meter_serial is None:
            account = await self.get_account()
            meter = account.primary_electricity
            if meter is None:
                raise OctopusError("No electricity meter found")
            mpan = meter.mpan
            meter_serial = meter.meter_serial

        return await self._rest_client.get_recent_consumption(
            mpan=mpan,
            meter_serial=meter_serial,
            periods=periods,
        )

    async def get_gas_consumption(
        self,
        mprn: str | None = None,
        meter_serial: str | None = None,
        periods: int = 48,
    ) -> list[GasConsumption]:
        """Get gas consumption data.

        If mprn/meter_serial not provided, uses primary meter from account.

        Args:
            mprn: Meter Point Reference Number.
            meter_serial: Meter serial number.
            periods: Number of half-hour periods to retrieve.

        Returns:
            List of GasConsumption objects, newest first.

        Raises:
            OctopusError: If request fails or no meter configured.
        """
        if mprn is None or meter_serial is None:
            account = await self.get_account()
            meter = account.primary_gas
            if meter is None:
                raise OctopusError("No gas meter found")
            mprn = meter.mprn
            meter_serial = meter.meter_serial

        return await self._rest_client.get_recent_gas_consumption(
            mprn=mprn,
            meter_serial=meter_serial,
            periods=periods,
        )

    async def get_daily_usage(
        self,
        days: int = 7,
    ) -> list[DailyUsage]:
        """Get daily aggregated usage for electricity and gas.

        Args:
            days: Number of days to retrieve.

        Returns:
            List of DailyUsage objects.

        Raises:
            OctopusError: If request fails.
        """
        account = await self.get_account()

        # Use defaultdict for O(1) aggregation instead of dict.get()
        electricity_daily: defaultdict[str, float] = defaultdict(float)
        gas_daily: defaultdict[str, float] = defaultdict(float)

        elec_meter = account.primary_electricity
        gas_meter = account.primary_gas

        # Define async helper functions for concurrent fetching
        async def fetch_electricity() -> None:
            """Fetch and aggregate electricity consumption."""
            if elec_meter is None:
                return
            try:
                consumption = await self._rest_client.get_electricity_consumption(
                    mpan=elec_meter.mpan,
                    meter_serial=elec_meter.meter_serial,
                    page_size=days * 48,
                    group_by="day",
                )
                for item in consumption:
                    date_str = item.interval_start.strftime("%Y-%m-%d")
                    electricity_daily[date_str] += item.kwh
            except OctopusError as err:
                _LOGGER.warning("Failed to get electricity consumption: %s", err)

        async def fetch_gas() -> None:
            """Fetch and aggregate gas consumption."""
            if gas_meter is None:
                return
            try:
                consumption = await self._rest_client.get_gas_consumption(
                    mprn=gas_meter.mprn,
                    meter_serial=gas_meter.meter_serial,
                    page_size=days * 48,
                    group_by="day",
                )
                for item in consumption:
                    date_str = item.interval_start.strftime("%Y-%m-%d")
                    gas_daily[date_str] += item.kwh
            except OctopusError as err:
                _LOGGER.warning("Failed to get gas consumption: %s", err)

        # Fetch electricity and gas concurrently
        await asyncio.gather(fetch_electricity(), fetch_gas())

        # Combine into DailyUsage objects
        all_dates = set(electricity_daily.keys()) | set(gas_daily.keys())
        return [
            DailyUsage(
                date=date,
                electricity_kwh=electricity_daily[date],
                gas_kwh=gas_daily[date],
            )
            for date in sorted(all_dates, reverse=True)
        ]

    # ========================================================================
    # Tariff Methods
    # ========================================================================

    async def get_electricity_tariff(
        self,
        tariff_code: str | None = None,
    ) -> Tariff | None:
        """Get electricity tariff details.

        If tariff_code not provided, uses current agreement from account.

        Args:
            tariff_code: Full tariff code.

        Returns:
            Tariff object, or None if not found.

        Raises:
            OctopusError: If request fails.
        """
        if tariff_code is None:
            account = await self.get_account()
            meter = account.primary_electricity
            if meter is None or not meter.agreements:
                return None
            tariff_code = meter.agreements[0].tariff_code

        product_code = self._rest_client.extract_product_code(tariff_code)

        # Get unit rates
        rates = await self._rest_client.get_electricity_standard_unit_rates(
            product_code=product_code,
            tariff_code=tariff_code,
            page_size=48,
        )

        # Get standing charge
        standing_charge = await self._rest_client.get_electricity_standing_charge(
            product_code=product_code,
            tariff_code=tariff_code,
        )

        # Determine tariff type
        tariff_type = TariffType.STANDARD
        if "AGILE" in product_code.upper():
            tariff_type = TariffType.AGILE
        elif "GO" in product_code.upper() or "INTELLI" in product_code.upper():
            tariff_type = TariffType.TIME_OF_USE
        elif "TRACKER" in product_code.upper():
            tariff_type = TariffType.TRACKER

        # Calculate average rate
        unit_rate = None
        if rates:
            unit_rate = sum(r.value_inc_vat for r in rates) / len(rates)

        # Detect off-peak windows for time-of-use tariffs
        off_peak_windows = []
        off_peak_rate = None
        peak_rate = None

        if tariff_type == TariffType.TIME_OF_USE and "INTELLI" in product_code.upper():
            # Intelligent Go: 23:30-05:30 off-peak
            off_peak_windows = [
                TimeWindow(
                    start_time=time(23, 30),
                    end_time=time(5, 30),
                    rate=7.5,  # Default, will be updated from rates
                )
            ]

        return Tariff(
            product_code=product_code,
            display_name=self._format_tariff_name(product_code),
            standing_charge=standing_charge or 0.0,
            tariff_type=tariff_type,
            unit_rate=unit_rate,
            off_peak_rate=off_peak_rate,
            peak_rate=peak_rate,
            off_peak_windows=off_peak_windows,
        )

    async def get_gas_tariff(
        self,
        tariff_code: str | None = None,
    ) -> GasTariff | None:
        """Get gas tariff details.

        If tariff_code not provided, uses current agreement from account.

        Args:
            tariff_code: Full tariff code.

        Returns:
            GasTariff object, or None if not found.

        Raises:
            OctopusError: If request fails.
        """
        if tariff_code is None:
            account = await self.get_account()
            meter = account.primary_gas
            if meter is None or not meter.agreements:
                return None
            tariff_code = meter.agreements[0].tariff_code

        product_code = self._rest_client.extract_product_code(tariff_code)

        # Get unit rates
        rates = await self._rest_client.get_gas_standard_unit_rates(
            product_code=product_code,
            tariff_code=tariff_code,
            page_size=1,
        )

        # Get standing charge
        standing_charge = await self._rest_client.get_gas_standing_charge(
            product_code=product_code,
            tariff_code=tariff_code,
        )

        unit_rate = rates[0].value_inc_vat if rates else 0.0

        return GasTariff(
            product_code=product_code,
            display_name=self._format_tariff_name(product_code),
            standing_charge=standing_charge or 0.0,
            unit_rate=unit_rate,
        )

    async def get_current_rate(
        self,
        tariff: Tariff | None = None,
    ) -> CurrentRate | None:
        """Get the current electricity rate with off-peak context.

        Args:
            tariff: Tariff to check (fetched if not provided).

        Returns:
            CurrentRate object, or None if unavailable.

        Raises:
            OctopusError: If request fails.
        """
        if tariff is None:
            tariff = await self.get_electricity_tariff()
            if tariff is None:
                return None

        now = datetime.now(timezone.utc)
        current_time = now.time()

        # Check if in off-peak window
        is_off_peak = False
        period_end = now.replace(
            minute=30 if now.minute < 30 else 0,
            second=0,
            microsecond=0,
        )
        if now.minute >= 30:
            period_end = period_end.replace(hour=(period_end.hour + 1) % 24)

        for window in tariff.off_peak_windows:
            if window.is_active(current_time):
                is_off_peak = True
                # Calculate when off-peak ends
                # This is simplified; real implementation would be more complex
                break

        # Get current rate
        rate = tariff.off_peak_rate if is_off_peak else tariff.peak_rate
        if rate is None:
            rate = tariff.unit_rate or 0.0

        return CurrentRate(
            rate=rate,
            is_off_peak=is_off_peak,
            period_end=period_end,
            next_rate=tariff.peak_rate if is_off_peak else tariff.off_peak_rate,
        )

    def _format_tariff_name(self, product_code: str) -> str:
        """Format product code into display name.

        Args:
            product_code: Product code.

        Returns:
            Human-readable name.
        """
        # Common mappings
        if "INTELLI" in product_code.upper():
            return "Intelligent Octopus Go"
        if "AGILE" in product_code.upper():
            return "Agile Octopus"
        if "GO" in product_code.upper():
            return "Octopus Go"
        if "TRACKER" in product_code.upper():
            return "Octopus Tracker"
        if "FLEX" in product_code.upper():
            return "Flexible Octopus"

        return product_code.replace("-", " ").title()

    # ========================================================================
    # Dispatch Methods
    # ========================================================================

    async def get_dispatches(self) -> DispatchStatus:
        """Get Intelligent Octopus dispatch schedule.

        Returns:
            DispatchStatus with current, upcoming, and completed dispatches.

        Raises:
            OctopusError: If request fails.
        """
        if self._account_number is None:
            raise OctopusError("Account number not set")

        data = await self._graphql(
            INTELLIGENT_DISPATCH_QUERY,
            build_account_variables(self._account_number),
        )

        now = datetime.now(timezone.utc)

        # Parse planned dispatches
        planned = []
        for d in data.get("plannedDispatches", []) or []:
            dispatch = parse_dispatch(d)
            planned.append(dispatch)

        # Parse completed dispatches
        completed = []
        for d in data.get("completedDispatches", []) or []:
            dispatch = parse_completed_dispatch(d)
            completed.append(dispatch)

        # Find current and next dispatch
        current_dispatch = None
        next_dispatch = None

        for dispatch in sorted(planned, key=lambda d: d.start):
            if dispatch.is_active(now):
                current_dispatch = dispatch
            elif dispatch.is_upcoming(now) and next_dispatch is None:
                next_dispatch = dispatch

        return DispatchStatus(
            is_dispatching=current_dispatch is not None,
            current_dispatch=current_dispatch,
            next_dispatch=next_dispatch,
            planned_dispatches=planned,
            completed_dispatches=completed,
        )

    # ========================================================================
    # Saving Sessions Methods
    # ========================================================================

    async def get_saving_sessions(self) -> list[SavingSession]:
        """Get available Saving Sessions.

        Returns:
            List of SavingSession events.

        Raises:
            OctopusError: If request fails.
        """
        if self._account_number is None:
            raise OctopusError("Account number not set")

        data = await self._graphql(
            SAVING_SESSIONS_QUERY,
            build_account_variables(self._account_number),
        )

        sessions_data = data.get("savingSessions", {})
        events = sessions_data.get("events", []) or []

        sessions = []
        for event in events:
            sessions.append(
                SavingSession(
                    code=event.get("code", ""),
                    start=datetime.fromisoformat(
                        event["startAt"].replace("Z", "+00:00")
                    ),
                    end=datetime.fromisoformat(event["endAt"].replace("Z", "+00:00")),
                    reward_per_kwh=event.get("rewardPerKwh", 0),
                    joined=False,  # Would need to cross-reference with joined query
                )
            )

        return sessions

    # ========================================================================
    # Cleanup
    # ========================================================================

    async def close(self) -> None:
        """Clean up resources.

        Note: Does not close the session as it's externally managed.
        """
        self._token_manager.invalidate_token()
        self._account = None
