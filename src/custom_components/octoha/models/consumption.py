"""Consumption data models.

Models adapted from the open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Consumption:
    """Half-hourly electricity consumption reading."""

    interval_start: datetime
    """Start of the 30-minute period (UTC)."""

    interval_end: datetime
    """End of the 30-minute period (UTC)."""

    consumption: float
    """Energy consumed in kWh."""

    @property
    def kwh(self) -> float:
        """Alias for consumption in kWh."""
        return self.consumption


@dataclass
class GasConsumption:
    """Half-hourly gas consumption reading."""

    interval_start: datetime
    """Start of the 30-minute period (UTC)."""

    interval_end: datetime
    """End of the 30-minute period (UTC)."""

    consumption: float
    """Energy consumed in kWh."""

    consumption_m3: float | None = None
    """Volume consumed in cubic metres (SMETS2 raw value)."""

    @property
    def kwh(self) -> float:
        """Energy in kWh."""
        return self.consumption

    @property
    def m3(self) -> float | None:
        """Volume in cubic metres."""
        return self.consumption_m3


@dataclass
class DailyUsage:
    """Aggregated daily usage for dashboard display."""

    date: str
    """Date in YYYY-MM-DD format."""

    electricity_kwh: float = 0.0
    """Total electricity consumption in kWh."""

    gas_kwh: float = 0.0
    """Total gas consumption in kWh."""

    electricity_cost: float | None = None
    """Electricity cost in GBP (if calculable)."""

    gas_cost: float | None = None
    """Gas cost in GBP (if calculable)."""

    @property
    def total_kwh(self) -> float:
        """Total energy consumption in kWh."""
        return self.electricity_kwh + self.gas_kwh

    @property
    def total_cost(self) -> float | None:
        """Total cost in GBP (if calculable)."""
        if self.electricity_cost is None and self.gas_cost is None:
            return None
        return (self.electricity_cost or 0.0) + (self.gas_cost or 0.0)


def parse_consumption(data: dict) -> Consumption:
    """Parse consumption data from API response.

    Args:
        data: Dictionary with interval_start, interval_end, consumption keys.

    Returns:
        Consumption object.
    """
    return Consumption(
        interval_start=datetime.fromisoformat(
            data["interval_start"].replace("Z", "+00:00")
        ),
        interval_end=datetime.fromisoformat(
            data["interval_end"].replace("Z", "+00:00")
        ),
        consumption=float(data["consumption"]),
    )


def parse_gas_consumption(data: dict) -> GasConsumption:
    """Parse gas consumption data from API response.

    Args:
        data: Dictionary with interval_start, interval_end, consumption keys.

    Returns:
        GasConsumption object.
    """
    return GasConsumption(
        interval_start=datetime.fromisoformat(
            data["interval_start"].replace("Z", "+00:00")
        ),
        interval_end=datetime.fromisoformat(
            data["interval_end"].replace("Z", "+00:00")
        ),
        consumption=float(data["consumption"]),
        # m3 not always available in API response
        consumption_m3=data.get("consumption_m3"),
    )
