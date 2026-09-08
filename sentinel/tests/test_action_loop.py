import json
import sqlite3
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest

from sentinel.__main__ import main
from sentinel.executor import Executor, Receipt, SignedPause
from sentinel.models import Proposal, Withdrawal, canonical_incident, incident_ref
from sentinel.policy import Policy
from sentinel.store import StateStore

GUARDIAN = "0x" + "11" * 20
VAULT = "0x" + "22" * 20
BLOCK = "0x" + "33" * 32
TX = "0x" + "44" * 32
PROPOSAL = Proposal("critical", "pause", 0.95, "Structured drain signal")


def event(index: int = 0, block: int = 100) -> Withdrawal:
    tx = "0x" + "55" * 32
    return Withdrawal(
        tx + index.to_bytes(4, "little").hex(),
        block * 1_000_000 + index,
        block,
        BLOCK,
        tx,
        index,
        1_700_000_000,
        "0x" + "66" * 20,
        10**18,
    )


class FakeChain:
    def __init__(self, store: StateStore) -> None:
        self.store = store
        self.signs = 0
        self.sends = 0
        self.chain = 84532
        self.height = 105
        self.current_paused = False
        self.final_paused = True
        self.receipt_status = 1
        self.receipt_hash = BLOCK
        self.return_receipt = True
        self.send_error = False
        self.ref: str | None = None
        self.receipt_ref: str | None = None
        self.sign_hook: Callable[[], object] | None = None
        self.send_hook: Callable[[], object] | None = None

    def identity(self) -> tuple[int, str, str]:
        return self.chain, GUARDIAN, VAULT

    def head(self) -> int:
        return self.height

    def block_hash(self, block: int) -> str:
        return BLOCK

    def paused(self, block: int | None = None) -> bool:
        return self.current_paused if block is None else self.final_paused

    def sign_pause(self, ref: str, severity: int) -> SignedPause:
        intent = self.store.intent(ref)
        assert intent is not None and intent["status"] == "reserved"
        assert severity == 3
        self.ref = ref
        self.signs += 1
        if self.sign_hook:
            self.sign_hook()
        return SignedPause(7, '{"maxFeePerGas":100}', TX, b"signed-pause")

    def send(self, signed: SignedPause) -> str:
        assert self.ref is not None
        row = self.store.intent(self.ref)
        assert row is not None
        assert row["nonce"] == 7 and row["tx_hash"] == TX and row["status"] == "prepared"
        self.sends += 1
        if self.send_hook:
            self.send_hook()
        if self.send_error:
            raise TimeoutError("Network did not return a hash")
        return TX

    def receipt(self, tx_hash: str) -> Receipt | None:
        assert tx_hash == TX
        if not self.return_receipt:
            return None
        return Receipt(
            TX, 102, self.receipt_hash, self.receipt_status, self.receipt_ref or self.ref, 3
        )


def test_verified_pause_and_replay_have_one_send(setup: Any) -> None:
    _, store, chain, executor, ev = setup
    ref = executor.act([ev], PROPOSAL)
    intent = store.intent(ref)
    assert intent is not None and intent["status"] == "success"
    assert store.proof(ref).encode() == canonical_incident([ev], GUARDIAN)
    assert executor.act([ev], PROPOSAL) is None
    assert chain.signs == chain.sends == 1
    assert store.pending_events(f"84532:{VAULT}") == []


def test_concurrent_executors_have_one_signer(setup: Any) -> None:
    settings, store, chain, _, ev = setup
    executors = [
        Executor(settings, StateStore(store.path), chain, Policy(GUARDIAN, VAULT), timeout=0)
        for _ in range(8)
    ]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda executor: executor.act([ev], PROPOSAL), executors))
    assert sum(value is not None for value in results) == 1
    assert chain.sends == chain.signs == 1


