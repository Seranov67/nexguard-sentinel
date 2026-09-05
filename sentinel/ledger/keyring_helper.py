#!/usr/bin/env python3
"""Ledger Key Ring integration helper for NexGuard Sentinel.

Demonstrates using `wallet-cli ring` (Ledger Agent Stack) as the secret
backend for .env.ethonline, replacing plaintext environment variable files.

Before (insecure):
    RPC_HTTP=https://... stored in .env.ethonline (plaintext on disk)

After (Ledger Key Ring):
    Secrets enrolled to wallet-cli ring vault; retrieved at runtime
    via this helper; never stored as plaintext on the filesystem.

Usage:
    # Enroll a secret:
    python -m sentinel.ledger.keyring_helper enroll RPC_HTTP

    # Retrieve a secret (for use in scripts):
    python -m sentinel.ledger.keyring_helper get RPC_HTTP

    # List enrolled keys:
    python -m sentinel.ledger.keyring_helper list

    # Check wallet-cli is installed:
    python -m sentinel.ledger.keyring_helper check

    # Export all enrolled secrets to environment (for subprocess launch):
    python -m sentinel.ledger.keyring_helper export-env
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import textwrap

WALLET_CLI = "wallet-cli"
RING_SUBCOMMAND = "ring"

# Secrets expected for NexGuard Sentinel operation
SENTINEL_SECRETS = [
    "RPC_HTTP",
    "SUBGRAPH_URL",
    "GUARDIAN_ADDRESS",
    "VAULT_ADDRESS",
    "KEEPER_PRIVATE_KEY",
]


def _run(args: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a wallet-cli command."""
    cmd = [WALLET_CLI, RING_SUBCOMMAND, *args]
    return subprocess.run(  # noqa: S603
        cmd,
        capture_output=capture,
        text=True,
    )


def check_installed() -> bool:
    """Return True if wallet-cli is installed and reachable."""
    try:
        result = subprocess.run(  # noqa: S603
            [WALLET_CLI, "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except (FileNotFoundError, OSError):
        return False


def cmd_check() -> None:
    """Verify wallet-cli is installed and print version info."""
    if check_installed():
        result = subprocess.run(  # noqa: S603
            [WALLET_CLI, "--version"], capture_output=True, text=True
        )
        print(f"[OK] wallet-cli found: {result.stdout.strip()}")
        print("   Install path: `npm i -g @ledgerhq/wallet-cli`")
    else:
        print("[X] wallet-cli not found.")
        print("   Install with: npm i -g @ledgerhq/wallet-cli")
        print("   Documentation: https://developers.ledger.com/docs/ai-tools/ledger-cli")
        sys.exit(1)


def cmd_enroll(key: str) -> None:
    """Enroll a secret into the Ledger Key Ring."""
    if not check_installed():
        print("[X] wallet-cli not found. Run: npm i -g @ledgerhq/wallet-cli")
        sys.exit(1)
    print(f"Enrolling secret '{key}' into Ledger Key Ring...")
    print("You will be prompted to enter the secret value.")
    result = _run(["set", key], capture=False)
    if result.returncode != 0:
        print(f"[X] Enrollment failed for key: {key}")
        sys.exit(1)
    print(f"[OK] Secret '{key}' enrolled successfully.")


def cmd_get(key: str) -> None:
    """Retrieve a secret from the Ledger Key Ring and print to stdout."""
    if not check_installed():
        print("[X] wallet-cli not found.")
        sys.exit(1)
    result = _run(["get", key])
    if result.returncode != 0:
        print(f"[X] Failed to retrieve '{key}': {result.stderr.strip()}")
        sys.exit(1)
    print(result.stdout.strip(), end="")


def cmd_list() -> None:
    """List all keys enrolled in the Ledger Key Ring."""
    if not check_installed():
        print("[X] wallet-cli not found.")
        sys.exit(1)
    result = _run(["list"])
    if result.returncode != 0:
        print(f"[X] Failed to list keys: {result.stderr.strip()}")
        sys.exit(1)
    keys = result.stdout.strip()
    print("Enrolled keys in Ledger Key Ring:")
    print(keys if keys else "  (none)")
    print()
    print("Expected for Sentinel:")
    for k in SENTINEL_SECRETS:
        status = "[OK]" if k in keys else "[ ] (not enrolled)"
        print(f"  {status} {k}")


def cmd_export_env() -> None:
    """Export all Sentinel secrets from Key Ring as shell export statements."""
    if not check_installed():
        print("# wallet-cli not found -- falling back to .env.ethonline", file=sys.stderr)
        sys.exit(1)
    lines: list[str] = []
    for key in SENTINEL_SECRETS:
        result = _run(["get", key])
        if result.returncode == 0 and result.stdout.strip():
            val = result.stdout.strip().replace("'", "'\\''")
            lines.append(f"export {key}='{val}'")
        else:
            print(f"# WARNING: {key} not found in Key Ring", file=sys.stderr)
    print("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NexGuard Sentinel -- Ledger Key Ring secret management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Ledger Key Ring replaces plaintext .env files with hardware-backed
            secret storage. Secrets are encrypted and retrieved only when needed.

            Quick start:
              npm i -g @ledgerhq/wallet-cli
              python -m sentinel.ledger.keyring_helper check
              python -m sentinel.ledger.keyring_helper enroll RPC_HTTP
              python -m sentinel.ledger.keyring_helper list

            Documentation: https://developers.ledger.com/docs/ai-tools/ledger-cli#key-ring
        """),
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check", help="Verify wallet-cli is installed")
    enroll_p = sub.add_parser("enroll", help="Enroll a secret into Key Ring")
    enroll_p.add_argument("key", choices=SENTINEL_SECRETS, help="Secret name to enroll")
    get_p = sub.add_parser("get", help="Retrieve a secret from Key Ring")
    get_p.add_argument("key", help="Secret name to retrieve")
    sub.add_parser("list", help="List enrolled keys")
    sub.add_parser("export-env", help="Export all secrets as shell export statements")

    args = parser.parse_args()
    if args.command == "check":
        cmd_check()
    elif args.command == "enroll":
        cmd_enroll(args.key)
    elif args.command == "get":
        cmd_get(args.key)
    elif args.command == "list":
        cmd_list()
    elif args.command == "export-env":
        cmd_export_env()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
