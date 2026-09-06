"""Deterministic ActionPolicy enforcing safety invariants before transaction reservation.

Invariants:
1. Final decision authority is deterministic code, not LLM output.
2. Policy refuses action if store is latched or action is not in allowlist.
3. Cooldown and rate limits prevent rapid repeated pause attempts.
4. Pre-read of contract state prevents redundant transaction if already paused.
5. Atomic reservation in StateStore ensures at-most-once execution per intent.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from sentinel.classifier import ClassificationResult
from sentinel.proof import incident_proof
from sentinel.store import StateStore

DecisionStatus = Literal[
    "allowed",
    "latched",
    "already_in_desired_state",
    "cooldown_active",
    "unauthorized_action",
    "low_severity",
    "reservation_failed",
]


@dataclass(frozen=True)
class PolicyDecision:
    """Result of policy evaluation for a candidate action."""

    status: DecisionStatus
    allowed: bool
    intent_id: str
    incident_id: str
    reason: str


class ActionPolicy:
    """Enforces protocol safety rules, rate limits, and durable reservations."""

    def __init__(
        self,
        store: StateStore,
        *,
        chain_id: int = 84532,
        guardian_address: str = "0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3",
        cooldown_seconds: int = 300,  # 5 minute cooldown between pause actions
        onchain_state_reader: Callable[[], bool] | None = None,
    ) -> None:
        self.store = store
        self.chain_id = chain_id
        self.guardian_address = guardian_address
        self.cooldown_seconds = cooldown_seconds
        self._onchain_state_reader = onchain_state_reader
        if chain_id != 84532 or cooldown_seconds < 0:
            raise ValueError("Unsafe policy chain or cooldown")

    def evaluate_and_reserve(
        self,
        classification: ClassificationResult,
        event_ids: list[str],
        *,
        current_time: float | None = None,
    ) -> PolicyDecision:
        """Evaluate candidate action and atomically reserve in StateStore if allowed."""
        now = time.time() if current_time is None else current_time

        # Compute stable deterministic incident_id and intent_id from event_ids
        canonical_json, incident_id = incident_proof(
            self.chain_id, self.guardian_address, event_ids
        )
        intent_id = f"intent_pause_{incident_id[2:]}"

        # 1. Gate: Check if policy is latched
        if self.store.is_latched():
            return PolicyDecision(
                status="latched",
                allowed=False,
                intent_id=intent_id,
                incident_id=incident_id,
                reason="StateStore is latched; manual reconciliation or reset required.",
            )

        # 2. Gate: Check actionability from classifier
        if not classification.is_actionable_pause():
            return PolicyDecision(
                status="low_severity",
                allowed=False,
                intent_id=intent_id,
                incident_id=incident_id,
                reason=(
                    f"Classification is not an actionable critical pause "
                    f"(severity={classification.severity}, "
                    f"action={classification.recommended_action}, "
                    f"confidence={classification.confidence:.2f})."
                ),
            )

        # 3. Gate: Check cooldown budget
        if self.store.rate_limited(now, self.cooldown_seconds):
            return PolicyDecision(
                status="cooldown_active",
                allowed=False,
                intent_id=intent_id,
                incident_id=incident_id,
                reason="Durable cooldown or action budget active.",
            )

        # 4. Gate: Pre-read onchain contract state
        if self._onchain_state_reader is not None:
            try:
                is_paused = self._onchain_state_reader()
                if is_paused:
                    return PolicyDecision(
                        status="already_in_desired_state",
                        allowed=False,
                        intent_id=intent_id,
                        incident_id=incident_id,
                        reason="Guardian is already paused onchain; no transaction needed.",
                    )
            except Exception as exc:
                self.store.set_latch("Contract state read failed")
                return PolicyDecision(
                    status="latched",
                    allowed=False,
                    intent_id=intent_id,
                    incident_id=incident_id,
                    reason=f"Failed to read onchain state: {exc}",
                )

        # 5. Gate: Atomic reservation in StateStore
        try:
            reserved = self.store.reserve(
                intent_id,
                incident_id,
                event_ids,
                now=now,
                cooldown=self.cooldown_seconds,
                canonical_json=canonical_json,
            )
            if not reserved:
                return PolicyDecision(
                    status="reservation_failed",
                    allowed=False,
                    intent_id=intent_id,
                    incident_id=incident_id,
                    reason=(
                        "Durable reservation rejected by store (duplicate event or active intent)."
                    ),
                )
            return PolicyDecision(
                status="allowed",
                allowed=True,
                intent_id=intent_id,
                incident_id=incident_id,
                reason=f"Action reserved successfully for {len(event_ids)} events.",
            )
        except Exception as exc:
            return PolicyDecision(
                status="reservation_failed",
                allowed=False,
                intent_id=intent_id,
                incident_id=incident_id,
                reason=f"Durable reservation failed: {exc}",
            )
