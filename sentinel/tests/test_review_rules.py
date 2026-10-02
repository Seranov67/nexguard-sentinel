import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sentinel.review.evidence import source_status
from sentinel.review.rules import ReviewPolicy, process_pending
from sentinel.review.store import ReviewConflictError, ReviewStore
from sentinel.tests.test_review_store import observation


@pytest.mark.parametrize("amount,breached", [("99", False), ("100", False), ("101", True)])
def test_exact_integer_boundary(amount: str, breached: bool) -> None:
    policy = ReviewPolicy(version="v1", withdrawal_limit="100")
    finding = policy.evaluate(observation(amount))
    assert finding["breached"] is breached
    assert finding["observed_amount"] == amount
    assert finding["authorization"] == "review_only"
    assert finding["synthetic"] is True


@pytest.mark.parametrize("limit", [-1, True, 1.5, "-1", "1e18", "01", str(2**256)])
def test_invalid_policy_is_rejected(limit: Any) -> None:
    with pytest.raises(ValidationError):
        ReviewPolicy(version="v1", withdrawal_limit=limit)


def test_uint256_precision_and_stable_policy_identity() -> None:
    large = str(2**255 + 1)
    policy = ReviewPolicy(version="v1", withdrawal_limit=str(2**255))
    a = policy.evaluate(observation(large))
    b = policy.evaluate(observation(large))
    assert a["observed_amount"] == large
    assert a["case_id"] == b["case_id"]
    other = ReviewPolicy(version="v2", withdrawal_limit=str(2**255)).evaluate(observation(large))
    assert a["case_id"] != other["case_id"]


def test_unverified_live_source_cannot_be_classified() -> None:
    row = observation()
    row["origin"] = "live_graph_rpc"
    with pytest.raises(ValueError, match="Confirmed source"):
        ReviewPolicy(version="v1", withdrawal_limit="100").evaluate(row)


def test_crash_after_ingestion_then_restart_evaluates_once(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    store.ingest([observation(), observation("10", 1)])
    store.health({"status": "synthetic"})
    policy = ReviewPolicy(version="v1", withdrawal_limit="100")
    assert process_pending(ReviewStore(store.path), policy, limit=1) == 1
    assert process_pending(ReviewStore(store.path), policy) == 1
    assert process_pending(ReviewStore(store.path), policy) == 0
    assert store.counts()["review_cases"] == 1
    assert store.counts()["evaluations"] == 2


def test_degraded_source_does_not_advance_evaluation(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    store.ingest([observation()])
    store.health({"status": "degraded"})
    with pytest.raises(ReviewConflictError):
        process_pending(store, ReviewPolicy(version="v1", withdrawal_limit="100"))
    assert store.counts()["evaluations"] == 0


@pytest.mark.parametrize("origin", ["synthetic_fixture", "live_graph_rpc"])
def test_conflicting_replay_does_not_block_next_event_or_restart(
    tmp_path: Path, origin: str
) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    rows = [observation("101"), observation("500", 1)]
    for row in rows:
        row["origin"] = origin
        row["proof"]["confirmations"] = 2
    store.ingest(rows)
    changed = observation("102")
    changed["origin"] = origin
    with pytest.raises(ReviewConflictError):
        store.ingest([changed])
    health = {"status": "healthy" if origin == "live_graph_rpc" else "synthetic"}
    store.health(health)
    policy = ReviewPolicy(version="v1", withdrawal_limit="100")

    assert process_pending(store, policy) == 1
    assert store.counts() == {
        "observations": 2, "review_cases": 1, "conflicts": 1, "evaluations": 1
    }
    case = store.detail(store.cases()[0]["id"])
    assert case["observation"]["raw"] == rows[1]["raw"]
    assert case["finding"]["observed_amount"] == "500"
    assert case["conflicts"] == []
    assert store.metadata("health") == health
    assert source_status(store)["status"] == "reconciliation_required"

    restarted = ReviewStore(store.path)
    assert process_pending(restarted, policy) == 0
    assert restarted.detail(case["id"]) == case
    with restarted.connection() as db:
        original = db.execute(
            "SELECT payload FROM observations WHERE id=?", (rows[0]["raw"]["id"],)
        ).fetchone()[0]
        assert json.loads(original) == rows[0]["raw"]
        assert db.execute("SELECT COUNT(*) FROM conflicts").fetchone()[0] == 1
        assert db.execute(
            "SELECT COUNT(*) FROM evaluations WHERE event_id=?", (rows[0]["raw"]["id"],)
        ).fetchone()[0] == 0


def test_more_than_one_batch_of_conflicts_cannot_consume_pending_limit(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    store.ingest([observation("101", index) for index in range(101)])
    for index in range(101):
        with pytest.raises(ReviewConflictError):
            store.ingest([observation("102", index)])
    valid = observation("500", 101)
    store.ingest([valid])
    store.health({"status": "synthetic"})
    policy = ReviewPolicy(version="v1", withdrawal_limit="100")
    fingerprint = store.register_policy(policy.definition())

    assert [row["id"] for row in store.pending(fingerprint, limit=100)] == [valid["raw"]["id"]]
    assert process_pending(store, policy) == 1
    assert store.counts() == {
        "observations": 102, "review_cases": 1, "conflicts": 101, "evaluations": 1
    }


def test_conflict_recorded_after_batch_selection_does_not_abort_remaining_events(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    first = observation("101")
    store.ingest([first, observation("500", 1)])
    store.health({"status": "synthetic"})
    evaluate = store.evaluated

    def record_with_concurrent_conflict(
        event_id: str, fingerprint: str, finding: dict[str, Any]
    ) -> str | None:
        if event_id == first["raw"]["id"]:
            with pytest.raises(ReviewConflictError):
                store.ingest([observation("102")])
        return evaluate(event_id, fingerprint, finding)

    monkeypatch.setattr(store, "evaluated", record_with_concurrent_conflict)
    assert process_pending(store, ReviewPolicy(version="v1", withdrawal_limit="100")) == 1
    assert store.counts() == {
        "observations": 2, "review_cases": 1, "conflicts": 1, "evaluations": 1
    }
    assert store.cases()[0]["finding"]["observed_amount"] == "500"


def test_policy_version_conflict_still_aborts_before_evaluating(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    store.ingest([observation("500")])
    store.health({"status": "synthetic"})
    store.register_policy(ReviewPolicy(version="v1", withdrawal_limit="100").definition())
    with pytest.raises(ReviewConflictError, match="Policy version"):
        process_pending(store, ReviewPolicy(version="v1", withdrawal_limit="200"))
    assert store.counts()["evaluations"] == 0
