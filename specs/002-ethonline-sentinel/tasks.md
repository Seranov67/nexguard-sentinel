# NexGuard Sentinel — task breakdown

Status: `[ ]` todo, `[/]` in progress, `[x]` complete, `[d]` deferred.

## Stage 0

### ES000 — event baseline and SSD package

**Status:** `[x]`
**Files:** tag/branch; `docs/ethonline/`; `docs/ssd/CONSTITUTION.md`;
`docs/ssd/ETHONLINE_QUALITY_GATES.md`; `specs/002-ethonline-sentinel/`;
`.gitleaks.toml`; `.env.ethonline.example`; `config/sentinel.example.yaml`
**Acceptance:** EG-0 passes and production code is unchanged.
**Verify:** Git refs/status/diff, document cross-reference review, secret scans.

### ES001 — workspace identity and agent onboarding

**Status:** `[x]` — documentation cross-reference and scoped diff checks passed;
branch and origin verified on 2026-09-05. Production code unchanged.
**Files:** `AGENTS.md`, `docs/ethonline/PROJECT_IDENTITY.md`,
`specs/002-ethonline-sentinel/tasks.md`
**Depends:** ES000; owner requested project/name preparation on 2026-09-05.
**Acceptance:** Record Sentinel's display name, existing repository and working
directory, event branch, preparation-only directory, and approved scope amendment.
Preserve previous MVP identity and existing unrelated working-tree changes.
**Justification:** Agent instructions still identify only the old MVP and omit
the approved Sentinel amendment. Documentation-only clarification avoids renaming
runtime identifiers or changing production behavior.
**Verify:** `git diff --check -- AGENTS.md docs/ethonline/PROJECT_IDENTITY.md specs/002-ethonline-sentinel/tasks.md`;
`git branch --show-current`; `git remote get-url origin`; manual cross-reference
with the Constitution amendment, Sentinel specification, and README.

## Stage 1

### ES101 — Guardian and Demo Vault

**Status:** `[x]`
**Files:** `contracts/src/Guardian.sol`, `contracts/src/DemoVault.sol`
**Depends:** ES000 approval
**Acceptance:** ES-FR-001, ES-FR-002.

### ES102 — contract tests and deployment

**Status:** `[x]` — Base Sepolia receipts, bytecode, confirmations and roles verified;
see `docs/ethonline/deployments/base-sepolia.json`.
**Files:** `contracts/test/`, `contracts/script/`, contract configuration
**Depends:** ES101
**Acceptance:** EG-1 and recorded Base Sepolia evidence.

## Stage 2

### ES201 — Subgraph

**Status:** `[x]` — Studio v0.1.0 returns a verified live Withdrawal and `_meta`;
see `docs/ethonline/deployments/subgraph-studio.json` for query and latency evidence.
**Files:** `subgraph/schema.graphql`, `subgraph/subgraph.yaml`, `subgraph/src/`, tests
**Depends:** ES102
**Acceptance:** ES-FR-003 and EG-2.

## Stage 3

### ES301 — package, configuration, and durable state

**Status:** `[x]` — SQLite schema v1 and environment settings implemented;
74 Python tests pass, including 19 Sentinel tests covering restart, process crash,
replay, concurrent reservation and transactional rollback; Ruff and strict MyPy pass.
**Files:** `sentinel/`, migrations, config loader, package/lock and unit tests
**Depends:** ES000 approval
**Acceptance:** durable schema covers cursor, dedupe, incidents, intents, tx data,
outcomes, latch, and outbox.

### ES302 — ingestion, policy, executor, and reconciliation

**Status:** `[x]` — durable ingestion, policy and canonical receipt reconciliation implemented; safety/restart/concurrency gates pass. See final audit report.
**Files:** Sentinel source modules and focused tests
**Depends:** ES201, ES301
**Acceptance:** ES-FR-004 and ES-FR-007 through ES-FR-011; EG-3.

## Stage 4

### ES401 — feature extraction and AI classifier

**Status:** `[x]` — bounded features, fail-closed Ollama transport, strict schema and persisted traces implemented and tested. Real-model live demonstration remains ES501 work.
**Files:** detector/classifier modules, bounded prompt, schema and tests
**Depends:** ES301
**Acceptance:** ES-FR-005, ES-FR-006 and EG-4.

### ES402 — durable notification outbox

**Status:** `[x]` — durable leased outbox with retries and terminal failure recording implemented; restart tests pass.
**Files:** outbox/notifier modules and restart/retry tests
**Depends:** ES301
**Acceptance:** ES-FR-012.

## Stage 5

### ES501 — live end-to-end evidence

**Status:** `[/]` — live Graph preview and historical receipts verified. New real-model-to-pause rehearsal and live restart evidence remain pending.
**Depends:** ES102, ES201, ES302, ES401, ES402
**Acceptance:** one live Graph event yields one verified pause; negative and
restart paths are evidenced.

### ES502 — submission package

**Status:** `[/]` — submission pack and narration script prepared; Dashboard draft saved on 2026-09-06. Video, partner selection and final confirmation remain pending; final submission is currently disabled.
**Files:** README, architecture/demo docs, disclosure/evidence, video and form
**Depends:** ES501
**Acceptance:** EG-5 and Dashboard confirmation before the deadline.


### ES503 — owner-authorized final audit repairs (2026-09-06)

**Status:** `[x]` — 181 Python tests, Ruff, strict Sentinel MyPy and package checks pass; contract/Subgraph/isolated Compose and secret scans pass. Unsupported claims corrected; live evidence remains explicitly pending.
**Authorization:** Owner instructed execution of the 2026-09-06 audit next steps.
**Files:** `sentinel/evidence_api.py`, `sentinel/bazantic/`, `sentinel/ledger/`,
focused Sentinel tests; `pyproject.toml`, `sentinel/requirements.lock`,
`scripts/trigger_exploit.py`, `.github/workflows/ci.yml`, README and submission docs.
**Locked acceptance:** Reject unverified payment proofs; require explicit server demo
mode for payment bypass; accept generated incident IDs; report recorded classification
rather than invented causes; independently recompute evidence fingerprints; replace
simulated A/B results with an executable real-model comparison and label unrun evidence
pending; remove incorrect SHA3 fallback; clearly distinguish Ledger simulation from
hardware proof; package all submodules/assets and pin direct runtime dependencies.
**Justification:** Existing partner claims and tests assert mock payment acceptance,
static causes and simulated benchmark scores as if verified; these must not be submitted.
**Verify:** full pytest, Ruff, strict MyPy, package install/import, secret scans,
contract/Subgraph/Compose checks and manual evidence-to-claim review.
