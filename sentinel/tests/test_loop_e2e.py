"""End-to-end integration tests for Sentinel loop, Actuator, and CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinel.actuator import Actuator, build_pause_calldata
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


def test_actuator_simulated_execution_flow(test_env: tuple[Settings, StateStore]) -> None:
    settings, store = test_env
    # Ingest event so foreign keys work
    store.ingest("source", "ev-1", 1, 100, "{}")
    store.reserve("intent-1", "inc-1", ["ev-1"])

    actuator = Actuator(
        store=store,
        rpc_http=settings.rpc_http,
        guardian_address=settings.guardian_address,
        chain_id=settings.chain_id,
    )
    result = actuator.execute_pause("intent-1", "inc-1", severity=2, dry_run=True)

    assert result.outcome == "success"
    assert result.tx_hash is not None
    assert result.tx_hash.startswith("0x")
    assert len(result.tx_hash) == 66
    # Verify intent updated in store
    intent = store.intent("intent-1")
    assert intent is not None
    assert intent["status"] == "success"
    assert intent["tx_hash"] == result.tx_hash


def test_loop_step_with_empty_events(test_env: tuple[Settings, StateStore]) -> None:
    settings, store = test_env
    result = run_loop_step(settings, store, events_override=[], dry_run=True)
    assert result.events_polled == 0
    assert result.new_events == 0
    assert result.is_latched is False
    assert result.decision is None


def test_loop_step_with_critical_events_triggers_pause(
    test_env: tuple[Settings, StateStore],
) -> None:
    settings, store = test_env
    critical_events = [
        {
            "id": "0xaaa-1",
            "sequence": "100",
            "blockNumber": 500,
            "amount": "5000000000000000000",  # 5 ETH
            "who": "0xAttacker",
            "timestamp": 1000,
        },
        {
            "id": "0xaaa-2",
            "sequence": "101",
            "blockNumber": 501,
            "amount": "6000000000000000000",  # 6 ETH -> Total 11 ETH (catastrophic)
            "who": "0xAttacker",
            "timestamp": 1010,
        },
    ]
    result = run_loop_step(settings, store, events_override=critical_events, dry_run=True)

    assert result.events_polled == 2
    assert result.classification is not None
    assert result.classification.severity == "critical"
    assert result.decision is not None
    assert result.decision.allowed is True
    assert result.execution is not None
    assert result.execution.outcome == "success"
    assert result.execution.tx_hash is not None
    assert result.cursor_advanced is True

    # Verify cursor was advanced in store
    cursor = store.cursor("the_graph_withdrawals")
    assert cursor is not None
    assert cursor[0] == 101


def test_loop_step_blocks_duplicate_event_reservation(
    test_env: tuple[Settings, StateStore],
) -> None:
    settings, store = test_env
    event = [
        {
            "id": "0xbbb-1",
            "sequence": "200",
            "blockNumber": 600,
            "amount": "15000000000000000000",
            "who": "0xAttacker",
            "timestamp": 2000,
        }
    ]
    # First pass runs pause
    r1 = run_loop_step(settings, store, events_override=event, dry_run=True)
    assert r1.execution is not None
    assert r1.execution.outcome == "success"

    # Second pass with same event will fail reservation (already reserved)
    r2 = run_loop_step(settings, store, events_override=event, dry_run=True)
    assert r2.decision is not None
    assert r2.decision.allowed is False
    assert r2.decision.status == "reservation_failed"


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
