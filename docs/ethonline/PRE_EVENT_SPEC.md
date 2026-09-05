# NexGuard Sentinel — architecture specification

> Pre-event specification, revised 3 September 2026. Implementation is event
> work and will be tracked from the `pre-ethonline-2026` baseline after the
> Dashboard-confirmed hacking start.

## Problem

On-chain monitoring usually stops at an alert. During an incident, the dangerous
gap is between detecting the signal and a human becoming available to respond.
An unguarded auto-responder is also dangerous: false positives, duplicate event
delivery, RPC uncertainty or a crash after sending a transaction can turn it
into a denial-of-service or duplicate-action engine.

Sentinel demonstrates a safer control pattern for testnet protocols:

```text
WATCH → DETECT → CLASSIFY → DECIDE → RESERVE → ACT → VERIFY → PROVE
```

## Scope

| In scope | Out of scope |
|---|---|
| Base Sepolia testnet | Mainnet or real funds |
| One deliberately vulnerable demo Vault | General multi-protocol registry |
| Live The Graph Subgraph | Custom production indexer |
| Deterministic features + structured AI classification | ML training/anomaly models |
| Automatic pause only | Automatic unpause/recovery |
| Durable action reservation and reconciliation | Distributed consensus between multiple keepers |
| Post-action state verification and audit ref | Fund recovery/emergency exits |

## Architecture

```text
Base Sepolia Vault events
        │
        ▼
The Graph live Subgraph ──► durable cursor + dedupe + finality rewind
        │
        ▼
feature extraction ──► structured AI classification
        │                    │ invalid/timeout
        │                    └──────────────► refuse + notify
        ▼
deterministic safety gates + durable ActionPolicy reservation
        │ allowed
        ▼
keeper pause(ref, severity) ──► confirmations ──► re-read paused()
        │                                           │
        └── atomic audit event                      └── finalise or latch
```

## 1. WATCH — event ingestion

The Graph is the load-bearing live data source. The Subgraph creates immutable
Withdrawal entities with:

- `id = transactionHash.concatI32(logIndex)`;
- monotonic `sequence = blockNumber * 1_000_000 + logIndex`;
- block number, transaction hash, log index, timestamp, actor and amount.

The consumer pages in ascending `sequence` order. Delivery is at-least-once:

1. load a durable cursor;
2. query records after the cursor;
3. ignore already committed entity IDs;
4. process only records behind the configured confirmation depth;
5. atomically commit processed IDs/state/cursor;
6. on restart, rewind a small block window and deduplicate again.

Cursor state is never advanced before downstream processing commits. A page full
of events with the same timestamp must not lose or duplicate actions.

## 2. DETECT and CLASSIFY

Deterministic feature extraction calculates count, sum, velocity and actor
diversity over a bounded window. A hard catastrophic threshold remains available
as a safety override.

The AI classifier receives only bounded structured features, not arbitrary
instructions from chain data, and returns validated JSON:

- `severity`: `info | warning | critical`;
- `recommended_action`: `none | notify | pause`;
- `confidence`: 0..1;
- `rationale`: at most 240 characters.

Temperature is zero. Timeout, invalid schema, unknown enum, excess length or low
confidence cannot authorize a transaction. The incident is logged and notified
as `classification_unavailable` or `classification_rejected`.

## 3. DECIDE and RESERVE

`ActionPolicy` is deterministic. It enforces:

- expected chain and contract;
- action allowlist (pause only);
- cooldown and sliding-window budget;
- durable latch;
- operator-attributed reset;
- one atomic reservation per stable `intent_id`.

Before execution:

1. pre-read desired state;
2. if already paused, return `already_in_desired_state` without reservation;
3. atomically `check_and_reserve(intent_id)` in durable storage;
4. only the successful reservation owner may call the signer.

An unfinished reservation found after restart latches the policy until
reconciliation determines the on-chain outcome.

## 4. ACT

The keeper calls `pause(incidentRef, severity)`. The hot keeper cannot unpause.
Nonce is allocated under a process lock from pending state and stored with the
intent. Chain ID is checked before signing and sending.

Immediately after `send_raw_transaction`, the tx hash and fee parameters are
durably attached to the reservation. Replacement, if explicitly approved by the
reconciliation path, uses the same nonce and a fee derived from the original
transaction rather than current defaults alone.

## 5. VERIFY

Receipt presence is not enough. Outcomes are explicit:

