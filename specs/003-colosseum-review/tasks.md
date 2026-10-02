# SPEC-003 — stages and tasks

Status: approved 2026-10-01. Implementation checkout: `D:\1111\sentinel-colosseum`.
No implementation task is marked complete based on the Node prototype.

CWF001 verification repair justification (before editing): the tracked baseline
Solidity files contain CRLF, so Foundry's format gate fails even from `git archive`.
Add `.gitattributes` for Solidity LF and normalize line endings only in
`contracts/src/Guardian.sol`, `contracts/src/DemoVault.sol`, and
`contracts/test/Guardian.t.sol`. No Solidity semantics change. Verify byte-equivalence
after CRLF normalization plus Foundry format/tests. POSIX controller tests run on
Linux, their supported target; do not weaken tests or rewrite the controller.

## Stage 0 — specification and baseline

**CWF000 / complete:** spec, plan, audit, tasks, acceptance and proposed Constitution amendment exist in `D:\1111`. Gate: owner approves scope; document requirements match acceptance IDs.

**CWF001 / complete:** record Colosseum baseline, prepare an isolated working branch/worktree from canonical Sentinel, run current quality gates and read-only live source checks. Proposed files: `docs/colosseum/BASELINE.md`, `DISCLOSURE.md`, `SOURCE_STATUS.md`, `docs/ssd/CONSTITUTION.md`, `AGENTS.md`, `specs/003-colosseum-review/`. Verify: Git status/diff/provenance; Python 3.12 pytest, Ruff, MyPy, required contract checks; Graph health and RPC chain/contract reads. Historical PASS is insufficient. Depends: CWF000 approval.

## Stage 1 — observation and review persistence

**CWF101 / complete:** add `sentinel/review/{__init__,models,store}.py` and `sentinel/tests/test_review_store.py`. Separate review-state file with replay-safe observation/rule bookkeeping, `review_cases`, `review_actions`, schema metadata and revisions. No legacy execution schema or source cursor is changed. Gate: restart, rollback, duplicate/conflicting source, competing updates and existing legacy-state isolation pass. Depends: CWF001.

**CWF102 / complete:** add `sentinel/review/observer.py` and `sentinel/tests/test_review_observer.py`. Reuse public Graph/RPC validation through a read-only interface; persistent source health/gap state; no signer/model requirement and no action reservation. Minimal shared-module edits require explicit justification in the task before editing. Gate: captured source parsing, confirmation/canonical hash checks, degraded source, crash between ingest and rule evaluation, and tests where every sign/send method fails if called. Depends: CWF101.

Verification: `python -m pytest -q sentinel/tests/test_review_store.py sentinel/tests/test_review_observer.py`; `python -m ruff check sentinel`; `python -m mypy sentinel`.

## Stage 2 — policy findings and evidence

**CWF201 / complete:** add `sentinel/review/rules.py`, `sentinel/tests/test_review_rules.py` and `config/review.example.yaml`. One integer withdrawal threshold; exact policy version/source IDs/evidence. Optional rolling window requires a separate completed first-rule gate. Verify threshold boundaries, unit labels, invalid input, duplicate source and deterministic identities. Depends: CWF102.

**CWF202 / complete:** add `sentinel/review/evidence.py`, `brief.py` and their tests. Legacy evidence is read via a read-only connection/reader, with explicit status and gaps; never infer a successful pause from a review result. Verify golden exported payload, genuine versus fixture links, indeterminate/reverted/no-action outcomes and legacy DB immutability. Depends: CWF201.

Verification: focused `python -m pytest -q sentinel/tests/test_review_rules.py sentinel/tests/test_review_evidence.py`; Ruff and strict MyPy.

## Stage 3 — local operator workflow

CWF301 shared-file justification before editing: add a freshness projection to
`sentinel/review/evidence.py`, so both API and exported brief label old health
observations as stale. Preserve recorded health facts separately. Extend its test
for a stale timestamp. No legacy module or signing API is modified.

**CWF301 / complete:** add `sentinel/review/api.py`, `sentinel/review/cli.py`, `sentinel/tests/test_review_api.py`. Local list/detail/acknowledge/resolve/export; server timestamps, idempotency/revisions, input validation, allowed-origin write checks. No calls into execution/reset/recovery. Depends: CWF202.

**CWF302 / complete:** add `sentinel/review/static/{index.html,app.js,style.css}` and package-data entries for those files. Three screens; keyboard-accessible decisions; clear accounting units/data status; actual action status separate from review status. Gate: direct local UI use creates correct reviewer metadata and brief; API concurrency/invalid-origin tests pass; stored data is rendered as text, not executable HTML. Depends: CWF301 and explicit UI amendment.

Verification: `python -m pytest -q sentinel/tests/test_review_api.py`; Ruff/MyPy; package asset check; local browser acceptance against an isolated test database.

## Stage 4 — live evidence, user feedback and delivery

