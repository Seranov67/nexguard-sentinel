"""Unit tests for deterministic ActionPolicy constraints and durable reservations."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinel.classifier import ClassificationResult
from sentinel.policy import ActionPolicy
from sentinel.store import StateStore


@pytest.fixture()
def store(tmp_path: Path) -> StateStore:
    db_path = tmp_path / "test_policy.db"
    s = StateStore(db_path)
    # Ingest dummy events so intent_events foreign key is satisfied
    s.ingest("source", "ev-1", 1, 100, "{}")
    s.ingest("source", "ev-2", 2, 101, "{}")
    return s


def _critical_classification() -> ClassificationResult:
    return ClassificationResult(
        severity="critical",
        recommended_action="pause",
        confidence=0.95,
        rationale="Critical rate of withdrawals detected.",
    )


def test_policy_allowed_and_reserved(store: StateStore) -> None:
    policy = ActionPolicy(store, cooldown_seconds=60)
    cls = _critical_classification()
    decision = policy.evaluate_and_reserve(cls, ["ev-1", "ev-2"])

    assert decision.allowed is True
    assert decision.status == "allowed"
    assert decision.intent_id.startswith("intent_pause_")
    # Verify reservation exists in store
    intent = store.intent(decision.intent_id)
    assert intent is not None
    assert intent["status"] == "reserved"


def test_policy_blocks_when_latched(store: StateStore) -> None:
    # Force latch
    store.reserve("intent-old", "inc-old", ["ev-1"])
    store.prepare("intent-old", 1, "{}")
    store.broadcast("intent-old", "0x" + "aa" * 32)
    store.finish("intent-old", "indeterminate", "Emergency latch test")
    assert store.is_latched() is True

    policy = ActionPolicy(store)
    cls = _critical_classification()
    decision = policy.evaluate_and_reserve(cls, ["ev-2"])

    assert decision.allowed is False
    assert decision.status == "latched"


def test_policy_blocks_low_severity(store: StateStore) -> None:
    policy = ActionPolicy(store)
    low_cls = ClassificationResult(
        severity="warning",
        recommended_action="notify",
        confidence=0.9,
        rationale="Moderate traffic.",
    )
    decision = policy.evaluate_and_reserve(low_cls, ["ev-1"])
    assert decision.allowed is False
    assert decision.status == "low_severity"


def test_policy_cooldown_active(store: StateStore) -> None:
    policy = ActionPolicy(store, cooldown_seconds=300)
    cls = _critical_classification()

    # First action allowed
    d1 = policy.evaluate_and_reserve(cls, ["ev-1"], current_time=1000.0)
    assert d1.allowed is True
    # Mark first intent finished so store allows subsequent intent
    store.prepare(d1.intent_id, 0, "{}")
    store.broadcast(d1.intent_id, "0x" + "11" * 32)
    store.finish(d1.intent_id, "success", "first action completed")

    # Ingest new event for second action
    store.ingest("source", "ev-3", 3, 102, "{}")

    # Second action within 300s window rejected by cooldown
    d2 = policy.evaluate_and_reserve(cls, ["ev-3"], current_time=1100.0)
    assert d2.allowed is False
    assert d2.status == "cooldown_active"

    # Catastrophic override bypasses cooldown
    cat_cls = ClassificationResult(
        severity="critical",
        recommended_action="pause",
        confidence=1.0,
        rationale="Catastrophic override",
        is_catastrophic_override=True,
    )
    d3 = policy.evaluate_and_reserve(cat_cls, ["ev-3"], current_time=1100.0)
    assert d3.allowed is True


def test_policy_already_in_desired_state(store: StateStore) -> None:
    # Reader returns True (already paused)
    policy = ActionPolicy(store, onchain_state_reader=lambda: True)
    cls = _critical_classification()
    decision = policy.evaluate_and_reserve(cls, ["ev-1"])

    assert decision.allowed is False
    assert decision.status == "already_in_desired_state"


def test_policy_reset_latch(store: StateStore) -> None:
    # Latch the store
    store.reserve("intent-old", "inc-old", ["ev-1"])
    store.prepare("intent-old", 1, "{}")
    store.broadcast("intent-old", "0x" + "aa" * 32)
    store.finish("intent-old", "indeterminate", "Emergency latch test")
    assert store.is_latched() is True

    # Reconcile indeterminate intent and reset latch
    store.finish("intent-old", "reverted", "Operator verified tx dropped/reverted onchain")
    store.reset_latch("operator_alice", "Resolved onchain state check")
    assert store.is_latched() is False

    # Now action can proceed
    policy = ActionPolicy(store)
    cls = _critical_classification()
    decision = policy.evaluate_and_reserve(cls, ["ev-2"])
    assert decision.allowed is True
