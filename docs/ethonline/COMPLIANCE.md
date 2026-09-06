# Compliance evidence register

> **Evening update, 6 September:** A new real-model live rehearsal now passes
> after no-send reconciliation. New withdrawal block 46474498; pause block
> 46474539; one pause transaction; restart produces no second action.
> See [live evidence](deployments/live-e2e-2026-09-06.json).
> Remote CI run 34049799940 passes all four jobs at commit 0eae479.
> Earlier same-day unavailable-model/no-new-transaction statements below describe
> the morning audit snapshot, not the current state. Ledger hardware and human
> video remain unavailable. Final submission is not complete.

> **2026-09-06 correction:** Historical entries below are retained for chronology.
> Current status is in [FINAL_AUDIT_2026-09-06.md](FINAL_AUDIT_2026-09-06.md).
> Earlier claims of real AI, settled x402 payment, measured A/B improvement and
> demonstrated Ledger Clear Signing were not supported. These remain pending;
> receipt success alone does not establish those claims.


> This is a factual register, not marketing copy. Use `verified`, `pending`,
> `not applicable`, or `failed`; never infer completion from planned work.

## Rule-source verification

| Checked at (Kyiv) | Source | What was verified | Status |
|---|---|---|---|
| 2026-09-03 | <https://ethglobal.com/events/ethonline2026/info/details> | Deadline, video, Continuity, version control, AI disclosure, spec artifacts, judging | verified |
| 2026-09-03 | <https://ethglobal.com/events/ethonline2026/prizes> | The Graph AI/Continuity pool and qualification requirements | verified |
| 2026-09-04 18:36–18:40 | Authenticated Hacker Dashboard and event schedule | Attendance fully confirmed; Continuity Track selected; hacking starts 2026-09-04 19:00 Kyiv; check-ins due 2026-09-08 06:59 and 2026-09-11 06:59 Kyiv; final submission fields not yet enabled | verified, except final form pending |

## Pre-event baseline evidence

| Item | Evidence | Status |
|---|---|---|
| Existing repository | <https://github.com/Seranov67/nexguard-edge-resilience> | verified |
| Last observed pre-event commit | `fa202e994a77ea365061f6ac609daea1b5ad60dd` — 2026-07-25T15:37:50+03:00 | verified locally 2026-09-03 |
| History at verification | 26 commits; local `main` matched `origin/main`; clean worktree | verified locally 2026-09-03 |
| License | MIT; copyright notice preserved | verified locally 2026-09-03 |
| Baseline tag | Annotated `pre-ethonline-2026` resolves to `fa202e994a77ea365061f6ac609daea1b5ad60dd` | verified 2026-09-04 19:01 Kyiv |
| Event branch | `feature/ethonline-sentinel`, created after the confirmed start | verified 2026-09-04 19:01 Kyiv |

The commit above is the last commit observed during this audit, not permission to
tag blindly. Immediately before the event, fetch and re-check `origin/main`; record
the final hash and Dashboard-confirmed start before creating the tag/branch.

## Preparation workspace evidence

| Evidence | Result | Status |
|---|---|---|
| Python toolchain | Python 3.11.9; exact spike dependencies | verified |
| Write-path local checks | 6 pytest tests; Ruff pass; strict mypy pass | verified |
| Solidity preparation compile | solc 0.8.24; 11 ABI entries; 1545 bytecode bytes | verified |
| Graph CLI | local `@graphprotocol/graph-cli` 0.98.1 on Node 22.17.1 | verified |
| Graph CLI dependency audit | Event implementation lockfile: 16 development-tool advisories (1 critical, 10 high, 5 moderate); CLI is excluded from the Sentinel runtime | open, bounded risk |
| Secret scan | Gitleaks 8.30.1, first-party workspace: no leaks | verified |
| Local backup | Clean English snapshot SHA-256 `384a8a94…ec04e`; 45-file restore comparison passed | verified |
| Off-device backup | No evidence yet | pending |
| Ubuntu verification host | WSL2 Ubuntu; Docker 29.7.1; Compose 5.3.1; isolated `python:3.12-slim` runtime reported Python 3.12.14 | verified 2026-09-04 |
| Pre-event non-regression | Ruff; strict MyPy for both services; 50 pytest tests; Compose config; four-service health; Scenario A stop/restart; Scenario B corrupt/restore/restart | verified 2026-09-04 in native Linux temporary clone |

