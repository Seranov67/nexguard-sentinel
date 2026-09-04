# NexGuard Sentinel — ETHOnline quality gates

These gates apply to `specs/002-ethonline-sentinel`. Existing non-regression
gates for the completed gateway MVP remain mandatory.

## EG-0 — specification and provenance

- `pre-ethonline-2026` points to the verified final pre-start commit.
- The event branch begins after 2026-09-04 19:00 Europe/Kyiv.
- Spec, plan, tasks, acceptance, disclosure, attribution, AI records, and threat
  model exist and contain no secret values.
- No production implementation is added before owner approval of Stage 0.

## EG-1 — contracts

- Keeper can pause and cannot unpause.
- Owner can unpause with an attributed reason hash.
- Duplicate incident references revert or return an idempotent result.
- Vault operations read Guardian pause state.
- Contract tests and Solidity lint/compile pass.

## EG-2 — live Graph data

- A Base Sepolia withdrawal is indexed by a deployed Subgraph.
- Entity ID is transaction hash plus log index; sequence ordering is stable.
- A live provider query returns the real entity and `_meta` block information.
- Indexing and query latency are recorded.

## EG-3 — safe action loop

- Cursor, processed IDs, incidents, reservations, tx hash/nonce, outcomes, and
  outbox entries survive restart.
- `check_and_reserve` is atomic under duplicate and concurrent delivery.
- Tx hash is persisted immediately after broadcast.
- Success requires receipt status 1, confirmation depth, and `paused()==true`.
- Timeout, RPC disagreement, state mismatch, and storage failure latch as
  indeterminate; no blind resend occurs.

## EG-4 — AI boundary

- The classifier consumes bounded features derived from live Graph entities.
- Output schema, enums, confidence, and rationale length are validated.
- Timeout, malformed/adversarial output, or low confidence cannot authorize a tx.
- Deterministic policy remains final authority and AI has no signer access.

## EG-5 — qualification and delivery

- One live event produces at most one verified pause transaction.
- Restart, duplicate, concurrency, revert, timeout, and invalid-AI tests pass.
- Clean clone installs and passes Ruff, strict MyPy, pytest, contract tests, and
  applicable Compose checks.
- Working-tree and full-history Gitleaks scans are clean.
- Public repository, video, contract links, and Graph evidence work anonymously.
- The Graph AI/Continuity prize and final submission are confirmed in Dashboard.
