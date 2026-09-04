# NexGuard Sentinel — ETHOnline 2026 specification

**Version:** 1.0.0-draft
**Status:** APPROVED — owner authorized implementation on 2026-09-04
**Baseline:** `pre-ethonline-2026` / `fa202e994a77ea365061f6ac609daea1b5ad60dd`
**Event start:** 2026-09-04 19:00 Europe/Kyiv

## Mission

Extend NexGuard from local gateway recovery into a testnet incident-response
prototype that consumes live The Graph data, classifies bounded risk features,
and can automatically pause—but never unpause—a deliberately vulnerable Vault.

```text
WATCH → DETECT → CLASSIFY → DECIDE → RESERVE → ACT → VERIFY → PROVE
```

## Scope

In scope: one Base Sepolia Vault and Guardian, one live Subgraph, one Python
Sentinel service, local SQLite state, structured AI classification, deterministic
safety policy, durable notification outbox, CLI status/reconcile/reset commands,
and submission evidence.

Out of scope: mainnet, real funds, automatic unpause, fund recovery, arbitrary
contract calls, multi-protocol registry, distributed keepers, model training,
production infrastructure, web administration, authentication, and cloud deploy.

## Functional requirements

- **ES-FR-001 Contracts:** Guardian grants a keeper pause-only authority. Only
  owner may unpause, and unpause records a reason hash. Duplicate incident
  references cannot create a second state transition.
- **ES-FR-002 Demo Vault:** Vault emits immutable withdrawal data and refuses
  guarded operations while Guardian is paused.
- **ES-FR-003 Graph source:** A deployed Subgraph indexes Withdrawal entities
  using transaction hash plus log index and exposes stable ascending sequence,
  block, timestamp, actor, amount, and transaction fields.
- **ES-FR-004 Ingestion:** Sentinel uses the live Graph provider as its runtime
  source, persists a cursor and processed IDs, applies a confirmation window,
  rewinds on restart, and accepts at-least-once delivery without duplicate action.
- **ES-FR-005 Classification:** Deterministic features include bounded count,
  sum, velocity, and actor diversity. AI receives only those structured features
  and returns validated severity, recommended action, confidence, and a rationale
  no longer than 240 characters.
- **ES-FR-006 Fail closed:** AI timeout, invalid JSON/schema, unknown enum,
  adversarial content, or confidence below the configured threshold cannot
  authorize an on-chain action.
- **ES-FR-007 Policy:** Deterministic policy checks chain and contract identity,
  pause-only allowlist, cooldown, action budget, latch, and a stable intent ID.
  An atomic durable reservation must precede signer access.
- **ES-FR-008 Execution:** Nonce and intent are stored before send; transaction
  hash and fee data are stored immediately after broadcast. Receipt timeout is
  indeterminate and never permits a blind second send.
- **ES-FR-009 Verification:** Confirmed success requires canonical receipt status
  1, configured confirmations, and a final `paused()==true` state read. Revert,
  already-desired, and indeterminate are distinct durable outcomes.
- **ES-FR-010 Proof:** The pause event atomically includes a versioned canonical
  incident reference and severity. Canonical JSON bytes and hash have a golden test.
- **ES-FR-011 Operations:** CLI exposes status, reconciliation, and attributed
  latch reset. Automated credentials cannot call unpause.
- **ES-FR-012 Notifications:** A durable outbox records, retries, and surfaces
  terminal notification failure without affecting action correctness.

## Non-functional requirements

- **ES-NFR-001 Safety:** Chain ID is fixed to Base Sepolia (`84532`); no mainnet
  or wallet containing real value is accepted.
- **ES-NFR-002 Reproducibility:** Python version and direct dependencies are
  locked; clean-clone lint, strict type checking, tests, and compile steps pass.
- **ES-NFR-003 Security:** Secrets exist only in ignored environment files;
  working tree and full Git history pass Gitleaks plus a private denylist scan.
- **ES-NFR-004 Auditability:** Every transition has UTC time, stable incident and
  intent identifiers, source entity IDs, policy decision, and final outcome.
- **ES-NFR-005 Isolation:** Existing gateway behavior and tests remain unchanged
  unless a task explicitly lists and justifies the affected file.

## Safety invariants

1. One canonical Graph entity can reserve at most one action.
2. Keeper can pause only; human owner alone can unpause.
3. AI proposes; deterministic policy authorizes.
4. Persist before irreversible action; uncertainty latches and reconciles.
5. Receipt alone is insufficient—confirmations and state re-read are required.
6. The Graph is load-bearing in the demonstrated runtime flow.

## Definition of done

All `EG-0` through `EG-5` gates pass, the live Base Sepolia flow is reproducible,
the event-only diff is auditable, public evidence works without authentication,
and Dashboard confirms submission to The Graph AI/Continuity before the deadline.
