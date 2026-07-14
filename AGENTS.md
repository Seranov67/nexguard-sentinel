# AGENTS.md — Instructions for IDE Agents

This file defines the rules for any AI coding assistant (Codex, Claude Code, Gemini,
Cursor, etc.) working on **NexGuard Edge Resilience**.

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

---

## Hard Rules

- **SEC**: Never commit secrets, tokens, or real passwords.
- **SCOPE**: Do not add Kubernetes, database, auth, AI/ML, web UI, or cloud infra.
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
