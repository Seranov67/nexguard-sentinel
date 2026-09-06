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
from dataclasses import asdict, dataclass
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


def ingest_live(settings: Settings, store: StateStore, actuator: Actuator) -> int:
    """Use the validated snapshot/replay ingestion path exclusively."""
    import httpx

    from sentinel.ingestion import Ingestor, natural

    def fetch(query: str, variables: dict[str, object]) -> dict[str, Any]:
        with httpx.Client(timeout=15) as client:
            response = client.post(
                settings.subgraph_url,
                json={
                    "query": query,
                    "variables": variables,
                },
            )
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, dict) or payload.get("errors"):
            raise ValueError("Graph query failed")
        if "block" in variables:
            block = actuator._rpc_call(
                "eth_getBlockByNumber", [hex(int(str(variables["block"]))), False]
            )
            if block is None or block["hash"] != payload["data"]["_meta"]["block"]["hash"]:
                raise ValueError("Graph snapshot disagrees with canonical RPC block")
        return payload

    actuator.verify_identity()
    meta = fetch("{ _meta { deployment hasIndexingErrors block { number } } }", {})["data"]["_meta"]
    if meta["deployment"] != settings.graph_deployment or meta["hasIndexingErrors"] is not False:
        raise ValueError("Unexpected Graph deployment or indexing errors")
    return Ingestor(
        store,
        fetch,
        settings.graph_deployment,
        settings.confirmations,
        settings.rewind_blocks,
    ).poll(int(actuator._rpc_call("eth_blockNumber", []), 16), natural(meta["block"]["number"]))


def run_loop_step(
    settings: Settings,
    store: StateStore,
    *,
    events_override: list[dict[str, Any]] | None = None,
    dry_run: bool = False,
    keeper_private_key: str | None = None,
    llm_evaluator: Callable[[dict[str, Any]], str] | None = None,
) -> LoopStepResult:
    """Process durable pending events; an ingest cursor is never a processing cursor."""
    import json
    import tempfile
    from pathlib import Path

    if dry_run:
        # A fresh isolated database guarantees rehearsal cannot consume live events,
        # reservations or cooldown. No signing or transaction simulation is performed.
        with tempfile.TemporaryDirectory(prefix="sentinel-preview-") as directory:
            preview = StateStore(Path(directory) / "state.db")
            actuator = Actuator(preview, settings.rpc_http, settings.guardian_address)
            if events_override is None:
                ingest_live(settings, preview, actuator)
                events_override = preview.pending_events("vault-withdrawals")
            features = extract_features(events_override)
            classification = classify_features(features, llm_evaluator=llm_evaluator)
            return LoopStepResult(
                len(events_override),
                len(events_override),
                store.is_latched(),
                features,
                classification,
            )
    if not keeper_private_key:
        raise ValueError("Live loop requires keeper key; use --dry-run for preview")
    if store.is_latched():
        return LoopStepResult(0, 0, True)
    if store.unfinished():
        store.set_latch("Unfinished intent requires reconciliation before further processing")
        return LoopStepResult(0, 0, True)

    source = "vault-withdrawals"
    actuator = Actuator(
        store,
        settings.rpc_http,
        settings.guardian_address,
        chain_id=settings.chain_id,
        keeper_private_key=keeper_private_key,
        confirmations=settings.confirmations,
    )
    try:
        if events_override is None:
            inserted = ingest_live(settings, store, actuator)
        else:
            inserted = 0
            for event in events_override:
                inserted += store.ingest(
                    source,
                    str(event["id"]),
                    int(event["sequence"]),
                    int(event["blockNumber"]),
                    json.dumps(event, sort_keys=True),
                )
        raw_events = store.pending_events(source)
        if not raw_events:
            return LoopStepResult(inserted, 0, False)
        features = extract_features(raw_events)
        classification = classify_features(features, llm_evaluator=llm_evaluator)
        from sentinel.ai import PROMPT_HASH, PROMPT_VERSION

        store.record_classification(
            [str(event["id"]) for event in raw_events],
            json.dumps(features.to_dict()),
            json.dumps(asdict(classification)),
            str(getattr(llm_evaluator, "model", "unconfigured")),
            PROMPT_VERSION,
            PROMPT_HASH,
        )
        policy = ActionPolicy(
            store,
            chain_id=settings.chain_id,
            guardian_address=settings.guardian_address,
            onchain_state_reader=actuator.is_paused_onchain,
        )
        event_ids = [str(event["id"]) for event in raw_events]
        decision = policy.evaluate_and_reserve(classification, event_ids)
        execution = None
        if decision.allowed:
            execution = actuator.execute_pause(decision.intent_id, decision.incident_id, severity=3)
        elif decision.status in ("low_severity", "already_in_desired_state"):
            if classification.error is None:
                store.mark_processed(event_ids, decision.reason)
        return LoopStepResult(
            inserted,
            len(event_ids),
            store.is_latched(),
            features,
            classification,
            decision,
            execution,
            inserted > 0,
        )
    except Exception:
        store.set_latch("Loop failed; inspect durable events and intents before reset")
        raise
