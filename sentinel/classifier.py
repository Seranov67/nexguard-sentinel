"""Deterministic feature extraction and structured AI incident classification.

Safety invariants:
1. Inputs to AI classifier are bounded numeric/structured features only.
2. AI responses are strictly validated JSON matching IncidentClassification schema.
3. Fail-closed: invalid schema, timeouts, unknown enums, or confidence < 0.8
   MUST NOT authorize an on-chain action (classified as rejected/unavailable).
4. Missing AI is unavailable; no deterministic fallback may authorize signing.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, cast

# Hard safety backstops (in Wei)
DEFAULT_CATASTROPHIC_THRESHOLD_WEI = 10 * 10**18
MIN_CONFIDENCE_THRESHOLD = 0.8
MAX_RATIONALE_LENGTH = 240

Severity = Literal["info", "warning", "critical"]
Action = Literal["none", "notify", "pause"]


@dataclass(frozen=True)
class EventFeatures:
    """Bounded aggregate features extracted over a sliding window of Graph events."""

    event_count: int
    total_amount_wei: int
    unique_actors: int
    window_seconds: int
    velocity_bps: int  # basis points (10000 bps = 100% / 1.0x baseline)
    max_single_amount_wei: int
    latest_block: int
    latest_timestamp: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_count": self.event_count,
            "total_amount_wei": str(self.total_amount_wei),
            "unique_actors": self.unique_actors,
            "window_seconds": self.window_seconds,
            "velocity_bps": self.velocity_bps,
            "max_single_amount_wei": str(self.max_single_amount_wei),
            "latest_block": self.latest_block,
            "latest_timestamp": self.latest_timestamp,
        }


@dataclass(frozen=True)
class ClassificationResult:
    """Structured decision returned by the classifier."""

    severity: Severity
    recommended_action: Action
    confidence: float
    rationale: str
    is_catastrophic_override: bool = False
    error: str | None = None

    def is_actionable_pause(self) -> bool:
        """Return True only if a circuit-breaker pause is safely authorized."""
        if self.error is not None:
            return False
        if self.confidence < MIN_CONFIDENCE_THRESHOLD:
            return False
        return self.severity == "critical" and self.recommended_action == "pause"


def extract_features(
    events: list[dict[str, Any]],
    *,
    window_seconds: int = 300,
    baseline_velocity_wei_per_sec: int = 10**15,  # 0.001 ETH / sec
) -> EventFeatures:
    """Extract bounded numeric features from raw Graph withdrawal event records."""
    if not 1 <= window_seconds <= 3600 or len(events) > 1000:
        raise ValueError("Feature window exceeds bounds")
    if events:
        latest = max(int(ev.get("timestamp", 0)) for ev in events)
        events = [ev for ev in events if latest - int(ev.get("timestamp", 0)) < window_seconds]
    if not events:
        return EventFeatures(
            event_count=0,
            total_amount_wei=0,
            unique_actors=0,
            window_seconds=window_seconds,
            velocity_bps=0,
            max_single_amount_wei=0,
            latest_block=0,
            latest_timestamp=0,
        )

    total_amount = 0
    max_single = 0
    actors: set[str] = set()
    max_block = 0
    max_ts = 0

    for ev in events:
        raw_amount = ev.get("amount", 0)
        try:
            amt = int(raw_amount)
        except (ValueError, TypeError):
            amt = 0
        if not 0 <= amt < 2**256:
            raise ValueError("Amount is outside uint256 bounds")
        total_amount += amt
        if amt > max_single:
            max_single = amt

        actor = str(ev.get("who") or ev.get("recipient") or "").lower()
        if actor:
            actors.add(actor)

        blk = int(ev.get("blockNumber", 0) or 0)
        if blk > max_block:
            max_block = blk

        ts = int(ev.get("timestamp", 0) or 0)
        if ts > max_ts:
            max_ts = ts

    effective_window = max(window_seconds, 1)
    current_velocity = total_amount // effective_window
    if baseline_velocity_wei_per_sec > 0:
        velocity_bps = min(10**9, (current_velocity * 10000) // baseline_velocity_wei_per_sec)
    else:
        velocity_bps = 0

    return EventFeatures(
        event_count=len(events),
        total_amount_wei=total_amount,
        unique_actors=len(actors),
        window_seconds=window_seconds,
        velocity_bps=velocity_bps,
        max_single_amount_wei=max_single,
        latest_block=max_block,
        latest_timestamp=max_ts,
    )


def validate_classification_json(raw_json: str) -> ClassificationResult:
    """Parse and strictly validate raw LLM JSON output."""
    try:
        if len(raw_json) > 4096:
            raise ValueError("Response too large")
        data = json.loads(raw_json)
    except Exception as exc:
        return ClassificationResult(
            severity="info",
            recommended_action="none",
            confidence=0.0,
            rationale="JSON parse error",
            error=f"Malformed JSON: {exc}",
        )

    if not isinstance(data, dict):
        return ClassificationResult(
            severity="info",
            recommended_action="none",
            confidence=0.0,
            rationale="Output is not a JSON object",
            error="Non-object JSON payload",
        )

    if set(data) != {"severity", "recommended_action", "confidence", "rationale"}:
        return ClassificationResult("info", "none", 0.0, "Invalid fields", error="Schema mismatch")

    sev = data.get("severity")
    if sev not in ("info", "warning", "critical"):
        return ClassificationResult(
            severity="info",
            recommended_action="none",
            confidence=0.0,
            rationale="Invalid severity enum",
            error=f"Unrecognized severity: {sev!r}",
        )

    act = data.get("recommended_action")
    if act not in ("none", "notify", "pause"):
        return ClassificationResult(
            severity="info",
            recommended_action="none",
            confidence=0.0,
            rationale="Invalid action enum",
            error=f"Unrecognized action: {act!r}",
        )

    conf_raw = data.get("confidence")
    if type(conf_raw) not in (int, float):
        return ClassificationResult(
            severity="info",
            recommended_action="none",
            confidence=0.0,
            rationale="Invalid confidence type",
            error=f"Invalid confidence: {conf_raw!r}",
        )
    try:
        conf = float(cast(float, conf_raw))
    except (ValueError, TypeError):
        return ClassificationResult(
            severity="info",
            recommended_action="none",
            confidence=0.0,
            rationale="Invalid confidence type",
            error=f"Invalid confidence: {conf_raw!r}",
        )
    if not math.isfinite(conf) or not (0.0 <= conf <= 1.0):
        return ClassificationResult(
            severity="info",
            recommended_action="none",
            confidence=0.0,
            rationale="Confidence out of bounds",
            error=f"Confidence out of bounds [0, 1]: {conf}",
        )

    if not isinstance(data.get("rationale"), str) or not data["rationale"].strip():
        return ClassificationResult(
            "info", "none", 0.0, "Invalid rationale", error="Invalid rationale"
        )
    rat = data["rationale"].strip()
    if len(rat) > MAX_RATIONALE_LENGTH:
        return ClassificationResult(
            severity="info",
            recommended_action="none",
            confidence=0.0,
            rationale="Rationale exceeded maximum length",
            error=f"Rationale too long ({len(rat)} > {MAX_RATIONALE_LENGTH})",
        )

    return ClassificationResult(
        severity=cast(Severity, sev),
        recommended_action=cast(Action, act),
        confidence=conf,
        rationale=rat,
        error=None,
    )


def classify_features(
    features: EventFeatures,
    *,
    llm_evaluator: Callable[[dict[str, Any]], str] | None = None,
) -> ClassificationResult:
    """Classify incident features."""
    # 2. Benign if no events
    if features.event_count == 0:
        return ClassificationResult(
            severity="info",
            recommended_action="none",
            confidence=1.0,
            rationale="No activity in current window.",
        )

    # 3. Custom LLM evaluator if injected
    if llm_evaluator is not None:
        try:
            raw_response = llm_evaluator(features.to_dict())
            return validate_classification_json(raw_response)
        except Exception as exc:
            return ClassificationResult(
                severity="info",
                recommended_action="none",
                confidence=0.0,
                rationale="LLM evaluator failed or timed out",
                error=f"Evaluation failed: {exc}",
            )

    return ClassificationResult(
        severity="info",
        recommended_action="none",
        confidence=0.0,
        rationale="No AI evaluator configured",
        error="AI unavailable",
    )
