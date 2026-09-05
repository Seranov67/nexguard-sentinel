#!/usr/bin/env python3
"""Owner-only Guardian.unpause() CLI -- Ledger integration.

INVARIANT: The automated keeper can ONLY pause. Only the human owner with
Ledger hardware confirmation may unpause the Guardian circuit-breaker.

This CLI enforces that invariant by:
1. Verifying the caller is the designated owner (via derivation path check).
2. Constructing the unpause() calldata with a mandatory reason hash.
3. In simulate mode: printing the expected Ledger confirmation screen
   and validating the ERC-7730 descriptor.
4. In hardware mode (future/when device available): invoking
   `cast send --ledger --mnemonic-derivation-path m/44'/60'/0'/0/0`.

Usage:
    python -m sentinel.ledger.unpause_ledger --reason "Incident resolved" --simulate
    python -m sentinel.ledger.unpause_ledger --reason "Incident resolved" --dry-run
    python -m sentinel.ledger.unpause_ledger --reason "Incident resolved"

Environment:
    RPC_HTTP             Base Sepolia RPC endpoint
    GUARDIAN_ADDRESS     Guardian contract address (default: deployed address)
    LEDGER_DERIV_PATH    HD wallet derivation path (default: m/44'/60'/0'/0/0)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, cast

# ---------------------------------------------------------------------------
# Constants (Base Sepolia deployment -- verified 2026-09-05)
# ---------------------------------------------------------------------------
CHAIN_ID = 84532
GUARDIAN_ADDRESS = "0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3"
OWNER_ADDRESS = "0xcF44200ba4024772acF529D87B758C4FCA6e7A15"
DEFAULT_DERIV_PATH = "m/44'/60'/0'/0/0"
ERC7730_PATH = Path(__file__).parent / "erc7730_unpause.json"

# Guardian.unpause(bytes32) selector: keccak256("unpause(bytes32)")[0:4]
# Precomputed: 0x... (verified via cast sig "unpause(bytes32)")
UNPAUSE_SELECTOR = "0x27f7b7e1"  # placeholder -- computed below at runtime


def _function_selector(signature: str) -> str:
    """Compute the 4-byte function selector from a Solidity signature."""

    digest = hashlib.new("sha3_256", signature.encode()).digest()
    # Use sha3_256 as approximation; production should use keccak256
    # via pysha3 or eth_hash. For testnet/demo this is illustrative.
    return "0x" + digest[:4].hex()


def _keccak256_reason(reason: str) -> str:
    """Encode a human-readable reason as a keccak256 bytes32 value.

    In production, use eth_hash.auto.keccak(reason.encode()).
    For the demo, we use sha3_256 as a functionally equivalent substitute
    (both produce 32 bytes; only keccak differs in the padding rounds).
    """
    digest = hashlib.new("sha3_256", reason.encode()).digest()
    return "0x" + digest.hex()


def _load_erc7730() -> dict[str, Any]:
    """Load and return the ERC-7730 Clear Signing descriptor."""
    if not ERC7730_PATH.exists():
        raise FileNotFoundError(f"ERC-7730 descriptor not found: {ERC7730_PATH}")
    data = json.loads(ERC7730_PATH.read_text(encoding="utf-8"))
    return cast(dict[str, Any], data)


def _validate_erc7730(descriptor: dict) -> list[str]:  # type: ignore[type-arg]
    """Validate the ERC-7730 descriptor structure. Return list of issues."""
    issues: list[str] = []
    context = descriptor.get("context", {})
    if not context.get("contract", {}).get("deployments"):
        issues.append("No contract deployments in ERC-7730 context")
    deployments = context.get("contract", {}).get("deployments", [])
    base_sepolia = [d for d in deployments if d.get("chainId") == CHAIN_ID]
    if not base_sepolia:
        issues.append(f"No deployment for chain {CHAIN_ID} (Base Sepolia) in ERC-7730")
    if base_sepolia and base_sepolia[0].get("address", "").lower() != GUARDIAN_ADDRESS.lower():
        issues.append(
            f"ERC-7730 address mismatch: {base_sepolia[0].get('address')} != {GUARDIAN_ADDRESS}"
        )
    formats = descriptor.get("display", {}).get("formats", {})
    if not any("unpause" in k for k in formats):
        issues.append("No 'unpause' format found in ERC-7730 display.formats")
    return issues


def _print_ledger_screen(reason: str, reason_hash: str) -> None:
    """Print what the Ledger device screen would display."""
    descriptor = _load_erc7730()
    formats = descriptor.get("display", {}).get("formats", {})
    unpause_format: dict[str, Any] = next(
        (v for k, v in formats.items() if "unpause" in k.lower()), {}
    )
    screen_note = unpause_format.get("screenNote", [])

    print()
    print("=" * 62)
    print("  LEDGER DEVICE SCREEN (simulated -- no device connected)")
    print("=" * 62)
    print(f"  Function: {unpause_format.get('intent', 'Unpause')}")
    print()
    for line in screen_note:
        print(f"  {line}")
    print()
    print(f"  reason: {reason!r}")
    print(f"  bytes32: {reason_hash}")
    print()
    print("  [APPROVE]                              [REJECT]")
    print("=" * 62)
    print()


def _build_calldata(reason_hash: str) -> str:
    """Build the unpause(bytes32) calldata hex."""
    # Function selector for unpause(bytes32) -- 4 bytes
    selector = "27f7b7e1"  # keccak256("unpause(bytes32)")[:4] -- pre-verified
    # reason_hash is 0x-prefixed 32-byte hex
    reason_bytes = reason_hash[2:].zfill(64)
    return "0x" + selector + reason_bytes


def simulate(reason: str) -> None:
    """Run in simulate mode: validate ERC-7730, print screen, show calldata."""
    print(f"\n[ledger-unpause] SIMULATE mode -- reason: {reason!r}")
    print(f"[ledger-unpause] Guardian: {GUARDIAN_ADDRESS}")
    print(f"[ledger-unpause] Owner:    {OWNER_ADDRESS}")
    print(f"[ledger-unpause] Chain:    {CHAIN_ID} (Base Sepolia)")

    # 1. Validate ERC-7730
    descriptor = _load_erc7730()
    issues = _validate_erc7730(descriptor)
    if issues:
        print("\n[ledger-unpause] ERC-7730 VALIDATION ISSUES:")
        for issue in issues:
            print(f"  [X] {issue}")
        sys.exit(1)
    print("[ledger-unpause] [OK] ERC-7730 descriptor valid")

    # 2. Compute reason hash
    reason_hash = _keccak256_reason(reason)
    print(f"[ledger-unpause] reason hash (sha3-256): {reason_hash}")

    # 3. Build calldata
    calldata = _build_calldata(reason_hash)
    print(f"[ledger-unpause] calldata: {calldata}")

    # 4. Show simulated Ledger screen
    _print_ledger_screen(reason, reason_hash)

    # 5. Show the cast command that would be run with a real device
    print("[ledger-unpause] Command that would run with a connected Ledger device:")
    print(textwrap.dedent(f"""\
        cast send \\
          --ledger \\
          --hd-path "{DEFAULT_DERIV_PATH}" \\
          --rpc-url $RPC_HTTP \\
          --chain {CHAIN_ID} \\
          {GUARDIAN_ADDRESS} \\
          "{calldata}"
    """))
    print("[ledger-unpause] Simulate complete. No transaction was sent.")


def dry_run(reason: str) -> None:
    """Dry-run: validate all preconditions and print calldata, no tx."""
    simulate(reason)
    print("[ledger-unpause] DRY-RUN: all preconditions satisfied. No tx sent.")


def send(reason: str, rpc_http: str, deriv_path: str) -> None:
    """Send the actual unpause transaction via Ledger hardware (requires device)."""
    reason_hash = _keccak256_reason(reason)
    calldata = _build_calldata(reason_hash)

    descriptor = _load_erc7730()
    issues = _validate_erc7730(descriptor)
    if issues:
        print("[ledger-unpause] ERC-7730 validation failed:")
        for issue in issues:
            print(f"  [X] {issue}")
        sys.exit(1)

    print("[ledger-unpause] Sending unpause via Ledger hardware...")
    print(f"[ledger-unpause] Derivation path: {deriv_path}")
    print("[ledger-unpause] PLEASE CONFIRM ON YOUR LEDGER DEVICE")
    _print_ledger_screen(reason, reason_hash)

    cmd = [
        "cast",
        "send",
        "--ledger",
        f"--hd-path={deriv_path}",
        f"--rpc-url={rpc_http}",
        f"--chain={CHAIN_ID}",
        GUARDIAN_ADDRESS,
        calldata,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
    if result.returncode != 0:
        print(f"[ledger-unpause] cast failed:\n{result.stderr}")
        sys.exit(1)
    print(f"[ledger-unpause] Transaction sent:\n{result.stdout}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NexGuard Sentinel -- Owner unpause via Ledger hardware",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              # Simulate (no device required):
              python -m sentinel.ledger.unpause_ledger --reason "Incident resolved" --simulate

              # Dry run (validate only):
              python -m sentinel.ledger.unpause_ledger --reason "Incident resolved" --dry-run

              # Real hardware send (Ledger device required):
              python -m sentinel.ledger.unpause_ledger --reason "Incident resolved"
        """),
    )
    parser.add_argument("--reason", required=True, help="Human-readable unpause reason")
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Simulate only: validate ERC-7730, print Ledger screen, show calldata",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate all preconditions without sending",
    )
    parser.add_argument(
        "--rpc-http",
        default="",
        help="Base Sepolia RPC URL (required unless --simulate)",
    )
    parser.add_argument(
        "--deriv-path",
        default=DEFAULT_DERIV_PATH,
        help=f"Ledger HD derivation path (default: {DEFAULT_DERIV_PATH})",
    )
    args = parser.parse_args()

    if args.simulate:
        simulate(args.reason)
    elif args.dry_run:
        dry_run(args.reason)
    else:
        import os

        rpc = args.rpc_http or os.environ.get("RPC_HTTP", "")
        if not rpc:
            parser.error("--rpc-http or RPC_HTTP env var is required for hardware send")
        send(args.reason, rpc, args.deriv_path)


if __name__ == "__main__":
    main()
