# SPEC-003 — Colosseum Incident Review Desk

Version: 0.1 approved. Status: owner approved 2026-10-01 ("так далі"). Canonical source: `D:\NexGuard Sentinel`; isolated implementation: `D:\1111\sentinel-colosseum`, Python 3.12. Existing baseline: `7a2a5092498aeffd47efd8ae5eed5815624554f4`. Development period: Colosseum 14 September–12 October 2026. The separate Node prototype is planning evidence, not canonical implementation.

## Mission

Extend existing Sentinel with a durable read-only observation path and an operator review workflow. Surface source evidence, deterministic review-policy findings, persisted legacy action outcomes and operator decisions accurately. Use one Base Sepolia DemoVault with valueless accounting credits.

## Approved Constitution amendment — 1 October 2026

Permit spec-003 to add **one local web review interface, a local API for reviewer metadata, and isolated SQLite review state**. Bind the service to 127.0.0.1; no remote/cloud exposure, authentication system, wallet signing, contract control, new autonomous action, mainnet or real-value custody. Keep existing gateway and Sentinel execution behavior, non-regression checks and fail-closed signing restrictions. Operator labels are declared local labels, not authenticated identities. This amendment was explicitly approved on 2026-10-01 and recorded in the Constitution.

## Functional requirements

- **CWF-FR-001 Observe-only:** A durable collector works without keeper credentials or an AI model. Its dependency graph exposes only read operations; no `ActionPolicy.evaluate_and_reserve`, executor, actuator send or recovery call is permitted. It stores observations in a separate review-state database and never consumes legacy pending actions.
- **CWF-FR-002 Source integrity:** Reuse supported Graph/RPC validation, canonical tx/log identities and confirmation checks. Store provider freshness, block/confirmation evidence and gap status. Failed/unconfirmed/unverified observations cannot be presented as confirmed policy breaches.
- **CWF-FR-003 Review policy:** Versioned integer thresholds describe one withdrawal limit; the optional rolling-window rule is added only after the first live path passes. Preserve rule input, source IDs, policy version and reason. Display values as DemoVault accounting units, not actual losses. Review findings never authorize signing.
- **CWF-FR-004 Cases:** Deterministic case identity from chain, supported vault, canonical source IDs, rule and policy version. Persist findings independently of chain-action intents. Duplicate replay preserves one case and reviewer history; conflicting evidence is flagged for reconciliation.
- **CWF-FR-005 Decisions:** `open → acknowledged → resolved`, with non-empty operator label, note, UTC server timestamp and explicit disposition (`policy_breach`, `expected_activity`, `insufficient_evidence`). Revision checks reject competing updates. Decisions do not update contract state, pause/unpause, reset a latch or imply action success.
- **CWF-FR-006 Evidence:** Expose original source data, policy finding, model trace only if recorded, legacy execution outcome only if actually persisted, confirmation/state evidence, and explicit gaps. Hashes demonstrate payload consistency; do not claim they prove provider authenticity.
- **CWF-FR-007 API/UI:** Local list/detail/decision/export API and three screens: source/vault status, cases, detail. Reject cross-origin write requests, validate input and use idempotency/revision for decisions. No credentials, mainnet controls or fabricated tx links in UI.
- **CWF-FR-008 Brief:** Export a versioned JSON/text incident brief containing evidence origin, real explorer links where available, measured facts, policy version, workflow history and unresolved limits. Fixtures must remain visibly synthetic.
- **CWF-FR-009 Reproduction:** Demonstrate a real supported Graph/RPC observation and new review case, restart/replay without duplicate case, expected/negative example and operator disposition. Current-HEAD tests and live checks precede claims about existing functionality.
- **CWF-FR-010 Provenance:** Preserve baseline/history; disclose pre-14 September Sentinel and all reuse. Record new modules/commits, prototype origin, AI assistance and current test evidence separately from historical ETHOnline records.

## Non-functional requirements

- **CWF-NFR-001 Isolation:** A separate review-state file/schema and separate processing bookkeeping; existing action ownership, pending work, proofs and reservations remain intact. Never alter the legacy schema version merely to add review tables.
- **CWF-NFR-002 Reliability:** Persist observations before processing completion. Recover outstanding rule evaluations after crash. SQL transaction/uniqueness/revision invariants are verified on a temporary database.
- **CWF-NFR-003 Quality:** Python 3.12, Ruff, strict MyPy, focused review tests and required legacy non-regression/contract gates. No new Node runtime is required for the canonical product.
- **CWF-NFR-004 Scope:** One chain, one vault, one required rule, one local operator. No billing, multi-user service, cloud deploy, new Solana adapter or broad contract support in this specification.

## Acceptance boundary

Approval covers the explicit amendment and staged tasks. The observe-only mode is not a weaker signing mode: its service graph has no signer. Legacy AI absence continues to prohibit legacy onchain action. Resolving a review case records a decision, not an onchain remedy. Final testnet transactions require the owner's existing operational authorization or an explicit separately authorized rehearsal.
