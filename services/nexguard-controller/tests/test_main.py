"""Tests for controller endpoints and healthy-state backup orchestration."""

import importlib
import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

import httpx
import pytest

if TYPE_CHECKING:
    from app import main as main_module
    from app.docker_manager import DockerClientProtocol
    from app.main import ControllerRuntime, Settings
    from app.models import HealthResult
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
    main_module = importlib.import_module(f"{package_name}.main")
    models_module = importlib.import_module(f"{package_name}.models")
    ControllerRuntime = main_module.ControllerRuntime
    Settings = main_module.Settings
    HealthResult = models_module.HealthResult

VALID_CONFIG = """\
gateway:
  id: gateway-001
  name: Test Gateway
  location: Kyiv
  sensors:
    - id: temperature-001
      type: temperature
      unit: celsius
  reporting_interval_seconds: 10
"""


class UnusedContainers:
    def get(self, _name: str) -> object:
        raise AssertionError("Docker must not be called for a healthy result")


class UnusedDockerClient:
    @property
    def containers(self) -> UnusedContainers:
        return UnusedContainers()


@pytest.mark.asyncio
async def test_controller_http_endpoints_export_all_metrics() -> None:
    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        health_response = await client.get("/health")
        metrics_response = await client.get("/metrics")

    assert health_response.status_code == 200
    assert health_response.json()["status"] in {"starting", "ready"}
    required = {
        "nexguard_gateway_up",
        "nexguard_config_integrity",
        "nexguard_incidents_total",
        "nexguard_recoveries_total",
        "nexguard_recovery_duration_seconds",
        "nexguard_last_backup_timestamp_seconds",
        "nexguard_consecutive_health_failures",
    }
    assert all(metric in metrics_response.text for metric in required)


@pytest.mark.asyncio
async def test_initial_healthy_check_creates_backup(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")
    settings = Settings(
        gateway_health_url="http://gateway/health",
        health_interval=10,
        failure_threshold=3,
        config_path=config_path,
        backup_dir=tmp_path / "backups",
        backup_interval=60,
        allowed_containers={"gateway-simulator"},
        container_name="gateway-simulator",
        recovery_cooldown=60,
        max_recoveries=3,
        recovery_window=600,
        restart_wait=30,
    )
    runtime = ControllerRuntime(settings, cast("DockerClientProtocol", UnusedDockerClient()))
    result = HealthResult(
        ok=True,
        reason="ok",
        checked_at=datetime(2026, 7, 14, 12, 0, tzinfo=UTC),
        status_code=200,
    )

    await runtime.handle_health_result(result)

    backups = runtime.backups.list_backups()
    assert len(backups) == 1
    assert runtime.backups.verify_backup(backups[0])
