import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from sentinel.store import StateStore


def test_restart_preserves_cursor_and_prepared_intent(tmp_path):
    path = tmp_path / "state.sqlite3"
    store = StateStore(path)
    sequence = 2**70
    store.ingest("vault", "e1", sequence, 100, "{}")
    assert store.reserve("i1", "incident1", ["e1"])
    store.prepare("i1", 4, '{"maxFeePerGas":100}')
    reopened = StateStore(path)
    assert reopened.cursor("vault") == (sequence, 100)
    assert reopened.intent("i1")["nonce"] == 4
    reopened.ingest("vault", "e2", sequence + 1, 101, "{}")
    assert not reopened.reserve("i2", "incident2", ["e2"])
    with pytest.raises(ValueError, match="not reserved"):
        reopened.prepare("i1", 5, "{}")


def test_concurrent_connections_reserve_exactly_once(tmp_path):
    path = tmp_path / "state.sqlite3"
    store = StateStore(path)
    store.ingest("vault", "event", 1, 1, "{}")
    stores = [StateStore(path) for _ in range(8)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(
                lambda pair: pair[1].reserve(f"i{pair[0]}", f"incident{pair[0]}", ["event"]),
                enumerate(stores),
            )
        )
    assert sum(results) == 1


def test_replay_and_conflict_do_not_advance_cursor(tmp_path):
    store = StateStore(tmp_path / "state.sqlite3")
    assert store.ingest("vault", "event", 10, 2, "{}")
    assert not store.ingest("vault", "event", 10, 2, "{}")
    with pytest.raises(ValueError, match="Conflicting replay"):
        store.ingest("vault", "event", 20, 3, "{}")
    assert store.cursor("vault") == (10, 2)


def test_cursor_and_event_rollback_together(tmp_path):
    path = tmp_path / "state.sqlite3"
    store = StateStore(path)
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TRIGGER fail_cursor BEFORE INSERT ON cursors "
            "BEGIN SELECT RAISE(ABORT, 'simulated storage failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError):
        store.ingest("vault", "event", 1, 1, "{}")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_indeterminate_latch_and_outbox_survive_restart(tmp_path):
    path = tmp_path / "state.sqlite3"
    store = StateStore(path)
    store.ingest("vault", "event", 1, 1, "{}")
    store.reserve("i", "incident", ["event"])
    store.prepare("i", 5, "{}")
    tx = "0x" + "ab" * 32
    store.broadcast("i", tx)
    store.finish("i", "indeterminate", "receipt timeout")
    reopened = StateStore(path)
    assert reopened.is_latched()
    assert reopened.intent("i")["tx_hash"] == tx
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 4


def test_completed_event_cannot_be_reserved_again(tmp_path):
    store = StateStore(tmp_path / "state.sqlite3")
    store.ingest("vault", "event", 1, 1, "{}")
    store.reserve("i", "incident", ["event"])
    store.prepare("i", 0, "{}")
    store.broadcast("i", "0x" + "12" * 32)
    store.finish("i", "success", "verified by executor")
    assert not store.reserve("different-intent", "different-incident", ["event"])


def test_unknown_event_and_future_schema_fail_closed(tmp_path):
    path = tmp_path / "state.sqlite3"
    store = StateStore(path)
    with pytest.raises(ValueError, match="unknown event"):
        store.reserve("i", "incident", ["missing"])
    assert store.intent("i") is None
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(ValueError, match="schema"):
        StateStore(path)


def test_outbox_failure_rolls_back_outcome_and_audit(tmp_path):
    path = tmp_path / "state.sqlite3"
    store = StateStore(path)
    store.ingest("vault", "event", 1, 1, "{}")
    store.reserve("i", "incident", ["event"])
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TRIGGER fail_outbox BEFORE INSERT ON outbox "
            "BEGIN SELECT RAISE(ABORT, 'simulated outbox failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError):
        store.finish("i", "indeterminate", "timeout")
    assert store.intent("i")["status"] == "reserved"
    assert not store.is_latched()
    assert not store.reserve("i2", "incident2", ["event"])


def test_no_receipt_success_without_transaction_hash(tmp_path):
    store = StateStore(tmp_path / "state.sqlite3")
    store.ingest("vault", "event", 1, 1, "{}")
    store.reserve("i", "incident", ["event"])
    store.finish("i", "indeterminate", "crash before broadcast")
    with pytest.raises(ValueError, match="transaction hash"):
        store.finish("i", "success", "unsubstantiated receipt")


def test_process_crash_after_prepare_blocks_resend(tmp_path):
    path = tmp_path / "state.sqlite3"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import os, sys
from pathlib import Path
from sentinel.store import StateStore
s = StateStore(Path(sys.argv[1]))
s.ingest('vault', 'event', 1, 1, '{}')
s.reserve('i', 'incident', ['event'])
s.prepare('i', 7, '{}')
os._exit(17)
""",
            str(path),
        ],
        check=False,
    )
    assert result.returncode == 17
    reopened = StateStore(path)
    assert reopened.intent("i")["status"] == "prepared"
    assert reopened.intent("i")["nonce"] == 7
    assert not reopened.reserve("new", "new-incident", ["event"])
