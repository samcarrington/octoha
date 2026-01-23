"""REST API client for Octopus Energy consumption and tariff data.

REST endpoints adapted from the open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from ..const import REST_API_URL
from ..models.consumption import (
    Consumption,
    GasConsumption,
    parse_consumption,
    parse_gas_consumption,
)
from ..models.tariff import Rate, parse_rate
from .exceptions import (
    AuthenticationError,
    OctopusError,
    RateLimitError,
    sanitize_log_message,
    validate_meter_serial,
    validate_mpan,
    validate_mprn,
)

if TYPE_CHECKING:
    import aiohttp

_LOGGER = logging.getLogger(__name__)


class MeterType(Enum):
    """Meter type identifiers for endpoint construction."""

    ELECTRICITY = "electricity-meter-points"
    GAS = "gas-meter-points"


class EndpointSuffix(Enum):
    """Common endpoint suffixes for meter endpoints."""

    CONSUMPTION = "consumption/"
    STANDARD_UNIT_RATES = "standard-unit-rates/"
    STANDING_CHARGES = "standing-charges/"


# Module-level templates for endpoint construction
METER_ENDPOINT_TEMPLATES = {
    MeterType.ELECTRICITY: (
        "/electricity-meter-points/{meter_id}/meters/{meter_serial}/"
    ),
    MeterType.GAS: ("/gas-meter-points/{meter_id}/meters/{meter_serial}/"),
}


class RestClient:
    """REST API client for consumption and tariff data.

    The REST API uses HTTP Basic Auth with the API key as username
    and an empty password.

    Attributes:
        api_key: The Octopus Energy API key.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
    ) -> None:
        """Initialize the REST client.

        Args:
            session: aiohttp client session for HTTP requests.
            api_key: Octopus Energy API key.
        """
        self._session = session
        self._api_key = api_key
        self._base_url = REST_API_URL

    def _build_meter_endpoint(
        self,
        meter_type: MeterType,
        meter_id: str,
        meter_serial: str,
        endpoint_suffix: EndpointSuffix | str = "",
    ) -> str:
        """Build meter endpoint with comprehensive validation.

        Args:
            meter_type: MeterType enum value.
            meter_id: MPAN or MPRN (already validated by validate_mpan/validate_mprn).
            meter_serial: Meter serial (already validated by validate_meter_serial).
            endpoint_suffix: Endpoint suffix or EndpointSuffix enum.

        Returns:
            Formatted endpoint path.

        Raises:
            ValueError: If meter_id or meter_serial are empty.
            KeyError: If meter_type not in template map.
        """
        # Validate non-empty required fields
        if not meter_id or not meter_id.strip():
            raise ValueError("meter_id cannot be empty")
        if not meter_serial or not meter_serial.strip():
            raise ValueError("meter_serial cannot be empty")

        # Ensure meter_type is valid
        if not isinstance(meter_type, MeterType):
            raise ValueError(f"Invalid meter_type: {meter_type}")

        # Build endpoint
        template = METER_ENDPOINT_TEMPLATES[meter_type]
        base_endpoint = template.format(meter_id=meter_id, meter_serial=meter_serial)

        # Normalize suffix (strip leading slashes to prevent duplicates)
        suffix_str = (
            endpoint_suffix.value
            if isinstance(endpoint_suffix, EndpointSuffix)
            else str(endpoint_suffix)
        )
        suffix_str = suffix_str.lstrip("/")

        return f"{base_endpoint}{suffix_str}" if suffix_str else base_endpoint

    def _get_auth(self) -> aiohttp.BasicAuth:
        """Get HTTP Basic Auth credentials.

        Returns:
            BasicAuth with API key as username.
        """
        import aiohttp

        return aiohttp.BasicAuth(self._api_key, "")

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict:
        """Make an authenticated REST API request.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            params: Optional query parameters.

        Returns:
            JSON response data.

        Raises:
            AuthenticationError: If authentication fails.
            RateLimitError: If rate limited.
            OctopusError: For other API errors.
        """
        url = f"{self._base_url}{endpoint}"

        try:
            async with self._session.request(
                method,
                url,
                auth=self._get_auth(),
                params=params,
            ) as response:
                if response.status == 401:
                    raise AuthenticationError(
                        "Invalid API key for REST API",
                        status_code=401,
                    )

                if response.status == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "REST API rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                        status_code=429,
                    )

                if response.status == 404:
                    raise OctopusError(
                        f"Resource not found: {endpoint}",
                        status_code=404,
                    )

                if response.status >= 400:
                    text = await response.text()
                    # Log full details, sanitize user-facing message
                    _LOGGER.error(
                        "REST API error: HTTP %s: %s",
                        response.status,
                        sanitize_log_message(text),
                    )
                    raise OctopusError(
                        f"API request failed (HTTP {response.status})",
                        status_code=response.status,
                    )

                return dict(await response.json())

        except (AuthenticationError, RateLimitError, OctopusError):
            raise
        except Exception as err:
            _LOGGER.exception("REST API request failed: %s", endpoint)
            raise OctopusError("Request failed") from err

    # ========================================================================
    # Consumption Endpoints
    # ========================================================================

    async def get_electricity_consumption(
        self,
        mpan: str,
        meter_serial: str,
        period_from: datetime | None = None,
        period_to: datetime | None = None,
        page_size: int = 48,
        order_by: str = "period",
        group_by: str | None = None,
    ) -> list[Consumption]:
        """Get electricity consumption data.

        Args:
            mpan: Meter Point Administration Number.
            meter_serial: Meter serial number.
            period_from: Start of period (inclusive).
            period_to: End of period (exclusive).
            page_size: Number of results per page (max 25000).
            order_by: Sort order (period for oldest first, -period for newest).
            group_by: Optional grouping (hour, day, week, month, quarter).

        Returns:
            List of Consumption objects.

        Raises:
            ValidationError: If MPAN or meter serial format is invalid.
            OctopusError: If request fails.
        """
        # Validate inputs before constructing URL
        validated_mpan = validate_mpan(mpan)
        validated_serial = validate_meter_serial(meter_serial)

        endpoint = self._build_meter_endpoint(
            meter_type=MeterType.ELECTRICITY,
            meter_id=validated_mpan,
            meter_serial=validated_serial,
            endpoint_suffix=EndpointSuffix.CONSUMPTION,
        )

        params: dict[str, Any] = {
            "page_size": page_size,
            "order_by": order_by,
        }

        if period_from:
            params["period_from"] = period_from.isoformat()
        if period_to:
            params["period_to"] = period_to.isoformat()
        if group_by:
            params["group_by"] = group_by

        data = await self._request("GET", endpoint, params)

        results = data.get("results", [])
        return [parse_consumption(item) for item in results]

    async def get_gas_consumption(
        self,
        mprn: str,
        meter_serial: str,
        period_from: datetime | None = None,
        period_to: datetime | None = None,
        page_size: int = 48,
        order_by: str = "period",
        group_by: str | None = None,
    ) -> list[GasConsumption]:
        """Get gas consumption data.

        Gas consumption is returned in kWh (already converted from m³).

        Args:
            mprn: Meter Point Reference Number.
            meter_serial: Meter serial number.
            period_from: Start of period (inclusive).
            period_to: End of period (exclusive).
            page_size: Number of results per page (max 25000).
            order_by: Sort order (period for oldest first, -period for newest).
            group_by: Optional grouping (hour, day, week, month, quarter).

        Returns:
            List of GasConsumption objects.

        Raises:
            ValidationError: If MPRN or meter serial format is invalid.
            OctopusError: If request fails.
        """
        # Validate inputs before constructing URL
        validated_mprn = validate_mprn(mprn)
        validated_serial = validate_meter_serial(meter_serial)

        endpoint = self._build_meter_endpoint(
            meter_type=MeterType.GAS,
            meter_id=validated_mprn,
            meter_serial=validated_serial,
            endpoint_suffix=EndpointSuffix.CONSUMPTION,
        )

        params: dict[str, Any] = {
            "page_size": page_size,
            "order_by": order_by,
        }

        if period_from:
            params["period_from"] = period_from.isoformat()
        if period_to:
            params["period_to"] = period_to.isoformat()
        if group_by:
            params["group_by"] = group_by

        data = await self._request("GET", endpoint, params)

        results = data.get("results", [])
        return [parse_gas_consumption(item) for item in results]

    # ========================================================================
    # Tariff Endpoints
    # ========================================================================

    async def get_electricity_standard_unit_rates(
        self,
        product_code: str,
        tariff_code: str,
        period_from: datetime | None = None,
        period_to: datetime | None = None,
        page_size: int = 100,
    ) -> list[Rate]:
        """Get standard electricity unit rates.

        Args:
            product_code: Product code (e.g., AGILE-FLEX-22-11-25).
            tariff_code: Full tariff code (e.g., E-1R-AGILE-FLEX-22-11-25-J).
            period_from: Start of period (inclusive).
            period_to: End of period (exclusive).
            page_size: Number of results per page.

        Returns:
            List of Rate objects.

        Raises:
            OctopusError: If request fails.
        """
        endpoint = (
            f"/products/{product_code}/electricity-tariffs/"
            f"{tariff_code}/standard-unit-rates/"
        )

        params: dict[str, Any] = {"page_size": page_size}

        if period_from:
            params["period_from"] = period_from.isoformat()
        if period_to:
            params["period_to"] = period_to.isoformat()

        data = await self._request("GET", endpoint, params)

        results = data.get("results", [])
        return [parse_rate(item) for item in results]

    async def get_electricity_standing_charge(
        self,
        product_code: str,
        tariff_code: str,
        period_from: datetime | None = None,
        period_to: datetime | None = None,
    ) -> float | None:
        """Get electricity standing charge.

        Args:
            product_code: Product code.
            tariff_code: Full tariff code.
            period_from: Start of period (inclusive).
            period_to: End of period (exclusive).

        Returns:
            Standing charge in pence/day, or None if not found.

        Raises:
            OctopusError: If request fails.
        """
        endpoint = (
            f"/products/{product_code}/electricity-tariffs/"
            f"{tariff_code}/standing-charges/"
        )

        params: dict[str, Any] = {"page_size": 1}

        if period_from:
            params["period_from"] = period_from.isoformat()
        if period_to:
            params["period_to"] = period_to.isoformat()

        data = await self._request("GET", endpoint, params)

        results = data.get("results", [])
        if results:
            return float(results[0].get("value_inc_vat", 0))
        return None

    async def get_gas_standard_unit_rates(
        self,
        product_code: str,
        tariff_code: str,
        period_from: datetime | None = None,
        period_to: datetime | None = None,
        page_size: int = 100,
    ) -> list[Rate]:
        """Get gas unit rates.

        Args:
            product_code: Product code.
            tariff_code: Full tariff code (e.g., G-1R-FLEX-22-11-25-J).
            period_from: Start of period (inclusive).
            period_to: End of period (exclusive).
            page_size: Number of results per page.

        Returns:
            List of Rate objects.

        Raises:
            OctopusError: If request fails.
        """
        endpoint = (
            f"/products/{product_code}/gas-tariffs/{tariff_code}/standard-unit-rates/"
        )

        params: dict[str, Any] = {"page_size": page_size}

        if period_from:
            params["period_from"] = period_from.isoformat()
        if period_to:
            params["period_to"] = period_to.isoformat()

        data = await self._request("GET", endpoint, params)

        results = data.get("results", [])
        return [parse_rate(item) for item in results]

    async def get_gas_standing_charge(
        self,
        product_code: str,
        tariff_code: str,
        period_from: datetime | None = None,
        period_to: datetime | None = None,
    ) -> float | None:
        """Get gas standing charge.

        Args:
            product_code: Product code.
            tariff_code: Full tariff code.
            period_from: Start of period (inclusive).
            period_to: End of period (exclusive).

        Returns:
            Standing charge in pence/day, or None if not found.

        Raises:
            OctopusError: If request fails.
        """
        endpoint = (
            f"/products/{product_code}/gas-tariffs/{tariff_code}/standing-charges/"
        )

        params: dict[str, Any] = {"page_size": 1}

        if period_from:
            params["period_from"] = period_from.isoformat()
        if period_to:
            params["period_to"] = period_to.isoformat()

        data = await self._request("GET", endpoint, params)

        results = data.get("results", [])
        if results:
            return float(results[0].get("value_inc_vat", 0))
        return None

    # ========================================================================
    # Product Endpoints
    # ========================================================================

    async def get_products(self) -> list[dict]:
        """Get list of available products.

        Returns:
            List of product dictionaries.

        Raises:
            OctopusError: If request fails.
        """
        endpoint = "/products/"
        data = await self._request("GET", endpoint)
        return list(data.get("results", []))

    async def get_product(self, product_code: str) -> dict | None:
        """Get details for a specific product.

        Args:
            product_code: Product code.

        Returns:
            Product details dictionary, or None if not found.

        Raises:
            OctopusError: If request fails.
        """
        endpoint = f"/products/{product_code}/"
        try:
            return await self._request("GET", endpoint)
        except OctopusError as err:
            if err.status_code == 404:
                return None
            raise

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def extract_product_code(self, tariff_code: str) -> str:
        """Extract product code from tariff code.

        Tariff codes follow the pattern:
        E-1R-{PRODUCT_CODE}-{REGION} for electricity
        G-1R-{PRODUCT_CODE}-{REGION} for gas

        Args:
            tariff_code: Full tariff code.

        Returns:
            Product code portion.

        Example:
            >>> extract_product_code("E-1R-INTELLI-VAR-22-10-14-J")
            "INTELLI-VAR-22-10-14"
        """
        parts = tariff_code.split("-")
        if len(parts) >= 4:
            # Skip E-1R- or G-1R- prefix and region suffix
            return "-".join(parts[2:-1])
        return tariff_code

    async def get_recent_consumption(
        self,
        mpan: str,
        meter_serial: str,
        periods: int = 48,
    ) -> list[Consumption]:
        """Get recent electricity consumption (last N half-hour periods).

        Args:
            mpan: Meter Point Administration Number.
            meter_serial: Meter serial number.
            periods: Number of 30-minute periods to retrieve (default 48 = 24h).

        Returns:
            List of Consumption objects, newest first.

        Raises:
            OctopusError: If request fails.
        """
        return await self.get_electricity_consumption(
            mpan=mpan,
            meter_serial=meter_serial,
            page_size=periods,
            order_by="-period",  # Newest first
        )

    async def get_recent_gas_consumption(
        self,
        mprn: str,
        meter_serial: str,
        periods: int = 48,
    ) -> list[GasConsumption]:
        """Get recent gas consumption (last N half-hour periods).

        Args:
            mprn: Meter Point Reference Number.
            meter_serial: Meter serial number.
            periods: Number of 30-minute periods to retrieve (default 48 = 24h).

        Returns:
            List of GasConsumption objects, newest first.

        Raises:
            OctopusError: If request fails.
        """
        return await self.get_gas_consumption(
            mprn=mprn,
            meter_serial=meter_serial,
            page_size=periods,
            order_by="-period",  # Newest first
        )
