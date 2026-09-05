"""SQLite transactions serialize dedupe, reservations and audit transitions.

No signer is available in this module. Any SQLite exception must stop execution.
Each operation uses its own connection, including across independent processes.
"""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

Outcome = Literal["success", "reverted", "already_desired", "indeterminate"]

SCHEMA = """
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
 status TEXT NOT NULL CHECK(status IN
 ('reserved','prepared','broadcast','success','reverted','already_desired','indeterminate')),
 created_at TEXT NOT NULL, nonce INTEGER, tx_hash TEXT, fee_data TEXT,
 outcome_evidence TEXT
);
CREATE TABLE IF NOT EXISTS intent_events (
 event_id TEXT PRIMARY KEY REFERENCES events(id),
 intent_id TEXT NOT NULL REFERENCES intents(id)
);
CREATE TABLE IF NOT EXISTS latch (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1), reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
 id INTEGER PRIMARY KEY, intent_id TEXT NOT NULL REFERENCES intents(id),
 payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at TEXT, last_error TEXT
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY, at TEXT NOT NULL, intent_id TEXT,
 transition TEXT NOT NULL, detail TEXT NOT NULL
);
"""


class StateStore:
    def __init__(self, path: Path) -> None:
        if str(path) == ":memory:":
            raise ValueError("In-memory state is not durable")
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            version = int(db.execute("PRAGMA user_version").fetchone()[0])
            if version not in (0, 1):
                raise ValueError("Unsupported state schema version")
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("BEGIN IMMEDIATE;" + SCHEMA + "PRAGMA user_version=1; COMMIT;")

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA synchronous=FULL")
            yield db
        finally:
            db.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    @staticmethod
    def _audit(db: sqlite3.Connection, intent: str, transition: str, detail: str) -> None:
        db.execute(
            "INSERT INTO audit(at,intent_id,transition,detail) VALUES(?,?,?,?)",
            (datetime.now(UTC).isoformat(), intent, transition, detail),
        )

    def ingest(self, source: str, event_id: str, sequence: int, block: int, payload: str) -> bool:
        """Persist an event and advance its cursor in the same transaction."""
        if sequence < 0 or block < 0 or not source or not event_id:
            raise ValueError("Invalid event position or identity")
        with self._transaction() as db:
            previous = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
            if previous is not None:
                if (
                    previous["source"],
                    previous["sequence"],
                    previous["block_number"],
                    previous["payload"],
                ) != (source, str(sequence), block, payload):
                    raise ValueError("Conflicting replay; reconciliation required")
                return False
            db.execute(
                "INSERT INTO events VALUES(?,?,?,?,?)",
                (event_id, source, str(sequence), block, payload),
            )
            cursor = db.execute("SELECT sequence FROM cursors WHERE source=?", (source,)).fetchone()
            if cursor is None or sequence > int(cursor[0]):
                db.execute(
                    "INSERT INTO cursors VALUES(?,?,?) ON CONFLICT(source) DO UPDATE "
                    "SET sequence=excluded.sequence,block_number=excluded.block_number",
                    (source, str(sequence), block),
                )
            return True

    def cursor(self, source: str) -> tuple[int, int] | None:
        with self._connection() as db:
            row = db.execute(
                "SELECT sequence,block_number FROM cursors WHERE source=?", (source,)
            ).fetchone()
            return None if row is None else (int(row[0]), int(row[1]))

    def reserve(self, intent: str, incident: str, event_ids: list[str]) -> bool:
        """Storage-level exclusivity; ES302 must additionally enforce policy.

        An unfinished intent prevents every new reservation, including after restart.
        """
        if not intent or not incident or not event_ids or len(set(event_ids)) != len(event_ids):
            raise ValueError("A reservation requires unique source events and stable IDs")
        with self._transaction() as db:
            if (
                db.execute("SELECT 1 FROM latch").fetchone()
                or db.execute(
                    "SELECT 1 FROM intents WHERE status IN "
                    "('reserved','prepared','broadcast','indeterminate')"
                ).fetchone()
            ):
                return False
            if db.execute("SELECT 1 FROM intents WHERE id=?", (intent,)).fetchone():
                return False
            for event in event_ids:
                if db.execute("SELECT 1 FROM intent_events WHERE event_id=?", (event,)).fetchone():
                    return False
                if not db.execute("SELECT 1 FROM events WHERE id=?", (event,)).fetchone():
                    raise ValueError("Cannot reserve an unknown event")
            now = datetime.now(UTC).isoformat()
            db.execute(
                "INSERT INTO incidents VALUES(?,?,?)", (incident, now, json.dumps(event_ids))
            )
            db.execute(
                "INSERT INTO intents(id,incident_id,status,created_at) VALUES(?,?,'reserved',?)",
                (intent, incident, now),
            )
            db.executemany(
                "INSERT INTO intent_events VALUES(?,?)", [(e, intent) for e in event_ids]
            )
            self._audit(db, intent, "reserved", "storage exclusivity passed; policy is external")
            return True

    def prepare(self, intent: str, nonce: int, fee_data: str) -> None:
        if nonce < 0:
            raise ValueError("Nonce cannot be negative")
        with self._transaction() as db:
            updated = db.execute(
                "UPDATE intents SET status='prepared',nonce=?,fee_data=? "
                "WHERE id=? AND status='reserved'",
                (nonce, fee_data, intent),
            )
            if updated.rowcount != 1:
                raise ValueError("Intent is not reserved; do not send")
            self._audit(db, intent, "prepared", "nonce and fee data persisted")

    def broadcast(self, intent: str, tx_hash: str) -> None:
        if len(tx_hash) != 66 or not tx_hash.startswith("0x"):
            raise ValueError("Invalid transaction hash")
        int(tx_hash[2:], 16)
        with self._transaction() as db:
            updated = db.execute(
                "UPDATE intents SET status='broadcast',tx_hash=? WHERE id=? AND status='prepared'",
                (tx_hash, intent),
            )
            if updated.rowcount != 1:
                raise ValueError("Intent is not prepared; reconcile")
            self._audit(db, intent, "broadcast", tx_hash)

    def finish(self, intent: str, outcome: Outcome, evidence: str) -> None:
        """Record a verifier's outcome; this method itself does not verify the chain."""
        if (
            outcome not in ("success", "reverted", "already_desired", "indeterminate")
            or not evidence
        ):
            raise ValueError("A recognized outcome and evidence are required")
        with self._transaction() as db:
            row = db.execute("SELECT status,tx_hash FROM intents WHERE id=?", (intent,)).fetchone()
            if row is None or row[0] not in ("reserved", "prepared", "broadcast", "indeterminate"):
                raise ValueError("No unfinished intent")
            if outcome in ("success", "reverted") and row[0] not in ("broadcast", "indeterminate"):
                raise ValueError("A receipt outcome requires a broadcast or reconciliation")
            if outcome in ("success", "reverted") and row[1] is None:
                raise ValueError("A receipt outcome requires a persisted transaction hash")
            if outcome == "already_desired" and row[0] != "reserved":
                raise ValueError("Already-desired is only valid before transaction preparation")
            db.execute(
                "UPDATE intents SET status=?,outcome_evidence=? WHERE id=?",
                (outcome, evidence, intent),
            )
            if outcome == "indeterminate":
                db.execute(
                    "INSERT INTO latch VALUES(1,?) ON CONFLICT(singleton) DO UPDATE "
                    "SET reason=excluded.reason",
                    (evidence,),
                )
            self._audit(db, intent, outcome, evidence)
            db.execute(
                "INSERT INTO outbox(intent_id,payload) VALUES(?,?)",
                (intent, json.dumps({"intent": intent, "outcome": outcome})),
            )

    def intent(self, intent: str) -> dict[str, str | int | None] | None:
        with self._connection() as db:
            row = db.execute("SELECT * FROM intents WHERE id=?", (intent,)).fetchone()
            return None if row is None else dict(row)

    def is_latched(self) -> bool:
        with self._connection() as db:
            return db.execute("SELECT 1 FROM latch").fetchone() is not None

    def latch_reason(self) -> str | None:
        with self._connection() as db:
            row = db.execute("SELECT reason FROM latch WHERE singleton=1").fetchone()
            return str(row[0]) if row else None

    def reset_latch(self, operator: str, reason: str) -> None:
        if not operator.strip() or not reason.strip():
            raise ValueError("Operator and reason required to reset latch")
        with self._transaction() as db:
            db.execute("DELETE FROM latch WHERE singleton=1")
            audit_payload = json.dumps({"operator": operator, "reason": reason})
            self._audit(db, "latch", "latch_reset", audit_payload)
