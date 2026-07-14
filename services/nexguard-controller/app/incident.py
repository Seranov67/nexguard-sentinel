"""Incident lifecycle and incident-related Prometheus metrics."""

import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge

from .models import Incident

EventLogger = Callable[[dict[str, object]], None]


def _default_logger(event: dict[str, object]) -> None:
    print(json.dumps(event, separators=(",", ":"), sort_keys=True), flush=True)


@dataclass(frozen=True)
class IncidentMetrics:
    """Prometheus collectors updated by the incident manager."""

    incidents_total: Counter
    consecutive_failures: Gauge

    @classmethod
    def create(cls, registry: CollectorRegistry = REGISTRY) -> "IncidentMetrics":
        return cls(
            incidents_total=Counter(
                "nexguard_incidents_total",
                "Total number of incidents opened.",
                registry=registry,
            ),
            consecutive_failures=Gauge(
                "nexguard_consecutive_health_failures",
                "Current consecutive gateway health-check failures.",
                registry=registry,
            ),
        )


DEFAULT_METRICS = IncidentMetrics.create()


@dataclass
class IncidentManager:
    """Open one incident after exactly ``failure_threshold`` failures."""

    failure_threshold: int = 3
    metrics: IncidentMetrics = DEFAULT_METRICS
    logger: EventLogger = _default_logger
    clock: Callable[[], datetime] = field(default=lambda: datetime.now(UTC))
    id_factory: Callable[[], str] = field(default=lambda: str(uuid.uuid4()))
    consecutive_failures: int = field(default=0, init=False)
    current_incident: Incident | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        self.metrics.consecutive_failures.set(0)

    def record_failure(self, reason: str) -> Incident | None:
        """Record a failure and return an incident only when one is newly opened."""

        self.consecutive_failures += 1
        self.metrics.consecutive_failures.set(self.consecutive_failures)
        if self.consecutive_failures != self.failure_threshold or self.current_incident is not None:
            return None

        opened_at = self.clock().astimezone(UTC)
        incident = Incident(
            id=self.id_factory(),
            reason=reason,
            opened_at=opened_at,
            consecutive_failures=self.consecutive_failures,
        )
        self.current_incident = incident
        self.metrics.incidents_total.inc()
        self.logger(
            {
                "timestamp": opened_at.isoformat().replace("+00:00", "Z"),
                "event_type": "incident_opened",
                "level": "ERROR",
                "message": "Gateway incident opened",
                "incident_id": incident.id,
                "reason": reason,
                "consecutive_failures": self.consecutive_failures,
            }
        )
        return incident

    def record_success(self) -> Incident | None:
        """Reset the failure counter and close an open incident."""

        self.consecutive_failures = 0
        self.metrics.consecutive_failures.set(0)
        incident = self.current_incident
        if incident is None:
            return None

        closed_at = self.clock().astimezone(UTC)
        incident.closed_at = closed_at
        self.current_incident = None
        self.logger(
            {
                "timestamp": closed_at.isoformat().replace("+00:00", "Z"),
                "event_type": "incident_closed",
                "level": "INFO",
                "message": "Gateway incident closed",
                "incident_id": incident.id,
            }
        )
        return incident
