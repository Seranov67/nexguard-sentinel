"""EG-3 regression tests exercise failure boundaries, not just happy-path mocks."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from sentinel.actuator import Actuator, build_pause_calldata
from sentinel.classifier import ClassificationResult
from sentinel.config import Settings
from sentinel.loop import run_loop_step
from sentinel.policy import ActionPolicy
from sentinel.proof import incident_proof
from sentinel.store import StateStore

GUARDIAN = "0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3"
TX = "0x" + "ab" * 32
BLOCK = "0x" + "cd" * 32


def reserved(tmp_path: Path) -> tuple[StateStore, Actuator]:
    store = StateStore(tmp_path / "state.db")
    store.ingest("vault-withdrawals", "e1", 1, 1, "{}")
    store.reserve("i1", "incident", ["e1"])
    store.prepare("i1", 4, "{}")
    store.broadcast("i1", TX)
    return store, Actuator(store, "https://example.org", GUARDIAN, confirmations=3)


@pytest.mark.parametrize("fault", ["none", "timeout", "depth", "reorg", "state", "chain", "revert"])
def test_receipt_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    store, actuator = reserved(tmp_path)
    methods: list[str] = []

    def rpc(method: str, params: list[Any]) -> Any:
        methods.append(method)
        if method == "eth_chainId":
            return "0x1" if fault == "chain" else hex(84532)
        if method == "eth_getCode":
            return "0x1234"
        if method == "eth_getTransactionReceipt":
            return (
                None
                if fault == "timeout"
                else {
                    "transactionHash": TX,
                    "to": GUARDIAN,
                    "blockNumber": hex(100),
                    "blockHash": BLOCK,
                    "status": "0x0" if fault == "revert" else "0x1",
                }
            )
        if method == "eth_getBlockByNumber":
            return {"hash": "different" if fault == "reorg" else BLOCK}
        if method == "eth_blockNumber":
            return hex(100 if fault == "depth" else 103)
        if method == "eth_call":
            return "0x" + ("0" * 64 if fault == "state" else "0" * 63 + "1")
        if method == "eth_getTransactionByHash":
            return {"to": GUARDIAN, "nonce": "0x4", "input": build_pause_calldata("incident", 3)}
        raise AssertionError(method)

    monkeypatch.setattr(actuator, "_rpc_call", rpc)
    monkeypatch.setattr("sentinel.actuator.time.sleep", lambda _: None)
    result = actuator.reconcile("i1")
    expected = (
        "success" if fault == "none" else "reverted" if fault == "revert" else "indeterminate"
    )
    assert result.outcome == expected
    assert store.is_latched() == (expected == "indeterminate")
    assert "eth_sendRawTransaction" not in methods


def test_cooldown_survives_new_policy_and_restart(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    for i in (1, 2):
        store.ingest("vault", f"e{i}", i, i, "{}")
    critical = ClassificationResult("critical", "pause", 0.95, "anomaly")
    decision = ActionPolicy(store).evaluate_and_reserve(critical, ["e1"], current_time=1000)
    store.finish(decision.intent_id, "already_desired", "already paused")
    reopened = StateStore(store.path)
    again = ActionPolicy(reopened).evaluate_and_reserve(critical, ["e2"], current_time=1100)
    assert again.status == "cooldown_active"


def test_crash_after_ingest_is_processed_on_restart(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = StateStore(tmp_path / "state.db")
    event = {
        "id": "e1",
        "sequence": "1",
        "blockNumber": 100,
        "amount": "1",
        "timestamp": 1000,
        "who": "actor",
    }
    store.ingest("vault-withdrawals", "e1", 1, 100, json.dumps(event, sort_keys=True))
    settings = Settings(
        "https://example.org", "https://example.org", GUARDIAN, GUARDIAN, store.path
    )
    monkeypatch.setattr("sentinel.loop.ingest_live", lambda *args: 0)
    result = run_loop_step(
        settings,
        StateStore(store.path),
        keeper_private_key="unused",
        llm_evaluator=lambda _: json.dumps(
            {
                "severity": "info",
                "recommended_action": "none",
                "confidence": 1.0,
                "rationale": "Normal activity",
            }
        ),
    )
    assert result.new_events == 1
    assert store.pending_events("vault-withdrawals") == []
    assert run_loop_step(settings, store, keeper_private_key="unused").new_events == 0


def test_signed_hash_survives_lost_broadcast_reply(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from eth_account import Account

    store = StateStore(tmp_path / "state.db")
    store.ingest("vault", "e1", 1, 1, "{}")
    store.reserve("i1", "incident", ["e1"])
    actuator = Actuator(
        store,
        "https://example.org",
        GUARDIAN,
        keeper_private_key=Account.create().key.hex(),
    )
    calls = 0

    def rpc(method: str, params: list[Any]) -> Any:
        nonlocal calls
        if method == "eth_chainId":
            return hex(84532)
        if method == "eth_getCode":
            return "0x1234"
        if method == "eth_call":
            return "0x" + "0" * 64
        if method in ("eth_getTransactionCount", "eth_gasPrice"):
            return "0x1"
        if method == "eth_sendRawTransaction":
            calls += 1
            record = store.intent("i1")
            assert record is not None and record["tx_hash"] is not None
            raise RuntimeError("Lost broadcast reply")
        raise AssertionError(method)

    monkeypatch.setattr(actuator, "_rpc_call", rpc)
    result = actuator.execute_pause("i1", "incident")
    assert calls == 1
    assert result.outcome == "indeterminate"
    assert result.tx_hash is not None
    reopened = StateStore(store.path)
    assert reopened.is_latched()
    assert not reopened.reserve("i2", "incident2", ["e1"])


def test_canonical_proof_golden() -> None:
    payload, reference = incident_proof(84532, "0x" + "12" * 20, ["b", "a"])
    golden = (
        '{"action":"pause","chain_id":84532,"event_ids":["a","b"],'
        '"guardian":"0x1212121212121212121212121212121212121212","version":1}'
    )
    assert payload == golden
    assert reference == "0x" + hashlib.sha256(golden.encode("ascii")).hexdigest()
