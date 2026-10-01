# NexGuard Sentinel — Crypto World's Fair submission draft

Prepared 1 October 2026. Reviewable local draft; not submitted or published.
Technical implementation through local commit `4144eeb` on `feat/colosseum-review`.

## Product summary

**One sentence:** NexGuard gives a protocol operator a durable review desk that
connects verified withdrawal evidence, a versioned policy finding and the human
decision in one exportable incident brief.

**Current target:** one Base Sepolia DemoVault, one single-withdrawal rule,
one local operator. DemoVault credits have no monetary value.

**New event-period work:** isolated observation without a key/model; canonical
Graph/RPC and receipt/log checks; durable observations and pending evaluations;
versioned integer rule; review cases with revision/idempotency protection;
local three-screen desk and JSON/text evidence briefs.

**Prior work:** existing gateway resilience MVP, Base Sepolia contracts,
deployed Subgraph, AI classification/execution runtime and historical ETHOnline
transactions. See DISCLOSURE.md and baseline `7a2a509` dated 13 September.
The review workflow does not invoke the existing signer.

## Presentation script — approximately 2–3 minutes, rehearse actual timing

When a protocol team sees a withdrawal alert, someone still has to work out what
happened. They inspect an explorer, check the rule, ask whether an action was
actually executed, and leave a record for the next person. We are testing whether
that review process can be made easier to understand and reproduce.

NexGuard Sentinel puts the source evidence, the policy finding, and the operator's
decision into one local review desk. Our current implementation supports one
DemoVault on Base Sepolia. Its credits are valueless accounting units, so this is
a testnet demonstration, with no claim about prevented losses.

The observer reads The Graph and public RPC without a keeper key or an AI model.
Before it stores an observation, it checks the chain, contract identity, canonical
block, transaction receipt and emitted withdrawal fields. It records gaps and
freshness information. A versioned integer threshold then creates a review case.

The operator can inspect the original evidence, acknowledge the case, record a
disposition and export a brief. Revisions and idempotency protect the local history.
Resolving the case records an assessment. The interface exposes no contract action.

We verified five historical withdrawals and created four new review cases.
Repeated ingestion and evaluation created no duplicates. The full local Python
suite passes 302 tests, including 63 new review tests. Our first owner-operated
session has started; independent user validation and a measured time-saving
comparison are still pending.

We reused contracts, a Subgraph and an execution runtime developed before this
event. Our new contribution is the durable observation and operator review layer.
We disclose that history and show the corresponding Git diff.

Our initial user hypothesis is small Base protocol teams that need a clear
incident handover. The next step is to test the workflow with independent
operators, measure the manual review effort, and establish whether teams want
a pilot. A paid team review workflow is a business hypothesis; pricing and demand
have not been validated. We are seeking operators who can test a real review
task and tell us which evidence they need before they would trust the handover.

## Product-demo storyboard — target 2:30, maximum 3:00

| Time | Screen and actual proof |
|---|---|
| 0:00–0:20 | Source overview: chain 84532, source timestamp, five historical observations, four cases and exact valueless-unit threshold |
| 0:20–0:55 | Queue → real case; show transaction/source identity, receipt/log checks and event block. Say that the event is historical |
| 0:55–1:20 | Show policy version and evidence gaps. Explain Guardian snapshot versus absent recorded action evidence |
| 1:20–1:55 | A human operator acknowledges and resolves an open case with a reasoned note. Record the actual disposition, without preselecting an invented verdict |
| 1:55–2:15 | Download/open text or JSON brief; show history and genuine explorer links |
| 2:15–2:30 | Show previously captured restart/replay evidence and baseline/new-work disclosure |

Use another open historical case if case one has already been resolved. Do not
reset real reviewer history for a recording. If the provider is down, show stored
evidence with the stale/degraded label or use the explicitly synthetic demo.
Synthetic mode must be announced and must not display invented chain links.

## Business assumptions to test

- Initial user/buyer: operator or technical lead of a small protocol team; unvalidated.
- Entry point: a concrete withdrawal review and a reusable incident brief.
- Distribution experiment: founder-led pilot conversations; none completed yet.
- Possible business model: paid workflow/support for teams; no price or revenue claim.
- Claimed differentiation must be supported by user evidence. No broad superiority,
  market-size number or measured incident-response improvement is asserted here.
- Founder background, full team, location, capacity and motivation must be supplied
  by the owner before the final presentation and portal entry.

## Evidence and links

- [Existing repository](https://github.com/Seranov67/nexguard-sentinel) — prior public
  repository. SPEC-003 commits are local and need publication before judge review.
- [Guardian](https://sepolia.basescan.org/address/0x8b7b1ee7e335fd00f35cc6272c113c8735cb8ed3)
- [DemoVault](https://sepolia.basescan.org/address/0xf1683d32fef59bbb95483561aba62a1bda65cd13)
- [Reviewed historical withdrawal](https://sepolia.basescan.org/tx/0x0867c938ef6038749b4142c77beb1778e315ce180010a0ffbe39b464caafbe31)
- Public Graph endpoint: https://api.studio.thegraph.com/query/1758726/nexguard-sentinel/v0.1.0
  (POST GraphQL; deployment/hash verification is in observer evidence).
- Local VERIFICATION.md, REHEARSAL.md, USER_FEEDBACK.md, RUNBOOK.md and DISCLOSURE.md.

## Delivery register

| Item | Current state |
|---|---|
| Colosseum registration and roster | Owner confirmation pending |
| Review feature repository/commit accessible to judges | Local only; publication pending |
| Current remote CI | Pending after publication; local gates recorded separately |
| Presentation video | Script ready; recording/link pending |
| Product-demo video | Storyboard ready; recording/link pending |
| Logo | Existing NexGuard visual identity; final portal asset pending |
| Human validation | Owner acknowledgment verified; resolution/feedback and independent sessions pending |
| Contract/Graph links | Public RPC/Graph checked; final anonymous explorer/video/repo checks pending |
| Submission | Not submitted; confirmation/URL pending |

Internal deadline: **12 October 2026, 20:00 Europe/Kyiv**. The campaign lists
12 October as the submission date. Use the dashboard/rules for the final cutoff.
The official FAQ requests a 2–3-minute presentation and a product-demo video
no longer than three minutes; reused code must be disclosed.
[Campaign](https://colosseum.com/worldsfair),
[submission FAQ](https://colosseum.com/hackathon?year=fall2026).

Plan target: Base integration and general Colosseum consideration. No eligibility
for Superteam Ukraine's Solana-specific prize is asserted for this Base-only scope.
