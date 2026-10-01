from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

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
