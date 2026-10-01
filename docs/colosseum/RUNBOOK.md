# Local Incident Review Desk

Use Python 3.12 and the committed lock. In this implementation checkout the
verified environment is `.venv\Scripts\python.exe`.

## Live source, no signing credentials

From `D:\1111\sentinel-colosseum`:

```powershell
.venv\Scripts\python.exe -m sentinel.review.cli serve
```

Open http://127.0.0.1:8089. The service polls the fixed public Graph/Base Sepolia
source every 15 seconds and drains durable evaluations after a complete verified
scan. State lives in `.sentinel/review.sqlite3`. No `.env` is loaded, no keeper or
model is needed, and no transaction is created. Stop with Ctrl+C and restart the
same command to preserve observations, cases and decisions.

Read once without the UI:

```powershell
.venv\Scripts\python.exe -m sentinel.review.cli observe --once
```

`serve --offline` opens stored evidence without polling; old health is labelled stale.
An optional `--legacy-state PATH` connects recorded prior action evidence using
SQLite read-only mode. It does not reverify current chain outcomes or bypass the
original evidence API's payment gate. Never use the same review and legacy file.

## Explicit synthetic demo

```powershell
.venv\Scripts\python.exe -m sentinel.review.cli demo --port 8090
```

Separate `.sentinel/review-demo.sqlite3`; three fixtures, two above the 100-unit
synthetic threshold and one negative example. The UI labels fixtures, leaves chain
state unknown, and supplies no fake explorer links. Restart preserves decisions.
Do not reuse a live database for this command; source binding rejects mixing.

## Review a case

1. Check source health and its timestamp. Open Review queue and select a case.
2. Compare exact amount, threshold, source ID and block/receipt evidence. Read gaps.
3. Enter your local operator label and a note, then acknowledge the case.
4. Enter a resolution note and choose policy_breach, expected_activity or
   insufficient_evidence. Resolving records your assessment; it changes no contract.
5. Export JSON and text briefs. If another window updated the revision, retain your
   note and reopen the case before retrying with the current revision.

Source conflicts require reconciliation and are retained. Operator decisions cannot
erase them. The local review feature has no reconciliation/reset/signing endpoints.

## Verification

Focused review tests: `python -m pytest -q sentinel/tests/test_review_*.py`.
Full tests and controller types run on Linux Python 3.12; the original controller
uses POSIX permission operations. See VERIFICATION.md for measured results.
