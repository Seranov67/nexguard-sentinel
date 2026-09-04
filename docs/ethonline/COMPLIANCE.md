# Compliance evidence register

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
| Graph CLI dependency audit | 15 advisories: 1 critical, 10 high, 4 moderate | open risk |
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
| Live Graph provider | Subgraph ID, public-safe endpoint form, query and response metadata | pending |
| Meaningful AI use | schema, prompt/version, Graph-derived inputs, output and policy trace | pending |
| Working automation | Graph entity → reservation → tx → confirmations → state re-read | pending |
| Testnet contracts | chain ID, addresses, deployment tx hashes, explorer links | pending |
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
| | Deployment | chain/address/tx | |
| | Graph deploy | Subgraph ID/version | |
| | Live query | indexed block/entity/latency | |
| | End-to-end run | incident ref/tx/final state | |
| | Check-in | Dashboard confirmation | |
| | Submission | Dashboard confirmation | |
