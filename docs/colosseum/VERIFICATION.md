# Verification record — SPEC-003

Baseline: 7a2a509; isolated checkout, 1 October 2026. Results refer to the local
source revision/diff named below, never implicitly to a remote CI revision.

## CWF001 baseline

- Python 3.12.14, pinned lock installed in isolated Windows venv.
- Windows full pytest: 231 PASS, 8 FAIL. All failures are unchanged POSIX
  controller backup/restore calls (`os.fchmod` unavailable on Windows).
- Windows Sentinel/contract/gateway subset: 197 PASS.
- Ruff entire repository: PASS.
- Strict MyPy Sentinel (40 files), gateway (6 files), deploy (1 file): PASS.
- Windows controller MyPy: 3 POSIX platform errors; supported Linux gate pending.
- Docker Compose configuration: PASS in WSL.
- Foundry baseline format: FAIL due CRLF in tracked Solidity; no semantic changes.
  After documented LF-only normalization: format PASS, 9 contract tests PASS.
  `git diff --ignore-space-at-eol -- contracts` is empty.
- Live public Graph/RPC reachability and indexed block hash agreement: PASS;
  receipt validation and new review implementation remain pending.

Linux Python 3.12 full baseline pytest: **239 PASS**; strict controller MyPy:
**PASS, 19 files**. Image built locally from python:3.12-slim and committed lock.
CWF001 applicable baseline gates pass after the LF-only repair. Review gates
are pending. No current remote CI, human feedback/video or submission is claimed.

## CWF101–102

- 27 focused review tests PASS. Full Linux suite: 266 PASS; repository Ruff,
  strict MyPy for Sentinel (46 files), gateway/controller/deploy and Compose PASS.
- Public live observer: 5 historical withdrawals verified against canonical RPC
  block hashes/timestamps, receipt status, vault/log identity and all emitted fields.
- Repeat poll: 0 new observations; persisted review database retained 5 rows.
- Guardian paused=true read at the reported snapshot, not inferred from a finding.
- Source clock ahead by approximately 12 seconds; explicit bounded future skew=30s.
- Number-pinned Graph _meta returned null hash. Hash-pinned queries return the
  anchor hash; observer requires equality and rechecks the anchor after paging.
  API semantics: https://thegraph.com/docs/en/subgraphs/querying/graphql-api/
- Evidence: observer-live-2026-10-01.json. No transaction sent; historical events
  are not new hackathon transactions. No review policy evaluated at this stage.

## CWF201–202

21 focused tests PASS. Full Linux suite: **287 PASS**. Ruff, strict MyPy
Sentinel (51 files), gateway/controller/deploy and Compose PASS.
Integer threshold boundaries, invalid/scientific/float parameters, uint256 precision,
restart evaluations, degraded-source block, version identity and evidence exports pass.
Recorded success/reverted/indeterminate/already_desired outcomes are read via mode=ro;
tests verify legacy database bytes are unchanged. Missing legacy state is not created.
Fixtures produce no explorer links. A review case never implies successful pause.

## CWF301–302

Full Linux suite: **302 PASS**, including **63 new review tests**. Repository Ruff,
strict MyPy Sentinel (54 files), gateway/controller/deploy and Compose PASS.
JavaScript syntax check PASS. Wheel builds and contains all three static assets.

Browser acceptance on 127.0.0.1:8090, isolated synthetic database:
source overview, queue, detail, acknowledgment, resolution with expected_activity,
history revision 2 and text-brief download PASS. HTML-like note is displayed as
literal text; no browser console errors. Screenshot: ui-fixture-acceptance.jpg;
downloaded brief: ui-fixture-brief.txt. Operator label explicitly identifies an
automated fixture test. This is not a human user session or a live chain decision.

Cross-origin/missing-origin/missing-header writes, hostile Host, oversized payload,
invalid state/revision/fields and unknown paths are rejected. Old source health is
projected as stale; its recorded facts remain intact.

## CWF401–402 preparation — 1 October 2026

Production implementation through `4144eeb`, plus the delivery documentation
and CI push-trigger diff. No remote CI run is implied.

