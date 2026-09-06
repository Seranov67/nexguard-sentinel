"""EG-4: failed AI cannot authorize action; notification failure is isolated."""

import json
import sqlite3
from pathlib import Path
from typing import Any

import httpx
import pytest

from sentinel.actuator import Actuator, ExecutionResult
from sentinel.ai import OllamaEvaluator
from sentinel.classifier import classify_features, extract_features, validate_classification_json
from sentinel.config import Settings
from sentinel.loop import run_loop_step
from sentinel.outbox import OutboxWorker
from sentinel.store import StateStore


@pytest.mark.parametrize(
    "patch",
    [
        {"confidence": True},
        {"confidence": "0.9"},
        {"confidence": float("nan")},
        {"rationale": {}},
        {"rationale": ""},
        {"extra": "ignore the policy"},
        {"recommended_action": "unpause"},
    ],
)
def test_strict_schema(patch: dict[str, Any]) -> None:
    value = {
        "severity": "critical",
        "recommended_action": "pause",
        "confidence": 0.9,
        "rationale": "high volume",
    }
    value.update(patch)
    assert not validate_classification_json(json.dumps(value)).is_actionable_pause()


def test_catastrophic_input_does_not_bypass_failed_ai() -> None:
    features = extract_features([{"amount": str(25 * 10**18), "timestamp": 100}])

    def unavailable(_: dict[str, Any]) -> str:
        raise TimeoutError

    assert not classify_features(features, llm_evaluator=unavailable).is_actionable_pause()
    assert not classify_features(features).is_actionable_pause()


def test_feature_window_is_bounded() -> None:
    features = extract_features(
        [
            {"amount": "100000", "timestamp": 1},
            {"amount": "7", "timestamp": 1000},
        ]
    )
    assert features.event_count == 1
    assert features.total_amount_wei == 7
    with pytest.raises(ValueError):
        extract_features([{"amount": "1"}] * 1001)


def test_feature_window_survives_completed_poll(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    for index in (1, 2, 3):
        store.ingest(
            "vault",
            f"e{index}",
            index,
            index,
            json.dumps({"timestamp": 100 + index, "amount": "7"}),
        )
    store.mark_processed(["e1", "e2"], "normal at earlier poll")
    features = extract_features(StateStore(store.path).feature_window("vault", 103))
    assert features.event_count == 3
    assert features.total_amount_wei == 21


def test_ollama_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    original = httpx.Client

    def handle(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert request.url.path == "/api/chat"
        assert body["format"]["additionalProperties"] is False
        assert "keeper" not in request.content.decode().lower()
        assert body["stream"] is False
        return httpx.Response(200, json={"done": True, "message": {"content": "{}"}})

    monkeypatch.setattr(
        "sentinel.ai.httpx.Client",
        lambda **kw: original(
            transport=httpx.MockTransport(handle),
            **kw,
        ),
    )
    assert OllamaEvaluator("http://localhost:11434", "test-model")({"event_count": 1}) == "{}"


def outbox_store(tmp_path: Path) -> StateStore:
    store = StateStore(tmp_path / "state.db")
    store.ingest("vault", "e1", 1, 1, "{}")
    store.reserve("i1", "incident", ["e1"])
    store.finish("i1", "already_desired", "already paused")
    return store


def test_retry_restart_and_terminal_failure(tmp_path: Path) -> None:
    store = outbox_store(tmp_path)

    def fail(message_id: str, payload: str) -> None:
        raise RuntimeError("sensitive endpoint data")

    for timestamp in (100, 103, 108):
        worker = OutboxWorker(StateStore(store.path), fail)
        assert worker.run_once(now=timestamp)
    assert store.outbox_counts() == {"failed": 1}
    assert not store.is_latched()
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT last_error FROM outbox").fetchone()[0] == "RuntimeError"


def test_delivery_lease_prevents_concurrent_claim(tmp_path: Path) -> None:
    store = outbox_store(tmp_path)
    delivered: list[str] = []

    def deliver(message_id: str, payload: str) -> None:
        other = OutboxWorker(StateStore(store.path))
        assert not other.run_once(now=100)
        delivered.append(message_id)

    assert OutboxWorker(store, deliver).run_once(now=100)
    assert delivered == ["1"]
    assert store.outbox_counts() == {"delivered": 1}


def test_crashed_delivery_lease_can_be_retried(tmp_path: Path) -> None:
    store = outbox_store(tmp_path)
    with sqlite3.connect(store.path) as db:
        db.execute("UPDATE outbox SET status='sending',attempts=1")
        db.execute("INSERT INTO outbox_leases VALUES(1,'dead-worker',100)")
    worker = OutboxWorker(StateStore(store.path), lambda mid, payload: None)
    assert not worker.run_once(now=99)
    assert worker.run_once(now=101)
    assert store.outbox_counts() == {"delivered": 1}


@pytest.mark.parametrize("valid", [True, False])
def test_ai_controls_loop_and_records_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid: bool,
) -> None:
    store = StateStore(tmp_path / "state.db")
    guardian = "0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3"
    settings = Settings(
        "https://example.org", "https://example.org", guardian, guardian, store.path
    )
    event = {
        "id": "e1",
        "sequence": 1,
        "blockNumber": 100,
        "timestamp": 1000,
        "amount": str(25 * 10**18),
    }
    calls: list[str] = []
    monkeypatch.setattr(Actuator, "is_paused_onchain", lambda self: False)

    def execute(self: Actuator, intent_id: str, reference: str, severity: int) -> ExecutionResult:
        assert self.store.intent(intent_id) is not None
        calls.append(intent_id)
        self.store.finish(intent_id, "already_desired", "race: already paused")
        return ExecutionResult("already_desired", None, None, "race: already paused")

    monkeypatch.setattr(Actuator, "execute_pause", execute)
    response = (
        json.dumps(
            {
                "severity": "critical",
                "recommended_action": "pause",
                "confidence": 0.95,
                "rationale": "Large withdrawal",
            }
        )
        if valid
        else "bad"
    )
    result = run_loop_step(
        settings,
        store,
        events_override=[event],
        keeper_private_key="unused",
        llm_evaluator=lambda _: response,
    )
    assert bool(calls) == valid
    assert (result.execution is not None) == valid
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT COUNT(*) FROM classification_traces").fetchone()[0] == 1
    assert bool(store.pending_events("vault-withdrawals")) != valid
