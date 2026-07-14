"""Controller Prometheus collectors and response rendering."""

from dataclasses import dataclass

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from .incident import DEFAULT_METRICS, IncidentMetrics


@dataclass(frozen=True)
class ControllerMetrics:
    gateway_up: Gauge
    config_integrity: Gauge
    incidents: IncidentMetrics
    recoveries_total: Counter
    recovery_duration_seconds: Histogram
    last_backup_timestamp_seconds: Gauge


METRICS = ControllerMetrics(
    gateway_up=Gauge(
        "nexguard_gateway_up",
        "Whether the latest gateway health check succeeded.",
    ),
    config_integrity=Gauge(
        "nexguard_config_integrity",
        "Whether the current gateway config is valid.",
    ),
    incidents=DEFAULT_METRICS,
    recoveries_total=Counter(
        "nexguard_recoveries_total",
        "Total successful gateway recoveries.",
    ),
    recovery_duration_seconds=Histogram(
        "nexguard_recovery_duration_seconds",
        "Duration of gateway recovery attempts.",
    ),
    last_backup_timestamp_seconds=Gauge(
        "nexguard_last_backup_timestamp_seconds",
        "Unix timestamp of the latest successful backup.",
    ),
)


def render_metrics() -> tuple[bytes, str]:
    """Return the default registry in Prometheus exposition format."""

    return generate_latest(), CONTENT_TYPE_LATEST
