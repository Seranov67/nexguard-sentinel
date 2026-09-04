# ETHOnline submission form — evidence-backed draft

> Do not submit this text unchanged. Replace every `PENDING` only with verified
> evidence from `docs/COMPLIANCE.md`. Delete unused claims rather than guessing.

## Core fields

**Project name:** NexGuard Sentinel

**Target pool:** The Graph — Best AI Tooling or AI Use Case with The Graph
(Continuity). Actual selection: `PENDING DASHBOARD`.

**One-line description:**

> NexGuard Sentinel extends an existing resilience engine with a pause-only,
> crash-safe incident-response loop driven by live on-chain data from The Graph.

**Repository:** `PENDING PUBLIC URL`

**Demo video:** `PENDING PUBLIC URL`
Duration/resolution/human narration verified: `PENDING`

## What existed before the event

The Continuity base is `nexguard-edge-resilience`, an MIT-licensed IoT gateway
reliability project. Before ETHOnline it already contained health monitoring,
incident state, recovery guards, a latch and notification concepts. `latch-agent`
was a separate pre-event design reference for durable reservations and recovery.
Preparation specs and spikes are also disclosed as pre-event work.

Baseline commit/tag: `PENDING AFTER CONFIRMED START`

## What was built during ETHOnline

`PENDING — populate only from the baseline diff and dated event commits.`

Minimum evidence table:

| New feature | Event files/commits | Test/live proof |
|---|---|---|
| Guardian/Vault contracts | PENDING | PENDING |
| Live Subgraph | PENDING | PENDING |
| Graph ingestion/cursor | PENDING | PENDING |
| Structured AI classifier | PENDING | PENDING |
| Durable pause executor | PENDING | PENDING |

## How The Graph is load-bearing

`PENDING FINAL PROOF.` The final answer must identify:

1. live Graph provider and Subgraph ID/version;
2. exact live entities/features consumed;
3. how Graph-derived data enters AI reasoning/classification;
4. how validated output affects the decision/automation;
5. what fails or becomes unavailable when the Graph source is removed.

Do not use mock/local/static data as the qualification demonstration. Do not
apply to the composable/standardized track for a single standalone Subgraph.

## Partner feedback

- What worked well: `PENDING AFTER LIVE USE`
- Friction/blockers: `PENDING AFTER LIVE USE`
- Documentation/product suggestion: `PENDING AFTER LIVE USE`

## AI assistance disclosure

Claude and ChatGPT Codex assisted planning, research, documentation and specified
pre-event spike areas. Event-period use must be summarized from `AI_USAGE.md` and
linked prompt/transcript evidence in `AI_PROMPTS.md`. Human contribution and
verification must be described factually; do not use a generic “AI was used” line.

## Deployment and reproducibility

| Artifact | Verified value |
|---|---|
| Network/chain ID | PENDING |
| Guardian address + deployment tx | PENDING |
| Vault address + deployment tx | PENDING |
| Subgraph ID/version | PENDING |
| Clean-clone command/result | PENDING |
| Test command/result | PENDING |

## Limitations

- Testnet prototype; not audited or production ready.
- Automated authority is pause-only; human owner controls unpause.
- Graph/RPC/provider latency and availability remain external dependencies.
- Additional limitations discovered during implementation: `PENDING`.

## Final truthfulness check

- [ ] Every completed claim has a commit, test, transaction, URL or screenshot.
- [ ] Every prior component is named and linked.
- [ ] No pre-event spec/spike is presented as event implementation.
- [ ] No private endpoint, API key, wallet secret or personal denylist value appears.
- [ ] Public links work in an anonymous/incognito session.
- [ ] Form selected The Graph AI/Continuity, not From Scratch/composable.
- [ ] Dashboard shows successful submission before 13 September 19:00 Kyiv.
