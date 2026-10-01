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
