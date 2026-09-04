# NexGuard Sentinel — acceptance map

| ID | Acceptance test or evidence | Gate |
|---|---|---|
| ES-FR-001 | keeper pause succeeds; keeper unpause fails; owner unpause with reason succeeds; duplicate ref is idempotent | EG-1 |
| ES-FR-002 | Vault operation succeeds unpaused and reverts paused | EG-1 |
| ES-FR-003 | deployed Subgraph returns real entity with canonical ID and `_meta` block | EG-2 |
| ES-FR-004 | cursor/replay/reorg-window/restart tests; duplicate entity yields no second reservation | EG-3 |
| ES-FR-005 | golden structured feature input and schema-valid classification trace | EG-4 |
| ES-FR-006 | malformed, hostile, timed-out, unknown, long, and low-confidence outputs refuse action | EG-4 |
| ES-FR-007 | concurrent `check_and_reserve` test has exactly one winner | EG-3 |
| ES-FR-008 | crash-after-reserve and crash-after-broadcast reconcile without blind resend | EG-3 |
| ES-FR-009 | success, already-desired, revert, timeout, reorg, and state-mismatch outcomes remain distinct | EG-3 |
| ES-FR-010 | canonical JSON golden bytes/hash match the emitted incident reference | EG-3 |
| ES-FR-011 | CLI reports state; reconcile resolves known outcome; reset requires operator and reason | EG-3 |
| ES-FR-012 | outbox survives restart, retries, and exposes terminal failure | EG-4 |
| ES-NFR-001 | chain mismatch and non-testnet policy tests refuse signing | EG-3 |
| ES-NFR-002 | clean clone passes locked install, lint, types, tests, compile | EG-5 |
| ES-NFR-003 | Gitleaks directory/history and private denylist scans are clean | EG-0, EG-5 |
| ES-NFR-004 | end-to-end audit record contains every required stable field | EG-5 |
| ES-NFR-005 | existing gateway test suite and applicable Compose gates remain green | EG-5 |

Approval of this document authorizes Stage 1 implementation only. Later stages
advance only after the preceding gate passes, following `AGENTS.md`.
