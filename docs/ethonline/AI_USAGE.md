# AI usage

This project uses AI assistance. This log records where and how it was used so
reviewers can distinguish model assistance from human decisions and prior work.

## Tools

| Tool | Used for |
|---|---|
| Claude Code (Opus) | Pre-event architecture discussion, drafting, review and documentation |
| ChatGPT Codex | 3 September audit, official-rule research, risk analysis, preparation-document revisions, spike code/tests and local verification |

## Working method

The human owner defines the problem, scope, safety posture and acceptance
criteria; reviews generated changes; supplies credentials; operates accounts;
executes live deployments; and makes the final product and submission decisions.

AI output is treated as a draft. Code must pass tests and live acceptance gates.
For irreversible actions, no generated recommendation bypasses deterministic
guards, access control or post-action verification.

## Activity log

| Date | File / area | AI role | Human role / required verification |
|---|---|---|---|
| Pre-event, before 03 Sep | Initial `docs/`, `templates/`, `spikes/` | Claude assisted drafting and review | Architecture direction and acceptance criteria |
| 03 Sep | `AUDIT-2026-09-03.md` | Codex inspected workspace and referenced repos, checked current official pages, produced findings and recovery plan | Requested full audit; reviews conclusions |
| 03 Sep | `README.md`, `PLAN.md`, `CHECKLIST.md`, `docs/PRIZES.md`, `docs/RULES.md`, `docs/DISCLOSURE.md`, `docs/SOS-TICKET.md`, `docs/AI_USAGE.md` | Codex revised documents to match audit and current rules | Must approve strategy and perform account-bound actions |
| 03 Sep | `spikes/writepath/deploy.py`, `pause_tx.py`, tests and tool config | Codex modified transaction safety/runtime semantics, wrote tests and pinned the local toolchain | Human must provide testnet credentials; live deployment is not yet verified |
| 03 Sep | `spikes/thegraph/query.py`, `package.json`, lockfile and docs | Codex pinned the local CLI, wrote the query client, tested local tooling and documented dependency advisories | Human must create/operate Studio account; live data is not yet verified |
| 03 Sep | `docs/SPEC.md`, `docs/GUARDIAN-REGISTRY.md`, `docs/THREAT_MODEL.md`, demo/porting/template docs | Codex reconciled architecture, authorization, failure semantics and disclosure boundaries | Must review before the event implementation begins |
| 03 Sep | `docs/RULES.md`, `COMPLIANCE.md`, `AI_PROMPTS.md`, disclosure/submission docs | Codex rechecked official ETHGlobal pages and separated verified rules, pending Dashboard facts and internal controls | Human must verify Dashboard-only facts and preserve/export prompt history |
| 04 Sep | Python/Solidity comments and output; README, audits, plan, checklist, prize/demo/porting/spike/template docs | Codex converted judge-facing material to English and retained verbatim Ukrainian prompts with translations | Human requested the language review; automated checks must confirm only prompt quotations remain in Ukrainian |
| 04 Sep, event period | Baseline refs; `docs/ethonline/`; `docs/ssd/CONSTITUTION.md`; `docs/ssd/ETHONLINE_QUALITY_GATES.md`; `specs/002-ethonline-sentinel/`; safe config and scan templates | Codex verified the authenticated Dashboard/schedule, checked the Git baseline, imported labelled pre-event artifacts, drafted the event SSD package, and ran secret scans | Human confirmed Dashboard login and instructed Codex to proceed; owner approval of the proposed event specification is still required before production code |
| 04 Sep, event period | Ubuntu/WSL2 pre-event non-regression verification | Codex discovered the available Ubuntu and Docker runtimes, isolated the test from occupied ports and NTFS ownership limitations, and ran Python and Docker gates in temporary Linux environments | Human pointed out Ubuntu was available; generated containers and temporary clone were removed after verification |
| 04 Sep, event period | `contracts/`, Foundry CI gate, ES101 task/evidence | Codex implemented the pause-only Guardian, valueless vulnerable Demo Vault, dependency-free Actor tests, pinned CI runtime, and contract evidence | Human approved the event specification and authorized expert execution; live deployment still requires a disposable testnet wallet and account-bound credentials |
| 04 Sep, event period | `contracts/deploy.py`, deployment tests, CI/type gates, secret-safe environment template | Codex added a Base-Sepolia-only EIP-1559 deployment and verification path, strengthened owner/keeper separation, and added five Python safety tests | Human delegated implementation decisions; no wallet secret or live deployment is claimed |
| 04 Sep, event period | `subgraph/` schema, mapping, tests and provider handoff notes | Codex implemented deterministic indexing for DemoVault withdrawals with a canonical event ID and durable ordering cursor | Human delegated implementation decisions; provider publication and live-query evidence remain pending |
| 04 Sep, event period | Ignored `.env.ethonline` disposable Base Sepolia roles | Codex generated separate testnet-only owner and keeper/deployer accounts without printing or committing private keys | Human must fund only the public deployer address with faucet ETH; wallets must never receive real value |
| 04 Sep, event period | `docs/ethonline/TESTNET_HANDOFF.md` | Codex recorded the verified state, safe funding steps, public addresses, and exact continuation checklist | Human requested a documented pause until the following day and must perform the wallet-authorized testnet transfer |

Add one row on every event day for every material code, test, documentation or
visual area touched with AI assistance. Do not pre-fill future work as completed.
The exact prompt register and known evidence gap are in `AI_PROMPTS.md`.

## Prior work, not generated for ETHOnline

- `nexguard-edge-resilience` control loop — pre-event MIT code; see
  `DISCLOSURE.md`.
- `latch-agent` durable ActionPolicy design — pre-event reference source; see
  `DISCLOSURE.md`.
- Demo narration remains human; no text-to-speech or AI voiceover.
