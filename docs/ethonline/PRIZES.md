# ETHOnline 2026 — partner strategy

> Sources verified on 5 September 2026:
> - https://ethglobal.com/events/ethonline2026/prizes
> - https://ethglobal.com/events/ethonline2026/prizes/ledger
> - https://developers.ledger.com/ethonline

## Decision — three load-bearing partners

All three partners have a natural, load-bearing role in the Sentinel lifecycle.
No partner is a bolt-on or decoration. Each is added only because the
integration makes Sentinel meaningfully stronger.

```
WATCH -> CLASSIFY -> DECIDE -> ACT -> PROVE
  |                                    |            |               |
The Graph              Bazantic Agent        Ledger Clear-Sign
(live data)            (post-incident      (owner-only unpause,
                        investigation)      Key Ring secrets)
```

---

## Partner 1 -- The Graph (primary)

**Track:** Best AI Tooling or AI Use Case with The Graph (Continuity)
**Pool:** $15,000 -- split $7,500 / $5,000 / $2,500

### Qualification map

| Requirement | Sentinel implementation | Required evidence |
|---|---|---|
| The Graph is load-bearing | Runtime reads live Vault entities from a Graph provider | Subgraph ID/version, query, live trace |
| Live provider data | Studio endpoint with API key | Indexed block, real tx/entity, latency measurement |
| Meaningful AI use | Graph-derived features enter structured classification | Input features, schema-valid output, decision trace |
| Reasoning/automation | Classification result drives incident decision; deterministic policy enforces permission | End-to-end run plus negative path |
| Continuity lineage | Existing project extended | Full history, pre-ethonline-2026 tag, prior/new diff table |
| Open source and runnable | Public repository with clean README | Anonymous clean-clone install/test run |
| Demo | Working integration in 2-4 minutes | Public video URL, >=720p, human narration, no speed-up |

If the demo shows only a deterministic threshold and AI output does not affect
reasoning, decision, or automation, the AI qualification has not been proven.
Invalid, adversarial, timed-out, or low-confidence model output must fail closed.

---

## Partner 2 -- Bazantic

**Track:** Help an Agent Use Your Hackathon Project (Continuity sub-prize)
**Pool:** $1,000 (up to two teams, $500 each -- Continuity variant)

### What Bazantic adds to Sentinel

After Sentinel auto-pauses the Vault, an AI agent can query the live Incident
Evidence API through a Bazantic Recipe to explain why the system stopped.
The agent scenario:

  "Find the latest critical incident, show the transaction, and explain why
  the system paused the Vault."

The agent retrieves cryptographic evidence (Guardian tx hash, Graph entity,
SHA-256 rollback fingerprint) and produces a verifiable explanation -- instead
of hallucinating one.

### Qualification map

| Requirement | Sentinel implementation | Required evidence |
|---|---|---|
| Bazantic MCP server | mcp_server.py exposes get_latest_incident and verify_incident_evidence tools | MCP server starts, tools callable |
| Bazantic Recipe | recipe.json registered in Bazantic gateway | Recipe registered, invocation recorded |
| x402 / MPP gateway | Evidence API middleware returns 402 with MPP payload | Gateway middleware active in dev server |
| A/B benchmark | Same LLM, same prompt, same API: without Recipe vs with Recipe | benchmark_ab.py output artifact |
| Screen recording | Working agent flow demonstrable | Demo segment in project video |

### Technical components

1. sentinel/evidence_api.py -- FastAPI server with /api/v1/incidents/latest
2. sentinel/bazantic/mcp_server.py -- MCP tools
3. sentinel/bazantic/recipe.json -- Bazantic Recipe spec
4. sentinel/bazantic/benchmark_ab.py -- A/B comparison runner

---

## Partner 3 -- Ledger

**Track:** Continuity
**Pool:** $1,500 -- split $1,000 / $500

### What Ledger adds to Sentinel

Sentinel enforces a critical safety invariant: the automated keeper can only
pause; only the human owner may unpause. Ledger makes this invariant
hardware-enforced:

- Key Ring (wallet-cli ring) stores .env.ethonline secrets so the keeper
  never holds a plaintext private key in a process-accessible file.
- Clear Signing (ERC-7730) ensures the owner sees a human-readable
  confirmation screen when calling Guardian.unpause() -- not an opaque hex blob.

### No physical device

A physical Ledger device is not available. The integration demonstrates:

1. wallet-cli ring fully functional as the secret backend (verifiable live).
2. ERC-7730 metadata descriptor (sentinel/ledger/erc7730_unpause.json) -- what
   the device screen would display, verifiable by any Clear Signing validator.
3. unpause_ledger.py --simulate -- builds transaction calldata, validates
   ERC-7730 compliance, and prints the expected Ledger confirmation screen.

This satisfies Continuity: "Put a device confirmation in front of an action
your product already performs" -- previously the owner had to send a raw tx
with no confirmation; now the path is architecturally hardware-ready.

### Qualification map

| Requirement | Sentinel implementation | Required evidence |
|---|---|---|
| Ledger Agent Stack usage | wallet-cli ring as Key Ring backend | wallet-cli ring enroll runs, secrets stored |
| Clear Signing specification | ERC-7730 JSON descriptor for unpause() | JSON validates against ERC-7730 schema |
| Device confirmation gate | unpause_ledger.py --simulate shows expected screen | Script output artifact |
| Meaningful before/after | Before: raw tx with MetaMask; after: hardware-ready path | Demo + code diff |

### Technical components

1. sentinel/ledger/erc7730_unpause.json -- ERC-7730 Clear Signing descriptor
2. sentinel/ledger/unpause_ledger.py -- Owner CLI with --simulate mode
3. sentinel/ledger/keyring_helper.py -- wallet-cli ring integration helper

---

## Scope exclusions

- Chainlink: no price-sensitive assets; adding a price feed is artificial.
- ENS: ENSv2 on Sepolia adds another network; less priority than security layer.
- 0G: not listed as an ETHOnline 2026 partner.

---

## Feature-freeze gate (10 September)

All three partner integrations must be complete and tested before feature freeze.
Adding a partner after freeze is not permitted -- the demo video must include it.
Partner slots are filled only when the integration is load-bearing, all required
evidence artifacts exist, and there is no regression in the core flow.
