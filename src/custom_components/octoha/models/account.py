"""Account and meter point data models.

Models adapted from the open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MeterPoint:
    """Electricity meter point (MPAN)."""

    mpan: str
    """13-digit Meter Point Administration Number."""

    meter_serial: str
    """Physical meter serial number."""

    is_smart: bool = True
    """Whether this is a SMETS1/SMETS2 smart meter."""

    is_export: bool = False
    """Whether this is an export meter."""

    agreements: list[Agreement] = field(default_factory=list)
    """Tariff agreements for this meter."""


@dataclass
class GasMeterPoint:
    """Gas meter point (MPRN)."""

    mprn: str
    """Meter Point Reference Number."""

    meter_serial: str
    """Physical meter serial number."""

    is_smart: bool = True
    """Whether this is a smart meter."""

    agreements: list[Agreement] = field(default_factory=list)
    """Tariff agreements for this meter."""


@dataclass
class Agreement:
    """Tariff agreement for a meter point."""

    tariff_code: str
    """Full tariff code (e.g., E-1R-INTELLI-VAR-22-10-14-J)."""

    valid_from: str
    """ISO 8601 datetime when agreement starts."""

    valid_to: str | None = None
    """ISO 8601 datetime when agreement ends, or None if ongoing."""

    @property
    def product_code(self) -> str:
        """Extract product code from tariff code.

        Example: E-1R-INTELLI-VAR-22-10-14-J -> INTELLI-VAR-22-10-14
        """
        parts = self.tariff_code.split("-")
        if len(parts) >= 3:
            # Remove prefix (E-1R- or G-1R-) and suffix (region code)
            return "-".join(parts[2:-1])
        return self.tariff_code


@dataclass
class Property:
    """Property associated with an Octopus account."""

    address_line_1: str
    postcode: str
    electricity_meter_points: list[MeterPoint] = field(default_factory=list)
    gas_meter_points: list[GasMeterPoint] = field(default_factory=list)

    @property
    def address(self) -> str:
        """Format full address."""
        return f"{self.address_line_1}, {self.postcode}"


@dataclass
class Account:
    """Octopus Energy account information."""

    account_number: str
    """Account number (e.g., A-FB05ED6C)."""

    balance: float = 0.0
    """Account balance in GBP (negative = credit)."""

    properties: list[Property] = field(default_factory=list)
    """Properties associated with this account."""

    @property
    def electricity_meter_points(self) -> list[MeterPoint]:
        """Get all electricity meter points across all properties."""
        return [
            mp
            for prop in self.properties
            for mp in prop.electricity_meter_points
            if not mp.is_export
        ]

    @property
    def gas_meter_points(self) -> list[GasMeterPoint]:
        """Get all gas meter points across all properties."""
        return [mp for prop in self.properties for mp in prop.gas_meter_points]

    @property
    def primary_electricity(self) -> MeterPoint | None:
        """Get the primary (first) electricity meter point."""
        meters = self.electricity_meter_points
        return meters[0] if meters else None

    @property
    def primary_gas(self) -> GasMeterPoint | None:
        """Get the primary (first) gas meter point."""
        meters = self.gas_meter_points
        return meters[0] if meters else None