- Full Linux Python 3.12 suite rerun: **302 PASS** in 11.46s, three dependency
  deprecation warnings. Repository Ruff and all four strict MyPy targets PASS
  (Sentinel 54, gateway 6, controller 19, deploy 1 files). Compose config PASS.
- Pinned Foundry image: format PASS and **9/9 contract tests PASS**.
- Node 22 container, committed Subgraph lock: codegen/build PASS. Local
  Matchstick 0.6.0 container: **1/1 mapping test PASS**. Generated dependencies
  and outputs remain in ignored `.venv/subgraph-gate`; source is unchanged.
- Official Gitleaks 8.30.1 container, digest
  `sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f`:
  working-directory scan PASS, zero leaks; full local history with `--all` PASS,
  **64 commits**, zero leaks. Existing config/default rules unchanged; generated
  dependency/cache paths are allowlisted. Findings are redacted. These scans
  precede the final delivery-document commit.
- CI YAML comparison PASS: only the existing push branch list gained
  `feat/colosseum-review`; jobs/permissions were unchanged.
- Original `D:\NexGuard Sentinel` checkout remains clean. No shared legacy
  runtime, contract semantics, source deployment or signing configuration changed.
- First human acknowledgment confirmed in live UI and local API: case
  `bbbfdd578c1c…ccaf9`, revision 1, 18:32:58.037924Z. Evidence:
  `first-operator-live-2026-10-01.json`, `first-operator-brief.{json,txt}` and
  `ui-first-operator-acknowledged.jpg`. Brief files were captured by the agent;
  they do not prove a human download.

Still pending: human resolution/export and qualitative feedback; a post-session
service restart retaining human history; independent operators; current remote
CI including Docker end-to-end scenarios; video recording/anonymous links and
actual submission confirmation. CWF401/CWF402 and A09/A10 remain partial.

## CWF403 local UI repair — 2 October 2026

Starting revision: `4608d44`, branch `feat/colosseum-review`; this section records
the CWF403 source diff, not remote CI. The confirmed defect was unconditional
draft loss when reopening a stale case. Regression tests against the old script
also exposed disposition carryover and an older read replacing the selected case.
Old JS: one passing test, three assertion failures and one cancelled pending test.
Repaired JS: **5/5 PASS**, using Node 22's built-in test runner and controlled
responses against the actual app script. JS syntax PASS.

- Linux Python 3.12 full suite: **302 PASS**, three dependency deprecation warnings.
  Source copied into a disposable verification container from the current diff;
  no signing credentials, networking or writable source mount. Ruff PASS; strict
  MyPy Sentinel/gateway/controller/deploy PASS (54/6/19/1 source files).
- Windows supported Sentinel/contract/gateway subset: **260 PASS**, same three
  warnings. The unchanged POSIX controller suite is covered by Linux.
- Compose configuration PASS; no stack restart or Docker e2e run in this cycle.
- Pinned Foundry format PASS, **9/9 tests PASS**. The first network-disabled run
  could not fetch Solc 0.8.24; the subsequent run fetched the compiler and passed.
  Source stayed read-only and compilation ran in temporary container storage.
- Wheel build initially lacked local setuptools. Standard isolated build obtained
  declared build dependencies and succeeded; all three packaged UI assets checked
  byte-for-byte against source. No product dependency/lock change was needed.
- Browser acceptance used only `.sentinel/qa-2026-10-02.sqlite3`, port 8091.
  Two tabs loaded synthetic case `cd5ba43c7d53…31a05` at revision 0. Tab A
  acknowledged it; tab B got HTTP 409. **Reload case retained tab B's exact note**
  and loaded revision 1; its synthetic resolution produced revision 2 and two
  history entries. Saved notes/history matched the downloaded text brief.
  No browser JS error logs were observed. Drafts are in page memory, not durable.
- A fresh service process on port 8092 read the same synthetic database and
  retained the exact case/history. Re-seeding preserved 3 observations,
  2 cases and 3 evaluations, with zero conflicts. The temporary process was stopped.

