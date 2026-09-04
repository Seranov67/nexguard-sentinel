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
