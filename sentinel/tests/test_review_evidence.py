import hashlib
from pathlib import Path
from typing import Any

import pytest

from sentinel.review.brief import json_brief, text_brief
from sentinel.review.evidence import LegacyEvidence, bundle, source_status
from sentinel.review.models import Decision
from sentinel.review.rules import ReviewPolicy, process_pending
from sentinel.review.store import ReviewStore
from sentinel.tests.test_review_store import observation


def review_case(tmp_path: Path, live: bool = False) -> tuple[ReviewStore, str]:
    store = ReviewStore(tmp_path / "review.sqlite3")
    row = observation()
    if live:
        row["origin"] = "live_graph_rpc"
        row["proof"]["confirmations"] = 2
    store.ingest([row])
    store.health({"status": "healthy" if live else "synthetic"})
    process_pending(store, ReviewPolicy(version="v1", withdrawal_limit="100"))
    return store, str(store.cases()[0]["id"])


def test_synthetic_brief_has_no_fabricated_explorer_links(tmp_path: Path) -> None:
    store, case_id = review_case(tmp_path)
    store.decide(
        case_id,
        Decision(
            action="acknowledge",
            revision=0,
            request_id="request_1",
            operator="tester",
            note="Synthetic rehearsal",
        ),
    )
    value = bundle(store, case_id, LegacyEvidence())
    assert value["synthetic"] is True
    assert value["links"] == {}
    assert value["schema_version"] == "nexguard.review-brief.v1"
    text = text_brief(value)
    assert "SYNTHETIC FIXTURE" in text and "Synthetic rehearsal" in text
    assert '"observed_amount": "101"' in json_brief(value)
    assert value["legacy_action"]["status"] == "synthetic_no_action"


def test_live_observation_is_not_successful_pause(tmp_path: Path) -> None:
    store, case_id = review_case(tmp_path, live=True)
    value = bundle(store, case_id, LegacyEvidence())
    assert value["legacy_action"]["status"] == "not_configured"
    assert "/tx/0x" in value["links"]["withdrawal"]
    assert "pause" not in value["links"]
    assert value["case"]["finding"]["authorization"] == "review_only"


@pytest.mark.parametrize("status", ["indeterminate", "reverted", "success", "already_desired"])
def test_actual_legacy_outcome_read_without_mutation(setup: Any, status: str) -> None:
    _, legacy_store, _, _, event = setup
    with legacy_store._transaction() as db:
        db.execute("INSERT INTO incidents VALUES('incident','2026-09-06','[]')")
        db.execute(
            "INSERT INTO intents(id,incident_id,status,created_at,outcome_evidence) "
            "VALUES('intent','incident',?,'2026-09-06','{}')",
            (status,),
        )
        db.execute("INSERT INTO intent_events VALUES(?,'intent')", (event.id,))
    before = hashlib.sha256(legacy_store.path.read_bytes()).hexdigest()
    result = LegacyEvidence(legacy_store.path).lookup(event.id)
    assert result["outcomes"][0]["recorded_status"] == status
    assert "not reverified" in result["gap"]
    assert hashlib.sha256(legacy_store.path.read_bytes()).hexdigest() == before


def test_missing_legacy_db_not_created(tmp_path: Path) -> None:
    path = tmp_path / "missing.sqlite3"
    assert LegacyEvidence(path).lookup("id")["status"] == "unavailable"
    assert not path.exists()


def test_old_source_health_is_stale_with_recorded_facts_preserved(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "review.sqlite3")
    store.health({"status": "healthy", "checked_at": "2026-09-06T12:00:00Z", "rpc_head": 100})
    health = source_status(store)
    assert health["status"] == "stale" and health["recorded_status"] == "healthy"
    assert health["rpc_head"] == 100


@pytest.mark.parametrize("status", ["stale", "degraded"])
def test_text_brief_summary_exposes_source_freshness_and_failure(
    tmp_path: Path, status: str
) -> None:
    store, case_id = review_case(tmp_path, live=True)
    original = store.detail(case_id)
    store.health(
        {
            "status": "healthy" if status == "stale" else "degraded",
            "checked_at": "2026-09-06T12:00:00Z",
            "rpc_head": 100,
            **(
                {"gap": "Source verification failed; stored evidence may be stale."}
                if status == "degraded"
                else {}
            ),
        }
    )
    value = bundle(store, case_id, LegacyEvidence())
    summary = text_brief(value).split("Full evidence:")[0]
    assert f"Source status: {status}" in summary
    assert "Source checked at: 2026-09-06T12:00:00Z" in summary
    expected_gap = "Source verification failed" if status == "degraded" else "Source check is stale"
    assert expected_gap in summary
    assert value["case"] == original
    assert value["source_health"]["rpc_head"] == 100
