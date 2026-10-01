import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from sentinel.review.models import Decision
from sentinel.review.store import ReviewConflictError, ReviewStore
from sentinel.store import StateStore


def observation(amount: Any = "101", index: Any = 0) -> dict[str, Any]:
    tx = "0x" + "12" * 32
    raw = {
        "id": tx + index.to_bytes(4, "little").hex(),
        "sequence": str(100_000_000 + index),
        "blockNumber": "100",
        "blockHash": "0x" + "34" * 32,
        "transactionHash": tx,
        "logIndex": str(index),
        "timestamp": "1788625242",
        "who": "0x" + "56" * 20,
        "amount": amount,
    }
    return {"raw": raw, "proof": {"receipt_status": 1}, "origin": "synthetic_fixture"}


def make_case(store: ReviewStore) -> str:
    row = observation()
    store.ingest([row])
    policy = store.register_policy({"version": "v1", "threshold": "100"})
    store.evaluated(row["raw"]["id"], policy, {"breached": True, "case_id": "case1"})
    return "case1"


def decision(
    action: Any = "acknowledge", revision: Any = 0, request_id: Any = "request_1", **kwargs: Any
) -> Decision:
    return Decision(
        action=action,
        revision=revision,
        request_id=request_id,
        operator="local operator",
        note=kwargs.pop("note", "reviewed evidence"),
        **kwargs,
    )


def test_restart_replay_and_unhandled_evaluation(tmp_path: Path) -> None:
    path = tmp_path / "review.sqlite3"
    store = ReviewStore(path)
    row = observation()
    assert store.ingest([row]) == 1
    policy = store.register_policy({"version": "v1", "threshold": "100"})
    reopened = ReviewStore(path)
    assert len(reopened.pending(policy)) == 1
    assert reopened.ingest([row]) == 0
    reopened.evaluated(row["raw"]["id"], policy, {"breached": True, "case_id": "case1"})
    assert not ReviewStore(path).pending(policy)
    assert len(store.cases()) == 1


def test_page_rollback_preserves_conflict(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    store.ingest([observation()])
    with pytest.raises(ReviewConflictError):
        store.ingest([observation(index=1), observation(amount="102")])
    assert store.counts()["observations"] == 1
    assert store.counts()["conflicts"] == 1
    assert store.cursor() == (100_000_000, 100)


def test_invalid_page_rolls_back(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    invalid = observation(index=1)
    invalid["raw"]["sequence"] = "1"
    with pytest.raises(ValueError):
        store.ingest([observation(), invalid])
    assert store.counts()["observations"] == 0


def test_legacy_database_rejected_without_mutation(tmp_path: Path) -> None:
    legacy = StateStore(tmp_path / "state.sqlite3")
    before = hashlib.sha256(legacy.path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="legacy"):
        ReviewStore(legacy.path)
    assert hashlib.sha256(legacy.path.read_bytes()).hexdigest() == before
    review = ReviewStore(tmp_path / "review.sqlite3")
    make_case(review)
    assert legacy.cursor("source") is None
    with legacy._connection() as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM intents").fetchone()[0] == 0


def test_transaction_rollback(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    with pytest.raises(RuntimeError), store.transaction() as db:
        db.execute("INSERT INTO metadata VALUES('test','{}')")
        raise RuntimeError("simulated crash")
    assert store.metadata("test") is None


def test_policy_version_and_source_are_immutable(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    store.bind({"origin": "fixture"})
    with pytest.raises(ReviewConflictError):
        store.bind({"origin": "live"})
    store.register_policy({"version": "v1", "threshold": "100"})
    with pytest.raises(ReviewConflictError):
        store.register_policy({"version": "v1", "threshold": "200"})


def test_decisions_restart_idempotency_and_revision(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    case_id = make_case(store)
    ack = decision()
    result = store.decide(case_id, ack)
    assert store.decide(case_id, ack) == result
    with pytest.raises(ReviewConflictError):
        store.decide(case_id, decision(request_id="request_2"))
    store = ReviewStore(store.path)
    resolved = store.decide(
        case_id, decision("resolve", 1, "request_3", disposition="policy_breach")
    )
    assert resolved["new_revision"] == 2
    assert store.decide(case_id, ack) == result
    assert len(store.detail(case_id)["history"]) == 2
    with pytest.raises(ReviewConflictError):
        store.decide(case_id, decision("resolve", 2, "request_4", disposition="expected_activity"))
    with pytest.raises(ReviewConflictError):
        store.decide(case_id, decision(request_id="request_1", note="changed"))


def test_competing_updates_have_one_winner(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    case_id = make_case(store)

    def update(index: Any) -> str:
        try:
            store.decide(case_id, decision(request_id=f"request_{index}"))
            return "accepted"
        except ReviewConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(update, [1, 2])) == ["accepted", "conflict"]
    assert len(store.detail(case_id)["history"]) == 1


def test_conflicted_case_cannot_be_confirmed(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    make_case(store)
    with pytest.raises(ReviewConflictError):
        store.ingest([observation(amount="102")])
    store.decide("case1", decision())
    with pytest.raises(ReviewConflictError):
        store.decide("case1", decision("resolve", 1, "request_2", disposition="policy_breach"))
    store.decide("case1", decision("resolve", 1, "request_3", disposition="insufficient_evidence"))
    assert store.detail("case1")["conflicts"]
