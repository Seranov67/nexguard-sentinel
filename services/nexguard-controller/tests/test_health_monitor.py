"""Tests for gateway health requests and fixed-deadline scheduling."""

import importlib
import importlib.util
import sys
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest

if TYPE_CHECKING:
    from app.health_monitor import HealthMonitor
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
    health_module = importlib.import_module(f"{package_name}.health_monitor")
    models_module = importlib.import_module(f"{package_name}.models")
    HealthMonitor = health_module.HealthMonitor
    HealthResult = models_module.HealthResult

FIXED_TIME = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)


def _monitor(
    requester: Callable[[str, float], Awaitable[httpx.Response]],
) -> HealthMonitor:
    return HealthMonitor(
        "http://gateway/health",
        requester=requester,
        logger=lambda _event: None,
        clock=lambda: FIXED_TIME,
    )


@pytest.mark.asyncio
async def test_check_once_success() -> None:
    async def requester(_url: str, _timeout: float) -> httpx.Response:
        return httpx.Response(200, json={"status": "healthy"})

    result = await _monitor(requester).check_once()

    assert result.ok
    assert result.reason == "ok"
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_check_once_unhealthy_response() -> None:
    async def requester(_url: str, _timeout: float) -> httpx.Response:
        return httpx.Response(503, json={"status": "unhealthy", "reason": "config_invalid"})

    result = await _monitor(requester).check_once()

    assert not result.ok
    assert result.reason == "config_invalid"
    assert result.status_code == 503


@pytest.mark.asyncio
async def test_network_error_becomes_failure() -> None:
    async def requester(_url: str, _timeout: float) -> httpx.Response:
        request = httpx.Request("GET", "http://gateway/health")
        raise httpx.ConnectError("offline", request=request)

    result = await _monitor(requester).check_once()

    assert not result.ok
    assert result.reason == "network_error"
    assert result.status_code is None


@pytest.mark.asyncio
async def test_health_loop_cadence() -> None:
    current_time = [0.0]
    check_starts: list[float] = []
    results: list[HealthResult] = []

    def monotonic() -> float:
        return current_time[0]

    async def requester(_url: str, _timeout: float) -> httpx.Response:
        check_starts.append(current_time[0])
        current_time[0] += 0.25
        return httpx.Response(200, json={"status": "healthy"})

    async def sleeper(delay: float) -> None:
        current_time[0] += delay

    async def callback(result: HealthResult) -> None:
        results.append(result)

    monitor = HealthMonitor(
        "http://gateway/health",
        interval_seconds=10,
        requester=requester,
        logger=lambda _event: None,
        monotonic=monotonic,
        sleeper=sleeper,
        clock=lambda: FIXED_TIME,
    )

    await monitor.run(callback, iterations=3)

    assert check_starts == pytest.approx([0.0, 10.0, 20.0])
    assert len(results) == 3
