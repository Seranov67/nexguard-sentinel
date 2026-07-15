"""Tests for atomic restore and recovery safety limits."""

import importlib
import importlib.util
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from app import recovery as recovery_module
    from app.backup import create_backup
    from app.models import HealthResult
    from app.recovery import RecoveryManager, restore_backup
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
    backup_module = importlib.import_module(f"{package_name}.backup")
    models_module = importlib.import_module(f"{package_name}.models")
    recovery_module = importlib.import_module(f"{package_name}.recovery")
    create_backup = backup_module.create_backup
    HealthResult = models_module.HealthResult
    RecoveryManager = recovery_module.RecoveryManager
    restore_backup = recovery_module.restore_backup

FIXED_TIME = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
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


class FakeDockerManager:
    def __init__(self, *, running: bool = True, restart_error: Exception | None = None) -> None:
        self.running = running
        self.restart_error = restart_error
        self.restart_calls = 0
        self.wait_calls = 0

    def restart_container(self, _name: str) -> None:
        self.restart_calls += 1
        if self.restart_error is not None:
            raise self.restart_error

    def wait_for_running(self, _name: str, *, timeout: float) -> bool:
        self.wait_calls += 1
        return self.running


def _health_result(ok: bool = True) -> HealthResult:
    return HealthResult(ok=ok, reason="ok" if ok else "still_unhealthy", checked_at=FIXED_TIME)


def _manager(
    tmp_path: Path,
    docker_manager: FakeDockerManager,
    current_time: list[float],
    *,
    cooldown: float = 60,
    max_attempts: int = 3,
) -> RecoveryManager:
    async def health_check() -> HealthResult:
        return _health_result()

    return RecoveryManager(
        config_path=tmp_path / "gateway.yaml",
        backup_dir=tmp_path / "backups",
        container_name="gateway-simulator",
        docker_manager=docker_manager,
        health_check=health_check,
        cooldown_seconds=cooldown,
        max_recoveries_per_window=max_attempts,
        logger=lambda _event: None,
        monotonic=lambda: current_time[0],
    )


def test_restore_atomic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")
    backup_path = create_backup(
        config_path,
        tmp_path / "backups",
        gateway_healthy=True,
        now=FIXED_TIME,
    )
    config_path.write_text("corrupt", encoding="utf-8")
    replace_targets: list[Path] = []
    original_replace = os.replace

    def recording_replace(source: str | Path, destination: str | Path) -> None:
        replace_targets.append(Path(destination))
        original_replace(source, destination)

    monkeypatch.setattr(recovery_module, "_atomic_replace", recording_replace)

    restore_backup(backup_path, config_path)

    assert config_path.read_text(encoding="utf-8") == VALID_CONFIG
    assert replace_targets == [config_path]


def test_restore_preserves_config_permissions(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")
    config_path.chmod(0o664)
    original_gid = config_path.stat().st_gid
    backup_path = create_backup(
        config_path,
        tmp_path / "backups",
        gateway_healthy=True,
        now=FIXED_TIME,
    )
    config_path.write_text("corrupt", encoding="utf-8")

    restore_backup(backup_path, config_path)

    assert config_path.stat().st_mode & 0o777 == 0o664
    assert config_path.stat().st_gid == original_gid


@pytest.mark.asyncio
async def test_cooldown_enforcement(tmp_path: Path) -> None:
    current_time = [0.0]
    docker_manager = FakeDockerManager()
    manager = _manager(tmp_path, docker_manager, current_time)

    assert (await manager.attempt_recovery(config_valid=True)).success
    current_time[0] = 10
    result = await manager.attempt_recovery(config_valid=True)

    assert not result.success
    assert result.reason == "cooldown_active"
    assert docker_manager.restart_calls == 1


@pytest.mark.asyncio
async def test_invalid_config_restore_branch(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")
    create_backup(
        config_path,
        tmp_path / "backups",
        gateway_healthy=True,
        now=FIXED_TIME,
    )
    config_path.write_text("bad: [unclosed", encoding="utf-8")
    docker_manager = FakeDockerManager()
    manager = _manager(tmp_path, docker_manager, [0.0])

    result = await manager.attempt_recovery(config_valid=False)

    assert result.success
    assert result.restored_config
    assert config_path.read_text(encoding="utf-8") == VALID_CONFIG
    assert docker_manager.restart_calls == 1


@pytest.mark.asyncio
async def test_max_recovery_limit(tmp_path: Path) -> None:
    current_time = [0.0]
    docker_manager = FakeDockerManager()
    manager = _manager(tmp_path, docker_manager, current_time, cooldown=0)

    for attempt in range(3):
        current_time[0] = float(attempt)
        assert (await manager.attempt_recovery(config_valid=True)).success
    current_time[0] = 3
    result = await manager.attempt_recovery(config_valid=True)

    assert not result.success
    assert result.reason == "manual_intervention_required"
    assert manager.status == "manual_intervention_required"
    assert docker_manager.restart_calls == 3


@pytest.mark.asyncio
async def test_post_recovery_health_check(tmp_path: Path) -> None:
    health_calls = 0
    docker_manager = FakeDockerManager()

    async def health_check() -> HealthResult:
        nonlocal health_calls
        health_calls += 1
        return _health_result()

    manager = RecoveryManager(
        config_path=tmp_path / "gateway.yaml",
        backup_dir=tmp_path / "backups",
        container_name="gateway-simulator",
        docker_manager=docker_manager,
        health_check=health_check,
        logger=lambda _event: None,
    )

    result = await manager.attempt_recovery(config_valid=True)

    assert result.success
    assert health_calls == 1
    assert docker_manager.restart_calls == 1
    assert docker_manager.wait_calls == 1


@pytest.mark.asyncio
async def test_post_recovery_health_check_retries_until_ready(tmp_path: Path) -> None:
    health_results = iter([_health_result(False), _health_result()])
    docker_manager = FakeDockerManager()

    async def health_check() -> HealthResult:
        return next(health_results)

    manager = RecoveryManager(
        config_path=tmp_path / "gateway.yaml",
        backup_dir=tmp_path / "backups",
        container_name="gateway-simulator",
        docker_manager=docker_manager,
        health_check=health_check,
        restart_wait_seconds=0.01,
        logger=lambda _event: None,
    )

    result = await manager.attempt_recovery(config_valid=True)

    assert result.success
    assert docker_manager.restart_calls == 1
    assert docker_manager.wait_calls == 1


@pytest.mark.asyncio
async def test_docker_failure_does_not_escape_recovery(tmp_path: Path) -> None:
    docker_manager = FakeDockerManager(restart_error=RuntimeError("daemon unavailable"))
    manager = _manager(tmp_path, docker_manager, [0.0])

    result = await manager.attempt_recovery(config_valid=True)

    assert not result.success
    assert result.reason == "docker_operation_failed"
    assert docker_manager.restart_calls == 1


@pytest.mark.asyncio
async def test_backup_listing_error_does_not_escape_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    docker_manager = FakeDockerManager()
    manager = _manager(tmp_path, docker_manager, [0.0])

    def failed_listing(_backup_dir: Path) -> Path | None:
        raise OSError("permission denied")

    monkeypatch.setattr(recovery_module, "get_latest_backup", failed_listing)

    result = await manager.attempt_recovery(config_valid=False)

    assert not result.success
    assert result.reason == "restore_failed"
    assert docker_manager.restart_calls == 0
