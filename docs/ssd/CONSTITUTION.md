# NexGuard Edge Resilience — SSD Constitution

> **Specification-Driven Development**: requirements and acceptance criteria are locked
> before any implementation begins. The IDE implements the project in small, verifiable
> stages and does NOT proceed to the next stage until the current one passes all quality gates.

---

## 1. Project Identity

| Field         | Value                                               |
|---------------|-----------------------------------------------------|
| Project       | NexGuard Edge Resilience                            |
| Version       | 0.1.0-mvp                                           |
| Scope         | Hackathon demonstrational MVP                       |
| Start date    | 2026-07-14                                          |
| Target        | Local Docker Compose stack, single-machine demo     |

---

## 2. Mission Statement

NexGuard reduces downtime of IoT gateways in regions with unstable power supply and
limited access to technical personnel by **automatically detecting failures, restoring
last-known-good configurations, and restarting supervised containers** — all without
human intervention.

---

## 3. Inviolable Rules (never override without explicit approval)

### 3.1 Security
- **SEC-1** — No secrets, tokens, or passwords may be committed to the repository.
- **SEC-2** — `.env.example` must contain only placeholder values (e.g. `YOUR_TOKEN_HERE`).
- **SEC-3** — Docker socket access grants high privileges; the README **must** contain a
  warning that a Docker Socket Proxy or host-agent is required for production.
- **SEC-4** — The controller **must never** restart a container that does not have
  **both** the label `io.nexguard.managed=true` **and** an explicit name in the
  `NEXGUARD_ALLOWED_CONTAINERS` allowlist.

### 3.2 Scope freeze (MVP boundaries)
The following are explicitly **out of scope** and must not be added:

| Category                | Examples                                  |
|-------------------------|-------------------------------------------|
| Orchestration           | Kubernetes, Swarm, Nomad                  |
| Real hardware           | Physical IoT devices, actual sensors      |
| Auth & multi-user       | Login, roles, JWT, OAuth                  |
| Web control panel       | Frontend dashboard, admin UI              |
| AI / ML                 | Anomaly detection, predictions            |
| Multi-server management | Remote agents, fleet control              |
| Database                | PostgreSQL, SQLite, Redis                 |
| Cloud deployment        | AWS, GCP, Azure, Terraform                |

### 3.3 Architectural invariants
- **ARCH-1** — The health-check loop runs **every 10 seconds** (configurable via env,
  but default must be 10 s).
- **ARCH-2** — An incident is opened after **exactly 3 consecutive failures** (threshold
  configurable, default = 3).
- **ARCH-3** — Config backup is created **only from a verified healthy state**.
- **ARCH-4** — Backup is written **atomically** (write to temp file → `os.replace`).
- **ARCH-5** — SHA-256 checksum is stored alongside every backup.
- **ARCH-6** — Telegram notifications are **non-blocking** and failures must not
  affect the recovery pipeline.
- **ARCH-7** — Cooldown between recoveries: **60 seconds** minimum.
- **ARCH-8** — Maximum **3 recovery attempts** per **10-minute** sliding window.
- **ARCH-9** — If the attempt limit is exceeded, the system enters
  `manual_intervention_required` status and stops automatic recovery.

---

## 4. Language and Stack

| Layer         | Technology                              |
|---------------|-----------------------------------------|
| Language      | Python 3.12                             |
| API Framework | FastAPI                                 |
| Health check  | HTTP `/health` endpoint                 |
| Metrics       | `prometheus-client` library             |
| Docker ops    | Docker SDK for Python (`docker`)        |
| Config format | YAML                                    |
| Containers    | Docker Compose (Compose V2)             |
| Monitoring    | Prometheus + Grafana                    |
| Notifications | Telegram Bot API (optional)             |
| Tests         | Pytest                                  |
| Linting       | Ruff                                    |
| Type checking | MyPy                                    |
| CI            | GitHub Actions                          |

---

## 5. SSD Process

```
ANALYZE → SPECIFY → REVIEW → IMPLEMENT (stage-by-stage) → VERIFY → COMMIT
```

- The IDE **must analyze** the repository and existing files before writing any code.
- The IDE **must not delete or rewrite** existing code without documented justification.
- After creating SSD documents the IDE **stops**, presents risks and open questions,
  and **waits for specification approval** before writing production code.
- Each implementation stage has a **quality gate**; only after passing it does the
  IDE proceed to the next stage.
- When the owner explicitly designates a development host as Docker-free, Docker-only
  gates may be recorded as **deferred** and verified later in CI or on the target host.
  Non-Docker work may continue, but deferred gates remain mandatory for the MVP
  Definition of Done and all Docker security rules remain in force.
- Every task in `tasks.md` has: unique ID · files · dependencies · acceptance criteria ·
  verification command.

---

## 6. Commit Policy

- Use [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `ci:`
- One logical change per commit.
- No commit may contain real secrets.
- `main` branch is the single source of truth.

---

## 7. Definition of Done (MVP)

- [x] `docker compose up -d --build` completes without errors.
- [x] All containers reach `healthy` status.
- [x] Scenario A (container stop) resolves automatically.
- [x] Scenario B (config corruption) resolves automatically.
- [x] Tests pass without a Telegram token configured.
- [x] No secrets or tokens in the repository.
- [x] `.env.example` contains only placeholder values.
- [x] Grafana dashboard loads automatically on first start.
- [x] README covers: quick-start, architecture, and demo scenarios.
- [x] A new user can run the full stack in **under 10 minutes**.

---

## 8. Amendment Process

Changes to this Constitution require:
1. An explicit written request from the project owner.
2. An updated version of this file with a change log entry below.
3. Re-review of `specs/001-nexguard-mvp/acceptance.md` for affected criteria.

### Change Log

| Date       | Author    | Change                  |
|------------|-----------|-------------------------|
| 2026-07-14 | bootstrap | Initial version created |
| 2026-07-14 | owner-approved amendment | Allow Docker-only gates to be deferred on an explicitly Docker-free development host |
| 2026-07-15 | owner-requested completion audit | Record all MVP Definition of Done gates as verified |
