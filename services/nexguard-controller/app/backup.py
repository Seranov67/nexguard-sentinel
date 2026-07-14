"""Atomic last-known-good configuration backups with SHA-256 integrity."""

import hashlib
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .config_checker import check_config_text


class BackupError(RuntimeError):
    """Base exception for backup operations."""


class BackupStateError(BackupError):
    """Raised when a backup is requested from a non-healthy state."""


class BackupValidationError(BackupError):
    """Raised when source content or a stored checksum is invalid."""


def checksum_path_for(backup_path: Path) -> Path:
    """Return the companion checksum path for a backup."""

    return Path(f"{backup_path}.sha256")


def _write_temp_file(target: Path, contents: bytes) -> Path:
    descriptor, temp_name = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as temp_file:
            temp_file.write(contents)
            temp_file.flush()
            os.fsync(temp_file.fileno())
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path


def _atomic_replace(source: Path, target: Path) -> None:
    os.replace(source, target)


def _write_backup_pair(
    backup_path: Path,
    backup_contents: bytes,
    checksum_contents: bytes,
) -> None:
    checksum_path = checksum_path_for(backup_path)
    backup_temp = _write_temp_file(backup_path, backup_contents)
    checksum_temp = _write_temp_file(checksum_path, checksum_contents)
    try:
        _atomic_replace(checksum_temp, checksum_path)
        _atomic_replace(backup_temp, backup_path)
    except BaseException:
        backup_temp.unlink(missing_ok=True)
        checksum_temp.unlink(missing_ok=True)
        if not backup_path.exists():
            checksum_path.unlink(missing_ok=True)
        raise


def create_backup(
    config_path: Path,
    backup_dir: Path,
    *,
    gateway_healthy: bool,
    now: datetime | None = None,
) -> Path:
    """Create a timestamped atomic backup from a verified healthy state."""

    if not gateway_healthy:
        raise BackupStateError("backup requires a verified healthy gateway state")

    try:
        config_contents = config_path.read_bytes()
        config_text = config_contents.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise BackupValidationError("source_config_unreadable") from exc

    valid, reason = check_config_text(config_text)
    if not valid:
        raise BackupValidationError(reason)

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = (now or datetime.now(UTC)).astimezone(UTC)
    timestamp_text = timestamp.strftime("%Y%m%dT%H%M%S.%fZ")
    backup_path = backup_dir / f"gateway-{timestamp_text}.yaml"
    digest = hashlib.sha256(config_contents).hexdigest()
    _write_backup_pair(backup_path, config_contents, f"{digest}\n".encode())
    return backup_path


def list_backups(backup_dir: Path) -> list[Path]:
    """List complete backups in timestamp order."""

    if not backup_dir.exists():
        return []
    return sorted(
        path
        for path in backup_dir.glob("gateway-*.yaml")
        if checksum_path_for(path).is_file()
    )


def get_latest_backup(backup_dir: Path) -> Path | None:
    """Return the newest complete backup, if one exists."""

    backups = list_backups(backup_dir)
    return backups[-1] if backups else None


def verify_backup(backup_path: Path) -> bool:
    """Verify a backup against its companion SHA-256 file."""

    checksum_path = checksum_path_for(backup_path)
    try:
        expected = checksum_path.read_text(encoding="ascii").strip()
        contents = backup_path.read_bytes()
    except (OSError, UnicodeError):
        return False
    if len(expected) != 64:
        return False
    try:
        int(expected, 16)
    except ValueError:
        return False
    actual = hashlib.sha256(contents).hexdigest()
    return actual == expected.lower()


@dataclass(frozen=True)
class BackupManager:
    """Configured facade for backup operations."""

    config_path: Path
    backup_dir: Path
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def create_backup(self, *, gateway_healthy: bool) -> Path:
        return create_backup(
            self.config_path,
            self.backup_dir,
            gateway_healthy=gateway_healthy,
            now=self.clock(),
        )

    def list_backups(self) -> list[Path]:
        return list_backups(self.backup_dir)

    def get_latest_backup(self) -> Path | None:
        return get_latest_backup(self.backup_dir)

    @staticmethod
    def verify_backup(backup_path: Path) -> bool:
        return verify_backup(backup_path)
