"""Operational CLI. No automatic unpause or raw transaction command exists."""

import argparse
import json
import os
from pathlib import Path

import httpx

from sentinel.config import Settings
from sentinel.executor import Executor
from sentinel.graph import GraphSource
from sentinel.policy import Policy
from sentinel.rpc import RpcChain
from sentinel.store import StateStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NexGuard Sentinel operations")
    parser.add_argument("--state", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    reset = commands.add_parser("reset")
    reset.add_argument("--operator", required=True)
    reset.add_argument("--reason", required=True)
    reconcile = commands.add_parser("reconcile")
    reconcile.add_argument("intent", nargs="?")
    commands.add_parser("ingest", help="Ingest one bounded live Graph batch; does not sign")
    args = parser.parse_args(argv)
    try:
        path = args.state or Path(os.environ.get("SENTINEL_STATE_PATH", ".sentinel/state.sqlite3"))
        store = StateStore(path)
        if args.command == "status":
            print(json.dumps(store.status(), sort_keys=True))
        elif args.command == "reset":
            store.reset_latch(args.operator, args.reason)
            print(json.dumps({"reset": True, "operator": args.operator}))
        else:
            settings = Settings.from_env(os.environ)
            chain = RpcChain(settings)  # Read-only: no key provider for operational commands.
            chain.identity()
            if args.command == "reconcile":
                executor = Executor(
                    settings,
                    store,
                    chain,
                    Policy(settings.guardian_address, settings.vault_address),
                )
                if args.intent:
                    print(
                        json.dumps(
                            {"intent": args.intent, "outcome": executor.reconcile(args.intent)}
                        )
                    )
                else:
                    executor.recover_startup()
                    print(json.dumps(store.status(), sort_keys=True))
            else:
                with httpx.Client() as client:
                    source = GraphSource(settings, store, chain.block_hash, client)
                    print(json.dumps({"ingested": source.poll(chain.head())}))
        return 0
    except Exception:
        # Provider exception text may include authenticated RPC/Graph URLs.
        print(json.dumps({"error": "Operation failed; inspect local state and configuration"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