**CWF404 / complete — 2 October 2026:** fix the owner-reproduced evaluation
queue blockage within FR-002/004 and NFR-002. Justification before editing:
`store.evaluated` rejects conflicted evidence but leaves it pending forever;
`process_pending` aborts the batch, so unrelated verified events never progress.
Exclude durable conflicts before applying the pending-query limit, and handle
only a conflict raised during the individual evaluation write (including one
recorded after selecting the batch). Retain conflicts and original evidence;
do not record a successful evaluation/case for rejected evidence. Preserve source
verification and policy-registration failures. No schema or signer change.
Files: `sentinel/review/{store,rules}.py`,
`sentinel/tests/{test_review_rules,test_review_api}.py`, this task list,
`docs/colosseum/{PLAN_v0.5_UK.md,VERIFICATION.md,RUNBOOK.md}` and the `D:\1111`
plan copy. Additional evidence/document files: `docs/colosseum/cwf404-*.{json,txt}`,
`USER_FEEDBACK.md`, `SUBMISSION_PACK.md`. Justification: owner requested immediate
agent-led verification; preserve separate live-data technical-review evidence and
update the verified official cutoff without claiming human validation.
Plan amendments: explicit conflict-plus-next-event rehearsal gate;
first remote CI on 3–5 October; remote preflight, cutoff and reviewer-slot work
on 2–3 October; fresh release Subgraph/secret scans remain mandatory.
Gate: old-source regression failure; known conflicts do not consume LIMIT 100;
an after-selection conflict cannot stop the next event; restart/replay keeps
conflicts and produces no duplicates; healthy source remains healthy in recorded
metadata while API reports reconciliation_required. Focused review tests, full
Linux Python suite, Ruff, strict types and Compose before commit.
Verification: `python -m pytest -q sentinel/tests/test_review_rules.py
sentinel/tests/test_review_api.py`, followed by the existing global source gates.
PASS: 308 Linux Python tests, 69 focused review tests, 5 JS tests, Ruff, all
strict MyPy targets, Compose and Gitleaks directory/history scans. Live
read-only poll/replay and a locally injected conflict in a separate captured-data
copy passed. Immediate automated API review/export/reopen evidence is recorded
in `cwf404-*`; human feedback and remote CI are still unverified.

**CWF403 / complete — 2 October 2026:** repair a confirmed local UI defect
within FR-005/007: `openCase` unconditionally clears the note after a stale-revision
conflict, contradicting the retry message and runbook. Preserve per-case drafts
in page memory, reset them only after a successful decision, offer an explicit
reload control, and prevent overlapping case reads/saves from targeting stale
screen state. Drafts are not persisted across page refresh or service restart.
Files: `sentinel/review/static/{app.js,index.html}`,
`sentinel/tests/review_ui.test.cjs`, `docs/colosseum/{RUNBOOK.md,VERIFICATION.md}`,
this task list and `docs/colosseum/PLAN_v0.5_UK.md` (with its `D:\1111` copy).
Justification before editing: retain operator work during the existing revision
workflow; no new scope, dependencies or chain/action endpoints. Node's built-in
test runner is verification tooling only, not a product runtime requirement.
Gate: reproduce failure against the old JS; stale conflict/reload retains the
draft, different cases keep separate drafts, delayed reads cannot replace the
selected case, retry retains the idempotency key, successful save clears the
draft; isolated browser check, Python non-regression, Ruff/MyPy and JS syntax.
Verification: `node --test sentinel/tests/review_ui.test.cjs`, plus the existing
Python/source gates. User authorized autonomous local work and verification.
PASS: five JS regressions, isolated two-tab browser conflict/reload/export,
synthetic fresh-process persistence/replay, 302 Linux Python tests, Ruff, all
strict MyPy targets, Compose, nine Foundry tests and packaged assets.
Evidence includes `docs/colosseum/ui-conflict-{brief,restart}-2026-10-02.*`
and `ui-conflict-regression-2026-10-02.png`; automated synthetic only.

Execution update, 2026-10-01: CWF101–302 passed their local gates and were
committed. CWF401 is in progress; the owner chose to be the first operator.
The first human session has started. Prepare CWF402 documents alongside that
session, but do not mark delivery complete before its dependencies pass.

CWF401 evidence files: save sanitized live session JSON/text briefs and actual
UI screenshots in `docs/colosseum/`. The first human acknowledgment is now
verified at 18:32:58Z; resolution/export/qualitative feedback remain pending.

CWF402 file-list extension and justification before editing: update
`.github/workflows/ci.yml` only to include `feat/colosseum-review` in the
existing push trigger, so a later authorized publication can run current-HEAD
CI. Add the ready-to-review plan `docs/colosseum/PLAN_v0.4_UK.md` and its copy
in `D:\1111`. Update this task list and acceptance matrix to reflect measured
results. These changes add no product runtime or remote publication.

**CWF401 / in progress:** new live controlled review rehearsal and restart/replay evidence; runbook and 2–3 operator sessions. Proposed files: `docs/colosseum/REHEARSAL.md`, `USER_FEEDBACK.md`, `deployments/` sanitized records. Any signing rehearsal follows owner authorization; historical read-only evidence can establish the first spike but cannot be presented as a newly executed transaction. Depends: CWF302.

**CWF402 / preparation in progress:** disclosure, current-HEAD verification/CI, English pitch/demo, source/contract links, Colosseum submission package and confirmation. Files: `docs/colosseum/SUBMISSION_PACK.md`, `DISCLOSURE.md`, `VERIFICATION.md`, `README.md`. Use actual evidence for assertions and list prior Sentinel development. Depends: CWF401.

Verification: required full suite/lint/types/contract/CI gates; anonymous repo/video/link checks; actual submission confirmation. Demo target: 8 October; internal submission target: 12 October 20:00 Kyiv.