@pytest.mark.parametrize(
    "proposal",
    [
        Proposal("critical", "unpause", 1, "deny"),
        Proposal("warning", "pause", 1, "deny"),
        Proposal("critical", "pause", 0.79, "deny"),
        Proposal("critical", "pause", float("nan"), "deny"),
        Proposal("critical", "pause", 1, "x" * 241),
    ],
)
def test_policy_rejects_without_signer(setup: Any, proposal: Proposal) -> None:
    _, store, chain, executor, ev = setup
    assert executor.act([ev], proposal) is None
    assert chain.signs == 0 and store.unfinished() == []


def test_wrong_chain_and_wrong_contract_never_sign(setup: Any) -> None:
    _, _, chain, executor, ev = setup
    chain.chain = 1
    assert executor.act([ev], PROPOSAL) is None
    chain.chain = 84532
    executor.policy = Policy("0x" + "ab" * 20, VAULT)
    assert executor.act([ev], PROPOSAL) is None
    assert chain.signs == chain.sends == 0


def test_already_desired_needs_no_signer(setup: Any) -> None:
    _, store, chain, executor, ev = setup
    chain.current_paused = True
    ref = executor.act([ev], PROPOSAL)
    intent = store.intent(ref)
    assert intent is not None and intent["status"] == "already_desired"
    assert chain.signs == chain.sends == 0


def test_revert_is_distinct_from_success(setup: Any) -> None:
    _, store, chain, executor, ev = setup
    chain.receipt_status = 0
    chain.final_paused = False
    ref = executor.act([ev], PROPOSAL)
    intent = store.intent(ref)
    assert intent is not None and intent["status"] == "reverted"
    assert not store.is_latched()


@pytest.mark.parametrize(
    "field,value",
    [
        ("final_paused", False),
        ("receipt_hash", "0x" + "aa" * 32),
        ("receipt_ref", "0x" + "bb" * 32),
        ("receipt_status", 7),
    ],
)
def test_bad_verification_latches(setup: Any, field: str, value: object) -> None:
    _, store, chain, executor, ev = setup
    setattr(chain, field, value)
    with pytest.raises(ValueError):
        executor.act([ev], PROPOSAL)
    assert store.is_latched()
    intent = store.intent(chain.ref)
    assert intent is not None and intent["status"] == "indeterminate"
    assert executor.act([ev], PROPOSAL) is None
    assert chain.sends == 1


@pytest.mark.parametrize("missing", [True, False])
def test_receipt_or_confirmation_timeout_then_reconciliation(setup: Any, missing: bool) -> None:
    settings, store, chain, executor, ev = setup
    chain.return_receipt = not missing
    chain.height = 102
    ref = executor.act([ev], PROPOSAL)
    intent = store.intent(ref)
    assert intent is not None and intent["status"] == "indeterminate"
    assert store.is_latched()
    with pytest.raises(ValueError, match="Reconcile"):
        store.reset_latch("operator", "not yet known")
    chain.return_receipt = True
    chain.height = 105
    reopened = StateStore(store.path)
    recovered = Executor(settings, reopened, chain, executor.policy, timeout=0)
    assert recovered.reconcile(ref) == "success"
    assert reopened.is_latched()
    reopened.reset_latch("operator", "verified transaction and pause state")
    assert not reopened.is_latched() and chain.sends == 1


def test_crash_between_send_and_hash_response_can_reconcile(setup: Any) -> None:
    settings, store, chain, executor, ev = setup
    chain.send_error = True
    with pytest.raises(TimeoutError):
        executor.act([ev], PROPOSAL)
    ref = chain.ref
    reopened = StateStore(store.path)
    intent = reopened.intent(ref)
    assert intent is not None and intent["tx_hash"] == TX
    Executor(settings, reopened, chain, executor.policy).recover_startup()
    intent = reopened.intent(ref)
    assert intent is not None and intent["status"] == "success"
    assert reopened.is_latched() and chain.sends == 1


