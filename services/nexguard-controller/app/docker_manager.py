"""Safe Docker operations guarded by an allowlist and managed label."""

import json
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Protocol


class SecurityBlockError(RuntimeError):
    """Raised when a requested container operation violates policy."""


class ContainerProtocol(Protocol):
    name: str
    status: str
    labels: Mapping[str, str]

    def restart(self, *, timeout: int = 10) -> None: ...

    def reload(self) -> None: ...


class ContainerCollectionProtocol(Protocol):
    def get(self, name: str) -> ContainerProtocol: ...


class DockerClientProtocol(Protocol):
    @property
    def containers(self) -> ContainerCollectionProtocol: ...


EventLogger = Callable[[dict[str, object]], None]


def _default_logger(event: dict[str, object]) -> None:
    print(json.dumps(event, separators=(",", ":"), sort_keys=True), flush=True)


class DockerManager:
    """Wrap the Docker client while enforcing both mandatory restart guards."""

    def __init__(
        self,
        client: DockerClientProtocol,
        allowed_containers: set[str],
        *,
        logger: EventLogger = _default_logger,
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._allowed_containers = {name.strip() for name in allowed_containers if name.strip()}
        self._logger = logger
        self._monotonic = monotonic
        self._sleeper = sleeper

    def _security_block(self, name: str, reason: str) -> None:
        self._logger(
            {
                "event_type": "SECURITY_BLOCK",
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "level": "ERROR",
                "message": "Container restart blocked by security policy",
                "container": name,
                "reason": reason,
            }
        )
        raise SecurityBlockError(reason)

    def restart_container(self, name: str) -> None:
        """Restart only an allowlisted container carrying the managed label."""

        if name not in self._allowed_containers:
            self._security_block(name, "container_not_in_allowlist")

        container = self._client.containers.get(name)
        if container.labels.get("io.nexguard.managed") != "true":
            self._security_block(name, "managed_label_missing")

        container.restart(timeout=10)

    def wait_for_running(
        self,
        name: str,
        *,
        timeout: float,
        poll_interval: float = 0.5,
    ) -> bool:
        """Poll container state until running or the monotonic deadline expires."""

        if timeout < 0 or poll_interval <= 0:
            raise ValueError("timeout must be non-negative and poll_interval must be positive")
        container = self._client.containers.get(name)
        deadline = self._monotonic() + timeout
        while True:
            container.reload()
            if container.status == "running":
                return True
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                return False
            self._sleeper(min(poll_interval, remaining))
