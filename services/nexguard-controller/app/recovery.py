"""Rate-limited recovery orchestration and atomic config restoration."""

import json
import os
import tempfile
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from .backup import get_latest_backup, verify_backup
from .models import HealthResult


class DockerOperations(Protocol):
    def restart_container(self, name: str) -> None: ...

    def wait_for_running(self, name: str, *, timeout: float) -> bool: ...


EventLogger = Callable[[dict[str, object]], None]
HealthCheck = Callable[[], Awaitable[HealthResult]]


def _default_logger(event: dict[str, object]) -> None:
    print(json.dumps(event, separators=(",", ":"), sort_keys=True), flush=True)


def _atomic_replace(source: Path, target: Path) -> None:
    os.replace(source, target)


def restore_backup(backup_path: Path, config_path: Path) -> None:
    """Verify and atomically restore one backup to the live config path."""

    if not verify_backup(backup_path):
        raise ValueError("backup_checksum_invalid")
    contents = backup_path.read_bytes()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=config_path.parent,
        prefix=f".{config_path.name}.",
        suffix=".tmp",
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as temp_file:
            temp_file.write(contents)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        _atomic_replace(temp_path, config_path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


@dataclass(frozen=True)
class RecoveryResult:
    success: bool
    reason: str
    restored_config: bool = False


@dataclass
class RecoveryManager:
    """Choose the recovery branch and enforce cooldown plus sliding-window limits."""

    config_path: Path
    backup_dir: Path
    container_name: str
    docker_manager: DockerOperations
    health_check: HealthCheck
    cooldown_seconds: float = 60.0
    max_recoveries_per_window: int = 3
    recovery_window_seconds: float = 600.0
    restart_wait_seconds: float = 30.0
    logger: EventLogger = _default_logger
    monotonic: Callable[[], float] = time.monotonic
    clock: Callable[[], datetime] = field(default=lambda: datetime.now(UTC))
    status: str = field(default="ready", init=False)
    _attempts: deque[float] = field(default_factory=deque, init=False)
    _last_attempt: float | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be non-negative")
        if self.max_recoveries_per_window < 1:
            raise ValueError("max_recoveries_per_window must be at least 1")
        if self.recovery_window_seconds <= 0 or self.restart_wait_seconds < 0:
            raise ValueError("recovery and restart windows must be valid")

    def _log(self, event_type: str, level: str, message: str, **context: object) -> None:
        self.logger(
            {
                "timestamp": self.clock().astimezone(UTC).isoformat().replace("+00:00", "Z"),
                "event_type": event_type,
                "level": level,
                "message": message,
                **context,
            }
        )

    async def attempt_recovery(self, *, config_valid: bool) -> RecoveryResult:
        """Attempt restart-only or restore-and-restart recovery."""

        now = self.monotonic()
        while self._attempts and now - self._attempts[0] >= self.recovery_window_seconds:
            self._attempts.popleft()

        if self.status == "manual_intervention_required":
            return RecoveryResult(False, "manual_intervention_required")
        if len(self._attempts) >= self.max_recoveries_per_window:
            self.status = "manual_intervention_required"
            self._log(
                "manual_intervention_required",
                "ERROR",
                "Automatic recovery rate limit exceeded",
                attempts=len(self._attempts),
            )
            return RecoveryResult(False, "manual_intervention_required")
        if self._last_attempt is not None and now - self._last_attempt < self.cooldown_seconds:
            self._log("recovery_deferred", "WARNING", "Recovery cooldown is active")
            return RecoveryResult(False, "cooldown_active")

        self._attempts.append(now)
        self._last_attempt = now
        restored = False
        self._log("recovery_started", "INFO", "Recovery attempt started")

        if not config_valid:
            backup_path = get_latest_backup(self.backup_dir)
            if backup_path is None:
                self._log("recovery_failed", "ERROR", "No valid backup is available")
                return RecoveryResult(False, "backup_not_found")
            try:
                restore_backup(backup_path, self.config_path)
            except (OSError, ValueError) as exc:
                self._log("recovery_failed", "ERROR", "Config restoration failed", reason=str(exc))
                return RecoveryResult(False, "restore_failed")
            restored = True
            self._log(
                "backup_verified",
                "INFO",
                "Backup checksum verified",
                backup=str(backup_path),
            )
            self._log("config_restored", "INFO", "Gateway config restored atomically")

        self.docker_manager.restart_container(self.container_name)
        self._log(
            "container_restarted",
            "INFO",
            "Managed container restart requested",
            container=self.container_name,
        )
        if not self.docker_manager.wait_for_running(
            self.container_name,
            timeout=self.restart_wait_seconds,
        ):
            self._log("recovery_failed", "ERROR", "Container did not reach running state")
            return RecoveryResult(False, "container_not_running", restored)

        health_result = await self.health_check()
        self._log(
            "recovery_verified",
            "INFO" if health_result.ok else "ERROR",
            "Post-recovery health check completed",
            ok=health_result.ok,
            reason=health_result.reason,
        )
        if not health_result.ok:
            return RecoveryResult(False, "post_recovery_health_failed", restored)
        return RecoveryResult(True, "ok", restored)
