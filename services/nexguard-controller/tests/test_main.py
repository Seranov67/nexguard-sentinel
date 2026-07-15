"""Tests for controller endpoints and healthy-state backup orchestration."""

import asyncio
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
    from app.notifier import TelegramNotifier
    from app.recovery import RecoveryResult
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
    recovery_module = importlib.import_module(f"{package_name}.recovery")
    ControllerRuntime = main_module.ControllerRuntime
    Settings = main_module.Settings
    HealthResult = models_module.HealthResult
    notifier_module = importlib.import_module(f"{package_name}.notifier")
    TelegramNotifier = notifier_module.TelegramNotifier
    RecoveryResult = recovery_module.RecoveryResult

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


def _settings(tmp_path: Path, *, backup_dir: Path | None = None) -> Settings:
    return Settings(
        gateway_health_url="http://gateway/health",
        health_interval=10,
        failure_threshold=3,
        config_path=tmp_path / "gateway.yaml",
        backup_dir=backup_dir or tmp_path / "backups",
        backup_interval=60,
        backup_retention_count=10,
        allowed_containers={"gateway-simulator"},
        container_name="gateway-simulator",
        recovery_cooldown=60,
        max_recoveries=3,
        recovery_window=600,
        restart_wait=30,
    )


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
    settings = _settings(tmp_path)
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


@pytest.mark.asyncio
async def test_open_incident_retries_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")
    runtime = ControllerRuntime(
        _settings(tmp_path),
        cast("DockerClientProtocol", UnusedDockerClient()),
    )
    attempts = 0

    async def failed_recovery(*, config_valid: bool) -> RecoveryResult:
        nonlocal attempts
        assert config_valid
        attempts += 1
        return RecoveryResult(False, "post_recovery_health_failed")

    monkeypatch.setattr(runtime.recovery, "attempt_recovery", failed_recovery)
    failure = HealthResult(ok=False, reason="network_error", checked_at=datetime.now(UTC))

    for _check in range(4):
        await runtime.handle_health_result(failure)

    assert attempts == 2
    assert runtime.incidents.current_incident is not None


@pytest.mark.asyncio
async def test_backup_io_error_does_not_escape_loop(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")
    invalid_backup_dir = tmp_path / "not-a-directory"
    invalid_backup_dir.write_text("occupied", encoding="utf-8")
    runtime = ControllerRuntime(
        _settings(tmp_path, backup_dir=invalid_backup_dir),
        cast("DockerClientProtocol", UnusedDockerClient()),
    )
    result = HealthResult(ok=True, reason="ok", checked_at=datetime.now(UTC))

    await runtime.handle_health_result(result)

    assert "backup_failed" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_notification_tasks_are_retained_and_cleaned_up(tmp_path: Path) -> None:
    started = asyncio.Event()
    release = asyncio.Event()

    async def sender(_token: str, _chat_id: str, _message: str) -> None:
        started.set()
        await release.wait()

    runtime = ControllerRuntime(
        _settings(tmp_path),
        cast("DockerClientProtocol", UnusedDockerClient()),
    )
    runtime.notifier = TelegramNotifier(token="token", chat_id="chat", sender=sender)

    runtime._notify("incident")
    await started.wait()

    assert len(runtime._notification_tasks) == 1
    task = next(iter(runtime._notification_tasks))

    release.set()
    await task
    await asyncio.sleep(0)

    assert not runtime._notification_tasks
