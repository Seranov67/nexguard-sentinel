"""Reserve before signer access; uncertain outcomes reconcile without resend."""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from sentinel.config import Settings
from sentinel.models import Proposal, Withdrawal, canonical_incident, incident_ref
from sentinel.policy import Policy
from sentinel.store import Outcome, StateStore


@dataclass(frozen=True)
class SignedPause:
    nonce: int
    fees: str
    tx_hash: str
    raw: bytes


@dataclass(frozen=True)
class Receipt:
    tx_hash: str
    block: int
    block_hash: str
    status: int
    incident_ref: str | None
    severity: int | None


class Chain(Protocol):
    def identity(self) -> tuple[int, str, str]: ...
    def head(self) -> int: ...
    def block_hash(self, block: int) -> str: ...
    def paused(self, block: int | None = None) -> bool: ...
    def sign_pause(self, ref: str, severity: int) -> SignedPause: ...
    def send(self, signed: SignedPause) -> str: ...
    def receipt(self, tx_hash: str) -> Receipt | None: ...


class Executor:
    def __init__(
        self,
        settings: Settings,
        store: StateStore,
        chain: Chain,
        policy: Policy,
        *,
        timeout: float = 60,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if settings.confirmations < 1 or settings.chain_id != 84532 or timeout < 0:
            raise ValueError("Invalid execution finality or timeout settings")
        self.settings, self.store, self.chain, self.policy = settings, store, chain, policy
        self.timeout, self.clock, self.sleep = timeout, clock, sleep

    def act(self, events: list[Withdrawal], proposal: Proposal) -> str | None:
        proof = canonical_incident(events, self.settings.guardian_address)
        ref = incident_ref(proof)
        try:
            identity = self.chain.identity()
            # Revalidate canonical source blocks immediately before reservation/signing.
            for event in events:
                if (
                    event.block_hash != self.chain.block_hash(event.block).lower()
                    or self.chain.head() - event.block + 1 < self.settings.confirmations
                ):
                    raise ValueError("Source event lost finality")
            if not self.store.check_and_reserve(
                ref, events, proof.decode(), self.policy, proposal, *identity
            ):
                return None
            if self.chain.paused():
                self.store.finish(ref, "already_desired", "Guardian pre-read is paused")
                return ref
            if self.chain.identity() != identity:
                raise ValueError("Chain identity changed before signing")
            signed = self.chain.sign_pause(ref, 3)
            # Includes deterministic signed hash BEFORE network send, so a process crash
            # after broadcast but before broadcast() can still be reconciled by hash.
            self.store.prepare(ref, signed.nonce, signed.fees, signed.tx_hash)
            if self.chain.identity() != identity or self.store.is_latched():
                raise ValueError("Identity changed or execution latched before send")
            actual_hash = self.chain.send(signed)
            if actual_hash.lower() != signed.tx_hash.lower():
                raise ValueError("RPC returned a different transaction hash")
            self.store.broadcast(ref, actual_hash)
            self.reconcile(ref, wait=True)
            return ref
        except Exception:
            self._uncertain(ref, "Action failed; inspect and reconcile persisted intent")
            raise

    def _uncertain(self, ref: str, reason: str) -> None:
        row = self.store.intent(ref)
        if row is not None and row["status"] in ("reserved", "prepared", "broadcast"):
            self.store.finish(ref, "indeterminate", reason)
        else:
            self.store.set_latch(reason)

    def recover_startup(self) -> None:
        unfinished = self.store.unfinished()
        if unfinished:
            self.store.set_latch("Unfinished intent found at startup; reconciliation required")
        for ref in unfinished:
            self.reconcile(ref)

    def reconcile(self, ref: str, *, wait: bool = False) -> Outcome:
        row = self.store.intent(ref)
        if row is None:
            raise ValueError("Unknown intent")
        status = row["status"]
        if status == "success":
            return "success"
        if status == "reverted":
            return "reverted"
        if status == "already_desired":
            return "already_desired"
        tx_hash = row["tx_hash"]
        if not isinstance(tx_hash, str):
            self._uncertain(ref, "No persisted signed hash; never resend automatically")
            return "indeterminate"
        deadline = self.clock() + (self.timeout if wait else 0)
        try:
            while True:
                chain, guardian, vault = self.chain.identity()
                if (
                    chain != 84532
                    or guardian.lower() != self.policy.guardian.lower()
                    or vault.lower() != self.policy.vault.lower()
                ):
                    raise ValueError("Reconciliation identity mismatch")
                receipt = self.chain.receipt(tx_hash)
                if receipt is not None:
                    if (
                        receipt.tx_hash.lower() != tx_hash.lower()
                        or receipt.status not in (0, 1)
                        or receipt.block_hash != self.chain.block_hash(receipt.block)
                    ):
                        raise ValueError("Noncanonical receipt")
                    head = self.chain.head()
                    if head - receipt.block + 1 >= self.settings.confirmations:
                        # State at a named block, followed by another canonicality check.
                        head_hash = self.chain.block_hash(head)
                        paused = self.chain.paused(head)
                        if head_hash != self.chain.block_hash(
                            head
                        ) or receipt.block_hash != self.chain.block_hash(receipt.block):
                            raise ValueError("Chain changed during verification")
                        if receipt.status == 1 and (
                            not paused or receipt.incident_ref != ref or receipt.severity != 3
                        ):
                            raise ValueError("Pause state or event proof mismatch")
                        outcome: Outcome = "success" if receipt.status == 1 else "reverted"
                        # A prepared hash may have been mined after a process crash.
                        if row["status"] == "prepared":
                            self.store.broadcast(ref, tx_hash)
                        evidence = json.dumps(
                            {
                                "tx_hash": tx_hash,
                                "block": receipt.block,
                                "block_hash": receipt.block_hash,
                                "verified_head": head,
                                "paused": paused,
                                "receipt_status": receipt.status,
                            }
                        )
                        self.store.finish(ref, outcome, evidence)
                        return outcome
                if self.clock() >= deadline:
                    break
                self.sleep(min(1, max(0, deadline - self.clock())))
        except Exception:
            self._uncertain(ref, "Receipt, RPC, proof or state verification failed")
            raise
        self._uncertain(ref, "Receipt or confirmation timeout; reconciliation required")
        return "indeterminate"
