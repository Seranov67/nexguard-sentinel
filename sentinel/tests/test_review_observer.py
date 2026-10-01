import ast
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from web3 import Web3

from sentinel.models import Withdrawal
from sentinel.review.models import DEPLOYMENT, VAULT
from sentinel.review.observer import ObserveConfig, Observer, ReadRpc
from sentinel.review.store import ReviewStore
from sentinel.tests.test_review_store import observation


class FakeReader:
    def __init__(self) -> None:
        self.now = int(datetime.now(UTC).timestamp())

    def identity(self) -> None:
        pass

    def head(self) -> int:
        return 104

    def block(self, number: Any) -> dict[str, Any]:
        return {
            "number": number,
            "hash": "0x" + "34" * 32,
            "timestamp": self.now if number == 104 else self.now - 8,
        }

    def paused(self, number: Any) -> bool:
        return True

    def verify(self, event: Withdrawal) -> dict[str, Any]:
        return {
            "receipt_status": 1,
            "recipient": event.actor,
            "triggered_by": event.actor,
            "remaining_credit": "99",
        }

    def sign_pause(self, *args: Any) -> None:
        pytest.fail("observer reached signer")

    def send(self, *args: Any) -> None:
        pytest.fail("observer reached transaction send")


def source(
    tmp_path: Path, mutation: Any = None, rows: Any = None
) -> tuple[Observer, httpx.Client, ReviewStore]:
    reader = FakeReader()
    raw = observation()["raw"]
    raw.update(
        timestamp=str(reader.now - 8),
        recipient=raw["who"],
        triggeredBy=raw["who"],
        remainingCredit="99",
    )
    rows = [raw] if rows is None else rows

    def handle(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        meta = {
            "deployment": DEPLOYMENT,
            "hasIndexingErrors": False,
            "block": {"number": 104, "hash": "0x" + "34" * 32},
        }
        data: dict[str, Any] = {"_meta": meta}
        if body["variables"]:
            after = int(body["variables"]["after"])
            data["withdrawals"] = [row for row in rows if int(row["sequence"]) > after][:100]
        if mutation:
            mutation(data)
        return httpx.Response(200, json={"data": data})

    client = httpx.Client(transport=httpx.MockTransport(handle))
    store = ReviewStore(tmp_path / "review.sqlite3")
    return Observer(ObserveConfig(), store, reader, client), client, store


def test_keyless_observe_restart_and_duplicate(tmp_path: Path) -> None:
    observer, client, store = source(tmp_path)
    with client:
        assert observer.poll()["added"] == 1
        assert observer.poll()["added"] == 0
    assert ReviewStore(store.path).counts()["observations"] == 1
    policy = store.register_policy({"version": "v1"})
    assert len(ReviewStore(store.path).pending(policy)) == 1
    assert (store.metadata("health") or {})["guardian_paused"] is True


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d["_meta"].update(hasIndexingErrors=True),
        lambda d: d["_meta"].update(deployment="wrong"),
        lambda d: d["_meta"]["block"].update(hash="0x" + "ff" * 32),
        lambda d: (
            d.get("withdrawals")
            and d["withdrawals"][0].update(blockNumber="104", sequence="104000000")
        ),
        lambda d: d.get("withdrawals") and d["withdrawals"][0].update(amount="0"),
        lambda d: d.get("withdrawals") and d["withdrawals"][0].update(recipient="0x" + "ff" * 20),
    ],
)
def test_invalid_or_unconfirmed_source_has_no_observation(tmp_path: Path, mutation: Any) -> None:
    observer, client, store = source(tmp_path, mutation)
    with client, pytest.raises(ValueError):
        observer.poll()
    assert store.counts()["observations"] == 0
    assert (store.metadata("health") or {})["status"] == "degraded"


def test_failed_provider_is_not_empty_healthy_page(tmp_path: Path) -> None:
    observer, client, store = source(tmp_path)
    client.close()
    with pytest.raises(RuntimeError):
        observer.poll()
    assert (store.metadata("health") or {})["status"] == "degraded"


def test_read_rpc_rejects_write_method_before_transport() -> None:
    with httpx.Client() as client:
        with pytest.raises(ValueError, match="Unsupported RPC"):
            ReadRpc("https://rpc.example", client)._read("eth_sendRawTransaction", [])


