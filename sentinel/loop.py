"""End-to-end event loop connecting The Graph, Classifier, Policy, and Actuator.

Lifecycle on each cycle:
1. Check latch state: if latched, halt processing and report status.
2. Query next page of confirmed events from The Graph Subgraph.
3. Extract aggregate features over the configured sliding window.
4. Classify incident features with structured fail-closed schema.
5. Evaluate ActionPolicy (cooldown, budget, pre-read, atomic reservation).
6. If policy permits: trigger Actuator to broadcast Guardian.pause().
7. Advance cursor and commit processed event IDs to StateStore.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sentinel.actuator import Actuator, ExecutionResult
from sentinel.classifier import (
    ClassificationResult,
    EventFeatures,
    classify_features,
    extract_features,
)
from sentinel.config import Settings
from sentinel.policy import ActionPolicy, PolicyDecision
from sentinel.store import StateStore

logger = logging.getLogger("sentinel.loop")


@dataclass(frozen=True)
class LoopStepResult:
    """Outcome of a single event loop iteration."""

    events_polled: int
    new_events: int
    is_latched: bool
    features: EventFeatures | None = None
    classification: ClassificationResult | None = None
    decision: PolicyDecision | None = None
    execution: ExecutionResult | None = None
    cursor_advanced: bool = False


def poll_graph_subgraph(
    subgraph_url: str,
    after_sequence: str,
    first: int = 100,
) -> list[dict[str, Any]]:
    """Poll The Graph endpoint for new confirmed withdrawal events."""
    import httpx

    if not subgraph_url:
        return []

    query = """query Withdrawals($after: BigInt!, $first: Int!) {
      withdrawals(
        first: $first,
        orderBy: sequence,
        orderDirection: asc,
        where: {sequence_gt: $after}
      ) {
        id sequence blockNumber blockHash transactionHash logIndex timestamp
        who recipient triggeredBy amount remainingCredit
      }
    }"""
    variables = {"after": after_sequence, "first": first}

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(subgraph_url, json={"query": query, "variables": variables})
            if resp.status_code != 200:
                return []
            data = resp.json().get("data", {})
            return list(data.get("withdrawals", []))
    except Exception:
        return []


def run_loop_step(
    settings: Settings,
    store: StateStore,
    *,
    events_override: list[dict[str, Any]] | None = None,
    dry_run: bool = False,
    keeper_private_key: str | None = None,
    llm_evaluator: Callable[[dict[str, Any]], str] | None = None,
) -> LoopStepResult:
    """Execute one atomic pass of the Sentinel control loop."""
    # 1. Check latch
    if store.is_latched():
        return LoopStepResult(events_polled=0, new_events=0, is_latched=True)

    # 2. Ingest events
    source_name = "the_graph_withdrawals"
    cursor_row = store.cursor(source_name)
    current_seq = str(cursor_row[0]) if cursor_row else "0"

    if events_override is not None:
        raw_events = events_override
    else:
        raw_events = poll_graph_subgraph(settings.subgraph_url, current_seq)

    if not raw_events:
        return LoopStepResult(events_polled=0, new_events=0, is_latched=False)

    # 3. Ingest events into StateStore first so foreign keys are satisfied
    import json
    for ev in raw_events:
        ev_id = str(ev.get("id"))
        ev_seq = int(ev.get("sequence", 0))
        ev_blk = int(ev.get("blockNumber", 0))
        store.ingest(source_name, ev_id, ev_seq, ev_blk, json.dumps(ev))

    # 4. Extract features & classify
    features = extract_features(raw_events)
    classification = classify_features(features, llm_evaluator=llm_evaluator)

    # 5. Evaluate ActionPolicy
    actuator = Actuator(
        store=store,
        rpc_http=settings.rpc_http,
        guardian_address=settings.guardian_address,
        chain_id=settings.chain_id,
        keeper_private_key=keeper_private_key,
        confirmations=settings.confirmations,
    )

    def safe_onchain_reader() -> bool:
        try:
            return actuator.is_paused_onchain()
        except Exception:
            if dry_run:
                return False
            raise

    policy = ActionPolicy(
        store=store,
        chain_id=settings.chain_id,
        guardian_address=settings.guardian_address,
        onchain_state_reader=safe_onchain_reader,
    )

    event_ids = [str(ev.get("id")) for ev in raw_events if ev.get("id")]
    decision = policy.evaluate_and_reserve(classification, event_ids)

    execution: ExecutionResult | None = None
    if decision.allowed:
        # 6. Actuate pause
        execution = actuator.execute_pause(
            intent_id=decision.intent_id,
            incident_ref=decision.incident_id,
            severity=2 if classification.severity == "critical" else 1,
            dry_run=dry_run,
        )

    return LoopStepResult(
        events_polled=len(raw_events),
        new_events=len(event_ids),
        is_latched=store.is_latched(),
        features=features,
        classification=classification,
        decision=decision,
        execution=execution,
        cursor_advanced=True,
    )