| Outcome | Meaning | Policy effect |
|---|---|---|
| `confirmed_success` | receipt status 1, confirmation depth reached, `paused()==true` | finalise success |
| `already_in_desired_state` | pre-read or race shows paused true | idempotent success; no new action |
| `confirmed_revert` | canonical receipt status 0 and state not changed | finalise failure |
| `indeterminate` | timeout, RPC disagreement, reorg uncertainty, storage failure or state mismatch | latch and reconcile |

The client never claims a timed-out transaction is merely "pending"; it performs
receipt/transaction/nonce lookup and preserves uncertainty if evidence is not
conclusive.

## 6. PROVE

The pause transaction emits the versioned canonical incident reference and
severity atomically with the state change. Separate proof transactions are not
part of the MVP because they create partial success and duplicate-record risk.

Canonical JSON v1 is UTF-8, sorted-key, whitespace-free JSON with explicit schema
version, UTC timestamps and decimal strings for large integers. A golden-vector
test fixes the exact bytes and keccak hash.

## Manual operations

- `sentinel status` shows latch, unfinished intents, cursor and last verified tx;
- `sentinel reconcile <intent>` compares receipt, nonce and current contract state;
- `sentinel reset --operator <name> --reason <text>` requires both fields and
  records the reset in the audit log;
- unpause is an owner-controlled on-chain operation with a reason hash.

## Trust boundaries and failure policy

- Graph gateway may be stale or unavailable: no new action from uncertain data;
- RPC may disagree or reorganize: confirmation depth + state re-read;
- LLM may fail or emit hostile output: strict schema + fail closed;
- keeper may be compromised: contract restricts it to pause-only;
- process may crash: durable reservation/hash/cursor and startup reconciliation;
- duplicate/concurrent signals are expected: stable IDs and atomic reservation;
- owner compromise and distributed keeper consensus remain accepted MVP risks.

## Prior work

The incident/recovery concepts come from `nexguard-edge-resilience`; durable
action semantics are informed by `latch-agent`; operational LLM prompting is
informed by `llm-log-monitor`. Exact lineage is documented in
[`DISCLOSURE.md`](DISCLOSURE.md). The blockchain, The Graph and event-period
Python implementation are new work after hacking opens.

---

## Bazantic integration (added 2026-09-05)

The automated keeper pause creates an evidence record. An AI agent can query
this record through the Bazantic MCP/Recipe interface:

```
GET /api/v1/incidents/latest  (sentinel/evidence_api.py)
         |
   Bazantic x402 / MPP Gateway
         |
   Bazantic Recipe + MCP Server  (sentinel/bazantic/)
         |
   AI Agent investigation:
     "Find the incident, show tx, explain why Vault was paused."
```

### Incident Evidence API

- `GET /api/v1/incidents/latest` — returns incident UUID, status, Guardian tx
  hash, Base Sepolia block number, The Graph entity IDs, SHA-256 state
  fingerprint, and a pre-composed agent_summary.
- `GET /api/v1/incidents/{id}` — historical incident lookup.
- x402/MPP middleware: returns 402 with payment details; bypassed in dev mode.

### Bazantic Recipe / MCP

- `sentinel/bazantic/mcp_server.py` — stdio MCP server exposing two tools:
  `get_latest_incident()` and `verify_incident_evidence(incident_id)`.
- `sentinel/bazantic/recipe.json` — Bazantic Recipe spec registered in the
  gateway; defines tool call order, field interpretation, and response format.
- `sentinel/bazantic/benchmark_ab.py` — A/B comparison: same LLM, same task,
  same API access; without Recipe vs with Recipe.

---

## Ledger integration (added 2026-09-05)

The keeper-cannot-unpause invariant is made hardware-enforceable:

### Key Ring secret backend

`sentinel/ledger/keyring_helper.py` integrates `wallet-cli ring` (Ledger
Agent Stack). Before: keeper reads secrets from `.env.ethonline` (plaintext).
After: secrets enrolled to Ledger Key Ring; retrieved at runtime without
plaintext disk storage.

### Clear Signing for unpause

`sentinel/ledger/erc7730_unpause.json` — ERC-7730 Clear Signing descriptor
for `Guardian.unpause(bytes32)`:
- Displays the function name, reason hash, contract address, network, and
  a WARNING screen on the Ledger device.
- Eliminates blind-signing risk for the human owner.

### Owner unpause CLI

`sentinel/ledger/unpause_ledger.py` — owner-only recovery CLI:
- `--simulate`: validates ERC-7730, builds calldata, prints expected Ledger
  screen. No device required.
- Hardware mode: invokes `cast send --ledger --hd-path m/44'/60'/0'/0/0`.