Evidence: `ui-conflict-regression-2026-10-02.png`,
`ui-conflict-brief-2026-10-02.txt`, `ui-conflict-restart-2026-10-02.json`.
This is automated synthetic acceptance, not human feedback or a live chain verdict.
Human resolution/export/feedback, independent sessions, current remote CI, video
publication and submission confirmation remain pending. A09/A10 remain partial.

## CWF404 conflict queue repair and immediate technical review — 2 October 2026

Starting revision: `adcd983`, `feat/colosseum-review`; results apply to the
CWF404 source diff. The owner reproduced a conflicting observation preventing
all later evaluations and requested immediate agent-led verification.

Before repair, four new regressions failed: synthetic/live-origin known conflict,
101 conflicts before a valid event, and a conflict recorded after selecting the
batch. A policy-version conflict guard passed. Repair excludes durable conflicts
with NOT EXISTS before LIMIT and catches the individual evaluation-write conflict
so the rest of the selected batch continues. Source health/policy registration
checks stay outside that handler. No schema change; original payload/conflicts and
pre-existing cases/history remain intact.

- **308 Python tests PASS** in Linux Python 3.12 (12.07s), including **69 review
  tests** and six new regressions. Ruff PASS, strict MyPy all four targets PASS
  (54/6/19/1 files). Disposable local container, network disabled, source read-only.
- Windows focused review subset: **69 PASS**. JS regressions: **5 PASS**.
  Whole Windows suite/Foundry/Subgraph/browser UI acceptance were not rerun in
  this cycle; prior results above retain their original revision/date.
- Real API background-loop regression uses a healthy poll fixture: unrelated
  event opens its case; recorded_status=healthy, public status=
  reconciliation_required; no evaluation_error metadata write. Tests exercise
  actual SQL conflicts, not merely a mocked exception. The concurrent-conflict
  regression injects the real conflict immediately before evaluated() writes.
- Compose configuration PASS. Gitleaks 8.30.1 directory scan: zero leaks;
  full-history scan with --all: **66 commits**, zero leaks, before this commit.
  Generated paths use the existing allowlist; findings are redacted.
- Real public read-only observer at 16:03:20Z: five historical withdrawals,
  five evaluations, four cases. Repeat at 16:05:17Z: zero new observations and
  evaluations; Graph/RPC healthy, canonical snapshot validated. Block clock was
  16 seconds ahead, within the existing explicit 30-second bound. No key/model,
  source deployment or onchain transaction was used.
- The isolated QA case `bbbfdd578c1c…ccaf9` was acknowledged/resolved via the
  actual API with operator `Codex automated technical review`. Exported JSON/text
  show revision 2, two actions and insufficient_evidence. Reopening the same file
  retained the exact history; rule replay created no additional evaluation.
  The original human-session database was not changed.
- An **isolated copy** of all five captured observations received a local injected
  conflict for the first event. All four following events evaluated and opened
  four cases; one conflict and zero evaluations for the rejected event remain.
  Reopening/reprocessing produced zero new evaluations. The injected conflict
  is a local test, not an observed provider discrepancy or a new chain event.

Evidence: `cwf404-rehearsal.json`, `cwf404-technical-review.{json,txt}`.
Technical review is automated and does not establish human feedback, independent
validation, exploit/financial loss or successful remediation. A09/A10 stay partial.

Delivery preflight: separate `github` remote configured; ls-remote found
main=`9ffdf26f09e4cfd1d9629c9d2d2d5cba84b09f76`, historical event branch=
`7a2a5092498aeffd47efd8ae5eed5815624554f4`, no remote feat/colosseum-review.
No push occurred. First remote CI target moved to 3–5 October, before 8 October
freeze. Fresh Subgraph/release-candidate scans remain mandatory before publication.

Official rules section 5, checked 2 October, specifies 12 October 2026 23:59 PT;
Windows timezone rules convert this to 13 October 2026 09:59 Europe/Kyiv.
Internal target remains 12 October 20:00 Kyiv. Personal-portal display is not
verified. Source: https://colosseum.com/legal/Crypto%20World%27s%20Fair%20Hackathon%20Rules.pdf.