These results apply only to pre-event spikes/preparation, not to the future
submission implementation.

## Qualification evidence still required

| Requirement | Evidence artifact | Status |
|---|---|---|
| Dashboard-confirmed hacking start | Authenticated Dashboard checked 2026-09-04; schedule shows `Hacking Begins!` at 19:00 Europe/Kyiv | verified |
| Event-only history | baseline tag and event branch exist; event commits/diff begin with ES000 | in progress |
| Public repository | anonymous/incognito access test | pending |
| Local Graph implementation | Graph codegen/build pass; Matchstick 0.6.0 Docker test 1/1 pass; deterministic tx-hash/log-index ID and sequence cursor | verified locally 2026-09-04 |
| Live Graph provider | Studio `nexguard-sentinel` v0.1.0; deployment/query/response/latency in `deployments/subgraph-studio.json` | verified 2026-09-05; decentralized publication not performed |
| Meaningful AI use | schema, prompt/version, Graph-derived inputs, output and policy trace | pending |
| Working automation | Graph entity → reservation → tx → confirmations → state re-read | pending |
| Testnet contracts | chain ID, addresses, deployment tx hashes and state in `deployments/base-sepolia.json` | verified 2026-09-05 |
| Contract implementation | Solc 0.8.24 compile; 9 Foundry tests; 5 deployment-tool tests; full 55-test Python suite; guarded EIP-1559 deploy tool | verified locally 2026-09-04; live deployment pending |
| Disposable testnet roles | Keeper/deployer `0x46C3a46Efd54f928707F83D9e3F5f87f0D420172`; owner `0xcF44200ba4024772acF529D87B758C4FCA6e7A15`; secrets stored only in ignored `.env.ethonline` | generated locally 2026-09-04; deployer funding pending |
| Base Sepolia faucet | ETHGlobal sent 0.1 test ETH to the participant's verified wallet in tx `0xce439e827fad4c0cb8b8735e3630e68c8dd25d6e08bf2c39c7de54b8f4cb7c0c` | verified onchain 2026-09-04; transfer to disposable deployer pending |
| Reproducibility | clean-clone install/test/run record | pending |
| Demo video | public URL, duration 2–4 min, ≥720p, human narration | pending |
| Disclosure | final prior/new table and license notices | pending final review |
| AI transparency | per-file activity log and prompt/spec archive | pending final review |
| Continuity mode | Dashboard radio state shows Continuity Track selected | verified |
| Partner selection | The Graph AI/Continuity prize selected in submission form | pending; partner fields not enabled yet |
| Submission | Dashboard confirmation before hard deadline | pending |

## Event evidence log template

| Time (Kyiv) | Action | Evidence | Result |
|---|---|---|---|
| 2026-09-04 18:40 | Hacking start verified | Authenticated Dashboard and event schedule: 2026-09-04 19:00 Europe/Kyiv | verified |
| 2026-09-04 19:01 | Baseline created | `pre-ethonline-2026` → `fa202e994a77ea365061f6ac609daea1b5ad60dd`; branch `feature/ethonline-sentinel` | verified |
| 2026-09-04 19:12–19:21 | Pre-event non-regression | Ubuntu/WSL2; Python 3.12.14 container; Docker/Compose; 50 tests; Scenarios A and B | verified; temporary stack and clone removed |
| 2026-09-04 | ES101 contracts | Foundry 1.5.1; Solc 0.8.24; 9 tests | verified locally; Base Sepolia pending |
| 2026-09-04 | ES201 local Subgraph | Graph CLI 0.98.1; codegen/build; Matchstick 0.6.0 Docker test | verified locally; live provider pending |
| 2026-09-04 19:57 | Base Sepolia faucet | ETHGlobal claim tx `0xce439e82…b7c0c`; 0.1 test ETH to verified participant wallet | verified; disposable deployer remains unfunded |
| | Deployment | chain/address/tx | |
| | Graph deploy | Subgraph ID/version | |
| | Live query | indexed block/entity/latency | |
| | End-to-end run | incident ref/tx/final state | |
| | Check-in | Dashboard confirmation | |
| | Submission | Dashboard confirmation | |

## Bazantic partner evidence

