"""Tests for gateway simulator HTTP endpoints."""

from pathlib import Path

import httpx
import pytest
from app.main import app

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


@pytest.mark.asyncio
async def test_health_when_config_is_valid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")
    monkeypatch.setenv("GATEWAY_CONFIG_PATH", str(config_path))

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_health_when_config_is_corrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text("bad: [unclosed", encoding="utf-8")
    monkeypatch.setenv("GATEWAY_CONFIG_PATH", str(config_path))

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "reason": "config_invalid"}


@pytest.mark.asyncio
async def test_metrics_are_prometheus_text() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "gateway_simulator_config_valid" in response.text
