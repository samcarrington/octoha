"""Tariff and rate data models.

Models adapted from the open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum


class TariffType(Enum):
    """Type of electricity tariff."""

    STANDARD = "standard"
    """Fixed rate tariff."""

    TIME_OF_USE = "time_of_use"
    """Time-of-use tariff (Go, Intelligent Go)."""

    AGILE = "agile"
    """Half-hourly variable tariff."""

    TRACKER = "tracker"
    """Daily variable tariff."""


@dataclass
class Rate:
    """Point-in-time rate information."""

    valid_from: datetime
    """When this rate becomes active."""

    valid_to: datetime | None
    """When this rate expires (None if ongoing)."""

    value_inc_vat: float
    """Rate in pence/kWh including VAT."""

    value_exc_vat: float | None = None
    """Rate in pence/kWh excluding VAT."""

    is_off_peak: bool = False
    """Whether this is an off-peak rate."""

    @property
    def value_gbp(self) -> float:
        """Rate in GBP/kWh including VAT."""
        return self.value_inc_vat / 100


@dataclass
class TimeWindow:
    """Off-peak time window definition."""

    start_time: time
    """Start of off-peak window (local time)."""

    end_time: time
    """End of off-peak window (local time)."""

    rate: float
    """Rate in pence/kWh during this window."""

    def is_active(self, current_time: time) -> bool:
        """Check if the window is currently active.

        Handles windows that cross midnight (e.g., 23:30 - 05:30).

        Args:
            current_time: Time to check.

        Returns:
            True if current_time is within the window.
        """
        if self.start_time <= self.end_time:
            # Normal window (e.g., 01:00 - 05:00)
            return self.start_time <= current_time < self.end_time
        # Window crosses midnight (e.g., 23:30 - 05:30)
        return current_time >= self.start_time or current_time < self.end_time


@dataclass
class Tariff:
    """Electricity tariff details."""

    product_code: str
    """Product code (e.g., INTELLI-VAR-22-10-14)."""

    display_name: str
    """Human-readable tariff name."""

    standing_charge: float
    """Standing charge in pence/day including VAT."""

    tariff_type: TariffType = TariffType.STANDARD
    """Type of tariff."""

    # Standard rate (for non-time-of-use tariffs)
    unit_rate: float | None = None
    """Unit rate in pence/kWh (standard tariffs only)."""

    # Time-of-use rates
    off_peak_rate: float | None = None
    """Off-peak rate in pence/kWh."""

    peak_rate: float | None = None
    """Peak rate in pence/kWh."""

    off_peak_windows: list[TimeWindow] = field(default_factory=list)
    """Time windows for off-peak rates."""

    @property
    def is_time_of_use(self) -> bool:
        """Check if this is a time-of-use tariff."""
        return self.tariff_type in (TariffType.TIME_OF_USE, TariffType.AGILE)

    @property
    def is_intelligent(self) -> bool:
        """Check if this is an Intelligent tariff."""
        return "INTELLI" in self.product_code.upper()


@dataclass
class GasTariff:
    """Gas tariff details."""

    product_code: str
    """Product code."""

    display_name: str
    """Human-readable tariff name."""

    standing_charge: float
    """Standing charge in pence/day including VAT."""

    unit_rate: float
    """Unit rate in pence/kWh including VAT."""


@dataclass
class CurrentRate:
    """Current rate with time-of-use context."""

    rate: float
    """Current rate in pence/kWh."""

    is_off_peak: bool
    """Whether currently in off-peak period."""

    period_end: datetime
    """When the current rate period ends."""

    next_rate: float | None = None
    """Rate after period_end (if known)."""

    @property
    def rate_gbp(self) -> float:
        """Current rate in GBP/kWh."""
        return self.rate / 100

    def time_remaining_seconds(self, now: datetime | None = None) -> int:
        """Seconds remaining in current rate period.

        Args:
            now: Current time (defaults to now).

        Returns:
            Seconds remaining.
        """
        if now is None:
            now = datetime.now(self.period_end.tzinfo)
        delta = self.period_end - now
        return max(0, int(delta.total_seconds()))


def parse_rate(data: dict) -> Rate:
    """Parse rate data from API response.

    Args:
        data: Dictionary with valid_from, valid_to, value_inc_vat keys.

    Returns:
        Rate object.
    """
    valid_to = None
    if data.get("valid_to"):
        valid_to = datetime.fromisoformat(data["valid_to"].replace("Z", "+00:00"))

    return Rate(
        valid_from=datetime.fromisoformat(data["valid_from"].replace("Z", "+00:00")),
        valid_to=valid_to,
        value_inc_vat=float(data["value_inc_vat"]),
        value_exc_vat=data.get("value_exc_vat"),
    )
