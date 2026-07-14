"""Tests for Docker restart security guards and state polling."""

import importlib
import importlib.util
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from app.docker_manager import DockerManager, SecurityBlockError
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
    docker_module = importlib.import_module(f"{package_name}.docker_manager")
    DockerManager = docker_module.DockerManager
    SecurityBlockError = docker_module.SecurityBlockError


class FakeContainer:
    def __init__(
        self,
        name: str,
        labels: Mapping[str, str],
        statuses: list[str] | None = None,
    ) -> None:
        self.name = name
        self.labels = labels
        self.status = "created"
        self.statuses = list(statuses or ["running"])
        self.restart_calls = 0

    def restart(self, *, timeout: int = 10) -> None:
        self.restart_calls += 1

    def reload(self) -> None:
        if self.statuses:
            self.status = self.statuses.pop(0)


class FakeContainers:
    def __init__(self, container: FakeContainer) -> None:
        self.container = container

    def get(self, name: str) -> FakeContainer:
        if name != self.container.name:
            raise KeyError(name)
        return self.container


class FakeClient:
    def __init__(self, container: FakeContainer) -> None:
        self.containers = FakeContainers(container)


def _manager(container: FakeContainer, allowed: set[str]) -> DockerManager:
    return DockerManager(FakeClient(container), allowed, logger=lambda _event: None)


def test_allowlist_enforcement() -> None:
    container = FakeContainer("gateway-simulator", {"io.nexguard.managed": "true"})
    manager = _manager(container, {"different-container"})

    with pytest.raises(SecurityBlockError, match="container_not_in_allowlist"):
        manager.restart_container("gateway-simulator")

    assert container.restart_calls == 0


def test_docker_label_enforcement() -> None:
    container = FakeContainer("gateway-simulator", {})
    manager = _manager(container, {"gateway-simulator"})

    with pytest.raises(SecurityBlockError, match="managed_label_missing"):
        manager.restart_container("gateway-simulator")

    assert container.restart_calls == 0


def test_restart_when_both_guards_pass() -> None:
    container = FakeContainer("gateway-simulator", {"io.nexguard.managed": "true"})
    manager = _manager(container, {"gateway-simulator"})

    manager.restart_container("gateway-simulator")

    assert container.restart_calls == 1


def test_wait_for_running() -> None:
    container = FakeContainer(
        "gateway-simulator",
        {"io.nexguard.managed": "true"},
        statuses=["created", "restarting", "running"],
    )
    current_time = [0.0]

    def monotonic() -> float:
        return current_time[0]

    def sleeper(delay: float) -> None:
        current_time[0] += delay

    manager = DockerManager(
        FakeClient(container),
        {"gateway-simulator"},
        logger=lambda _event: None,
        monotonic=monotonic,
        sleeper=sleeper,
    )

    assert manager.wait_for_running("gateway-simulator", timeout=2, poll_interval=0.5)
    assert current_time[0] == 1.0
