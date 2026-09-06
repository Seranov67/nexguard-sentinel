# NexGuard Sentinel — implementation plan

## Stage 0 — ES000 specification and provenance

Create the baseline tag and event branch; import labelled pre-event artifacts;
add this spec, plan, task list, acceptance map, event quality gates, and the narrow
Constitution amendment. Stop for owner approval before production code.

## Stage 1 — ES100 contracts and tests

Implement Guardian and Demo Vault, role/idempotency tests, deployment scripts,
and Base Sepolia address evidence. Gate: keeper cannot unpause and manual pause
blocks a Vault operation.

## Stage 2 — ES200 Subgraph and live query

Implement schema, mappings, tests, deployment config, and a credential-safe query
client. Gate: a real Base Sepolia Withdrawal is returned by the live provider.

## Stage 3 — ES300 durable core and executor

Implement models, SQLite migrations/store, Graph cursor/dedupe, deterministic
policy, reservation, executor, confirmation/state verification, reconciliation,
and CLI. Gate: duplicate/concurrent/restart paths produce at most one tx.

## Stage 4 — ES400 AI and outbox

Implement bounded feature extraction, schema-validated classifier, fail-closed
tests, and durable notification outbox. Gate: Graph-derived classification affects
the decision while invalid output cannot authorize action.

## Stage 5 — ES500 live demo and submission

Run Base Sepolia end-to-end, clean-clone and failure-path rehearsals; finish README,
architecture, disclosure, evidence, video, scans, anonymous-link checks, Dashboard
check-ins, prize selection, and submission.

Feature freeze is 10 September. Internal submission target is 13 September 17:00
Europe/Kyiv; the hard deadline is 19:00.

## Current execution schedule (6 September audit)

The IoT MVP T000–T027 is complete and remains a non-regression baseline. Sentinel
ES000–ES402 and ES503 are implemented and locally checked. ES501/ES502 remain open.

| Target | Work | Completion evidence |
|---|---|---|
| 6–7 September | ES504 documentation/CI; configure real model | Consistent records and remote CI diagnosis/result |
| 7–9 September | ES501 live flow and restart; ES505 real A/B | Model trace, canonical action receipt, restart record, transcripts |
| By 10 September | ES506 hardware decision; feature freeze | Hardware proof or explicit limitation; final regression checks |
| 11–12 September | ES507 human video, anonymous links, final text | Reviewed export and submission-ready links |
| 13 September, 17:00 Kyiv | ES502 final Dashboard delivery | Submission confirmation before the hard deadline |

These are internal targets, not claims that external services or hardware are ready.
The immediate dependency is a reachable model. Human narration and Ledger actions
require the owner. Final form availability is controlled by ETHGlobal.

No post-hackathon production roadmap is approved. Mainnet, real-value custody,
web administration, cloud infrastructure and multi-protocol expansion remain out
of scope; proposing them requires a separate SSD specification.

Evening update: ES501 live evidence and ES504 remote CI/plan reconciliation pass.
Ollama is installed and the model is configured. ES506 records the no-hardware
limitation. ES502/ES507 remain open for human video and final submission.
