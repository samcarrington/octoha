"""Data coordinators for Octoha integration.

Coordinators handle periodic data fetching from the Octopus Energy API
with proper error handling, update intervals, and listener notifications.

Includes graceful degradation support:
- Retains cached data on API failures
- Tracks consecutive failure count and first failure timestamp
- Reports data staleness for UI indication
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, TypeVar

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api.client import OctohaApiClient
from .api.exceptions import AuthenticationError, OctopusError, RateLimitError
from .const import (
    DOMAIN,
    UPDATE_INTERVAL_DISPATCH,
    UPDATE_INTERVAL_ELECTRICITY,
    UPDATE_INTERVAL_GAS,
    UPDATE_INTERVAL_TARIFF,
)
from .models.consumption import Consumption, DailyUsage, GasConsumption
from .models.dispatch import DispatchStatus
from .models.tariff import CurrentRate, GasTariff, Tariff

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

# Data older than this is considered stale (15 minutes by default)
DEFAULT_STALE_THRESHOLD = timedelta(minutes=15)


@dataclass
class ElectricityData:
    """Data from electricity coordinator."""

    consumption: list[Consumption]
    daily_usage: list[DailyUsage]


@dataclass
class GasData:
    """Data from gas coordinator."""

    consumption: list[GasConsumption]
    daily_usage: list[DailyUsage]


@dataclass
class TariffData:
    """Data from tariff coordinator."""

    electricity_tariff: Tariff | None
    gas_tariff: GasTariff | None
    current_rate: CurrentRate | None


class OctohaBaseCoordinator(DataUpdateCoordinator[T]):
    """Base coordinator for Octoha data fetching.

    Extends Home Assistant's DataUpdateCoordinator with Octoha-specific
    error handling, logging, and graceful degradation support.

    Attributes:
        client: The OctohaApiClient instance for API calls.
        consecutive_failures: Number of consecutive failed update attempts.
        first_failure_time: Timestamp of when failures started (None if healthy).
        stale_threshold: How old data can be before considered stale.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: OctohaApiClient,
        name: str,
        update_interval: timedelta,
        stale_threshold: timedelta | None = None,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            client: OctohaApiClient for API calls.
            name: Descriptive name for this coordinator.
            update_interval: How often to fetch data.
            stale_threshold: How old data can be before considered stale.
        """
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )
        self.client = client
        self.consecutive_failures: int = 0
        self.first_failure_time: datetime | None = None
        self.stale_threshold = stale_threshold or DEFAULT_STALE_THRESHOLD
        self._last_successful_update: datetime | None = None

    @property
    def data_age_seconds(self) -> float | None:
        """Return the age of the data in seconds.

        Returns:
            Age of the last successful data in seconds, or None if no data.
        """
        if self._last_successful_update is None:
            return None
        now = datetime.now(UTC)
        return (now - self._last_successful_update).total_seconds()

    @property
    def is_data_stale(self) -> bool:
        """Check if the current data is stale.

        Returns:
            True if data is older than the stale threshold, False otherwise.
        """
        age = self.data_age_seconds
        if age is None:
            return True  # No data is considered stale
        return age > self.stale_threshold.total_seconds()

    def _handle_update_success(self) -> None:
        """Handle a successful update - reset failure tracking."""
        self.consecutive_failures = 0
        self.first_failure_time = None
        self._last_successful_update = datetime.now(UTC)

    def _handle_update_failure(self) -> None:
        """Handle a failed update - update failure tracking."""
        self.consecutive_failures += 1
        if self.first_failure_time is None:
            self.first_failure_time = datetime.now(UTC)

    async def _async_update_data(self) -> T:
        """Fetch data from API.

        Override in subclasses to implement specific data fetching.

        Returns:
            The fetched data.

        Raises:
            UpdateFailed: If the update fails.
        """
        raise NotImplementedError("Subclasses must implement _async_update_data")


class ElectricityCoordinator(OctohaBaseCoordinator[ElectricityData]):
    """Coordinator for electricity consumption data.

    Fetches electricity consumption and daily usage data from the API
    every 5 minutes.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: OctohaApiClient,
        update_interval: timedelta | None = None,
    ) -> None:
        """Initialize the electricity coordinator.

        Args:
            hass: Home Assistant instance.
            client: OctohaApiClient for API calls.
            update_interval: Custom update interval. Uses default if None.
        """
        super().__init__(
            hass=hass,
            client=client,
            name=f"{DOMAIN}_electricity",
            update_interval=update_interval or UPDATE_INTERVAL_ELECTRICITY,
        )

    async def _async_update_data(self) -> ElectricityData:
        """Fetch electricity consumption data.

        Returns:
            ElectricityData with consumption and daily usage.

        Raises:
            UpdateFailed: If the API call fails.
        """
        _LOGGER.debug("Starting electricity data fetch")
        try:
            consumption = await self.client.get_electricity_consumption()
            daily_usage = await self.client.get_daily_usage()

            result = ElectricityData(
                consumption=consumption,
                daily_usage=daily_usage,
            )
            self._handle_update_success()
            _LOGGER.debug(
                "Electricity data fetch complete: %d consumption, %d daily usage",
                len(consumption) if consumption else 0,
                len(daily_usage) if daily_usage else 0,
            )
            return result

        except AuthenticationError as err:
            self._handle_update_failure()
            _LOGGER.error("Authentication error fetching electricity data: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except RateLimitError as err:
            self._handle_update_failure()
            retry_msg = f" (retry after {err.retry_after}s)" if err.retry_after else ""
            _LOGGER.warning("Rate limited fetching electricity data%s", retry_msg)
            raise UpdateFailed(f"Rate limited{retry_msg}") from err
        except OctopusError as err:
            self._handle_update_failure()
            _LOGGER.error("Error fetching electricity data: %s", err)
            raise UpdateFailed(f"Error fetching electricity data: {err}") from err
        except Exception as err:
            self._handle_update_failure()
            _LOGGER.exception("Unexpected error fetching electricity data")
            raise UpdateFailed(f"Unexpected error: {err}") from err


class GasCoordinator(OctohaBaseCoordinator[GasData]):
    """Coordinator for gas consumption data.

    Fetches gas consumption and daily usage data from the API
    every 5 minutes.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: OctohaApiClient,
        update_interval: timedelta | None = None,
    ) -> None:
        """Initialize the gas coordinator.

        Args:
            hass: Home Assistant instance.
            client: OctohaApiClient for API calls.
            update_interval: Custom update interval. Uses default if None.
        """
        super().__init__(
            hass=hass,
            client=client,
            name=f"{DOMAIN}_gas",
            update_interval=update_interval or UPDATE_INTERVAL_GAS,
        )

    async def _async_update_data(self) -> GasData:
        """Fetch gas consumption data.

        Returns:
            GasData with consumption and daily usage.

        Raises:
            UpdateFailed: If the API call fails.
        """
        _LOGGER.debug("Starting gas data fetch")
        try:
            consumption = await self.client.get_gas_consumption()
            daily_usage = await self.client.get_daily_usage()

            result = GasData(
                consumption=consumption,
                daily_usage=daily_usage,
            )
            self._handle_update_success()
            _LOGGER.debug(
                "Gas data fetch complete: %d consumption, %d daily usage",
                len(consumption) if consumption else 0,
                len(daily_usage) if daily_usage else 0,
            )
            return result

        except AuthenticationError as err:
            self._handle_update_failure()
            _LOGGER.error("Authentication error fetching gas data: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except RateLimitError as err:
            self._handle_update_failure()
            retry_msg = f" (retry after {err.retry_after}s)" if err.retry_after else ""
            _LOGGER.warning("Rate limited fetching gas data%s", retry_msg)
            raise UpdateFailed(f"Rate limited{retry_msg}") from err
        except OctopusError as err:
            self._handle_update_failure()
            _LOGGER.error("Error fetching gas data: %s", err)
            raise UpdateFailed(f"Error fetching gas data: {err}") from err
        except Exception as err:
            self._handle_update_failure()
            _LOGGER.exception("Unexpected error fetching gas data")
            raise UpdateFailed(f"Unexpected error: {err}") from err


class TariffCoordinator(OctohaBaseCoordinator[TariffData]):
    """Coordinator for tariff and rate data.

    Fetches electricity tariff, gas tariff, and current rate data
    from the API every 30 minutes.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: OctohaApiClient,
        update_interval: timedelta | None = None,
    ) -> None:
        """Initialize the tariff coordinator.

        Args:
            hass: Home Assistant instance.
            client: OctohaApiClient for API calls.
            update_interval: Custom update interval. Uses default if None.
        """
        super().__init__(
            hass=hass,
            client=client,
            name=f"{DOMAIN}_tariff",
            update_interval=update_interval or UPDATE_INTERVAL_TARIFF,
        )

    async def _async_update_data(self) -> TariffData:
        """Fetch tariff and rate data.

        Returns:
            TariffData with electricity tariff, gas tariff, and current rate.

        Raises:
            UpdateFailed: If the API call fails.
        """
        _LOGGER.debug("Starting tariff data fetch")
        try:
            electricity_tariff = await self.client.get_electricity_tariff()
            gas_tariff = await self.client.get_gas_tariff()
            current_rate = await self.client.get_current_rate(tariff=electricity_tariff)

            result = TariffData(
                electricity_tariff=electricity_tariff,
                gas_tariff=gas_tariff,
                current_rate=current_rate,
            )
            self._handle_update_success()
            _LOGGER.debug(
                "Tariff fetch: elec=%s, gas=%s, rate=%.2f (off_peak=%s)",
                electricity_tariff.display_name if electricity_tariff else None,
                gas_tariff.display_name if gas_tariff else None,
                current_rate.rate if current_rate else 0,
                current_rate.is_off_peak if current_rate else None,
            )
            return result

        except AuthenticationError as err:
            self._handle_update_failure()
            _LOGGER.error("Authentication error fetching tariff data: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except RateLimitError as err:
            self._handle_update_failure()
            retry_msg = f" (retry after {err.retry_after}s)" if err.retry_after else ""
            _LOGGER.warning("Rate limited fetching tariff data%s", retry_msg)
            raise UpdateFailed(f"Rate limited{retry_msg}") from err
        except OctopusError as err:
            self._handle_update_failure()
            _LOGGER.error("Error fetching tariff data: %s", err)
            raise UpdateFailed(f"Error fetching tariff data: {err}") from err
        except Exception as err:
            self._handle_update_failure()
            _LOGGER.exception("Unexpected error fetching tariff data")
            raise UpdateFailed(f"Unexpected error: {err}") from err


class DispatchCoordinator(OctohaBaseCoordinator[DispatchStatus]):
    """Coordinator for Intelligent Octopus dispatch data.

    Fetches dispatch schedules from the API every 5 minutes.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: OctohaApiClient,
        update_interval: timedelta | None = None,
    ) -> None:
        """Initialize the dispatch coordinator.

        Args:
            hass: Home Assistant instance.
            client: OctohaApiClient for API calls.
            update_interval: Custom update interval. Uses default if None.
        """
        super().__init__(
            hass=hass,
            client=client,
            name=f"{DOMAIN}_dispatch",
            update_interval=update_interval or UPDATE_INTERVAL_DISPATCH,
        )

    async def _async_update_data(self) -> DispatchStatus:
        """Fetch dispatch data.

        Returns:
            DispatchStatus with current and planned dispatches.

        Raises:
            UpdateFailed: If the API call fails.
        """
        _LOGGER.debug("Starting dispatch data fetch")
        try:
            result = await self.client.get_dispatches()
            self._handle_update_success()
            _LOGGER.debug(
                "Dispatch fetch: dispatching=%s, planned=%d, completed=%d",
                result.is_dispatching,
                len(result.planned_dispatches) if result.planned_dispatches else 0,
                len(result.completed_dispatches) if result.completed_dispatches else 0,
            )
            return result

        except AuthenticationError as err:
            self._handle_update_failure()
            _LOGGER.error("Authentication error fetching dispatch data: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except RateLimitError as err:
            self._handle_update_failure()
            retry_msg = f" (retry after {err.retry_after}s)" if err.retry_after else ""
            _LOGGER.warning("Rate limited fetching dispatch data%s", retry_msg)
            raise UpdateFailed(f"Rate limited{retry_msg}") from err
        except OctopusError as err:
            self._handle_update_failure()
            _LOGGER.error("Error fetching dispatch data: %s", err)
            raise UpdateFailed(f"Error fetching dispatch data: {err}") from err
        except Exception as err:
            self._handle_update_failure()
            _LOGGER.exception("Unexpected error fetching dispatch data")
            raise UpdateFailed(f"Unexpected error: {err}") from err
