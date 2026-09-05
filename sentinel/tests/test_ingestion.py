from copy import deepcopy

import pytest

from sentinel.ingestion import Ingestor
from sentinel.store import StateStore


def event(block=10, log=0):
    tx = "0x" + "ab" * 32
    return {
        "id": tx + log.to_bytes(4, "little").hex(),
        "sequence": str(block * 1_000_000 + log),
        "blockNumber": str(block),
        "logIndex": str(log),
        "transactionHash": tx,
        "blockHash": "0x" + "cd" * 32,
        "timestamp": "100",
        "who": "0x" + "12" * 20,
        "recipient": "0x" + "12" * 20,
        "triggeredBy": "0x" + "12" * 20,
        "amount": "100",
        "remainingCredit": "900",
    }


def reply(rows, block=10):
    return {
        "data": {
            "_meta": {
                "deployment": "expected",
                "hasIndexingErrors": False,
                "block": {"number": block, "hash": "0x" + "cd" * 32},
            },
            "withdrawals": rows,
        }
    }


def test_fixed_snapshot_pagination_and_restart_dedupe(tmp_path):
    path = tmp_path / "db"
    observations = []
    rows = [event(log=0), event(log=1)]

    def fetch(query, variables):
        observations.append(variables)
        return reply([r for r in rows if int(r["sequence"]) > int(variables["after"])][:1])

    ingestor = Ingestor(StateStore(path), fetch, "expected", page_size=1)
    assert ingestor.poll(12, 15) == 2
    assert all(v["block"] == 10 for v in observations)
    assert Ingestor(StateStore(path), fetch, "expected", page_size=1).poll(12, 15) == 0


@pytest.mark.parametrize("mutation", ["identity", "order", "unconfirmed", "deployment", "error"])
def test_bad_pages_never_advance_cursor(tmp_path, mutation):
    store = StateStore(tmp_path / "db")
    response = reply([event()])
    if mutation == "identity":
        response["data"]["withdrawals"][0]["id"] = "0x" + "00" * 36
    elif mutation == "order":
        response["data"]["withdrawals"].append(event())
    elif mutation == "unconfirmed":
        response = reply([event(block=11)])
    elif mutation == "deployment":
        response["data"]["_meta"]["deployment"] = "other"
    else:
        response["errors"] = [{"message": "provider failed"}]
    with pytest.raises(ValueError):
        Ingestor(store, lambda q, v: deepcopy(response), "expected").poll(12, 12)
    assert store.cursor("vault-withdrawals") is None
