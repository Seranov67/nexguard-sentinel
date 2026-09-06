# NexGuard Sentinel: engineering audit, 6 September 2026

> **Evening update, 6 September:** A new real-model live rehearsal now passes
> after no-send reconciliation. New withdrawal block 46474498; pause block
> 46474539; one pause transaction; restart produces no second action.
> See [live evidence](deployments/live-e2e-2026-09-06.json).
> Remote CI run 34049799940 passes all four jobs at commit 0eae479.
> Earlier same-day unavailable-model/no-new-transaction statements below describe
> the morning audit snapshot, not the current state. Ledger hardware and human
> video remain unavailable. Final submission is not complete.

## Current stage

Stage 5: qualification evidence and delivery. The original assertion that only
video/form work remained was not supported by the code. Stages 3–4 were repaired
during this audit. Final qualification is **not complete**.

Branch: `feature/ethonline-sentinel`; repository: `Seranov67/nexguard-sentinel`.
The older IoT MVP and separate legacy checkout were preserved.

## Implemented and repaired

- Durable pending processing, rolling windows across polling cycles, atomic
  cooldown/action budgets, incident proofs and restart recovery.
- Signed transaction identity persisted before broadcast; canonical receipts,
  confirmations and final paused state checked; no blind resend.
- Real Ollama structured-output transport, bounded fail-closed validation and
  persisted model/prompt/input traces; durable notification leases and retries.
- Evidence API rejects arbitrary payment proofs. Demo bypass requires explicit
  server opt-in. MCP recomputes fingerprints, which prove payload integrity only.
- Real-model A/B runner replaces invented scores; no live result is claimed.
- Ledger uses Ethereum Keccak and a descriptor validated against the pinned
  official ERC-7730 schema; hardware owner address is checked before sending.
  Terminal previews remain simulations, not hardware Clear Signing evidence.
- Python 3.12 dependencies locked; package submodules and assets included.

## Verification

| Check | Result |
|---|---|
| Clean locked Python 3.12 install, full pytest | 181 passed, including 126 Sentinel tests |
| Repository Ruff | PASS |
| Strict MyPy, including Sentinel tests | PASS, 30 source files |
| Wheel installation, submodule imports and package assets | PASS |
| Foundry tests and formatting | 9 tests PASS; LF-normalized source |
| Subgraph install/codegen/build, Node 22 | PASS |
| Matchstick | 1 test PASS |
| Isolated Compose restart and corrupt-config recovery | PASS |
| Gitleaks source/history and local secret denylist | PASS |
| SQLite migration on a copy | PASS; original state untouched |

Only the labelled, allowlisted audit gateway was stopped for Compose checks.
Audit resources were cleaned; unrelated containers were untouched. Python reports
three dependency deprecation warnings; no failing tests. Legacy services require
separate MyPy invocations because both expose a package named `app`.

## Live evidence and limitations

Graph Studio v0.1.0 returns real data. The read-only preview polled four events
and produced a three-event rolling window. Historical number-pinned Graph metadata
returned a null hash; transport now pins queries by canonical RPC hash and rechecks
that hash after the response. A regression test covers this provider behavior.
See [read-only evidence](deployments/live-read-audit-2026-09-06.json).

Historical pause succeeded at block **46433932**, and owner unpause at **46434002**.
The earlier incorrect pause block was corrected. These receipts do not prove the
repaired runtime, real AI or Ledger use. No new onchain transaction was sent.

The configured SQLite database contains zero events. Local Ollama is unavailable
and no model is selected. The preview consequently produced no decision or action.
Real-model A/B evidence, settled payments, device rendering and hardware-signed
recovery are not established.

## Delivery and remaining work

The authenticated ETHGlobal description and technical explanation were updated;
the form confirmed **Saved!**. Title, category, Continuity selection and repository
were preserved. No demo URL was invented. The Dashboard currently says final
submissions are not enabled yet.

Project: https://ethglobal.com/showcase/nexguard-sentinel-1czjq

1. Configure a reachable Ollama endpoint/model and record a real classification
   trace; run and review the real-model A/B transcript.
2. Rehearse the repaired Graph-to-AI-to-pause flow on disposable Base Sepolia state
   and retain transaction/restart evidence.
3. Obtain Ledger hardware evidence if claiming that integration; otherwise retain
   the simulation limitation and review prize eligibility.
4. Record human narration and screen footage, export 2–4 minutes at >=720p, and
   verify the public/unlisted video link without authentication.
5. Add video and eligible partner choices when final submission becomes available;
   retain Dashboard confirmation before 13 September 2026, 19:00 Europe/Kyiv.

The [submission pack](SUBMISSION_PACK.md) contains corrected descriptions and a
roughly three-minute narration script. Official rules:
https://ethglobal.com/events/ethonline2026/info/details

## Git delivery

Audit implementation commits: `dce41aa` and `a8ea64f`; partner/packaging repairs and
this report follow in the final audit commit on the same event branch.
Local checks are not evidence of remote GitHub Actions success.