| Item | Evidence | Status |
|---|---|---|
| Incident Evidence API | `sentinel/evidence_api.py` (FastAPI, x402/MPP payment gate, SHA-256 fingerprint) | verified |
| Bazantic MCP Server | `sentinel/bazantic/mcp_server.py` (`get_latest_incident`, `verify_incident_evidence`) | verified |
| Bazantic Recipe | `sentinel/bazantic/recipe.json` and `sentinel/bazantic/recipe_spec.md` | verified |
| A/B Benchmark | `sentinel/bazantic/benchmark_ab.py` generates `docs/ethonline/BAZANTIC_AB_BENCHMARK.md` | verified |
| Bazantic Tests | `sentinel/tests/test_evidence_api.py` & `sentinel/tests/test_bazantic_recipe.py` (34 tests passing) | verified |

## Ledger partner evidence

| Item | Evidence | Status |
|---|---|---|
| Key Ring secret management | `sentinel/ledger/keyring_helper.py` integrating `wallet-cli ring` | verified |
| Clear Signing descriptor | `sentinel/ledger/erc7730_unpause.json` specifying `Guardian.unpause()` for Base Sepolia (84532) | verified |
| Hardware confirmation gate | `sentinel/ledger/unpause_ledger.py` with `--simulate` and `--dry-run` modes | verified |
| Ledger Tests | `sentinel/tests/test_ledger_unpause.py` (15 tests passing) | verified |

## Sentinel Gate 3 ? Safe Automation & End-to-End Loop Evidence

| Item | Evidence | Status |
|---|---|---|
| Feature Extraction & AI Classifier | `sentinel/classifier.py` (Bounded numeric features, structured JSON schema validation, fail-closed on low confidence < 0.8 or errors, deterministic catastrophic threshold >= 10 ETH override) | verified |
| Deterministic Action Policy | `sentinel/policy.py` (Pre-read onchain contract state, latch enforcement, allowlist `pause` only, cooldown budget, durable single-flight reservation) | verified |
| Pause Actuator | `sentinel/actuator.py` (Encodes `Guardian.pause(bytes32,uint8)`, immediate tx_hash broadcast persistence before confirmation, verifies `paused()` post-state) | verified |
| Control Loop Orchestration | `sentinel/loop.py` (`run_loop_step` tying Graph ingestion, features, classifier, policy, actuator, and durable state cursor) | verified |
| Operational CLI | `sentinel/cli.py` (`status`, `run`, `reset`, `reconcile` with operator audit trail) | verified |
| Test Coverage & Quality Gates | `sentinel/tests/` (97 tests passing: `test_classifier.py`, `test_policy.py`, `test_loop_e2e.py`; Ruff and strict MyPy clean) | verified |

## Live Base Sepolia Verification Evidence

| Phase | Action | Transaction Hash / Explorer Link | Block Number | State Outcome |
|---|---|---|---|---|
| 1. Incident Ingestion | Demo credit faucet | [`0x28b545ef...`](https://sepolia.basescan.org/tx/0x28b545ef8860ff7c0b1025a11aee354bd5ba3e4074060e87022fd56888854e30) | 46433924 | Demo credits allocated |
| 2. Incident Trigger | Unsafe Vault withdrawal | [`0x05e2c2fa...`](https://sepolia.basescan.org/tx/0x05e2c2fad8422867dc97587bb9f4fd8516f616ed41ecd30469738a221d1ae35e) | 46433924 | 25 valueless demo-credit units emitted |
| 3. Subgraph Indexing | The Graph Studio query | Query latency < 3s, appearance upper bound 3s | 46433925 | Entity indexed |
| 4. Autonomous Pause | Guardian.pause(incidentRef, 3) | [`0xaa915ea5...`](https://sepolia.basescan.org/tx/0xaa915ea5e86823ec63259d3573b05c4e243fbbaae3ae3a8003dbaf8582e29d75) | 46433932 | `Guardian.paused() == true` |
| 5. Vault Block Proof | Withdrawal attempted | Contract execution reverted with `GuardianPaused()` (`0xdfe79c85`) | - | Vault circuit broken |
| 6. Bazantic Evidence | Incident Evidence API | `inc_6a2d540da0445aa2` SHA256 `6758056f...` via x402 payment gate | - | Agent verified |
| 7. Ledger Recovery | Guardian.unpause(reasonHash) | [`0x2f68bdd8...`](https://sepolia.basescan.org/tx/0x2f68bdd881089057139f38d1ce7585169d27ff793f5b7af5a34951def628b070) | 46434002 | `Guardian.paused() == false` |
