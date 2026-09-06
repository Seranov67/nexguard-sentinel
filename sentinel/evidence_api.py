"""Incident Evidence API for NexGuard Sentinel -- Bazantic integration.

Provides agent-readable endpoints exposing incident records with cryptographic
evidence. Intended for consumption via Bazantic Recipe / MCP.

No signing keys are loaded by this module. All data is read-only from the durable
SQLite state store and supplemented with known deployment constants.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from sentinel.proof import evidence_fingerprint

# ---------------------------------------------------------------------------
# Deployment constants (Base Sepolia, verified 2026-09-05)
# ---------------------------------------------------------------------------
CHAIN_ID = 84532
GUARDIAN_ADDRESS = "0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3"
VAULT_ADDRESS = "0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13"
BASESCAN_TX = "https://sepolia.basescan.org/tx/{tx_hash}"
BASESCAN_ADDR = "https://sepolia.basescan.org/address/{address}"

# x402 / MPP gateway -- price for reading an incident report (testnet units only)
MPP_PRICE_USDC = "0.001"
MPP_NETWORK = "base-sepolia"

app = FastAPI(
    title="NexGuard Sentinel -- Incident Evidence API",
    description=(
        "Agent-readable incident evidence for NexGuard Sentinel. "
        "Exposes cryptographic proof of automatic circuit-breaker events "
        "on Base Sepolia via The Graph + Guardian.sol."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ContractRef(BaseModel):
    """Onchain contract identity."""

    name: str
    address: str
    chain_id: int
    explorer_url: str


class PauseEvidence(BaseModel):
    """Evidence of the Guardian.pause() transaction."""

    tx_hash: str | None
    block_number: int | None
    explorer_url: str | None
    nonce: int | None
    status: str


class IncidentResponse(BaseModel):
    """Full incident evidence record returned to the agent."""

    incident_id: str
    intent_id: str
    created_at: str
    status: str
    trigger_cause: str
    source_event_ids: list[str]
    pause_evidence: PauseEvidence
    guardian: ContractRef
    vault: ContractRef
    chain_id: int
    sha256_state_fingerprint: str
    schema_version: int = 1
    agent_summary: str


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str
    db_reachable: bool
    latest_incident_id: str | None
    timestamp: str


# ---------------------------------------------------------------------------
# x402 / MPP middleware helper
# ---------------------------------------------------------------------------


def _mpp_402_response() -> Response:
    """Return a 402 Payment Required with MPP payment details."""
    payment_details = {
        "version": "1.0",
        "scheme": "x402",
        "network": MPP_NETWORK,
        "price": MPP_PRICE_USDC,
        "asset": "USDC",
        "description": "Payment prototype only; settlement is not implemented",
        "implemented": False,
        "payTo": GUARDIAN_ADDRESS,  # testnet: use Guardian address as placeholder
    }
    return JSONResponse(
        status_code=402,
        content={"error": "Payment required", "payment": payment_details},
        headers={"X-Payment-Required": json.dumps(payment_details)},
    )


# ---------------------------------------------------------------------------
# Database helpers (read-only; no StateStore dependency to keep API lightweight)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _IncidentRow:
    incident_id: str
    intent_id: str
    created_at: str
    status: str
    source_ids: list[str]
    nonce: int | None
    tx_hash: str | None
    outcome_evidence: str | None
    classification: str | None = None


def _db_path() -> Path:
    """Resolve the durable state DB path from environment or default."""
    import os

    return Path(os.environ.get("SENTINEL_STATE_PATH", ".sentinel/state.sqlite3"))


def _classification_cause(conn: sqlite3.Connection, source_ids: list[str]) -> str | None:
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='classification_traces'"
    ).fetchone():
        return None
    rows = conn.execute(
        "SELECT source_ids,result FROM classification_traces ORDER BY id DESC LIMIT 100"
    ).fetchall()
    for row in rows:
        if sorted(json.loads(row[0])) == sorted(source_ids):
            result = json.loads(row[1])
            return (
                f"Recorded classification: severity={result['severity']}, "
                f"confidence={result['confidence']}; {result['rationale']}"
            )
    return None


def _fetch_latest_incident(db_path: Path) -> _IncidentRow | None:
    """Return the most recent incident row joined with its intent."""
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT
                i.id AS incident_id,
                i.created_at,
                i.source_ids,
                t.id AS intent_id,
                t.status,
                t.nonce,
                t.tx_hash,
                t.outcome_evidence
            FROM incidents i
            LEFT JOIN intents t ON t.incident_id = i.id
            ORDER BY i.created_at DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return _IncidentRow(
            incident_id=row["incident_id"],
            intent_id=row["intent_id"] or "",
            created_at=row["created_at"],
            status=row["status"] or "reserved",
            source_ids=json.loads(row["source_ids"]),
            nonce=row["nonce"],
            tx_hash=row["tx_hash"],
            outcome_evidence=row["outcome_evidence"],
            classification=_classification_cause(conn, json.loads(row["source_ids"])),
        )
    finally:
        conn.close()


def _fetch_incident_by_id(db_path: Path, incident_id: str) -> _IncidentRow | None:
    """Return a specific incident row joined with its intent."""
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT
                i.id AS incident_id,
                i.created_at,
                i.source_ids,
                t.id AS intent_id,
                t.status,
                t.nonce,
                t.tx_hash,
                t.outcome_evidence
            FROM incidents i
            LEFT JOIN intents t ON t.incident_id = i.id
            WHERE i.id = ?
            LIMIT 1
            """,
            (incident_id,),
        ).fetchone()
        if row is None:
            return None
        return _IncidentRow(
            incident_id=row["incident_id"],
            intent_id=row["intent_id"] or "",
            created_at=row["created_at"],
            status=row["status"] or "reserved",
            source_ids=json.loads(row["source_ids"]),
            nonce=row["nonce"],
            tx_hash=row["tx_hash"],
            outcome_evidence=row["outcome_evidence"],
            classification=_classification_cause(conn, json.loads(row["source_ids"])),
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Evidence builder
# ---------------------------------------------------------------------------


def _build_response(row: _IncidentRow) -> IncidentResponse:
    """Transform a DB row into a structured agent-readable evidence response."""
    pause_ev = PauseEvidence(
        tx_hash=row.tx_hash,
        block_number=None,  # populated from outcome_evidence if available
        explorer_url=(BASESCAN_TX.format(tx_hash=row.tx_hash) if row.tx_hash else None),
        nonce=row.nonce,
        status=row.status,
    )

    # Extract block number from outcome_evidence JSON if present
    if row.outcome_evidence:
        try:
            ev = json.loads(row.outcome_evidence)
            block = ev.get("block_number")
            if isinstance(block, int):
                pause_ev = pause_ev.model_copy(update={"block_number": block})
        except (json.JSONDecodeError, AttributeError):
            pass

    trigger_cause = row.classification or (
        "Historical incident: no persisted AI classification trace is available."
    )

    status_label = {
        "success": "paused and verified on-chain",
        "reverted": "pause transaction reverted",
        "already_desired": "vault was already paused",
        "indeterminate": "outcome uncertain, latch active",
        "broadcast": "pause transaction broadcast, awaiting confirmation",
        "prepared": "pause transaction prepared, not yet sent",
        "reserved": "incident reserved, action pending",
    }.get(row.status, row.status)

    pause_msg = (
        f"Pause tx: {BASESCAN_TX.format(tx_hash=row.tx_hash)} "
        if row.tx_hash
        else "No tx hash yet. "
    )
    agent_summary = (
        f"Incident {row.incident_id[:8]}... detected at {row.created_at}. "
        f"Vault {VAULT_ADDRESS[:10]}... on Base Sepolia (chain {CHAIN_ID}) was "
        f"automatically paused via Guardian {GUARDIAN_ADDRESS[:10]}... "
        f"Status: {status_label}. "
        f"{pause_msg}"
    )

    result = IncidentResponse(
        incident_id=row.incident_id,
        intent_id=row.intent_id,
        created_at=row.created_at,
        status=row.status,
        trigger_cause=trigger_cause,
        source_event_ids=row.source_ids,
        pause_evidence=pause_ev,
        guardian=ContractRef(
            name="Guardian",
            address=GUARDIAN_ADDRESS,
            chain_id=CHAIN_ID,
            explorer_url=BASESCAN_ADDR.format(address=GUARDIAN_ADDRESS),
        ),
        vault=ContractRef(
            name="DemoVault",
            address=VAULT_ADDRESS,
            chain_id=CHAIN_ID,
            explorer_url=BASESCAN_ADDR.format(address=VAULT_ADDRESS),
        ),
        chain_id=CHAIN_ID,
        sha256_state_fingerprint="",
        agent_summary=agent_summary,
    )
    return result.model_copy(
        update={
            "sha256_state_fingerprint": evidence_fingerprint(result.model_dump()),
        }
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.middleware("http")
async def x402_payment_gate(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """x402/MPP payment gate for incident read endpoints.

    In development/test mode (X-Dev-Mode: 1 header), payment is bypassed.
    In production, agents must supply a valid payment proof header.
    """
    if request.url.path.startswith("/api/v1/incidents"):
        dev_mode = request.headers.get("X-Dev-Mode", "")
        demo_enabled = os.environ.get("SENTINEL_EVIDENCE_DEMO", "") == "1"
        # No payment verifier is implemented. Never accept an unverified proof.
        if not (demo_enabled and dev_mode == "1"):
            return _mpp_402_response()
    return await call_next(request)


@app.get("/health", response_model=HealthResponse, tags=["infrastructure"])
async def health() -> HealthResponse:
    """Health-check endpoint -- no payment required."""
    db = _db_path()
    reachable = False
    latest: str | None = None
    try:
        if db.exists():
            conn = sqlite3.connect(db, timeout=3)
            try:
                row = conn.execute(
                    "SELECT id FROM incidents ORDER BY created_at DESC LIMIT 1"
                ).fetchone()
                latest = row[0] if row else None
                reachable = True
            finally:
                conn.close()
    except sqlite3.Error:
        reachable = False
    return HealthResponse(
        status="ok" if reachable else "degraded",
        db_reachable=reachable,
        latest_incident_id=latest,
        timestamp=datetime.now(UTC).isoformat(),
    )


@app.get(
    "/api/v1/incidents/latest",
    response_model=IncidentResponse,
    tags=["incidents"],
    summary="Latest incident with cryptographic evidence",
    description=(
        "Returns the most recent Sentinel incident record with Guardian tx hash, "
        "Base Sepolia explorer link, Graph event IDs, and a SHA-256 state fingerprint. "
        "Designed for Bazantic Recipe / MCP agent consumption."
    ),
)
async def latest_incident(
    x_dev_mode: Annotated[str | None, Header(alias="X-Dev-Mode")] = None,
    x_payment_proof: Annotated[str | None, Header(alias="X-Payment-Proof")] = None,
) -> IncidentResponse:
    """Return the most recent incident evidence record."""
    row = _fetch_latest_incident(_db_path())
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "no_incidents",
                "message": "No incidents have been recorded yet. "
                "The Sentinel event loop must process at least one critical event.",
            },
        )
    return _build_response(row)


@app.get(
    "/api/v1/incidents/{incident_id}",
    response_model=IncidentResponse,
    tags=["incidents"],
    summary="Specific incident evidence by ID",
)
async def get_incident(
    incident_id: str,
    x_dev_mode: Annotated[str | None, Header(alias="X-Dev-Mode")] = None,
    x_payment_proof: Annotated[str | None, Header(alias="X-Payment-Proof")] = None,
) -> IncidentResponse:
    """Return evidence for a specific incident by its UUID."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", incident_id):
        raise HTTPException(status_code=400, detail={"error": "invalid_incident_id"})
    row = _fetch_incident_by_id(_db_path(), incident_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "incident_id": incident_id},
        )
    return _build_response(row)
