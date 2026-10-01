"""Read recorded legacy outcomes with SQLite mode=ro, without its runtime/API."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from sentinel.models import hex_value
from sentinel.review.models import CHAIN_ID, GUARDIAN, VAULT, utc_now
from sentinel.review.store import ReviewStore


class LegacyEvidence:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path.resolve() if path else None

    def lookup(self, event_id: str) -> dict[str, Any]:
        if self.path is None:
            return {
                "status": "not_configured",
                "outcomes": [],
                "classification": None,
                "gap": "Legacy action evidence was not connected.",
            }
        if not self.path.is_file():
            return {
                "status": "unavailable",
                "outcomes": [],
                "classification": None,
                "gap": "Legacy database unavailable; no action outcome inferred.",
            }
        try:
            with closing(sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)) as db:
                db.row_factory = sqlite3.Row
                db.execute("PRAGMA query_only=ON")
                if db.execute("PRAGMA user_version").fetchone()[0] != 2:
                    raise ValueError("Unsupported legacy schema")
                rows = db.execute(
                    "SELECT i.id,i.incident_id,i.status,i.created_at,i.nonce,i.tx_hash,"
                    "i.outcome_evidence FROM intents i JOIN intent_events e ON e.intent_id=i.id "
                    "WHERE e.event_id=?",
                    (event_id,),
                ).fetchall()
                traces = db.execute(
                    "SELECT * FROM classification_traces ORDER BY id DESC LIMIT 1000"
                )
                classification = next(
                    (dict(t) for t in traces if event_id in json.loads(t["source_ids"])), None
                )
                if classification:
                    for key in ("source_ids", "features", "result"):
                        classification[key] = json.loads(classification[key])
                outcomes = []
                for row in rows:
                    outcome = dict(row)
                    outcome["recorded_status"] = outcome.pop("status")
                    outcome["outcome_evidence"] = (
                        json.loads(row["outcome_evidence"]) if row["outcome_evidence"] else None
                    )
                    outcome["explorer_url"] = (
                        "https://sepolia.basescan.org/tx/" + hex_value(row["tx_hash"], 32)
                        if row["tx_hash"]
                        else None
                    )
                    outcomes.append(outcome)
                return {
                    "status": "recorded" if outcomes else "no_matching_record",
                    "outcomes": outcomes,
                    "classification": classification,
                    "classification_lookup_limit": 1000,
                    "gap": "Recorded prior outcomes; current receipt/state not reverified here.",
                }
        except (sqlite3.Error, ValueError, TypeError, KeyError) as exc:
            return {
                "status": "unavailable",
                "outcomes": [],
                "classification": None,
                "error_type": type(exc).__name__,
                "gap": "Legacy evidence could not be read.",
            }


def bundle(store: ReviewStore, case_id: str, legacy: LegacyEvidence) -> dict[str, Any]:
    case = store.detail(case_id)
    observation = case["observation"]
    synthetic = observation["origin"] == "synthetic_fixture"
    raw = observation["raw"]
    tx = hex_value(raw["transactionHash"], 32)
    return {
        "schema_version": "nexguard.review-brief.v1",
        "exported_at": utc_now(),
        "chain_id": CHAIN_ID,
        "vault": VAULT,
        "guardian": GUARDIAN,
        "case": case,
        "synthetic": synthetic,
        "finding_integrity": "conflicting" if case["conflicts"] else "recorded",
        "source_health": store.metadata("health"),
        "source": store.metadata("scope"),
        "legacy_action": legacy.lookup(raw["id"])
        if not synthetic
        else {"status": "synthetic_no_action", "outcomes": [], "classification": None},
        "links": {}
        if synthetic
        else {
            "withdrawal": "https://sepolia.basescan.org/tx/" + tx,
            "vault": "https://sepolia.basescan.org/address/" + VAULT,
            "guardian": "https://sepolia.basescan.org/address/" + GUARDIAN,
        },
        "limits": [
            "Payload SHA-256 proves consistency, not provider authenticity.",
            "A review finding is not proof of an exploit or financial loss.",
            "Resolution records a local decision and does not remediate chain state.",
            "Operator labels are locally declared; no authenticated identity.",
        ],
    }
