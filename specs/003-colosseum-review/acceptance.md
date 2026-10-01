# SPEC-003 — acceptance matrix

Status: proposed. Only planning artifacts and the separate experimental prototype are completed today.

| Check | Requirement | Proof needed |
|---|---|---|
| A01 Approved scope and UI amendment | CWF-FR-010, NFR-004 | Owner approval plus preserved baseline/history |
| A02 No-key durable observer | FR-001, NFR-001 | Run without keeper/model; signer methods inaccessible; legacy DB unchanged |
| A03 Verified source and degraded state | FR-002 | Captured Graph/RPC cases, confirmations/hash mismatch tests, gap UI |
| A04 Deterministic threshold | FR-003 | Exact integer boundary/unit/version tests; no authorization of action |
| A05 Replay/restart/conflict | FR-004, NFR-002 | Temporary DB crash/restart/replay; one case; conflicting payload flagged |
| A06 Workflow and concurrency | FR-005, FR-007 | open→acknowledged→resolved; actor/note/disposition; revision conflict rejects duplicate decision |
| A07 Evidence and actual action outcomes | FR-006 | Source IDs, policy/model/receipt/state distinguished; no fabricated cause or success |
| A08 Local UI and export | FR-007/008 | Three usable screens, allowed-origin validation, package assets, JSON/text brief with correct provenance |
| A09 Live product | FR-009 | Actual supported onchain event→review case→operator decision; restart/replay record; operator feedback |
| A10 Current quality and delivery | FR-009/010, NFR-003 | Current-HEAD required tests/CI, disclosure, English pitch/demo and actual submission receipt |

Prototype verification on 1 October: Node v22.17.1, `node --test` 17/17 passed and `node src/demo.mjs` passed. This verifies only the independent synthetic authority-policy prototype. No acceptance check above is satisfied by substituting that result for canonical Python/live verification.
