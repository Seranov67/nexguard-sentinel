"""On-chain action execution and state verification for Guardian circuit-breaker.

Invariants:
1. Keeper can ONLY call pause(bytes32,uint8); cannot unpause.
2. Transaction hash is immediately persisted in StateStore after broadcast.
3. Receipts require confirmation depth before marking success.
4. Onchain paused() state is re-read to confirm desired state reached.
5. Any timeout, RPC disagreement, or state mismatch latches the policy (indeterminate).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any

import httpx
from eth_utils.address import to_checksum_address

from sentinel.store import Outcome, StateStore

PAUSE_SELECTOR = "0xeb63b014"  # keccak256("pause(bytes32,uint8)")[:4]
PAUSED_SELECTOR = "0x5c975abb"  # keccak256("paused()")[:4]


def build_pause_calldata(incident_ref: str, severity: int = 2) -> str:
    """Encode Guardian.pause(bytes32,uint8) calldata hex."""
    if severity not in (1, 2, 3):
        raise ValueError("Invalid pause severity")
    clean_ref = incident_ref.removeprefix("0x")
    try:
        int(clean_ref, 16)
        if len(clean_ref) == 64:
            ref_hex = clean_ref
        else:
            ref_hex = hashlib.sha256(incident_ref.encode("utf-8")).hexdigest()
    except ValueError:
        ref_hex = hashlib.sha256(incident_ref.encode("utf-8")).hexdigest()

    sev_hex = hex(severity).removeprefix("0x").zfill(64)
    return PAUSE_SELECTOR + ref_hex + sev_hex


@dataclass(frozen=True)
class ExecutionResult:
    """Result of an on-chain action execution."""

    outcome: Outcome
    tx_hash: str | None
    block_number: int | None
    evidence: str
    error: str | None = None


class Actuator:
    """Coordinates transaction signing, broadcasting, and post-action verification."""

    def __init__(
        self,
        store: StateStore,
        rpc_http: str,
        guardian_address: str,
        *,
        chain_id: int = 84532,
        keeper_private_key: str | None = None,
        confirmations: int = 2,
    ) -> None:
        if chain_id != 84532 or confirmations < 1:
            raise ValueError("Unsafe chain or confirmation depth")
        self.store = store
        self.rpc_http = rpc_http
        self.guardian_address = guardian_address
        self.chain_id = chain_id
        self.keeper_private_key = keeper_private_key
        self.confirmations = confirmations

    def _rpc_call(self, method: str, params: list[Any]) -> Any:  # noqa: ANN401
        """Send JSON-RPC call to Base Sepolia node."""
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        with httpx.Client(timeout=3) as client:
            resp = client.post(self.rpc_http, json=payload)
            resp.raise_for_status()
            data = resp.json()
        if "error" in data:
            raise RuntimeError(f"RPC error {method}: {data['error']['message']}")
        return data.get("result")

    def verify_identity(self) -> None:
        if self.guardian_address.lower() != "0x8b7b1ee7e335fd00f35cc6272c113c8735cb8ed3":
            raise ValueError("Guardian is outside the approved deployment allowlist")
        if int(self._rpc_call("eth_chainId", []), 16) != 84532:
            raise ValueError("RPC chain mismatch")
        code = self._rpc_call("eth_getCode", [self.guardian_address, "latest"])
        if not code or code == "0x":
            raise ValueError("Guardian has no deployed code")

    def is_paused_onchain(self) -> bool:
        result = self._rpc_call(
            "eth_call", [{"to": self.guardian_address, "data": PAUSED_SELECTOR}, "latest"]
        )
        if result not in ("0x" + "0" * 64, "0x" + "0" * 63 + "1"):
            raise ValueError("Malformed Guardian state")
        return int(result, 16) == 1

    def _uncertain(self, intent_id: str, tx_hash: str | None, reason: str) -> ExecutionResult:
        evidence = json.dumps({"error": reason, "tx_hash": tx_hash})
        # Storage failure propagates and stops the caller; never silently continue.
        self.store.finish(intent_id, "indeterminate", evidence)
        return ExecutionResult("indeterminate", tx_hash, None, evidence, reason)

    def verify_transaction(self, intent_id: str, tx_hash: str) -> ExecutionResult:
        """Confirm receipt identity, canonical block, depth and final state without sending."""
        try:
            self.verify_identity()
            for _ in range(12):
                receipt = self._rpc_call("eth_getTransactionReceipt", [tx_hash])
                if receipt is not None:
                    if receipt["transactionHash"].lower() != tx_hash.lower():
                        raise ValueError("Receipt transaction mismatch")
                    if receipt["to"].lower() != self.guardian_address.lower():
                        raise ValueError("Receipt destination mismatch")
                    block = int(receipt["blockNumber"], 16)
                    head = int(self._rpc_call("eth_blockNumber", []), 16)
                    canonical = self._rpc_call("eth_getBlockByNumber", [hex(block), False])
                    if canonical is None or canonical["hash"] != receipt["blockHash"]:
                        raise ValueError("Receipt is not canonical")
                    if head - block + 1 >= self.confirmations:
                        # Re-fetch after observing depth: a reorg must not become success.
                        again = self._rpc_call("eth_getTransactionReceipt", [tx_hash])
                        if again != receipt:
                            raise ValueError("Receipt changed during verification")
                        status = int(receipt["status"], 16)
                        if status not in (0, 1):
                            raise ValueError("Invalid receipt status")
                        transaction = self._rpc_call("eth_getTransactionByHash", [tx_hash])
                        intent = self.store.intent(intent_id)
                        if intent is None or transaction is None:
                            raise ValueError("Missing transaction identity")
                        expected = build_pause_calldata(str(intent["incident_id"]), 3)
                        actual = transaction["input"].lower()
                        if (
                            transaction["to"].lower() != self.guardian_address.lower()
                            or int(transaction["nonce"], 16) != intent["nonce"]
                            or actual[:-64] != expected[:-64]
                            or int(actual[-64:], 16) not in (1, 2, 3)
                        ):
                            raise ValueError("Transaction does not match reserved pause intent")
                        if status == 1 and not self.is_paused_onchain():
                            raise ValueError("Confirmed receipt but Guardian is not paused")
                        outcome: Outcome = "success" if status == 1 else "reverted"
                        evidence = json.dumps(
                            {
                                "tx_hash": tx_hash,
                                "block_number": block,
                                "block_hash": receipt["blockHash"],
                                "status": status,
                                "confirmations": head - block + 1,
                                "simulated": False,
                            }
                        )
                        self.store.finish(intent_id, outcome, evidence)
                        return ExecutionResult(outcome, tx_hash, block, evidence)
                time.sleep(2)
            return self._uncertain(intent_id, tx_hash, "Receipt or confirmation timeout")
        except (ValueError, KeyError, TypeError, RuntimeError, httpx.HTTPError):
            return self._uncertain(intent_id, tx_hash, "RPC verification failed or disagreed")

    def reconcile(self, intent_id: str) -> ExecutionResult:
        intent = self.store.intent(intent_id)
        if intent is None or intent["status"] not in (
            "reserved",
            "prepared",
            "broadcast",
            "indeterminate",
        ):
            raise ValueError("Reconciliation requires an unfinished intent")
        tx_hash = intent["tx_hash"]
        if not isinstance(tx_hash, str):
            return self._uncertain(
                intent_id, None, "No persisted hash; manual investigation required"
            )
        return self.verify_transaction(intent_id, tx_hash)

    def execute_pause(
        self,
        intent_id: str,
        incident_ref: str,
        severity: int = 2,
        *,
        dry_run: bool = False,
    ) -> ExecutionResult:
        """Persist the signed hash before send; never infer simulation from a missing key."""
        calldata = build_pause_calldata(incident_ref, severity)
        if dry_run:
            raise ValueError("Dry-run must not reserve or mutate the live action store")
        if not self.keeper_private_key:
            raise ValueError("Live execution requires a keeper key")
        tx_hash: str | None = None
        try:
            from eth_account import Account

            self.verify_identity()
            if self.is_paused_onchain():
                evidence = json.dumps({"reason": "Already paused", "simulated": False})
                self.store.finish(intent_id, "already_desired", evidence)
                return ExecutionResult("already_desired", None, None, evidence)
            account = Account.from_key(self.keeper_private_key)
            nonce = int(self._rpc_call("eth_getTransactionCount", [account.address, "pending"]), 16)
            gas_price = int(self._rpc_call("eth_gasPrice", []), 16)
            self.store.prepare(intent_id, nonce, json.dumps({"gasPrice": gas_price}))
            signed = account.sign_transaction(
                {
                    "to": to_checksum_address(self.guardian_address),
                    "value": 0,
                    "gas": 150000,
                    "gasPrice": gas_price,
                    "nonce": nonce,
                    "chainId": 84532,
                    "data": calldata,
                }
            )
            tx_hash = "0x" + signed.hash.hex()
            # Persist the deterministic signed hash BEFORE broadcasting. A lost RPC
            # response can then be reconciled by hash with no replacement/resend.
            self.store.broadcast(intent_id, tx_hash)
            returned = self._rpc_call(
                "eth_sendRawTransaction", ["0x" + signed.raw_transaction.hex()]
            )
            if returned != tx_hash:
                return self._uncertain(intent_id, tx_hash, "Broadcast hash mismatch")
        except (ValueError, KeyError, TypeError, RuntimeError, httpx.HTTPError):
            return self._uncertain(intent_id, tx_hash, "Signing or broadcast failed; reconcile")
        return self.verify_transaction(intent_id, tx_hash)
