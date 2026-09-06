"""End-to-end integration tests for Sentinel loop, Actuator, and CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinel.actuator import build_pause_calldata
from sentinel.cli import cmd_reset, cmd_status
from sentinel.config import Settings
from sentinel.loop import run_loop_step
from sentinel.store import StateStore


@pytest.fixture()
def test_env(tmp_path: Path) -> tuple[Settings, StateStore]:
    db_path = tmp_path / "test_loop.db"
    store = StateStore(db_path)
    settings = Settings(
        rpc_http="http://127.0.0.1:8545",
        subgraph_url="https://api.studio.thegraph.com/query/test/subgraph",
        guardian_address="0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3",
        vault_address="0x4F12f20Cae514dD0f666f2C015797305dE75e533",
        state_path=db_path,
        chain_id=84532,
        confirmations=2,
        rewind_blocks=2,
    )
    return settings, store


def test_actuator_calldata_format() -> None:
    calldata = build_pause_calldata("incident_1234567890abcdef", severity=2)
    assert calldata.startswith("0xeb63b014")
    # 4-byte selector (8 chars) + 32-byte ref (64 chars) + 32-byte severity (64 chars) = 136 + 2
    assert len(calldata) == 2 + 8 + 64 + 64


def test_dry_run_never_changes_live_state(test_env: tuple[Settings, StateStore]) -> None:
    settings, store = test_env
    event = {
        "id": "e1",
        "sequence": "1",
        "blockNumber": 100,
        "amount": str(25 * 10**18),
        "timestamp": 1000,
        "who": "actor",
    }
    result = run_loop_step(settings, store, events_override=[event], dry_run=True)
    assert result.classification is not None
    assert result.execution is None
    assert store.cursor("vault-withdrawals") is None
    assert store.unfinished() == []


def test_missing_key_never_means_simulation(test_env: tuple[Settings, StateStore]) -> None:
    settings, store = test_env
    with pytest.raises(ValueError, match="keeper key"):
        run_loop_step(settings, store, events_override=[])


def test_cli_status_and_reset(
    test_env: tuple[Settings, StateStore], capsys: pytest.CaptureFixture[str]
) -> None:
    settings, store = test_env
    # Call status on empty store
    cmd_status(settings, store)
    out = capsys.readouterr().out
    assert "NexGuard Sentinel" in out
    assert "Base Sepolia" in out
    assert "[NORMAL]" in out

    # Latch store and verify status reports latched
    store.ingest("source", "ev-latch", 1, 100, "{}")
    store.reserve("intent-latch", "inc-latch", ["ev-latch"])
    store.prepare("intent-latch", 1, "{}")
    store.broadcast("intent-latch", "0x" + "b" * 64)
    store.finish("intent-latch", "indeterminate", "Emergency latch reason")

    cmd_status(settings, store)
    out_latched = capsys.readouterr().out
    assert "[LATCHED]" in out_latched

    # Reset latch via CLI
    cmd_reset(store, "operator_bob", "Verification completed onchain")
    out_reset = capsys.readouterr().out
    assert "successfully reset" in out_reset
    assert store.is_latched() is False
