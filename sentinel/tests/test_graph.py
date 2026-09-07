import json

import httpx
import pytest

from sentinel.graph import GraphSource
from sentinel.models import Withdrawal, canonical_incident, incident_ref
from sentinel.runtime import Runtime
from sentinel.store import StateStore
from sentinel.tests.test_action_loop import BLOCK, GUARDIAN, PROPOSAL, event


def raw_event(index=0, block=100):
    ev = event(index, block)
    return {
        "id": ev.id,
        "sequence": str(ev.sequence),
        "blockNumber": str(ev.block),
        "blockHash": ev.block_hash,
        "transactionHash": ev.tx_hash,
        "logIndex": str(ev.log_index),
        "timestamp": str(ev.timestamp),
        "who": ev.actor,
        "amount": str(ev.amount),
    }


def graph_client(rows, *, height=104, changes=None):
    requests = []

    def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        meta = {"block": {"number": height, "hash": BLOCK}, "hasIndexingErrors": False}
        data = {"_meta": meta}
        if body["variables"]:
            after = int(body["variables"]["after"])
            through = int(body["variables"]["through"])
            data["withdrawals"] = [
                row
                for row in rows
                if int(row["sequence"]) > after and int(row["blockNumber"]) <= through
            ][:100]
        if changes:
            changes(data)
        return httpx.Response(200, json={"data": data})

    return httpx.Client(transport=httpx.MockTransport(handle)), requests


def test_same_timestamp_pagination_confirmation_and_restart(setup):
    settings, store, chain, _, _ = setup
    rows = [raw_event(i) for i in range(101)] + [raw_event(0, 104)]
    client, requests = graph_client(rows)
    with client:
        source = GraphSource(settings, store, chain.block_hash, client)
        assert source.poll(104) == 100  # event zero was already durably ingested by fixture
        assert store.cursor(source.source) == (100_000_100, 100)
        assert len([r for r in requests if r["variables"]]) == 2
        assert len(store.pending_events(source.source, 200)) == 101
        reopened = StateStore(store.path)
        replay = GraphSource(settings, reopened, chain.block_hash, client)
        assert replay.poll(104) == 0
        page_requests = [r for r in requests if r["variables"]]
        assert page_requests[2]["variables"]["after"] == "97999999"
        assert page_requests[2]["variables"]["snapshot"] == 104


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data["_meta"].update(hasIndexingErrors=True),
        lambda data: data["_meta"]["block"].update(hash="0x" + "ab" * 32),
        lambda data: data.update(withdrawals=[raw_event(1), raw_event(0)]),
        lambda data: data.update(withdrawals=[raw_event(0, 104)]),
        lambda data: data.update(withdrawals=[{**raw_event(), "blockHash": "0x" + "ab" * 32}]),
        lambda data: data.update(withdrawals=[{**raw_event(), "id": "0x" + "00" * 36}]),
    ],
)
def test_unhealthy_unordered_unconfirmed_or_noncanonical_pages_latch(setup, mutation):
    settings, store, chain, _, _ = setup
    client, _ = graph_client([raw_event()], changes=mutation)
    with client:
        source = GraphSource(settings, store, chain.block_hash, client)
        before = store.cursor(source.source)
        with pytest.raises(ValueError):
            source.poll(104)
        assert store.cursor(source.source) == before
        assert store.is_latched()


def test_graph_error_is_not_an_empty_page(setup):
    settings, store, chain, _, _ = setup
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"data": None, "errors": [{"message": "no"}]}),
        )
    ) as client:
        source = GraphSource(settings, store, chain.block_hash, client)
        with pytest.raises(ValueError, match="Invalid Graph"):
            source.poll(105)
        assert store.is_latched()


def test_conflicting_replay_latches_and_preserves_original(setup):
    settings, store, chain, _, ev = setup
    client, _ = graph_client([{**raw_event(), "amount": "1"}])
    with client:
        source = GraphSource(settings, store, chain.block_hash, client)
        with pytest.raises(ValueError, match="Conflicting replay"):
            source.poll(105)
        assert store.pending_events(source.source) == [ev]
        assert store.is_latched()


def test_crash_after_ingestion_recovers_unhandled_event(setup):
    settings, store, chain, executor, _ = setup
    client, _ = graph_client([raw_event()])
    with client:
        reopened = StateStore(store.path)
        source = GraphSource(settings, reopened, chain.block_hash, client)
        executor.store = reopened
        runtime = Runtime(source, executor, lambda events: PROPOSAL)
        assert runtime.tick() is not None
        assert runtime.tick() is None
        assert chain.sends == 1


def test_regressed_graph_head_stops_processing(setup):
    settings, store, chain, _, _ = setup
    client, _ = graph_client([], height=99)
    with client:
        with pytest.raises(ValueError, match="regressed"):
            GraphSource(settings, store, chain.block_hash, client).poll(105)
        assert store.is_latched()


@pytest.mark.parametrize(
    "field,value",
    [("amount", "-1"), ("sequence", "1"), ("timestamp", True), ("logIndex", "1000000")],
)
def test_graph_entity_validation(field, value):
    with pytest.raises(ValueError):
        Withdrawal.parse({**raw_event(), field: value})


def test_canonical_incident_golden_vector():
    expected = (
        b'{"chain_id":"84532","guardian":"0x1111111111111111111111111111111111111111",'
        b'"schema_version":1,"severity":"critical","source_ids":['
        b'"0x555555555555555555555555555555555555555555555555555555555555555500000000"],'
        b'"timestamp":"2023-11-14T22:13:20Z"}'
    )
    assert canonical_incident([event()], GUARDIAN) == expected
    assert (
        incident_ref(expected)
        == "0xabb6f5135c6bdbdbc56bd7c89cb9554b28fb6eb97ab81f1c8d771564eb53c01a"
    )
