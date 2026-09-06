# NexGuard Sentinel: engineering status, 6 September 2026

## Outcome

Stage 5 live evidence is verified. Final hackathon delivery remains open because
human video and final Dashboard confirmation are unavailable. The earlier morning
audit and its unavailable-model findings are preserved in Git history.

Working branch: `feature/ethonline-sentinel`; workspace: `D:\NexGuard Sentinel`.
The IoT MVP remains preserved and regression-tested.

## New live rehearsal

- Local Ollama 0.33.3 / Qwen3 4B Instruct, Python 3.12.14, locked dependencies.
- New valueless withdrawal: block **46474498**.
- Live Graph indexed the entity; bounded AI features included that single new
  withdrawal. Five pending historical/new entity IDs were reserved in one intent.
- Real model returned critical/pause; deterministic policy reserved one action.
- Pause transaction: `0x26f2076b9dc3c1e7313f68cd0506e393e38a11a4680b06eb6a558bd77b59a750`,
  block **46474539**.
- Initial RPC verification was indeterminate and latched. A separate no-send
  reconcile verified the canonical receipt, confirmations and paused state.
- Attributed latch reset followed successful reconciliation. A separate process
  rerun found no new events and created no second pause transaction.
- Withdrawal eth_call in paused state reverted. Both outbox notifications delivered.
- Three new transactions total: demo credit, demo withdrawal and one pause.
  No owner unpause was performed. **Guardian is currently paused.**

Full records: [live-e2e-2026-09-06.json](deployments/live-e2e-2026-09-06.json).
The model rationale contains qualitative overstatement; the earlier preview also
misstated numeric values. Preserve exact outputs and treat recorded numeric inputs
as authoritative. This is not a measured claim of model explanation accuracy.

## Verification

| Check | Result |
|---|---|
| Python 3.12 full suite | 186 PASS, including 131 Sentinel tests |
| Repository Ruff / strict Sentinel MyPy | PASS; types include tests |
| Foundry | 9 tests PASS |
| Subgraph codegen/build and Matchstick | PASS; 1 mapping test |
| Isolated Compose restart/config recovery | PASS |
| Package install/import/assets | PASS in preceding engineering audit |
| Gitleaks source/history and private denylist | PASS |
| GitHub CI at 6f03dff | All four jobs PASS, run 34050527569 |

CI initially failed because Foundry could not write to the runner's checkout.
The job now builds a temporary copy of read-only source. The later code change
adds only a bounded configurable A/B timeout plus five rejection cases; local
checks and the subsequent remote run both pass. The final documentation-only
commit follows this verified code revision.

## Partner and delivery status

The Graph is demonstrated in the real model-backed action path. Recipe/MCP tools
retrieve the persisted incident and recompute payload integrity. The real-model
A/B status and unedited outputs are recorded in BAZANTIC_AB_BENCHMARK.md; structural
checks are not explanation-accuracy or statistically significant improvement claims.
Payment settlement is not implemented.

The owner confirmed there is no Ledger device and no human voice recording.
ERC-7730 schema/CLI simulation is retained as a prototype, without a hardware
Clear Signing qualification claim. Do not select a prize based on unperformed
hardware work.

The earlier ETHGlobal project draft was saved. An evening attempt to update it
failed because the local browser tool could not initialize its assets. Current
copy is in [SUBMISSION_PACK.md](SUBMISSION_PACK.md). Final submission availability
must be rechecked in the authenticated Dashboard; no final confirmation exists.

## Remaining work

1. Human review of real A/B explanations and accurate partner choices.
2. Record human narration and screen footage; export 2–4 minutes at >=720p.
3. Verify the video URL without authentication; paste current project text and
   select supported prizes in Dashboard when final submission is available.
4. Retain final confirmation. Internal target: 13 September 17:00 Europe/Kyiv;
   hard deadline: 19:00. Do not introduce new product scope before submission.

Official rules: https://ethglobal.com/events/ethonline2026/info/details
