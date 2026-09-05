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

**Status:** `[/]`
**Files:** `subgraph/schema.graphql`, `subgraph/subgraph.yaml`, `subgraph/src/`, tests
**Depends:** ES102
**Acceptance:** ES-FR-003 and EG-2.

## Stage 3

### ES301 — package, configuration, and durable state

**Status:** `[ ]`
**Files:** `sentinel/`, migrations, config loader, package/lock and unit tests
**Depends:** ES000 approval
**Acceptance:** durable schema covers cursor, dedupe, incidents, intents, tx data,
outcomes, latch, and outbox.

### ES302 — ingestion, policy, executor, and reconciliation

**Status:** `[ ]`
**Files:** Sentinel source modules and focused tests
**Depends:** ES201, ES301
**Acceptance:** ES-FR-004 and ES-FR-007 through ES-FR-011; EG-3.

## Stage 4

### ES401 — feature extraction and AI classifier

**Status:** `[ ]`
**Files:** detector/classifier modules, bounded prompt, schema and tests
**Depends:** ES301
**Acceptance:** ES-FR-005, ES-FR-006 and EG-4.

### ES402 — durable notification outbox

**Status:** `[ ]`
**Files:** outbox/notifier modules and restart/retry tests
**Depends:** ES301
**Acceptance:** ES-FR-012.

## Stage 5

### ES501 — live end-to-end evidence

**Status:** `[ ]`
**Depends:** ES102, ES201, ES302, ES401, ES402
**Acceptance:** one live Graph event yields one verified pause; negative and
restart paths are evidenced.

### ES502 — submission package

**Status:** `[ ]`
**Files:** README, architecture/demo docs, disclosure/evidence, video and form
**Depends:** ES501
**Acceptance:** EG-5 and Dashboard confirmation before the deadline.
