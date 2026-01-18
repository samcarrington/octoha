"""Data coordinators for Octoha integration.

Coordinators handle periodic data fetching from the Octopus Energy API
with proper error handling, update intervals, and listener notifications.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypeVar

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api.client import OctohaApiClient
from .api.exceptions import AuthenticationError, OctopusError
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
    error handling and logging.

    Attributes:
        client: The OctohaApiClient instance for API calls.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: OctohaApiClient,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            client: OctohaApiClient for API calls.
            name: Descriptive name for this coordinator.
            update_interval: How often to fetch data.
        """
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )
        self.client = client

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
    ) -> None:
        """Initialize the electricity coordinator.

        Args:
            hass: Home Assistant instance.
            client: OctohaApiClient for API calls.
        """
        super().__init__(
            hass=hass,
            client=client,
            name=f"{DOMAIN}_electricity",
            update_interval=UPDATE_INTERVAL_ELECTRICITY,
        )

    async def _async_update_data(self) -> ElectricityData:
        """Fetch electricity consumption data.

        Returns:
            ElectricityData with consumption and daily usage.

        Raises:
            UpdateFailed: If the API call fails.
        """
        try:
            consumption = await self.client.get_electricity_consumption()
            daily_usage = await self.client.get_daily_usage()

            return ElectricityData(
                consumption=consumption,
                daily_usage=daily_usage,
            )

        except AuthenticationError as err:
            _LOGGER.error("Authentication error fetching electricity data: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except OctopusError as err:
            _LOGGER.error("Error fetching electricity data: %s", err)
            raise UpdateFailed(f"Error fetching electricity data: {err}") from err
        except Exception as err:
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
    ) -> None:
        """Initialize the gas coordinator.

        Args:
            hass: Home Assistant instance.
            client: OctohaApiClient for API calls.
        """
        super().__init__(
            hass=hass,
            client=client,
            name=f"{DOMAIN}_gas",
            update_interval=UPDATE_INTERVAL_GAS,
        )

    async def _async_update_data(self) -> GasData:
        """Fetch gas consumption data.

        Returns:
            GasData with consumption and daily usage.

        Raises:
            UpdateFailed: If the API call fails.
        """
        try:
            consumption = await self.client.get_gas_consumption()
            daily_usage = await self.client.get_daily_usage()

            return GasData(
                consumption=consumption,
                daily_usage=daily_usage,
            )

        except AuthenticationError as err:
            _LOGGER.error("Authentication error fetching gas data: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except OctopusError as err:
            _LOGGER.error("Error fetching gas data: %s", err)
            raise UpdateFailed(f"Error fetching gas data: {err}") from err
        except Exception as err:
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
    ) -> None:
        """Initialize the tariff coordinator.

        Args:
            hass: Home Assistant instance.
            client: OctohaApiClient for API calls.
        """
        super().__init__(
            hass=hass,
            client=client,
            name=f"{DOMAIN}_tariff",
            update_interval=UPDATE_INTERVAL_TARIFF,
        )

    async def _async_update_data(self) -> TariffData:
        """Fetch tariff and rate data.

        Returns:
            TariffData with electricity tariff, gas tariff, and current rate.

        Raises:
            UpdateFailed: If the API call fails.
        """
        try:
            electricity_tariff = await self.client.get_electricity_tariff()
            gas_tariff = await self.client.get_gas_tariff()
            current_rate = await self.client.get_current_rate(tariff=electricity_tariff)

            return TariffData(
                electricity_tariff=electricity_tariff,
                gas_tariff=gas_tariff,
                current_rate=current_rate,
            )

        except AuthenticationError as err:
            _LOGGER.error("Authentication error fetching tariff data: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except OctopusError as err:
            _LOGGER.error("Error fetching tariff data: %s", err)
            raise UpdateFailed(f"Error fetching tariff data: {err}") from err
        except Exception as err:
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
    ) -> None:
        """Initialize the dispatch coordinator.

        Args:
            hass: Home Assistant instance.
            client: OctohaApiClient for API calls.
        """
        super().__init__(
            hass=hass,
            client=client,
            name=f"{DOMAIN}_dispatch",
            update_interval=UPDATE_INTERVAL_DISPATCH,
        )

    async def _async_update_data(self) -> DispatchStatus:
        """Fetch dispatch data.

        Returns:
            DispatchStatus with current and planned dispatches.

        Raises:
            UpdateFailed: If the API call fails.
        """
        try:
            return await self.client.get_dispatches()

        except AuthenticationError as err:
            _LOGGER.error("Authentication error fetching dispatch data: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except OctopusError as err:
            _LOGGER.error("Error fetching dispatch data: %s", err)
            raise UpdateFailed(f"Error fetching dispatch data: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching dispatch data")
            raise UpdateFailed(f"Unexpected error: {err}") from err
