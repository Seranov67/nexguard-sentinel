# Bazantic Recipe Specification: NexGuard Sentinel Incident Investigator

## Overview

- **Recipe Name**: `nexguard-sentinel-incident-investigator`
- **Display Name**: `NexGuard Sentinel - Incident Investigator`
- **Version**: `1.0.0`
- **Category**: `security-automation`
- **Target Platform**: ETHOnline 2026 / Bazantic Continuity Track

This Bazantic Recipe guides an autonomous AI agent to investigate, verify, and report on circuit-breaker incidents in NexGuard Sentinel. When the Sentinel keeper detects critical anomalies (e.g. repeated node failures or excessive withdrawal rate), it automatically triggers `Guardian.pause()` on Base Sepolia. The Bazantic Recipe enables an agent to query verifiable incident proofs, cross-reference The Graph indexer data, inspect onchain receipts, and produce a human-readable explanation with full cryptographic provenance.

---

## Architecture and Integration Flow

```
+-------------------+        +---------------------------+        +-------------------------+
|   The Graph       |  --->  |  Sentinel Keeper Core     |  --->  | Base Sepolia Guardian   |
|   (Event Index)   |        |  (Automated Circuit Break)|        | (0x8B7B...8Ed3 paused)  |
+-------------------+        +---------------------------+        +-------------------------+
                                        |
                                        v
                             +--------------------+
                             | SQLite Evidence DB |
                             +--------------------+
                                        |
                                        v
                             +--------------------+
                             | Evidence API       | (FastAPI, port 8080)
                             | (x402 Micropayment)|
                             +--------------------+
                                        |
                                        v
                             +--------------------+
                             | MCP Server / Recipe| (stdio JSON-RPC)
                             +--------------------+
                                        |
                                        v
                             +--------------------+
                             | Investigating Agent|
                             +--------------------+
```

---

## MCP Tools Defined by Recipe

### 1. `get_latest_incident`
- **Description**: Fetch the latest circuit-breaker incident from the Sentinel Evidence API.
- **Inputs**: None (`{}`).
- **Returns**:
  - `incident_id`: UUID of the incident.
  - `timestamp`: UTC ISO-8601 timestamp.
  - `status`: Incident status (`HALTED`, `INVESTIGATING`, `RESOLVED`).
  - `trigger_cause`: Descriptive cause (e.g. `3 consecutive health check timeouts`).
  - `pause_evidence`:
    - `tx_hash`: Base Sepolia transaction hash.
    - `block_number`: Block number of pause transaction.
    - `guardian_address`: Deployed Guardian contract address.
  - `graph_evidence`:
    - `subgraph_endpoint`: Endpoint of the indexing subgraph.
    - `entity_id`: Entity ID of the trigger event.
  - `rollback_hash`: SHA-256 state snapshot hash for cryptographic immutability.
  - `agent_summary`: Pre-formatted natural language explanation.

### 2. `verify_incident_evidence`
- **Description**: Cross-reference onchain Base Sepolia pause receipt and SHA-256 state hash against the local incident store.
- **Inputs**:
  - `incident_id` (string, required): Incident UUID to verify.
- **Returns**:
  - `verified`: Boolean (`true`/`false`).
  - `tx_valid`: Confirmation of valid 0x hex transaction hash.
  - `hash_valid`: Confirmation of valid 64-char SHA-256 hash.
  - `guardian_match`: Confirmation that the guardian address matches Base Sepolia deployment.
  - `basescan_url`: Direct link to Basescan for user verification (`https://sepolia.basescan.org/tx/{tx_hash}`).

---

## Payment Scheme (x402 / MPP)

The Recipe specifies a Bazantic Gateway with micro-payments:
- **Payment Scheme**: `x402`
- **Asset**: USDC on Base Sepolia (`0.001 USDC` per query demonstration)
- **Header Flow**:
  - Unauthenticated requests receive `402 Payment Required` with `X-Bazantic-Payment-Required: true`.
  - In development mode (`DEV_MODE=true`) or when supplying `X-Bazantic-Proof`, access is granted.

---

## A/B Benchmark Evaluation

The Bazantic track requires demonstrating measurable improvement when an agent uses the Recipe versus without it:
- **Baseline (Without Recipe)**:
  - Agent attempts to answer from generalized LLM knowledge.
  - Cannot query local Sentinel SQLite evidence or verified Base Sepolia receipts.
  - Vulnerable to hallucinated transaction hashes and outdated contract addresses.
  - Score: **0/4** on deterministic verification points.
- **With Recipe (`sentinel/bazantic/recipe.json`)**:
  - Agent loads the MCP tools, queries `get_latest_incident`, and calls `verify_incident_evidence`.
  - Accurately cites exact Base Sepolia tx hash and verified Basescan URL.
  - Validates SHA-256 rollback state hash.
  - Score: **4/4** across all verification metrics.

Refer to `sentinel/bazantic/benchmark_ab.py` for automated benchmark reproduction.
