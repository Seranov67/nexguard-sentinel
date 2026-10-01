# SPEC-003 — acceptance matrix

Measured status: 1 October 2026, local implementation through commit `4144eeb`.
The owner approved SPEC-003 and the narrow local UI amendment with “так далі”.
Automated fixture acceptance and human operator activity are recorded separately.

| Check | Requirement | Status and evidence |
|---|---|---|
| A01 Approved scope and UI amendment | FR-010, NFR-004 | PASS — AGENTS.md, Constitution amendment, BASELINE.md and preserved Git history |
| A02 No-key durable observer | FR-001, NFR-001 | PASS — read-only RPC allowlist, import isolation, independent schema, legacy DB immutability tests |
| A03 Verified source and degraded state | FR-002 | PASS — five historical live withdrawals with canonical receipt/log/block validation; health/hash/degraded tests; SOURCE_STATUS.md |
| A04 Deterministic threshold | FR-003 | PASS — integer/uint256 boundaries, exact units, immutable policy versions and case IDs; four live cases, one negative event |
| A05 Replay/restart/conflict | FR-004, NFR-002 | PASS — durable pending evaluations, repeat live poll/evaluation creates zero new rows; rollback/conflict/concurrency tests |
| A06 Workflow and concurrency | FR-005, FR-007 | PASS for implementation — fixture open→acknowledged→resolved, revision 2, history and idempotency tests; first human acknowledgment at 18:32:58Z |
| A07 Evidence and actual action outcomes | FR-006 | PASS — read-only legacy adapter, explicit missing/recorded/current-state distinctions, real versus fixture links, JSON/text exports |
| A08 Local UI and export | FR-007/008 | PASS — three screens, browser fixture acceptance, literal-text rendering, origin/Host/body guards, wheel assets; first human live use started |
| A09 Live product | FR-009 | PARTIAL — historical onchain events→new review cases, replay and first human acknowledgment verified. Human resolution/export/qualitative feedback remain pending. No newly executed transaction is claimed |
| A10 Current quality and delivery | FR-009/010, NFR-003 | PARTIAL — local 302 tests, Ruff, strict types, Compose and nine contract tests pass. See VERIFICATION.md for subsequent delivery checks. Remote CI, recorded videos and submission receipt remain pending |

Evidence lives in [docs/colosseum](../../docs/colosseum/): VERIFICATION.md,
REHEARSAL.md, USER_FEEDBACK.md and sanitized source snapshots. Completion of
automated tests does not establish demand, revenue or independent user validation.

The separate Node prototype passed 17 tests, but it supplies no acceptance
evidence for this canonical Python product.
