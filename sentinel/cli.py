"""Command line operational interface for NexGuard Sentinel.

Commands:
  sentinel status                       Show latch, cursor, Guardian state, and recent intents
  sentinel run [--once] [--dry-run]     Start or step the Sentinel control loop
  sentinel reset --operator X --reason Y Reset the durable safety latch with audit trail
  sentinel reconcile <intent_id>        Check onchain state for an unresolved intent
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from sentinel.actuator import Actuator
from sentinel.config import Settings
from sentinel.loop import run_loop_step
from sentinel.store import StateStore


def _load_settings_and_store() -> tuple[Settings, StateStore]:
    from dotenv import load_dotenv

    if Path(".env.ethonline").exists():
        load_dotenv(".env.ethonline")
    else:
        load_dotenv()

    settings = Settings.from_env(os.environ)
    store = StateStore(settings.state_path)
    return settings, store


def cmd_status(settings: Settings, store: StateStore) -> None:
    """Display system status, latch state, cursor position, and onchain state."""
    print("==================================================")
    print("  NexGuard Sentinel -- System Status")
    print("==================================================")
    print(f"Chain ID:           {settings.chain_id} (Base Sepolia)")
    print(f"Guardian Contract:  {settings.guardian_address}")
    print(f"Vault Contract:     {settings.vault_address}")
    print(f"State DB:           {settings.state_path}")

    # Latch status
    if store.is_latched():
        reason = store.latch_reason() or "Indeterminate state"
        print(f"Safety Latch:       [LATCHED] (Reason: {reason})")
    else:
        print("Safety Latch:       [NORMAL] (Not latched)")

    # Cursor status
    cursor = store.cursor("the_graph_withdrawals")
    if cursor:
        print(f"Cursor Sequence:    {cursor[0]} (Block: {cursor[1]})")
    else:
        print("Cursor Sequence:    (No events ingested yet)")

    # Onchain Guardian pause status
    actuator = Actuator(
        store=store,
        rpc_http=settings.rpc_http,
        guardian_address=settings.guardian_address,
    )
    try:
        is_paused = actuator.is_paused_onchain()
        print(f"Guardian Status:    {'PAUSED' if is_paused else 'ACTIVE (Unpaused)'}")
    except Exception as exc:
        print(f"Guardian Status:    [RPC Query Failed: {exc}]")

    print("==================================================")


def cmd_reset(store: StateStore, operator: str, reason: str) -> None:
    """Reset the safety latch with operator attribution."""
    if not store.is_latched():
        print("[sentinel] Store is not latched. Nothing to reset.")
        return
    store.reset_latch(operator, reason)
    print(f"[sentinel] Safety latch successfully reset by operator '{operator}'.")
    print(f"[sentinel] Reason logged: '{reason}'")


def cmd_reconcile(settings: Settings, store: StateStore, intent_id: str) -> None:
    """Reconcile an intent against onchain transaction and state."""
    intent = store.intent(intent_id)
    if not intent:
        print(f"[sentinel] Error: intent '{intent_id}' not found in store.")
        sys.exit(1)

    print(f"Reconciling Intent: {intent_id}")
    print(f"  Status:   {intent['status']}")
    print(f"  Nonce:    {intent['nonce']}")
    print(f"  Tx Hash:  {intent['tx_hash']}")

    actuator = Actuator(
        store=store,
        rpc_http=settings.rpc_http,
        guardian_address=settings.guardian_address,
    )
    is_paused = actuator.is_paused_onchain()
    print(f"  Guardian Paused Onchain: {is_paused}")

    if intent['status'] in ('success', 'already_desired') and is_paused:
        print("  Reconciliation result: Intent matches onchain state.")
    elif intent['status'] == 'indeterminate':
        print("  Reconciliation warning: Intent marked indeterminate. Check tx hash on Basescan.")


def cmd_run(
    settings: Settings, store: StateStore, *, once: bool = False, dry_run: bool = False
) -> None:
    """Run the Sentinel event loop."""
    print(f"[sentinel] Starting loop (dry_run={dry_run}, once={once}) ...")
    keeper_key = os.environ.get("KEEPER_PRIVATE_KEY", "")

    while True:
        result = run_loop_step(settings, store, dry_run=dry_run, keeper_private_key=keeper_key)
        if result.is_latched:
            print("[sentinel] Loop stopped: StateStore is latched.")
            break

        if result.new_events > 0:
            dec_str = result.decision.status if result.decision else "None"
            print(f"[sentinel] Processed {result.new_events} events. Decision: {dec_str}")
            if result.execution:
                outcome = result.execution.outcome
                tx_hash = result.execution.tx_hash
                print(f"[sentinel] Pause execution: {outcome} (tx: {tx_hash})")

        if once:
            print("[sentinel] Single pass completed.")
            break

        time.sleep(10)


def main() -> None:
    parser = argparse.ArgumentParser(description="NexGuard Sentinel -- Autonomous Circuit Breaker")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # status
    sub.add_parser("status", help="Show system and latch status")

    # run
    run_p = sub.add_parser("run", help="Run the Sentinel loop")
    run_p.add_argument("--once", action="store_true", help="Run a single iteration and exit")
    run_p.add_argument(
        "--dry-run", action="store_true", help="Simulate actions without broadcasting transactions"
    )

    # reset
    reset_p = sub.add_parser("reset", help="Reset the safety latch")
    reset_p.add_argument("--operator", required=True, help="Operator identifier for audit trail")
    reset_p.add_argument(
        "--reason", required=True, help="Mandatory explanation for resetting latch"
    )

    # reconcile
    rec_p = sub.add_parser("reconcile", help="Reconcile an intent against onchain state")
    rec_p.add_argument("intent_id", help="The intent identifier to reconcile")

    args = parser.parse_args()

    try:
        settings, store = _load_settings_and_store()
    except Exception as exc:
        print(f"[sentinel] Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.subcommand == "status":
        cmd_status(settings, store)
    elif args.subcommand == "run":
        cmd_run(settings, store, once=args.once, dry_run=args.dry_run)
    elif args.subcommand == "reset":
        cmd_reset(store, args.operator, args.reason)
    elif args.subcommand == "reconcile":
        cmd_reconcile(settings, store, args.intent_id)


if __name__ == "__main__":
    main()
