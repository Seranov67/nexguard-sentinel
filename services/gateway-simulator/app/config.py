"""Load and validate the gateway simulator configuration."""

import os
from pathlib import Path

import yaml
from pydantic import ValidationError

from .schemas import GatewayConfigDocument

DEFAULT_CONFIG_PATH = Path("/data/gateway/gateway.yaml")


def get_config_path() -> Path:
    """Return the configured YAML path, resolving the environment on each call."""

    return Path(os.getenv("GATEWAY_CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))


def load_config(path: Path | None = None) -> GatewayConfigDocument:
    """Read and validate a gateway config.

    The file is intentionally read for every call so on-disk corruption is visible
    immediately to the health endpoint.
    """

    config_path = path if path is not None else get_config_path()
    try:
        raw_config = config_path.read_text(encoding="utf-8")
        if not raw_config.strip():
            raise ValueError("configuration is empty")
        parsed_config = yaml.safe_load(raw_config)
        if not isinstance(parsed_config, dict):
            raise ValueError("configuration root must be a mapping")
        return GatewayConfigDocument.model_validate(parsed_config)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError, ValidationError) as exc:
        raise ValueError("config_invalid") from exc


def config_is_valid(path: Path | None = None) -> bool:
    """Return whether the current gateway configuration is valid."""

    try:
        load_config(path)
    except ValueError:
        return False
    return True
