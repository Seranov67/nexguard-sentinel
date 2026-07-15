"""FastAPI controller and background NexGuard supervision loop."""

import asyncio
import contextlib
import json
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import docker
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

from .backup import BackupError, BackupManager
from .config_checker import check_config
from .docker_manager import DockerClientProtocol, DockerManager
from .health_monitor import HealthMonitor
from .incident import IncidentManager
from .metrics import METRICS, render_metrics
from .models import HealthResult
from .notifier import TelegramNotifier
from .recovery import RecoveryManager


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    gateway_health_url: str
    health_interval: float
    failure_threshold: int
    config_path: Path
    backup_dir: Path
    backup_interval: float
    backup_retention_count: int
    allowed_containers: set[str]
    container_name: str
    recovery_cooldown: float
    max_recoveries: int
    recovery_window: float
    restart_wait: float

    @classmethod
    def from_env(cls) -> "Settings":
        allowed = {
            item.strip()
            for item in os.getenv("NEXGUARD_ALLOWED_CONTAINERS", "gateway-simulator").split(",")
            if item.strip()
        }
        return cls(
            gateway_health_url=os.getenv(
                "GATEWAY_HEALTH_URL",
                "http://gateway-simulator:8080/health",
            ),
            health_interval=_env_float("HEALTH_CHECK_INTERVAL_SECONDS", 10),
            failure_threshold=_env_int("FAILURE_THRESHOLD", 3),
            config_path=Path(os.getenv("CONFIG_PATH", "/data/gateway/gateway.yaml")),
            backup_dir=Path(os.getenv("BACKUP_DIR", "/data/backups")),
            backup_interval=_env_float("BACKUP_INTERVAL_SECONDS", 60),
            backup_retention_count=_env_int("BACKUP_RETENTION_COUNT", 10),
            allowed_containers=allowed,
            container_name=os.getenv("GATEWAY_CONTAINER_NAME", "gateway-simulator"),
            recovery_cooldown=_env_float("RECOVERY_COOLDOWN_SECONDS", 60),
            max_recoveries=_env_int("MAX_RECOVERIES_PER_WINDOW", 3),
            recovery_window=_env_float("RECOVERY_WINDOW_SECONDS", 600),
            restart_wait=_env_float("RESTART_WAIT_SECONDS", 30),
        )


def _log_event(event_type: str, level: str, message: str, **context: object) -> None:
    event = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "event_type": event_type,
        "level": level,
        "message": message,
        **context,
    }
    print(json.dumps(event, separators=(",", ":"), sort_keys=True), flush=True)


class ControllerRuntime:
    """Wire health results to backups, incidents, recovery, and metrics."""

    def __init__(self, settings: Settings, docker_client: DockerClientProtocol) -> None:
        self.settings = settings
        self.monitor = HealthMonitor(
            settings.gateway_health_url,
            interval_seconds=settings.health_interval,
            logger=lambda event: print(json.dumps(event, separators=(",", ":")), flush=True),
        )
        self.incidents = IncidentManager(
            failure_threshold=settings.failure_threshold,
            metrics=METRICS.incidents,
        )
        self.backups = BackupManager(
            settings.config_path,
            settings.backup_dir,
            settings.backup_retention_count,
        )
        self.notifier = TelegramNotifier.from_env()
        docker_manager = DockerManager(docker_client, settings.allowed_containers)
        self.recovery = RecoveryManager(
            config_path=settings.config_path,
            backup_dir=settings.backup_dir,
            container_name=settings.container_name,
            docker_manager=docker_manager,
            health_check=self.monitor.check_once,
            cooldown_seconds=settings.recovery_cooldown,
            max_recoveries_per_window=settings.max_recoveries,
            recovery_window_seconds=settings.recovery_window,
            restart_wait_seconds=settings.restart_wait,
        )
        self.last_backup_monotonic: float | None = None
        self._notification_tasks: set[asyncio.Task[None]] = set()

    def _notify(self, message: str) -> None:
        task = self.notifier.send_async(message)
        if task is None:
            return
        self._notification_tasks.add(task)
        task.add_done_callback(self._notification_tasks.discard)

    async def close(self) -> None:
        tasks = tuple(self._notification_tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def handle_health_result(self, result: HealthResult) -> None:
        METRICS.gateway_up.set(1 if result.ok else 0)
        config_valid, config_reason = check_config(self.settings.config_path)
        METRICS.config_integrity.set(1 if config_valid else 0)

        if result.ok:
            self.incidents.record_success()
            now = time.monotonic()
            backup_due = (
                self.backups.get_latest_backup() is None
                or self.last_backup_monotonic is None
                or now - self.last_backup_monotonic >= self.settings.backup_interval
            )
            if config_valid and backup_due:
                try:
                    backup_path = self.backups.create_backup(gateway_healthy=True)
                except (BackupError, OSError) as exc:
                    _log_event("backup_failed", "ERROR", "Config backup failed", reason=str(exc))
                else:
                    self.last_backup_monotonic = now
                    METRICS.last_backup_timestamp_seconds.set(time.time())
                    _log_event(
                        "backup_created",
                        "INFO",
                        "Healthy gateway config backed up",
                        backup=str(backup_path),
                    )
            return

        new_incident = self.incidents.record_failure(result.reason)
        if new_incident is not None:
            self._notify(f"NexGuard incident opened: {new_incident.reason}")
        if self.incidents.current_incident is None:
            return
        if self.recovery.status == "manual_intervention_required":
            return
        started = time.monotonic()
        recovery_result = await self.recovery.attempt_recovery(config_valid=config_valid)
        METRICS.recovery_duration_seconds.observe(max(0.0, time.monotonic() - started))
        if recovery_result.success:
            METRICS.recoveries_total.inc()
            METRICS.gateway_up.set(1)
            METRICS.config_integrity.set(1)
            self.incidents.record_success()
            self._notify("NexGuard recovery completed successfully")
        else:
            self._notify(f"NexGuard recovery failed: {recovery_result.reason}")
            _log_event(
                "recovery_failed",
                "ERROR",
                "Recovery attempt did not restore health",
                reason=recovery_result.reason,
                config_reason=config_reason,
            )


runtime: ControllerRuntime | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    global runtime
    settings = Settings.from_env()
    docker_client = cast(DockerClientProtocol, docker.from_env())
    runtime = ControllerRuntime(settings, docker_client)
    monitor_task = asyncio.create_task(runtime.monitor.run(runtime.handle_health_result))
    try:
        yield
    finally:
        monitor_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await monitor_task
        if runtime is not None:
            await runtime.close()


app = FastAPI(title="NexGuard Controller", version="0.1.0", lifespan=lifespan)


@app.get("/health", response_class=JSONResponse)
def health() -> JSONResponse:
    status = "starting" if runtime is None else runtime.recovery.status
    return JSONResponse({"status": status})


@app.get("/metrics", response_class=Response)
def metrics() -> Response:
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)
