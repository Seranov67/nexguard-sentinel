"""Tests for incident lifecycle, logging, and metrics."""

import importlib
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from prometheus_client import CollectorRegistry

if TYPE_CHECKING:
    from app.incident import IncidentManager, IncidentMetrics
else:
    package_name = "nexguard_controller_app"
    app_dir = Path(__file__).resolve().parents[1] / "app"
    if package_name not in sys.modules:
        package_spec = importlib.util.spec_from_file_location(
            package_name,
            app_dir / "__init__.py",
            submodule_search_locations=[str(app_dir)],
        )
        if package_spec is None or package_spec.loader is None:
            raise RuntimeError("unable to load controller application package")
        package = importlib.util.module_from_spec(package_spec)
        sys.modules[package_name] = package
        package_spec.loader.exec_module(package)
    incident_module = importlib.import_module(f"{package_name}.incident")
    IncidentManager = incident_module.IncidentManager
    IncidentMetrics = incident_module.IncidentMetrics

FIXED_TIME = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)


def _manager() -> tuple[IncidentManager, CollectorRegistry]:
    registry = CollectorRegistry()
    metrics = IncidentMetrics.create(registry)
    manager = IncidentManager(
        metrics=metrics,
        logger=lambda _event: None,
        clock=lambda: FIXED_TIME,
        id_factory=lambda: "incident-001",
    )
    return manager, registry


def test_incident_after_3_failures() -> None:
    manager, _registry = _manager()

    assert manager.record_failure("network_error") is None
    assert manager.record_failure("network_error") is None
    incident = manager.record_failure("network_error")

    assert incident is not None
    assert incident.id == "incident-001"
    assert incident.consecutive_failures == 3
    assert manager.record_failure("network_error") is None
    assert manager.current_incident is incident


def test_counter_reset_on_success() -> None:
    manager, registry = _manager()
    manager.record_failure("network_error")
    manager.record_failure("network_error")

    assert manager.record_success() is None
    assert manager.consecutive_failures == 0
    assert registry.get_sample_value("nexguard_consecutive_health_failures") == 0
    assert manager.record_failure("network_error") is None


def test_incident_json_log(capsys: pytest.CaptureFixture[str]) -> None:
    registry = CollectorRegistry()
    manager = IncidentManager(
        metrics=IncidentMetrics.create(registry),
        clock=lambda: FIXED_TIME,
        id_factory=lambda: "incident-001",
    )

    for _attempt in range(3):
        manager.record_failure("network_error")

    event = json.loads(capsys.readouterr().out)
    assert event["timestamp"] == "2026-07-14T12:00:00Z"
    assert event["event_type"] == "incident_opened"
    assert event["level"] == "ERROR"
    assert event["message"] == "Gateway incident opened"


def test_metric_consecutive_failures() -> None:
    manager, registry = _manager()

    manager.record_failure("network_error")
    manager.record_failure("network_error")

    assert registry.get_sample_value("nexguard_consecutive_health_failures") == 2


def test_metric_incidents_total() -> None:
    manager, registry = _manager()

    for _attempt in range(5):
        manager.record_failure("network_error")

    assert registry.get_sample_value("nexguard_incidents_total") == 1

    manager.record_success()
    for _attempt in range(3):
        manager.record_failure("config_invalid")

    assert registry.get_sample_value("nexguard_incidents_total") == 2
