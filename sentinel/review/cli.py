"""Keyless review commands. Does not load .env files or execution credentials."""

import argparse
import json
import time
from pathlib import Path

import httpx
import uvicorn

from sentinel.review.api import create_app
from sentinel.review.evidence import LegacyEvidence
from sentinel.review.models import GUARDIAN, VAULT, utc_now
from sentinel.review.observer import ObserveConfig, Observer, ReadRpc
from sentinel.review.rules import ReviewPolicy, process_pending
from sentinel.review.store import ReviewStore


def seed_demo(store: ReviewStore) -> ReviewPolicy:
    store.bind(
        {"origin": "synthetic_fixture", "chain_id": 84532, "vault": VAULT, "guardian": GUARDIAN}
    )
    rows = []
    for i, amount in enumerate((101, 10, 151)):
        tx = "0x" + f"{i + 1:064x}"
        actor = "0x" + "56" * 20
        rows.append(
            {
                "raw": {
                    "id": tx + "00000000",
                    "sequence": str((100 + i) * 1_000_000),
                    "blockNumber": str(100 + i),
                    "blockHash": "0x" + "34" * 32,
                    "transactionHash": tx,
                    "logIndex": "0",
                    "timestamp": "1788625242",
                    "who": actor,
                    "recipient": actor,
                    "triggeredBy": actor,
                    "remainingCredit": "900",
                    "amount": str(amount),
                },
                "origin": "synthetic_fixture",
                "proof": {"verification": "synthetic"},
            }
        )
    store.ingest(rows)
    store.health(
        {
            "status": "synthetic",
            "checked_at": utc_now(),
            "scan_complete": True,
            "guardian_paused": None,
            "gap": "Synthetic fixtures; no chain state queried.",
        }
    )
    policy = ReviewPolicy(version="synthetic-v1", withdrawal_limit="100")
    process_pending(store, policy)
    return policy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("serve", "observe", "demo"))
    parser.add_argument("--state", type=Path)
    parser.add_argument("--policy", type=Path, default=Path("config/review.example.yaml"))
    parser.add_argument("--legacy-state", type=Path)
    parser.add_argument("--port", type=int, default=8089)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use a port between 1024 and 65535")
    path = args.state or Path(
        ".sentinel/review-demo.sqlite3" if args.command == "demo" else ".sentinel/review.sqlite3"
    )
    if args.legacy_state and path.resolve() == args.legacy_state.resolve():
        parser.error("Review and legacy databases must be separate")
    store = ReviewStore(path)
    policy = seed_demo(store) if args.command == "demo" else ReviewPolicy.load(args.policy)
    config = ObserveConfig()
    if args.command == "observe":
        with httpx.Client() as client:
            observer = Observer(config, store, ReadRpc(config.rpc_url, client), client)
            while True:
                try:
                    health = observer.poll()
                    count = process_pending(store, policy)
                    print(
                        json.dumps({"health": health, "evaluated": count, "counts": store.counts()})
                    )
                except Exception as exc:
                    print(json.dumps({"status": "degraded", "error_type": type(exc).__name__}))
                    if args.once:
                        raise SystemExit(1) from None
                if args.once:
                    return
                time.sleep(15)
    else:
        app = create_app(
            store,
            policy,
            LegacyEvidence(args.legacy_state),
            origin=f"http://127.0.0.1:{args.port}",
            observe=None if args.offline or args.command == "demo" else config,
        )
        uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
