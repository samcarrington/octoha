"""Dispatch and Intelligent Go data models.

Models adapted from the open-octopus project
(https://github.com/abracadabra50/open-octopus) under MIT license.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DispatchSource(Enum):
    """Source of a dispatch slot."""

    SMART_CHARGE = "smart-charge"
    """Scheduled by Octopus Intelligent system."""

    BUMP_CHARGE = "bump-charge"
    """User-requested boost charge."""


class DispatchType(Enum):
    """Type of a dispatch slot (new API format)."""

    SMART_CHARGE = "SMART_CHARGE"
    """Scheduled by Octopus Intelligent system."""

    BUMP_CHARGE = "BUMP_CHARGE"
    """User-requested boost charge."""


@dataclass
class Dispatch:
    """Intelligent Octopus dispatch slot."""

    start: datetime
    """Start of the dispatch window."""

    end: datetime
    """End of the dispatch window."""

    source: DispatchSource = DispatchSource.SMART_CHARGE
    """Source of the dispatch."""

    charge_kwh: float | None = None
    """Energy transferred in kWh (completed dispatches only)."""

    energy_added_kwh: float | None = None
    """Energy to be added in kWh (planned dispatches, new API format)."""

    location: str | None = None
    """Location of the dispatch (e.g., 'AT_HOME')."""

    @property
    def duration_minutes(self) -> int:
        """Duration of the dispatch in minutes."""
        return int((self.end - self.start).total_seconds() / 60)

    @property
    def duration_hours(self) -> float:
        """Duration of the dispatch in hours."""
        return self.duration_minutes / 60

    def is_active(self, now: datetime | None = None) -> bool:
        """Check if the dispatch is currently active.

        Args:
            now: Current time (defaults to now with same timezone).

        Returns:
            True if currently within the dispatch window.
        """
        if now is None:
            now = datetime.now(self.start.tzinfo)
        return self.start <= now <= self.end

    def is_upcoming(self, now: datetime | None = None) -> bool:
        """Check if the dispatch is in the future.

        Args:
            now: Current time (defaults to now with same timezone).

        Returns:
            True if dispatch hasn't started yet.
        """
        if now is None:
            now = datetime.now(self.start.tzinfo)
        return now < self.start

    def time_until_start_seconds(self, now: datetime | None = None) -> int:
        """Seconds until dispatch starts.

        Args:
            now: Current time.

        Returns:
            Seconds until start (0 if already started or past).
        """
        if now is None:
            now = datetime.now(self.start.tzinfo)
        delta = self.start - now
        return max(0, int(delta.total_seconds()))


@dataclass
class DispatchStatus:
    """Aggregated dispatch state for sensors."""

    is_dispatching: bool = False
    """Whether a dispatch is currently active."""

    current_dispatch: Dispatch | None = None
    """The currently active dispatch (if any)."""

    next_dispatch: Dispatch | None = None
    """The next upcoming dispatch (if any)."""

    planned_dispatches: list[Dispatch] = field(default_factory=list)
    """All planned future dispatches."""

    completed_dispatches: list[Dispatch] = field(default_factory=list)
    """Recently completed dispatches."""

    @property
    def has_upcoming(self) -> bool:
        """Check if there are any upcoming dispatches."""
        return self.next_dispatch is not None or len(self.planned_dispatches) > 0


@dataclass
class SavingSession:
    """Saving Session / Free Electricity event."""

    code: str
    """Unique event code."""

    start: datetime
    """Event start time."""

    end: datetime
    """Event end time."""

    reward_per_kwh: int = 0
    """Octopoints reward per kWh saved."""

    joined: bool = False
    """Whether the user has opted into this session."""

    def is_active(self, now: datetime | None = None) -> bool:
        """Check if the session is currently active.

        Args:
            now: Current time.

        Returns:
            True if currently within the session window.
        """
        if now is None:
            now = datetime.now(self.start.tzinfo)
        return self.start <= now <= self.end

    @property
    def duration_minutes(self) -> int:
        """Duration of the session in minutes."""
        return int((self.end - self.start).total_seconds() / 60)


def parse_dispatch(data: dict) -> Dispatch:
    """Parse dispatch data from GraphQL response.

    Handles both old format (plannedDispatches with 'source') and
    new format (flexPlannedDispatches with 'type').

    Args:
        data: Dictionary with start, end, and source/type keys.

    Returns:
        Dispatch object.
    """
    # Handle new API format with 'type' field
    if "type" in data:
        type_str = data.get("type", "SMART_CHARGE")
        try:
            dispatch_type = DispatchType(type_str)
            # Map DispatchType to DispatchSource
            if dispatch_type == DispatchType.BUMP_CHARGE:
                source = DispatchSource.BUMP_CHARGE
            else:
                source = DispatchSource.SMART_CHARGE
        except ValueError:
            source = DispatchSource.SMART_CHARGE
    else:
        # Handle old API format with 'source' field
        source_str = data.get("source", "smart-charge")
        try:
            source = DispatchSource(source_str)
        except ValueError:
            source = DispatchSource.SMART_CHARGE

    return Dispatch(
        start=datetime.fromisoformat(data["start"].replace("Z", "+00:00")),
        end=datetime.fromisoformat(data["end"].replace("Z", "+00:00")),
        source=source,
        charge_kwh=data.get("delta_kwh") or data.get("charge_kwh"),
        energy_added_kwh=data.get("energyAddedKwh"),
    )


def parse_completed_dispatch(data: dict) -> Dispatch:
    """Parse completed dispatch data from GraphQL response.

    Args:
        data: Dictionary with start, end, delta keys and optional meta.

    Returns:
        Dispatch object with charge data.
    """
    # Extract source from meta if available (new API format)
    meta = data.get("meta", {})
    source = DispatchSource.SMART_CHARGE
    location = None

    if meta:
        source_str = meta.get("source", "smart-charge")
        try:
            source = DispatchSource(source_str)
        except ValueError:
            source = DispatchSource.SMART_CHARGE
        location = meta.get("location")

    return Dispatch(
        start=datetime.fromisoformat(data["start"].replace("Z", "+00:00")),
        end=datetime.fromisoformat(data["end"].replace("Z", "+00:00")),
        source=source,
        charge_kwh=data.get("delta"),
        location=location,
    )
