"""Asynchronous gateway health checks with drift-resistant scheduling."""

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx

from .models import HealthResult

HealthRequester = Callable[[str, float], Awaitable[httpx.Response]]
HealthCallback = Callable[[HealthResult], Awaitable[None]]
EventLogger = Callable[[dict[str, object]], None]
Sleeper = Callable[[float], Awaitable[None]]


async def _default_request(url: str, timeout: float) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        return await client.get(url, timeout=timeout)


def _default_logger(event: dict[str, object]) -> None:
    print(json.dumps(event, separators=(",", ":"), sort_keys=True), flush=True)


@dataclass
class HealthMonitor:
    """Perform individual checks or run a periodic health loop."""

    health_url: str
    interval_seconds: float = 10.0
    timeout_seconds: float = 5.0
    requester: HealthRequester = _default_request
    logger: EventLogger = _default_logger
    monotonic: Callable[[], float] = time.monotonic
    sleeper: Sleeper = asyncio.sleep
    clock: Callable[[], datetime] = field(default=lambda: datetime.now(UTC))

    async def check_once(self) -> HealthResult:
        """Return a failure result for HTTP and network errors, never propagating them."""

        started = self.monotonic()
        checked_at = self.clock().astimezone(UTC)
        error_type: str | None = None
        try:
            response = await self.requester(self.health_url, self.timeout_seconds)
            duration = max(0.0, self.monotonic() - started)
            if response.status_code == httpx.codes.OK:
                result = HealthResult(
                    ok=True,
                    reason="ok",
                    checked_at=checked_at,
                    status_code=response.status_code,
                    duration_seconds=duration,
                )
            else:
                reason = f"http_{response.status_code}"
                try:
                    payload = response.json()
                    if isinstance(payload, dict) and isinstance(payload.get("reason"), str):
                        reason = payload["reason"]
                except ValueError:
                    pass
                result = HealthResult(
                    ok=False,
                    reason=reason,
                    checked_at=checked_at,
                    status_code=response.status_code,
                    duration_seconds=duration,
                )
        except httpx.RequestError as exc:
            result = HealthResult(
                ok=False,
                reason="network_error",
                checked_at=checked_at,
                duration_seconds=max(0.0, self.monotonic() - started),
            )
            error_type = type(exc).__name__

        event: dict[str, object] = {
            "timestamp": checked_at.isoformat().replace("+00:00", "Z"),
            "event_type": "health_check",
            "level": "INFO" if result.ok else "WARNING",
            "message": (
                "Gateway health check succeeded"
                if result.ok
                else "Gateway health check failed"
            ),
            "ok": result.ok,
            "reason": result.reason,
            "status_code": result.status_code,
            "duration_seconds": result.duration_seconds,
        }
        if error_type is not None:
            event["error_type"] = error_type
        self.logger(event)
        return result

    async def run(self, callback: HealthCallback, *, iterations: int | None = None) -> None:
        """Run checks on fixed deadlines so request duration does not accumulate drift."""

        completed = 0
        next_deadline = self.monotonic()
        while iterations is None or completed < iterations:
            result = await self.check_once()
            await callback(result)
            completed += 1
            if iterations is not None and completed >= iterations:
                return
            next_deadline += self.interval_seconds
            await self.sleeper(max(0.0, next_deadline - self.monotonic()))
