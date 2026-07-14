"""Shared controller domain models."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HealthResult:
    """Outcome of one gateway health request."""

    ok: bool
    reason: str
    checked_at: datetime
    status_code: int | None = None
    duration_seconds: float = 0.0


@dataclass
class Incident:
    """An incident opened after the configured failure threshold."""

    id: str
    reason: str
    opened_at: datetime
    consecutive_failures: int
    closed_at: datetime | None = None

    @property
    def is_open(self) -> bool:
        return self.closed_at is None
