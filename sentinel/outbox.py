"""Leased at-least-once notification delivery independent of action correctness."""

import json
import time
import uuid
from collections.abc import Callable

from sentinel.store import StateStore


def stdout_delivery(message_id: str, payload: str) -> None:
    """Local structured notification; consumers should dedupe by message_id."""
    print(json.dumps({"notification_id": message_id, "payload": json.loads(payload)}), flush=True)


class OutboxWorker:
    def __init__(
        self,
        store: StateStore,
        deliver: Callable[[str, str], None] = stdout_delivery,
        *,
        max_attempts: int = 3,
        lease_seconds: int = 60,
    ) -> None:
        if not 1 <= max_attempts <= 10 or lease_seconds < 1:
            raise ValueError("Invalid delivery bounds")
        self.store = store
        self.deliver = deliver
        self.max_attempts = max_attempts
        self.lease_seconds = lease_seconds

    def run_once(self, *, now: float | None = None) -> bool:
        timestamp = time.time() if now is None else now
        token = uuid.uuid4().hex
        with self.store._transaction() as db:
            row = db.execute(
                "SELECT o.* FROM outbox o LEFT JOIN outbox_leases l ON l.outbox_id=o.id "
                "WHERE o.status IN ('pending','retry','sending') "
                "AND (o.next_attempt_at IS NULL OR CAST(o.next_attempt_at AS REAL)<=?) "
                "AND (l.expires IS NULL OR l.expires<=?) ORDER BY o.id LIMIT 1",
                (timestamp, timestamp),
            ).fetchone()
            if row is None:
                return False
            message_id = int(row["id"])
            attempts = int(row["attempts"])
            if attempts >= self.max_attempts:
                db.execute("UPDATE outbox SET status='failed' WHERE id=?", (message_id,))
                return True
            db.execute(
                "INSERT INTO outbox_leases VALUES(?,?,?) ON CONFLICT(outbox_id) "
                "DO UPDATE SET token=excluded.token,expires=excluded.expires",
                (message_id, token, timestamp + self.lease_seconds),
            )
            db.execute(
                "UPDATE outbox SET status='sending',attempts=attempts+1 WHERE id=?",
                (message_id,),
            )
            payload = str(row["payload"])
        error = None
        try:
            self.deliver(str(message_id), payload)
        except Exception as exc:
            # Exception type only: endpoint exceptions can contain credentials.
            error = type(exc).__name__
        with self.store._transaction() as db:
            lease = db.execute(
                "SELECT token FROM outbox_leases WHERE outbox_id=?",
                (message_id,),
            ).fetchone()
            if lease is None or lease[0] != token:
                return True
            status = (
                "delivered"
                if error is None
                else ("failed" if attempts + 1 >= self.max_attempts else "retry")
            )
            db.execute(
                "UPDATE outbox SET status=?,last_error=?,next_attempt_at=? WHERE id=?",
                (status, error, str(timestamp + min(300, 2 ** (attempts + 1))), message_id),
            )
            db.execute("DELETE FROM outbox_leases WHERE outbox_id=?", (message_id,))
        return True
