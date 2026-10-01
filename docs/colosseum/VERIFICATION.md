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