def test_process_death_after_broadcast_before_store_update(setup: Any) -> None:
    settings, store, chain, executor, ev = setup
    chain.send_hook = lambda: (_ for _ in ()).throw(SystemExit(17))
    with pytest.raises(SystemExit):
        executor.act([ev], PROPOSAL)
    intent = store.intent(chain.ref)
    assert intent is not None and intent["status"] == "prepared"
    reopened = StateStore(store.path)
    Executor(settings, reopened, chain, executor.policy).recover_startup()
    intent = reopened.intent(chain.ref)
    assert intent is not None and intent["status"] == "success"
    assert chain.sends == 1 and reopened.is_latched()


def test_crash_after_reservation_without_hash_never_resends(setup: Any) -> None:
    settings, store, chain, executor, ev = setup
    chain.sign_hook = lambda: (_ for _ in ()).throw(SystemExit(17))
    with pytest.raises(SystemExit):
        executor.act([ev], PROPOSAL)
    reopened = StateStore(store.path)
    Executor(settings, reopened, chain, executor.policy).recover_startup()
    intent = reopened.intent(chain.ref)
    assert intent is not None and intent["status"] == "indeterminate"
    assert reopened.is_latched() and chain.sends == 0


def test_storage_failure_before_send_prevents_broadcast(setup: Any) -> None:
    _, store, chain, executor, ev = setup
    with sqlite3.connect(store.path) as db:
        db.execute(
            "CREATE TRIGGER fail_prepare BEFORE UPDATE ON intents "
            "WHEN NEW.status='prepared' BEGIN SELECT RAISE(ABORT,'disk failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError):
        executor.act([ev], PROPOSAL)
    assert chain.sends == 0 and store.is_latched()


def test_storage_failure_after_send_preserves_hash_and_blocks_retry(setup: Any) -> None:
    _, store, chain, executor, ev = setup
    with sqlite3.connect(store.path) as db:
        db.execute(
            "CREATE TRIGGER fail_broadcast BEFORE UPDATE ON intents "
            "WHEN NEW.status='broadcast' BEGIN SELECT RAISE(ABORT,'disk failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError):
        executor.act([ev], PROPOSAL)
    intent = store.intent(chain.ref)
    assert intent is not None and intent["tx_hash"] == TX
    assert store.is_latched() and chain.sends == 1
    assert executor.act([ev], PROPOSAL) is None


def test_identity_change_after_signing_prevents_send(setup: Any) -> None:
    _, store, chain, executor, ev = setup
    chain.sign_hook = lambda: setattr(chain, "chain", 1)
    with pytest.raises(ValueError, match="Identity"):
        executor.act([ev], PROPOSAL)
    assert chain.sends == 0 and store.is_latched()


def test_cooldown_budget_and_clock_rollback_survive_restart(setup: Any) -> None:
    settings, store, chain, executor, ev = setup
    ref = executor.act([ev], PROPOSAL)
    new_event = event(1)
    store.ingest(
        f"84532:{VAULT}", new_event.id, new_event.sequence, new_event.block, new_event.payload()
    )
    reopened = StateStore(store.path)
    recovered = Executor(settings, reopened, chain, executor.policy, timeout=0)
    for age in (10, 301, -100):
        with sqlite3.connect(store.path) as db:
            db.execute(
                "UPDATE intents SET created_at=? WHERE id=?",
                ((datetime.now(UTC) - timedelta(seconds=age)).isoformat(), ref),
            )
        assert recovered.act([new_event], PROPOSAL) is None
    assert chain.sends == 1
    with sqlite3.connect(store.path) as db:
        db.execute(
            "UPDATE intents SET created_at=? WHERE id=?",
            ((datetime.now(UTC) - timedelta(seconds=3601)).isoformat(), ref),
        )
    assert recovered.act([new_event], PROPOSAL) is not None
    assert chain.sends == 2


def test_unknown_or_modified_source_event_is_not_authorized(setup: Any) -> None:
    _, _, chain, executor, ev = setup
    with pytest.raises(ValueError, match="persisted Graph"):
        executor.act([replace(ev, amount=ev.amount + 1)], PROPOSAL)
    assert chain.signs == 0


def test_cli_status_reset_audit_and_no_unpause(setup: Any, capsys: Any) -> None:
    _, store, _, _, _ = setup
    store.set_latch("manual inspection")
    assert main(["--state", str(store.path), "status"]) == 0
    assert json.loads(capsys.readouterr().out)["latch"] == "manual inspection"
    assert main(["--state", str(store.path), "reset", "--operator", " ", "--reason", "x"]) == 1
    assert store.is_latched()
    assert (
        main(["--state", str(store.path), "reset", "--operator", "owner", "--reason", "verified"])
        == 0
    )
    with sqlite3.connect(store.path) as db:
        detail = db.execute(
            "SELECT detail FROM audit WHERE transition='operator_reset'"
        ).fetchone()[0]
    assert json.loads(detail) == {"operator": "owner", "reason": "verified"}
    with pytest.raises(SystemExit):
        main(["unpause"])


def test_reorg_during_final_state_read_latches(setup: Any) -> None:
    _, store, chain, executor, ev = setup
    original = chain.paused

    def paused(block: int | None = None) -> bool:
        if block is not None:
            chain.block_hash = lambda height: "0x" + "ab" * 32
        return cast(bool, original(block))

    chain.paused = paused
    with pytest.raises(ValueError, match="Chain changed"):
        executor.act([ev], PROPOSAL)
    assert store.is_latched() and chain.sends == 1


def test_total_storage_failure_keeps_unfinished_reservation_as_safety_barrier(
    setup: Any,
) -> None:
    _, store, chain, executor, ev = setup
    with sqlite3.connect(store.path) as db:
        db.execute(
            "CREATE TRIGGER fail_write BEFORE UPDATE ON intents "
            "BEGIN SELECT RAISE(ABORT,'disk failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError):
        executor.act([ev], PROPOSAL)
    intent = store.intent(chain.ref)
    assert intent is not None and intent["status"] == "reserved"
    assert executor.act([ev], PROPOSAL) is None
    assert chain.sends == 0


def test_schema_v1_upgrade_preserves_existing_state(setup: Any) -> None:
    _, store, _, _, ev = setup
    with sqlite3.connect(store.path) as db:
        db.execute("DROP TABLE proofs")
        db.execute("PRAGMA user_version=1")
    reopened = StateStore(store.path)
    assert reopened.pending_events(f"84532:{VAULT}") == [ev]
    with sqlite3.connect(store.path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2


def test_process_exit_after_send_has_durable_signed_hash(setup: Any) -> None:
    import subprocess
    import sys

    settings, store, chain, executor, ev = setup
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import os, sys
from pathlib import Path
from sentinel.config import Settings
from sentinel.store import StateStore
from sentinel.executor import Executor
from sentinel.policy import Policy
from sentinel.tests.test_action_loop import FakeChain, GUARDIAN, VAULT, PROPOSAL, event
store = StateStore(Path(sys.argv[1]))
settings = Settings('https://rpc.example', 'https://graph.example', GUARDIAN, VAULT, store.path)
chain = FakeChain(store)
chain.send_hook = lambda: os._exit(17)
Executor(settings, store, chain, Policy(GUARDIAN, VAULT)).act([event()], PROPOSAL)
""",
            str(store.path),
        ],
        check=False,
    )
    assert result.returncode == 17
    ref = incident_ref(canonical_incident([ev], GUARDIAN))
    reopened = StateStore(store.path)
    intent = reopened.intent(ref)
    assert intent is not None and intent["status"] == "prepared"
    assert intent["tx_hash"] == TX
    chain.ref = ref
    Executor(settings, reopened, chain, executor.policy).recover_startup()
    intent = reopened.intent(ref)
    assert intent is not None and intent["status"] == "success"
    assert reopened.is_latched() and chain.sends == 0
