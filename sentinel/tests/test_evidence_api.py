"""Tests for the NexGuard Sentinel Incident Evidence API (Bazantic integration)."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    """Create a minimal SQLite state store with one incident and intent."""
    db_path = tmp_path / "state.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS cursors (
            source TEXT PRIMARY KEY, sequence TEXT NOT NULL, block_number INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY, source TEXT NOT NULL, sequence TEXT NOT NULL,
            block_number INTEGER NOT NULL, payload TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL, source_ids TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS intents (
            id TEXT PRIMARY KEY, incident_id TEXT NOT NULL REFERENCES incidents(id),
            status TEXT NOT NULL, created_at TEXT NOT NULL,
            nonce INTEGER, tx_hash TEXT, fee_data TEXT, outcome_evidence TEXT
        );
    """)
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO events VALUES(?,?,?,?,?)",
        ("evt-001", "thegraph", "1000001", 46427900, '{"amount": 100}'),
    )
    conn.execute(
        "INSERT INTO incidents VALUES(?,?,?)",
        ("inc-abc123-uuid", now, json.dumps(["evt-001"])),
    )
    conn.execute(
        "INSERT INTO intents(id,incident_id,status,created_at,nonce,tx_hash,outcome_evidence)"
        " VALUES(?,?,?,?,?,?,?)",
        (
            "intent-xyz",
            "inc-abc123-uuid",
            "success",
            now,
            42,
            "0x92ce8c8a0bb445d35dfd18aba65157f5e171011ebbc3c9a48d96b813d1ef148f",
            json.dumps({"block_number": 46427900}),
        ),
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture()
def client(tmp_db: Path) -> Generator[TestClient, None, None]:
    """Create a test client with the DB path patched."""
    from sentinel.evidence_api import app

    with patch("sentinel.evidence_api._db_path", return_value=tmp_db):
        yield TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db_reachable"] is True
    assert data["latest_incident_id"] == "inc-abc123-uuid"


def test_health_no_db(tmp_path: Path) -> None:
    from sentinel.evidence_api import app

    missing = tmp_path / "nonexistent.sqlite3"
    with patch("sentinel.evidence_api._db_path", return_value=missing):
        c = TestClient(app)
        resp = c.get("/health")
    assert resp.status_code == 200
    assert resp.json()["db_reachable"] is False


# ---------------------------------------------------------------------------
# x402 payment gate
# ---------------------------------------------------------------------------


def test_requires_payment_without_headers(client: TestClient) -> None:
    """Without X-Dev-Mode or X-Payment-Proof the API returns 402."""
    resp = client.get("/api/v1/incidents/latest")
    assert resp.status_code == 402
    data = resp.json()
    assert data["error"] == "Payment required"
    assert "payment" in data


def test_dev_mode_bypasses_payment(client: TestClient) -> None:
    """X-Dev-Mode: 1 header bypasses payment gate."""
    resp = client.get("/api/v1/incidents/latest", headers={"X-Dev-Mode": "1"})
    assert resp.status_code == 200


def test_payment_proof_bypasses_gate(client: TestClient) -> None:
    """X-Payment-Proof header also bypasses the gate."""
    resp = client.get(
        "/api/v1/incidents/latest",
        headers={"X-Payment-Proof": "mock-proof"},
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Latest incident endpoint
# ---------------------------------------------------------------------------


def test_latest_incident_schema(client: TestClient) -> None:
    resp = client.get("/api/v1/incidents/latest", headers={"X-Dev-Mode": "1"})
    assert resp.status_code == 200
    data = resp.json()
    # Required top-level fields
    assert data["incident_id"] == "inc-abc123-uuid"
    assert data["intent_id"] == "intent-xyz"
    assert data["status"] == "success"
    assert data["chain_id"] == 84532
    assert data["schema_version"] == 1
    assert len(data["sha256_state_fingerprint"]) == 64
    assert data["source_event_ids"] == ["evt-001"]


def test_latest_incident_pause_evidence(client: TestClient) -> None:
    resp = client.get("/api/v1/incidents/latest", headers={"X-Dev-Mode": "1"})
    ev = resp.json()["pause_evidence"]
    assert ev["tx_hash"] == "0x92ce8c8a0bb445d35dfd18aba65157f5e171011ebbc3c9a48d96b813d1ef148f"
    assert ev["block_number"] == 46427900
    assert "basescan" in ev["explorer_url"]
    assert ev["nonce"] == 42


def test_latest_incident_agent_summary(client: TestClient) -> None:
    resp = client.get("/api/v1/incidents/latest", headers={"X-Dev-Mode": "1"})
    summary = resp.json()["agent_summary"]
    assert "paused" in summary.lower() or "pause" in summary.lower()
    assert "Base Sepolia" in summary or "84532" in summary


def test_latest_incident_sha256_deterministic(client: TestClient) -> None:
    """SHA-256 fingerprint is deterministic for the same record."""
    r1 = client.get("/api/v1/incidents/latest", headers={"X-Dev-Mode": "1"}).json()
    r2 = client.get("/api/v1/incidents/latest", headers={"X-Dev-Mode": "1"}).json()
    assert r1["sha256_state_fingerprint"] == r2["sha256_state_fingerprint"]


def test_latest_incident_404_when_no_db(tmp_path: Path) -> None:
    from sentinel.evidence_api import app

    with patch("sentinel.evidence_api._db_path", return_value=tmp_path / "missing.sqlite3"):
        c = TestClient(app)
        resp = c.get("/api/v1/incidents/latest", headers={"X-Dev-Mode": "1"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "no_incidents"


# ---------------------------------------------------------------------------
# Specific incident endpoint
# ---------------------------------------------------------------------------


def test_get_incident_by_id_found(client: TestClient) -> None:
    resp = client.get(
        "/api/v1/incidents/inc-abc123-uuid", headers={"X-Dev-Mode": "1"}
    )
    assert resp.status_code == 200
    assert resp.json()["incident_id"] == "inc-abc123-uuid"


def test_get_incident_by_id_not_found(client: TestClient) -> None:
    resp = client.get("/api/v1/incidents/nonexistent-id-123", headers={"X-Dev-Mode": "1"})
    assert resp.status_code == 404


def test_get_incident_invalid_id(client: TestClient) -> None:
    resp = client.get("/api/v1/incidents/!!invalid!!", headers={"X-Dev-Mode": "1"})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Guardian contract ref
# ---------------------------------------------------------------------------


def test_guardian_ref(client: TestClient) -> None:
    data = client.get("/api/v1/incidents/latest", headers={"X-Dev-Mode": "1"}).json()
    guardian = data["guardian"]
    assert guardian["name"] == "Guardian"
    assert guardian["address"] == "0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3"
    assert guardian["chain_id"] == 84532
    assert "basescan" in guardian["explorer_url"]
