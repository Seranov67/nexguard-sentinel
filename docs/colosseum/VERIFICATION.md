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
