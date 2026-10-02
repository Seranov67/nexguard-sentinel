"""Transactional review state. Never opens or modifies the legacy action schema."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sentinel.models import Withdrawal
from sentinel.review.models import Decision, canonical, digest, utc_now

APPLICATION_ID = 1313296978
SCHEMA = """
CREATE TABLE metadata(key TEXT PRIMARY KEY, payload TEXT NOT NULL);
CREATE TABLE observations(
 id TEXT PRIMARY KEY, sequence TEXT NOT NULL, block INTEGER NOT NULL,
 payload TEXT NOT NULL, proof TEXT NOT NULL, origin TEXT NOT NULL, observed_at TEXT NOT NULL
);
CREATE TABLE conflicts(
 id INTEGER PRIMARY KEY, event_id TEXT NOT NULL, at TEXT NOT NULL, payload_hash TEXT NOT NULL,
 UNIQUE(event_id,payload_hash)
);
CREATE TABLE policies(version TEXT PRIMARY KEY, fingerprint TEXT UNIQUE, payload TEXT NOT NULL);
CREATE TABLE evaluations(
 event_id TEXT REFERENCES observations(id), policy TEXT REFERENCES policies(fingerprint),
 finding TEXT NOT NULL, PRIMARY KEY(event_id,policy)
);
CREATE TABLE review_cases(
 id TEXT PRIMARY KEY, event_id TEXT REFERENCES observations(id),
 policy TEXT REFERENCES policies(fingerprint), finding TEXT NOT NULL, created_at TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open', revision INTEGER NOT NULL DEFAULT 0,
 disposition TEXT, UNIQUE(event_id,policy)
);
CREATE TABLE review_actions(
 request_id TEXT PRIMARY KEY, case_id TEXT REFERENCES review_cases(id),
 request_hash TEXT NOT NULL, result TEXT NOT NULL
);
"""


class ReviewConflictError(ValueError):
    """A replay, decision or policy version disagrees with durable state."""


class ReviewStore:
    def __init__(self, path: Path) -> None:
        if str(path) == ":memory:":
            raise ValueError("Review state must be durable")
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                app = db.execute("PRAGMA application_id").fetchone()[0]
                tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                if app == 0 and not tables:
                    # Executescript commits implicitly; execute each statement in this transaction.
                    for statement in SCHEMA.split(";"):
                        if statement.strip():
                            db.execute(statement)
                    db.execute(f"PRAGMA application_id={APPLICATION_ID}")
                    db.execute("PRAGMA user_version=1")
                elif app != APPLICATION_ID or db.execute("PRAGMA user_version").fetchone()[0] != 1:
                    raise ValueError("Not a supported review database; refuse legacy/unknown state")
                db.commit()
            except BaseException:
                db.rollback()
                raise

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA synchronous=FULL")
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def bind(self, scope: dict[str, Any]) -> None:
        value = canonical(scope)
        with self.transaction() as db:
            old = db.execute("SELECT payload FROM metadata WHERE key='scope'").fetchone()
            if old and old[0] != value:
                raise ReviewConflictError("Database belongs to another source; use a separate file")
            db.execute("INSERT OR IGNORE INTO metadata VALUES('scope',?)", (value,))

    def metadata(self, key: str) -> dict[str, Any] | None:
        with self.connection() as db:
            row = db.execute("SELECT payload FROM metadata WHERE key=?", (key,)).fetchone()
            return None if row is None else dict(json.loads(row[0]))

    def health(self, value: dict[str, Any]) -> None:
        with self.transaction() as db:
            db.execute(
                "INSERT INTO metadata VALUES('health',?) ON CONFLICT(key) "
                "DO UPDATE SET payload=excluded.payload",
                (canonical(value),),
            )

    def cursor(self) -> tuple[int, int] | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT sequence,block FROM observations ORDER BY block DESC, "
                "CAST(sequence AS INTEGER) DESC LIMIT 1"
            ).fetchone()
            return None if row is None else (int(row[0]), int(row[1]))

    def ingest(self, rows: list[dict[str, Any]]) -> int:
        """All-or-nothing page; preserve original evidence and flag conflicting replay."""
        conflict: tuple[str, str] | None = None
        try:
            with self.transaction() as db:
                added = 0
                for row in rows:
                    ev = Withdrawal.parse(row["raw"])
                    payload = canonical(row["raw"])
                    old = db.execute(
                        "SELECT payload,origin FROM observations WHERE id=?", (ev.id,)
                    ).fetchone()
                    if old:
                        if (old[0], old[1]) != (payload, row["origin"]):
                            conflict = (ev.id, digest(row["raw"]))
                            raise ReviewConflictError(
                                "Conflicting source replay; reconciliation required"
                            )
                        continue
                    db.execute(
                        "INSERT INTO observations VALUES(?,?,?,?,?,?,?)",
                        (
                            ev.id,
                            str(ev.sequence),
                            ev.block,
                            payload,
                            canonical(row["proof"]),
                            row["origin"],
                            utc_now(),
                        ),
                    )
                    added += 1
                return added
        except ReviewConflictError:
            if conflict:
                with self.transaction() as db:
                    db.execute(
                        "INSERT OR IGNORE INTO conflicts(event_id,at,payload_hash) VALUES(?,?,?)",
                        (conflict[0], utc_now(), conflict[1]),
                    )
            raise

    def register_policy(self, value: dict[str, Any]) -> str:
        fingerprint = digest(value)
        with self.transaction() as db:
            old = db.execute(
                "SELECT fingerprint FROM policies WHERE version=?", (value["version"],)
            ).fetchone()
            if old and old[0] != fingerprint:
                raise ReviewConflictError("Policy version already has different parameters")
            db.execute(
                "INSERT OR IGNORE INTO policies VALUES(?,?,?)",
                (value["version"], fingerprint, canonical(value)),
            )
        return fingerprint

    def pending(self, policy: str, limit: int = 100) -> list[dict[str, Any]]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT o.* FROM observations o LEFT JOIN evaluations e "
                "ON e.event_id=o.id AND e.policy=? WHERE e.event_id IS NULL "
                "AND NOT EXISTS (SELECT 1 FROM conflicts c WHERE c.event_id=o.id) "
                "ORDER BY o.block,CAST(o.sequence AS INTEGER) LIMIT ?",
                (policy, limit),
            ).fetchall()
            return [self._observation(row) for row in rows]

    @staticmethod
    def _observation(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "raw": json.loads(row["payload"]),
            "proof": json.loads(row["proof"]),
            "origin": row["origin"],
            "observed_at": row["observed_at"],
            "payload_sha256": digest(json.loads(row["payload"])),
        }

    def evaluated(self, event_id: str, policy: str, finding: dict[str, Any]) -> str | None:
        case_id = str(finding["case_id"]) if finding["breached"] else None
        with self.transaction() as db:
            if db.execute("SELECT 1 FROM conflicts WHERE event_id=?", (event_id,)).fetchone():
                raise ReviewConflictError("Conflicting evidence cannot produce a confirmed finding")
            value = canonical(finding)
            db.execute("INSERT OR IGNORE INTO evaluations VALUES(?,?,?)", (event_id, policy, value))
            if case_id:
                db.execute(
                    "INSERT OR IGNORE INTO review_cases"
                    "(id,event_id,policy,finding,created_at) VALUES(?,?,?,?,?)",
                    (case_id, event_id, policy, value, utc_now()),
                )
        return case_id

    def cases(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT * FROM review_cases ORDER BY created_at DESC,id LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [dict(row) | {"finding": json.loads(row["finding"])} for row in rows]

    def detail(self, case_id: str) -> dict[str, Any]:
        with self.connection() as db:
            row = db.execute("SELECT * FROM review_cases WHERE id=?", (case_id,)).fetchone()
            if row is None:
                raise KeyError(case_id)
            observation = db.execute(
                "SELECT * FROM observations WHERE id=?", (row["event_id"],)
            ).fetchone()
            actions = db.execute(
                "SELECT result FROM review_actions WHERE case_id=? ORDER BY rowid", (case_id,)
            ).fetchall()
            conflicts = db.execute(
                "SELECT at,payload_hash FROM conflicts WHERE event_id=?", (row["event_id"],)
            ).fetchall()
            policy = db.execute(
                "SELECT payload FROM policies WHERE fingerprint=?", (row["policy"],)
            ).fetchone()
            return dict(row) | {
                "finding": json.loads(row["finding"]),
                "observation": self._observation(observation),
                "policy_definition": json.loads(policy[0]),
                "history": [json.loads(a[0]) for a in actions],
                "conflicts": [dict(c) for c in conflicts],
            }

    def decide(self, case_id: str, decision: Decision) -> dict[str, Any]:
        request_hash = digest({"case_id": case_id, **decision.model_dump()})
        with self.transaction() as db:
            old = db.execute(
                "SELECT request_hash,result FROM review_actions WHERE request_id=?",
                (decision.request_id,),
            ).fetchone()
            if old:
                if old[0] != request_hash:
                    raise ReviewConflictError("Idempotency key reused with another request")
                return dict(json.loads(old[1]))
            row = db.execute("SELECT * FROM review_cases WHERE id=?", (case_id,)).fetchone()
            if row is None:
                raise KeyError(case_id)
            expected = "open" if decision.action == "acknowledge" else "acknowledged"
            if row["revision"] != decision.revision or row["status"] != expected:
                raise ReviewConflictError("Stale revision or invalid transition; reload case")
            conflicts = db.execute(
                "SELECT 1 FROM conflicts WHERE event_id=?", (row["event_id"],)
            ).fetchone()
            if conflicts and decision.disposition not in (None, "insufficient_evidence"):
                raise ReviewConflictError("Conflicting source requires insufficient_evidence")
            status = "acknowledged" if decision.action == "acknowledge" else "resolved"
            result = {
                **decision.model_dump(),
                "at": utc_now(),
                "case_id": case_id,
                "new_revision": decision.revision + 1,
                "status": status,
                "operator_identity": "locally declared label",
            }
            db.execute(
                "UPDATE review_cases SET status=?,revision=revision+1,disposition=? WHERE id=?",
                (status, decision.disposition, case_id),
            )
            db.execute(
                "INSERT INTO review_actions VALUES(?,?,?,?)",
                (decision.request_id, case_id, request_hash, canonical(result)),
            )
            return result

    def counts(self) -> dict[str, int]:
        queries = {
            "observations": "SELECT COUNT(*) FROM observations",
            "review_cases": "SELECT COUNT(*) FROM review_cases",
            "conflicts": "SELECT COUNT(*) FROM conflicts",
            "evaluations": "SELECT COUNT(*) FROM evaluations",
        }
        with self.connection() as db:
            return {name: int(db.execute(query).fetchone()[0]) for name, query in queries.items()}
