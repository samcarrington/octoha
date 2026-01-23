"""Octoha data models package.

This package contains dataclasses for representing data from the
Octopus Energy API. Models are adapted from the open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

from .account import Account, Agreement, GasMeterPoint, MeterPoint, Property
from .consumption import (
    Consumption,
    DailyUsage,
    GasConsumption,
    parse_consumption,
    parse_gas_consumption,
)
from .dispatch import (
    Dispatch,
    DispatchSource,
    DispatchStatus,
    SavingSession,
    parse_completed_dispatch,
    parse_dispatch,
)
from .tariff import (
    CurrentRate,
    GasTariff,
    Rate,
    Tariff,
    TariffType,
    TimeWindow,
    parse_rate,
)

__all__ = [
    # Account models
    "Account",
    "Agreement",
    "GasMeterPoint",
    "MeterPoint",
    "Property",
    # Consumption models
    "Consumption",
    "DailyUsage",
    "GasConsumption",
    "parse_consumption",
    "parse_gas_consumption",
    # Dispatch models
    "Dispatch",
    "DispatchSource",
    "DispatchStatus",
    "SavingSession",
    "parse_completed_dispatch",
    "parse_dispatch",
    # Tariff models
    "CurrentRate",
    "GasTariff",
    "Rate",
    "Tariff",
    "TariffType",
    "TimeWindow",
    "parse_rate",
]
