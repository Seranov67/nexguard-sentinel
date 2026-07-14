"""Tests for gateway config integrity checks."""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config_checker import check_config
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
    check_config = importlib.import_module(f"{package_name}.config_checker").check_config

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


def test_valid_config(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(VALID_CONFIG, encoding="utf-8")

    assert check_config(config_path) == (True, "ok")


def test_detect_corrupt_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text("bad: [unclosed", encoding="utf-8")

    assert check_config(config_path) == (False, "yaml_parse_error")


def test_missing_required_key(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text("gateway:\n  id: gateway-001\n", encoding="utf-8")

    assert check_config(config_path) == (False, "missing_required_key")


def test_reject_invalid_value(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text(
        VALID_CONFIG.replace("reporting_interval_seconds: 10", "reporting_interval_seconds: 0"),
        encoding="utf-8",
    )

    assert check_config(config_path) == (False, "schema_validation_error")
