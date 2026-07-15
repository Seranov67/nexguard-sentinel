"""Tests for atomic configuration backups and integrity verification."""

import importlib
import importlib.util
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from app import backup as backup_module
    from app.backup import (
        BackupStateError,
        BackupValidationError,
        checksum_path_for,
        create_backup,
        get_latest_backup,
        list_backups,
        verify_backup,
    )
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
    BackupStateError = backup_module.BackupStateError
    BackupValidationError = backup_module.BackupValidationError
    checksum_path_for = backup_module.checksum_path_for
    create_backup = backup_module.create_backup
    get_latest_backup = backup_module.get_latest_backup
    list_backups = backup_module.list_backups
    verify_backup = backup_module.verify_backup

FIXED_TIME = datetime(2026, 7, 14, 12, 30, tzinfo=UTC)
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


def _write_valid_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")
    return config_path


def test_backup_only_when_healthy(tmp_path: Path) -> None:
    config_path = _write_valid_config(tmp_path)
    backup_dir = tmp_path / "backups"

    with pytest.raises(BackupStateError):
        create_backup(config_path, backup_dir, gateway_healthy=False, now=FIXED_TIME)

    assert not backup_dir.exists()


def test_no_backup_when_unhealthy(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text("bad: [unclosed", encoding="utf-8")
    backup_dir = tmp_path / "backups"

    with pytest.raises(BackupValidationError, match="yaml_parse_error"):
        create_backup(config_path, backup_dir, gateway_healthy=True, now=FIXED_TIME)

    assert not backup_dir.exists()


def test_atomic_write_and_sha256(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_valid_config(tmp_path)
    backup_dir = tmp_path / "backups"
    replace_targets: list[Path] = []
    original_replace = os.replace

    def recording_replace(source: str | Path, destination: str | Path) -> None:
        replace_targets.append(Path(destination))
        original_replace(source, destination)

    monkeypatch.setattr(backup_module, "_atomic_replace", recording_replace)

    backup_path = create_backup(
        config_path,
        backup_dir,
        gateway_healthy=True,
        now=FIXED_TIME,
    )

    checksum_path = checksum_path_for(backup_path)
    assert backup_path.name == "gateway-20260714T123000.000000Z.yaml"
    assert backup_path.read_text(encoding="utf-8") == VALID_CONFIG
    assert checksum_path.is_file()
    assert verify_backup(backup_path)
    assert backup_path.stat().st_mode & 0o777 == 0o640
    assert checksum_path.stat().st_mode & 0o777 == 0o640
    assert backup_path.stat().st_gid == backup_dir.stat().st_gid
    assert checksum_path.stat().st_gid == backup_dir.stat().st_gid
    assert replace_targets == [checksum_path, backup_path]
    assert not list(backup_dir.glob("*.tmp"))


def test_sha256_validation(tmp_path: Path) -> None:
    config_path = _write_valid_config(tmp_path)
    backup_dir = tmp_path / "backups"
    backup_path = create_backup(
        config_path,
        backup_dir,
        gateway_healthy=True,
        now=FIXED_TIME,
    )

    backup_path.write_text("tampered", encoding="utf-8")

    assert not verify_backup(backup_path)


def test_list_and_get_latest_backup(tmp_path: Path) -> None:
    config_path = _write_valid_config(tmp_path)
    backup_dir = tmp_path / "backups"
    first = create_backup(
        config_path,
        backup_dir,
        gateway_healthy=True,
        now=FIXED_TIME,
    )
    second = create_backup(
        config_path,
        backup_dir,
        gateway_healthy=True,
        now=FIXED_TIME.replace(minute=31),
    )

    assert list_backups(backup_dir) == [first, second]
    assert get_latest_backup(backup_dir) == second
