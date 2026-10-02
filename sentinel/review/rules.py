"""Integer review findings. These rules never authorize chain actions."""

from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.models import Withdrawal
from sentinel.review.models import CHAIN_ID, UNIT, VAULT, digest
from sentinel.review.store import ReviewConflictError, ReviewStore


class ReviewPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    version: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    withdrawal_limit: str = Field(min_length=1, max_length=78, pattern=r"^(0|[1-9][0-9]*)$")

    @model_validator(mode="after")
    def uint256_limit(self) -> Self:
        if int(self.withdrawal_limit) >= 2**256:
            raise ValueError("Threshold exceeds uint256")
        return self

    @classmethod
    def load(cls, path: Path) -> "ReviewPolicy":
        if path.stat().st_size > 65536:
            raise ValueError("Policy file too large")
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

    def definition(self) -> dict[str, Any]:
        return {
            **self.model_dump(),
            "chain_id": CHAIN_ID,
            "vault": VAULT,
            "rule": "single_withdrawal_limit",
            "comparison": ">",
            "unit": UNIT,
        }

    def evaluate(self, observation: dict[str, Any]) -> dict[str, Any]:
        event = Withdrawal.parse(observation["raw"])
        if not 0 < event.amount < 2**256:
            raise ValueError("Withdrawal amount must be a positive uint256")
        origin = observation["origin"]
        if origin not in ("live_graph_rpc", "synthetic_fixture"):
            raise ValueError("Unknown evidence origin")
        if origin == "live_graph_rpc" and (
            observation["proof"].get("receipt_status") != 1
            or observation["proof"].get("confirmations", 0) < 2
        ):
            raise ValueError("Confirmed source proof required")
        breached = event.amount > int(self.withdrawal_limit)
        fingerprint = digest(self.definition())
        identity = {
            "chain_id": CHAIN_ID,
            "vault": VAULT,
            "source_ids": [event.id],
            "rule": "single_withdrawal_limit",
            "policy": fingerprint,
        }
        return {
            **identity,
            "case_id": digest(identity) if breached else None,
            "policy_version": self.version,
            "breached": breached,
            "observed_amount": str(event.amount),
            "threshold": self.withdrawal_limit,
            "unit": UNIT,
            "comparison": ">",
            "authorization": "review_only",
            "origin": origin,
            "synthetic": origin == "synthetic_fixture",
            "reason": "Withdrawal exceeds configured limit"
            if breached
            else "Withdrawal is within configured limit",
        }


def process_pending(store: ReviewStore, policy: ReviewPolicy, limit: int = 100) -> int:
    """Crash retry is driven by unevaluated durable observations, not the source cursor."""
    health = store.metadata("health") or {}
    if health.get("status") not in ("healthy", "synthetic"):
        raise ReviewConflictError("Complete source verification required before evaluating")
    fingerprint = store.register_policy(policy.definition())
    processed = 0
    for observation in store.pending(fingerprint, limit):
        finding = policy.evaluate(observation)
        try:
            store.evaluated(observation["id"], fingerprint, finding)
        except ReviewConflictError:
            # A replay can flag this event after pending() selected the batch.
            # Preserve the conflict without blocking unrelated verified observations.
            continue
        processed += 1
    return processed
