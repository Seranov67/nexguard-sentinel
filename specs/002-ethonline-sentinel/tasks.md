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

**Status:** `[x]` — SQLite schema v2 and environment settings implemented; current complete suite has
181 tests, including 126 Sentinel tests. Restart, process crash, replay, concurrent
reservation and transactional rollback checks pass; Ruff and strict MyPy pass.
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

**Status:** `[x]` — new withdrawal 46474498 classified by real Qwen3; one pause
at 46474539. Initial RPC uncertainty latched; no-send reconcile confirmed success,
attributed reset and separate process replay produced no second action. Paused
withdrawal eth_call reverted. See deployments/live-e2e-2026-09-06.json.
**Depends:** ES102, ES201, ES302, ES401, ES402
**Acceptance:** one live Graph event yields one verified pause; negative and
restart paths are evidenced.
**Files:** live evidence records and `scripts/trigger_exploit.py` demo instructions.
**Justification:** Correct stale ETH-value terminology and Python 3.11 guidance;
retain the valueless Base Sepolia demonstration behavior.

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

### ES504 — reconcile project plans and verify remote CI

**Status:** `[x]` — plans reconciled; remote CI run 34049799940 passes all four jobs at 0eae479.
**Authorization:** Owner requested execution of the full-project plan review on 2026-09-06.
**Files:** AGENTS.md, event identity/disclosure/preparation records, this task list,
plan.md, submission checklist and evidence documents; CI configuration if diagnosis
shows a necessary correction.
**Depends:** ES503
**Acceptance:** One current workspace and status map; historical records clearly
labelled; remote CI outcome recorded separately from local checks.
**Verify:** document cross-reference review, git diff --check, GitHub Actions API.

### ES505 — real-model Bazantic comparison

**Status:** `[ ]`
**Files:** docs/ethonline/BAZANTIC_AB_BENCHMARK.md, sanitized transcript evidence,
`sentinel/bazantic/benchmark_ab.py`, Recipe metadata and focused tests.
**Justification:** CPU live run exceeded the fixed 30-second benchmark timeout.
Allow an explicit bounded 1–120 second request timeout, identical in both variants
and recorded in the report; keep signing runtime timeout unchanged.
**Depends:** reachable model, persisted incident evidence; ES501 for live-action claims.
**Acceptance:** Same model/task/tools/settings with and without Recipe; real tool
transcripts, measured structural checks and human review of explanatory accuracy.
No synthetic score, settled-payment claim or unverified gateway registration.
**Verify:** python -m sentinel.bazantic.benchmark_ab --help; execute configured runner
and inspect its transcript against the persisted incident.

### ES506 — Ledger hardware qualification decision

**Status:** `[x]` — owner confirmed no device on 6 September. Retain simulation
limitation; no hardware/Clear Signing qualification claim or Ledger prize selection
is authorized by this evidence. Hardware demonstration itself remains unperformed.
**Files:** docs/ethonline/PRIZES.md, SUBMISSION_PACK.md and hardware evidence.
**Depends:** owner-operated compatible Ledger and confirmed owner address.
**Acceptance:** Record actual device behavior and recovery evidence if claiming
hardware integration; otherwise explicitly retain the simulation limitation and
omit unsupported prize claims. No terminal preview may count as hardware proof.
**Verify:** official-schema validation; owner-observed device demonstration and
receipt, or documented decision to retain prototype scope.

### ES507 — narrated video and final delivery

**Status:** `[/]` — script and Dashboard draft prepared; human recording pending.
**Files:** video, docs/ethonline/SUBMISSION_PACK.md and submission evidence.
**Depends:** ES501; ES505/ES506 for any corresponding prize claims.
**Acceptance:** Human voice, 2–4 minutes, >=720p, anonymous video access; accurate
partner choices; final Dashboard confirmation. Internal target: 13 September 17:00
Europe/Kyiv. ES502 closes only when final delivery evidence exists.
**Verify:** inspect exported media metadata and playback, anonymous links and
Dashboard confirmation. Do not substitute AI/TTS narration.
