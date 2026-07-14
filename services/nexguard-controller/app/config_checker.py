"""Validate gateway YAML syntax and required schema."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class _SensorConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    unit: str = Field(min_length=1)


class _GatewayConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    location: str = Field(min_length=1)
    sensors: list[_SensorConfig] = Field(min_length=1)
    reporting_interval_seconds: int = Field(gt=0)


class _GatewayDocument(BaseModel):
    model_config = ConfigDict(strict=True)

    gateway: _GatewayConfig


def _parse_yaml(contents: str) -> tuple[object | None, str]:
    if not contents.strip():
        return None, "empty_config"
    try:
        return yaml.safe_load(contents), "ok"
    except yaml.YAMLError:
        return None, "yaml_parse_error"


def is_valid_yaml(path: Path) -> tuple[bool, str]:
    """Check that a file exists and contains a non-empty YAML mapping."""

    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False, "file_not_found"
    except (OSError, UnicodeError):
        return False, "read_error"

    parsed, reason = _parse_yaml(contents)
    if reason != "ok":
        return False, reason
    if not isinstance(parsed, dict):
        return False, "schema_validation_error"
    return True, "ok"


def validate_schema(data: object) -> tuple[bool, str]:
    """Validate parsed YAML against the mandatory gateway schema."""

    try:
        _GatewayDocument.model_validate(data)
    except ValidationError as exc:
        errors = exc.errors()
        if any(error.get("type") == "missing" for error in errors):
            return False, "missing_required_key"
        return False, "schema_validation_error"
    return True, "ok"


def check_config_text(contents: str) -> tuple[bool, str]:
    """Validate an in-memory YAML snapshot."""

    parsed, reason = _parse_yaml(contents)
    if reason != "ok":
        return False, reason
    return validate_schema(parsed)


def check_config(path: Path) -> tuple[bool, str]:
    """Read a config once, then validate its YAML and schema."""

    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False, "file_not_found"
    except (OSError, UnicodeError):
        return False, "read_error"
    return check_config_text(contents)
