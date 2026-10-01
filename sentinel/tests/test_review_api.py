from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sentinel.review.api import create_app
from sentinel.review.cli import seed_demo
from sentinel.review.rules import ReviewPolicy
from sentinel.review.store import ReviewStore
from sentinel.tests.test_review_evidence import review_case

ORIGIN = "http://127.0.0.1:8089"
HEADERS = {"Origin": ORIGIN, "X-NexGuard-Review": "1"}


def test_local_workflow_revision_idempotency_and_brief(tmp_path: Path) -> None:
    store, case_id = review_case(tmp_path)
    app = create_app(store, ReviewPolicy(version="v1", withdrawal_limit="100"))
    with TestClient(app, base_url=ORIGIN) as client:
        assert client.get("/api/status").json()["health"]["status"] == "synthetic"
        assert client.get("/api/cases").json()["total"] == 1
        ack = {
            "action": "acknowledge",
            "revision": 0,
            "operator": "Local tester",
            "note": "Reviewed raw evidence",
            "request_id": "request_1",
        }
        path = f"/api/cases/{case_id}/decisions"
        first = client.post(path, json=ack, headers=HEADERS)
        assert first.status_code == 200
        assert client.post(path, json=ack, headers=HEADERS).json() == first.json()
        assert (
            client.post(path, json=ack | {"request_id": "request_2"}, headers=HEADERS).status_code
            == 409
        )
        resolve = {
            **ack,
            "action": "resolve",
            "revision": 1,
            "request_id": "request_3",
            "disposition": "expected_activity",
            "note": "Controlled test activity",
        }
        assert client.post(path, json=resolve, headers=HEADERS).status_code == 200
        value = client.get(f"/api/cases/{case_id}").json()
        assert value["case"]["disposition"] == "expected_activity"
        assert len(value["case"]["history"]) == 2
        brief = client.get(f"/api/cases/{case_id}/export/txt")
        assert "Controlled test activity" in brief.text
        assert "SYNTHETIC FIXTURE" in brief.text
        assert client.get(f"/api/cases/{case_id}/export/json").json()["links"] == {}


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Origin": "https://evil.example", "X-NexGuard-Review": "1"},
        {"Origin": "null", "X-NexGuard-Review": "1"},
        {"Origin": ORIGIN},
        HEADERS | {"Sec-Fetch-Site": "cross-site"},
    ],
)
def test_cross_origin_or_missing_guard_cannot_write(
    tmp_path: Path, headers: dict[str, str]
) -> None:
    store, case_id = review_case(tmp_path)
    with TestClient(
        create_app(store, ReviewPolicy(version="v1", withdrawal_limit="100")), base_url=ORIGIN
    ) as client:
        response = client.post(
            f"/api/cases/{case_id}/decisions",
            headers=headers,
            json={
                "action": "acknowledge",
                "revision": 0,
                "request_id": "request_1",
                "operator": "x",
                "note": "x",
            },
        )
        assert response.status_code == 403
        assert store.detail(case_id)["revision"] == 0


@pytest.mark.parametrize(
    "change",
    [
        {"operator": " "},
        {"note": ""},
        {"revision": True},
        {"action": "pause"},
        {"disposition": "policy_breach"},
        {"unknown": "field"},
    ],
)
def test_invalid_decision_rejected(tmp_path: Path, change: dict[str, object]) -> None:
    store, case_id = review_case(tmp_path)
    with TestClient(
        create_app(store, ReviewPolicy(version="v1", withdrawal_limit="100")), base_url=ORIGIN
    ) as client:
        decision = {
            "action": "acknowledge",
            "revision": 0,
            "request_id": "request_1",
            "operator": "tester",
            "note": "reviewed",
        } | change
        assert (
            client.post(
                f"/api/cases/{case_id}/decisions", headers=HEADERS, json=decision
            ).status_code
            == 422
        )


def test_host_guards_payload_bound_assets_and_pagination(tmp_path: Path) -> None:
    store, case_id = review_case(tmp_path)
    with TestClient(
        create_app(store, ReviewPolicy(version="v1", withdrawal_limit="100")), base_url=ORIGIN
    ) as client:
        assert client.get("/api/status", headers={"Host": "evil.example"}).status_code == 400
        assert client.get("/assets/unknown").status_code == 404
        assert client.get("/api/cases/missing").status_code == 404
        assert client.get("/api/cases?limit=101").status_code == 422
        large = client.post(
            f"/api/cases/{case_id}/decisions",
            content=b"x" * 20000,
            headers=HEADERS | {"Content-Type": "application/json"},
        )
        assert large.status_code == 413
        assert client.get("/").status_code == 200
        assert "frame-ancestors 'none'" in client.get("/").headers["Content-Security-Policy"]
        js = client.get("/assets/app.js").text
        assert "textContent" in js and "innerHTML" not in js
        assert client.get("/assets/style.css").status_code == 200


def test_fixture_seed_is_distinct_replay_safe_and_negative_case_present(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "demo.sqlite3")
    policy = seed_demo(store)
    assert policy.version == "synthetic-v1"
    assert store.counts()["observations"] == 3
    assert store.counts()["review_cases"] == 2
    seed_demo(ReviewStore(store.path))
    assert store.counts()["review_cases"] == 2
    assert (store.metadata("scope") or {})["origin"] == "synthetic_fixture"
