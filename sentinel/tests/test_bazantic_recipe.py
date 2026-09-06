"""Tests for Bazantic Recipe schema and MCP server tool dispatch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

RECIPE_PATH = Path("sentinel/bazantic/recipe.json")
ERC7730_PATH = Path("sentinel/ledger/erc7730_unpause.json")


# ---------------------------------------------------------------------------
# Recipe schema validation
# ---------------------------------------------------------------------------


def test_recipe_file_exists() -> None:
    assert RECIPE_PATH.exists(), f"Recipe not found: {RECIPE_PATH}"


def test_recipe_json_valid() -> None:
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    assert isinstance(recipe, dict)


def test_recipe_required_fields() -> None:
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    assert "name" in recipe
    assert "description" in recipe
    assert "mcp" in recipe
    assert "tools" in recipe
    assert "primaryTask" in recipe


def test_recipe_has_primary_task_prompt() -> None:
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    prompt = recipe["primaryTask"]["prompt"]
    assert len(prompt) > 20
    assert "incident" in prompt.lower() or "vault" in prompt.lower()


def test_recipe_tools_present() -> None:
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    tool_names = [t["name"] for t in recipe["tools"]]
    assert "get_latest_incident" in tool_names
    assert "verify_incident_evidence" in tool_names


def test_recipe_mcp_transport() -> None:
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    assert recipe["mcp"]["transport"] == "stdio"
    assert "mcp_server" in recipe["mcp"]["serverArgs"][-1]


def test_recipe_bazantic_gateway_present() -> None:
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    gateway = recipe.get("bazanticGateway", {})
    assert gateway.get("paymentScheme") == "x402"
    assert "endpoint" in gateway


# ---------------------------------------------------------------------------
# MCP server tool definitions
# ---------------------------------------------------------------------------


def test_mcp_tool_definitions_valid() -> None:
    from sentinel.bazantic.mcp_server import TOOL_DEFINITIONS

    assert len(TOOL_DEFINITIONS) == 2
    names = {t["name"] for t in TOOL_DEFINITIONS}
    assert "get_latest_incident" in names
    assert "verify_incident_evidence" in names


def test_mcp_tool_definitions_have_descriptions() -> None:
    from sentinel.bazantic.mcp_server import TOOL_DEFINITIONS

    for tool in TOOL_DEFINITIONS:
        assert len(tool["description"]) > 30, f"Tool {tool['name']} description too short"
        assert "inputSchema" in tool


def test_mcp_verify_tool_requires_incident_id() -> None:
    from sentinel.bazantic.mcp_server import TOOL_DEFINITIONS

    verify = next(t for t in TOOL_DEFINITIONS if t["name"] == "verify_incident_evidence")
    schema = cast(dict[str, Any], verify["inputSchema"])
    assert "incident_id" in cast(dict[str, Any], schema["properties"])
    assert "incident_id" in cast(list[str], schema["required"])


# ---------------------------------------------------------------------------
# ERC-7730 descriptor
# ---------------------------------------------------------------------------


def test_erc7730_file_exists() -> None:
    assert ERC7730_PATH.exists(), f"ERC-7730 descriptor not found: {ERC7730_PATH}"


def test_erc7730_json_valid() -> None:
    descriptor = json.loads(ERC7730_PATH.read_text(encoding="utf-8"))
    assert isinstance(descriptor, dict)


def test_erc7730_has_base_sepolia_deployment() -> None:
    descriptor = json.loads(ERC7730_PATH.read_text(encoding="utf-8"))
    deployments = descriptor["context"]["contract"]["deployments"]
    chain_ids = [d["chainId"] for d in deployments]
    assert 84532 in chain_ids


def test_erc7730_guardian_address_correct() -> None:
    descriptor = json.loads(ERC7730_PATH.read_text(encoding="utf-8"))
    deployments = descriptor["context"]["contract"]["deployments"]
    base = next(d for d in deployments if d["chainId"] == 84532)
    assert base["address"] == "0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3"


def test_erc7730_unpause_format_present() -> None:
    descriptor = json.loads(ERC7730_PATH.read_text(encoding="utf-8"))
    formats = descriptor["display"]["formats"]
    keys = list(formats.keys())
    assert any("unpause" in k.lower() for k in keys), f"No unpause format in {keys}"


def test_erc7730_uses_schema_supported_fields() -> None:
    descriptor = json.loads(ERC7730_PATH.read_text(encoding="utf-8"))
    unpause = descriptor["display"]["formats"]["unpause(bytes32)"]
    assert "screenNote" not in unpause
    assert unpause["fields"][0]["format"] == "raw"


# ---------------------------------------------------------------------------
# Unpause Ledger simulator
# ---------------------------------------------------------------------------


def test_simulate_mode_runs(capsys: pytest.CaptureFixture[str]) -> None:
    """--simulate must complete without error and print calldata."""
    from sentinel.ledger.unpause_ledger import simulate

    simulate("Incident resolved in test")
    out = capsys.readouterr().out
    assert "SIMULATE" in out
    assert "calldata" in out.lower() or "0x" in out
    assert "ERC-7730" in out


def test_validate_erc7730_no_issues() -> None:
    from sentinel.ledger.unpause_ledger import _load_erc7730, _validate_erc7730

    descriptor = _load_erc7730()
    issues = _validate_erc7730(descriptor)
    assert issues == [], f"ERC-7730 validation issues: {issues}"


def test_build_calldata_format() -> None:
    from sentinel.ledger.unpause_ledger import _build_calldata, _keccak256_reason

    reason_hash = _keccak256_reason("test reason")
    calldata = _build_calldata(reason_hash)
    assert calldata.startswith("0x")
    # 4-byte selector (8 hex) + 32-byte reason (64 hex) = 72 hex + "0x" prefix
    assert len(calldata) == 2 + 8 + 64


def test_reason_hash_is_32_bytes() -> None:
    from sentinel.ledger.unpause_ledger import _keccak256_reason

    h = _keccak256_reason("any reason")
    assert h.startswith("0x")
    # 32 bytes = 64 hex chars
    assert len(h) == 2 + 64


@pytest.mark.parametrize("timeout", [0.0, -1.0, 121.0, float("nan"), float("inf")])
def test_benchmark_rejects_unbounded_timeout(timeout: float) -> None:
    from sentinel.bazantic.benchmark_ab import run_agent

    with pytest.raises(ValueError, match="timeout"):
        run_agent("http://127.0.0.1:11434", "unused", "", timeout)
