# AGENTS.md — Instructions for IDE Agents

This file defines the rules for any AI coding assistant (Codex, Claude Code, Gemini,
Cursor, etc.) working on **NexGuard Sentinel** and the pre-existing
**NexGuard Edge Resilience** MVP in this repository.

## Active Project Identity

- Display/submission name: **NexGuard Sentinel**.
- Primary workspace: `D:\nexguard-edge-resilience`.
- GitHub repository: `Seranov67/nexguard-sentinel`.
- Event working branch: `feature/ethonline-sentinel`; verify before editing.
- `D:\NexGuard Sentinel` contains preparation materials; implement event work here.
- Keep the existing local workspace path and legacy runtime identifiers. The previous
  MVP retains its name and provenance.
- See `docs/ethonline/PROJECT_IDENTITY.md` for the component map.

---

## Development Method

**Specification-Driven Development (SSD)**

> Requirements and acceptance criteria are locked BEFORE implementation.
> The IDE implements the project in small, verifiable stages.
> Each stage has a quality gate. The IDE does NOT proceed until the gate passes.

---

## Mandatory First Steps

1. Read `docs/ssd/CONSTITUTION.md` — inviolable rules.
2. Read `docs/ssd/QUALITY_GATES.md` — per-stage pass/fail criteria.
3. Read `specs/001-nexguard-mvp/spec.md` — functional requirements.
4. Read `specs/001-nexguard-mvp/tasks.md` — task list with IDs.
5. Run `git status` and check existing files before writing anything.
6. **Never delete or rewrite existing code without written justification.**
7. For Sentinel work, also read `specs/002-ethonline-sentinel/spec.md`,
   `specs/002-ethonline-sentinel/tasks.md`, and
   `docs/ssd/ETHONLINE_QUALITY_GATES.md` before implementation.

---

## Stage Workflow

```
1. Announce which stage and task IDs you are starting.
2. Implement only the files listed in that task.
3. Run the verification command from tasks.md.
4. Report: PASS or FAIL with output.
5. If PASS → commit with conventional commit message.
6. If FAIL → fix, re-run, report again.
7. Ask for approval before proceeding to the next stage.
```

When the owner explicitly designates a host as Docker-free, Docker-only gates are marked
`DEFERRED` and verified later in CI or on a Docker-capable target. Non-Docker gates may
continue; deferred gates remain mandatory for the MVP Definition of Done.

---

## Hard Rules

- **SEC**: Never commit secrets, tokens, or real passwords.
- **SCOPE**: Do not add Kubernetes, database, auth, AI/ML, web UI, or cloud infra.
  For Sentinel only, the owner-approved 2026-09-04 Constitution amendment permits
  Base Sepolia contracts, live The Graph data, schema-validated AI classification,
  and local SQLite durability within `specs/002-ethonline-sentinel`. All other
  exclusions and the existing MVP non-regression requirements remain in force.
- **DOCKER**: Only restart containers with label `io.nexguard.managed=true` AND in allowlist.
- **TELEGRAM**: Must be optional and non-blocking; tests pass without a token.
- **ATOMICITY**: All file writes (backup, restore) must use `os.replace`.
- **TYPES**: All Python code must pass `mypy` strict mode.
- **LINT**: All Python code must pass `ruff check` with zero errors.

---

## Commit Convention

```
feat(stage-N): short description
fix(component): what was broken
test(component): what is tested
docs: what is documented
chore: maintenance tasks
```

---

## Technology Stack

| Component  | Technology                    |
|------------|-------------------------------|
| Language   | Python 3.12                   |
| API        | FastAPI + uvicorn             |
| Metrics    | prometheus-client             |
| Docker SDK | docker (Python SDK)           |
| Config     | PyYAML + Pydantic             |
| Tests      | Pytest + pytest-asyncio       |
| Lint       | Ruff                          |
| Types      | MyPy                          |
| CI         | GitHub Actions                |

---

## File Layout

See `README.md` for the complete repository layout.