def test_observer_imports_no_execution_surface() -> None:
    code = Path("sentinel/review/observer.py").read_text(encoding="utf-8")
    imports = {
        node.module for node in ast.walk(ast.parse(code)) if isinstance(node, ast.ImportFrom)
    }
    assert not imports.intersection(
        {
            "sentinel.rpc",
            "sentinel.executor",
            "sentinel.policy",
            "sentinel.runtime",
            "sentinel.ai",
            "sentinel.store",
        }
    )


@pytest.mark.parametrize(
    "field,value",
    [("status", "0x0"), ("blockHash", "0x" + "ff" * 32), ("transactionHash", "0x" + "ff" * 32)],
)
def test_rpc_receipt_disagreement_fails(field: str, value: str) -> None:
    event = Withdrawal.parse(observation()["raw"])
    receipt = {
        "status": "0x1",
        "transactionHash": event.tx_hash,
        "blockNumber": hex(event.block),
        "blockHash": event.block_hash,
        "logs": [],
    }
    receipt[field] = value
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"result": receipt}))
        ) as client,
        pytest.raises(ValueError),
    ):
        ReadRpc("https://rpc.example", client).verify(event)


def test_rpc_validated_receipt_and_amount_mismatch() -> None:
    event = Withdrawal.parse(observation()["raw"])
    topic = "0x" + Web3.keccak(text="Withdrawal(address,address,address,uint256,uint256)").hex()
    actor_topic = "0x" + "0" * 24 + event.actor[2:]
    log = {
        "logIndex": "0x0",
        "address": VAULT,
        "topics": [topic] + [actor_topic] * 3,
        "data": "0x" + f"{event.amount:064x}{99:064x}",
        "removed": False,
    }
    receipt = {
        "status": "0x1",
        "transactionHash": event.tx_hash,
        "blockNumber": hex(event.block),
        "blockHash": event.block_hash,
        "logs": [log],
    }
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"result": receipt}))
    ) as client:
        rpc = ReadRpc("https://rpc.example", client)
        assert rpc.verify(event)["receipt_status"] == 1
        log["data"] = "0x" + f"{event.amount + 1:064x}{99:064x}"
        with pytest.raises(ValueError, match="amount mismatch"):
            rpc.verify(event)


def test_stale_head_and_incomplete_scan_surface_gaps(tmp_path: Path) -> None:
    observer, client, store = source(tmp_path)
    observer.reader.now -= 1000  # type: ignore[attr-defined]
    with client, pytest.raises(ValueError, match="stale"):
        observer.poll()
    assert (store.metadata("health") or {})["status"] == "degraded"


@pytest.mark.parametrize("skew,accepted", [(12, True), (120, False)])
def test_future_clock_skew_is_bounded(tmp_path: Path, skew: int, accepted: bool) -> None:
    observer, client, store = source(tmp_path)
    assert isinstance(observer.reader, FakeReader)
    observer.reader.now += skew
    if accepted:
        # Event timestamp must agree with the newly reported canonical block.
        with client, pytest.raises(ValueError, match="noncanonical"):
            observer.poll()
    else:
        with client, pytest.raises(ValueError, match="stale"):
            observer.poll()
    assert store.counts()["observations"] == 0


def test_bounded_pages_continue_after_restart(tmp_path: Path) -> None:
    observer, client, store = source(tmp_path)
    # Build 101 confirmed withdrawals in one block and a one-page work budget.
    assert isinstance(observer.reader, FakeReader)
    now = observer.reader.now
    rows = [observation(index=i)["raw"] for i in range(101)]
    for row in rows:
        row.update(
            timestamp=str(now - 8),
            recipient=row["who"],
            triggeredBy=row["who"],
            remainingCredit="99",
        )
    client.close()
    observer, client, store = source(tmp_path, rows=rows)
    observer.config = ObserveConfig(max_pages=1)
    with client:
        assert observer.poll()["status"] == "catching_up"
        observer.store = ReviewStore(store.path)
        assert observer.poll()["status"] == "healthy"
    assert store.counts()["observations"] == 101
