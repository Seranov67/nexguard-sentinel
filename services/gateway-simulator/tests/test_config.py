"""Tests for gateway YAML loading and schema validation."""

from pathlib import Path

import pytest
from app.config import config_is_valid, load_config

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


def test_load_valid_config(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")

    config = load_config(config_path)

    assert config.gateway.id == "gateway-001"
    assert config_is_valid(config_path)


@pytest.mark.parametrize("contents", ["", "bad: [unclosed"])
def test_reject_empty_or_corrupt_yaml(tmp_path: Path, contents: str) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match="config_invalid"):
        load_config(config_path)

    assert not config_is_valid(config_path)


def test_reject_missing_required_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text("gateway:\n  id: gateway-001\n", encoding="utf-8")

    with pytest.raises(ValueError, match="config_invalid"):
        load_config(config_path)


def test_reject_missing_file(tmp_path: Path) -> None:
    assert not config_is_valid(tmp_path / "missing.yaml")
