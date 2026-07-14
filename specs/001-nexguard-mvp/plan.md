# specs/001-nexguard-mvp/plan.md
# NexGuard MVP — Implementation Plan

**Version**: 1.0.1
**Spec reference**: `specs/001-nexguard-mvp/spec.md`  
**Status**: APPROVED — owner approval recorded 2026-07-14

---

## Stage Map

```
Stage 0 ──► Stage 1 ──► Stage 2 ──► Stage 3 ──► Stage 4 ──► Stage 5 ──► Stage 6 ──► Stage 7 ──► Stage 8
  SSD        Compose    Backup     Incident    Restore     Prometheus  Telegram    Tests       Docs
 Docs      +Simulator  +YAML      Detection   +Docker      +Grafana    (optional)  +CI         +README
```

Each arrow represents a quality gate that must pass before proceeding.

---

## Stage 0 — Analysis & SSD Documents (Completed)

**Goal**: Lock the specification before writing any code.

**Deliverables**:
- `docs/ssd/CONSTITUTION.md` ✓
- `docs/ssd/QUALITY_GATES.md` ✓
- `specs/001-nexguard-mvp/spec.md` ✓
- `specs/001-nexguard-mvp/plan.md` ✓ (this file)
- `specs/001-nexguard-mvp/tasks.md` ✓
- `specs/001-nexguard-mvp/acceptance.md` ✓

**Risks identified**:
- Docker socket access is high-privilege — mitigated by allowlist + label guard.
- Atomic file operations on bind-mounted volumes may behave differently across OS
  — mitigated by using `os.replace` which is atomic on POSIX filesystems.
- Grafana auto-provisioning requires exact JSON structure — mitigated by testing
  provisioning on first `docker compose up`.

**Resolved decisions**: See `spec.md` § 9.

**Exit criterion**: Met on 2026-07-14. Owner approved implementation to proceed.

---

## Stage 1 — Docker Compose + Gateway Simulator

**Goal**: A working Docker Compose stack with a gateway simulator that passes health checks.

**Components**:

### `compose.yaml`
- Stage 1 service: `gateway-simulator` only
- Bind mount: `./data/gateway:/data/gateway:ro`
- Managed label: `io.nexguard.managed=true`
- Health check defined for `gateway-simulator`
- Controller is added in Stage 4; Prometheus and Grafana are added in Stage 5

### `services/gateway-simulator/`

| File | Purpose |
|------|---------|
| `Dockerfile` | Python 3.12-slim, uvicorn, non-root user |
| `app/main.py` | FastAPI app: `/health`, `/metrics` |
| `app/config.py` | YAML loader with validation |
| `app/schemas.py` | Pydantic model for gateway YAML schema |

**Implementation notes**:
- Use `uvicorn` with `--reload` disabled in production mode
- `/health` reloads config on every call (FR-002, OQ-01 decision)
- `/metrics` uses `prometheus-client` `generate_latest()`
- Simulator exposes `gateway_simulator_config_valid`; the seven required `nexguard_*`
  metrics remain the responsibility of the controller.

---

## Stage 2 — Backup & Config Integrity

**Goal**: Atomic backup and SHA-256 verification.

### `services/nexguard-controller/app/backup.py`

| Function / Class | Responsibility |
|-----------------|----------------|
| `BackupManager` | Manages backup creation and listing |
| `create_backup(config_path, backup_dir, gateway_healthy)` | Reject unhealthy state; validate config; atomic write + SHA-256 file |
| `list_backups(backup_dir)` | Sorted list of available backups |
| `get_latest_backup(backup_dir)` | Returns path to most recent backup |
| `verify_backup(backup_path)` | Reads `.sha256` and validates checksum |

### `services/nexguard-controller/app/config_checker.py`

| Function | Responsibility |
|----------|----------------|
| `is_valid_yaml(path)` | Returns `(valid: bool, reason: str)` |
| `validate_schema(data)` | Validates against gateway YAML schema |
| `check_config(path)` | Combines YAML parsing + schema validation |

The controller creates an initial backup on the first verified healthy check, then refreshes
it after `BACKUP_INTERVAL_SECONDS` (default 60 s) while the gateway remains healthy.

---

## Stage 3 — Incident Detection

**Goal**: State machine that counts failures and creates incidents.

### `services/nexguard-controller/app/health_monitor.py`

| Class | Responsibility |
|-------|----------------|
| `HealthMonitor` | Runs the 10-second loop, calls health URL |
| `check_once()` | Single HTTP health check, returns `HealthResult` |

### `services/nexguard-controller/app/incident.py`

| Class | Responsibility |
|-------|----------------|
| `IncidentManager` | Tracks consecutive failures, manages incident lifecycle |
| `record_failure()` | Increments counter; fires incident at threshold |
| `record_success()` | Resets counter; closes open incident |
| `current_incident` | Property: `None` or `Incident` dataclass |

---

## Stage 4 — Restore & Docker Restart

**Goal**: Automatic recovery pipeline that is safe-by-default.

### `services/nexguard-controller/app/recovery.py`

| Class | Responsibility |
|-------|----------------|
| `RecoveryManager` | Orchestrates restore → restart → verify |
| `attempt_recovery()` | Main entry: safety checks → select recovery branch → health-check |
| `_check_cooldown()` | Enforces 60 s minimum between attempts |
| `_check_rate_limit()` | Enforces max 3 per 10 min sliding window |

### `services/nexguard-controller/app/docker_manager.py`

| Class | Responsibility |
|-------|----------------|
| `DockerManager` | Wraps Docker SDK with allowlist enforcement |
| `restart_container(name)` | Validates label + allowlist, then restarts |
| `wait_for_running(name, timeout)` | Polls until container is running |

Recovery has two explicit branches:
1. Valid config + unavailable container: guarded restart → health-check.
2. Invalid config: verify backup → atomic restore → guarded restart → health-check.

---

## Stage 5 — Prometheus & Grafana

**Goal**: All metrics visible; Grafana dashboard auto-provisioned.

### `monitoring/prometheus.yml`
- Scrape configs: `nexguard-controller:8081` and `gateway-simulator:8080`

### Grafana provisioning
```
monitoring/grafana/provisioning/
  datasources/prometheus.yaml   ← auto-wires Prometheus
  dashboards/nexguard.yaml      ← points to dashboards/ folder
monitoring/grafana/dashboards/
  nexguard.json                 ← pre-built dashboard JSON
```

---

## Stage 6 — Telegram Notifier

**Goal**: Optional, non-blocking notifications.

### `services/nexguard-controller/app/notifier.py`

| Class | Responsibility |
|-------|----------------|
| `TelegramNotifier` | Sends messages via Bot API |
| `send_async(message)` | Fire-and-forget in a daemon thread |
| `is_configured()` | Returns `True` only if both env vars are set |

---

## Stage 7 — Tests & CI

**Goal**: All quality gates are green in CI.

### Test structure
```
services/
  gateway-simulator/tests/
    test_health.py
    test_config.py
  nexguard-controller/tests/
    test_backup.py
    test_config_checker.py
    test_health_monitor.py
    test_incident.py
    test_recovery.py
    test_docker_manager.py
    test_notifier.py
```

### CI pipeline (`.github/workflows/ci.yml`)
```yaml
jobs:
  lint: ruff check . && mypy services/gateway-simulator && mypy services/nexguard-controller
  test: pytest --tb=short
  compose-check: docker compose config --quiet
  secret-scan: grep -rIE "g""hp_|xo""xb-|AK""IA|bo""t[0-9]{8,}:" . --exclude-dir=.git --exclude-dir=.venv && exit 1 || exit 0
```

---

## Stage 8 — Documentation & Demo Scripts

**Goal**: A new user can run the demo in under 10 minutes.

### Script logic

| Script | What it does |
|--------|-------------|
| `demo-stop.sh` | Stops the gateway-simulator container |
| `demo-corrupt-config.sh` | Overwrites gateway.yaml with invalid YAML |
| `reset-demo.sh` | `docker compose down && restore known-good config && docker compose up -d` |
| `verify-demo.sh` | Polls `/health` and controller logs; exits 0 on success, 1 on timeout |

---

## Dependency Graph (Stages)

```
Stage 0 (SSD)
    │
    ▼
Stage 1 (Simulator + Compose)
    │
    ▼
Stage 2 (Backup + Config Check)
    │
    ├──► Stage 3 (Incident Detection)
    │         │
    │         ▼
    │     Stage 4 (Restore + Docker)
    │         │
    └─────────┤
              ▼
          Stage 5 (Prometheus + Grafana)
              │
              ▼
          Stage 6 (Telegram — optional)
              │
              ▼
          Stage 7 (Tests + CI)
              │
              ▼
          Stage 8 (Docs + Demo)
```

---

## Risk Register

| ID   | Risk                                              | Probability | Impact | Mitigation                                    |
|------|---------------------------------------------------|-------------|--------|-----------------------------------------------|
| R-01 | Docker socket bind causes security concern        | High        | High   | Allowlist + label guard + README warning      |
| R-02 | `os.replace` not atomic on some Docker volume drivers | Low    | High   | Document assumption; test on Linux            |
| R-03 | Recovery loop triggered too aggressively          | Medium      | Medium | Cooldown + rate limit (ARCH-7, ARCH-8, ARCH-9)|
| R-04 | Telegram API timeout blocks recovery              | Low         | High   | Non-blocking thread (FR-013, ARCH-6)          |
| R-05 | Grafana provisioning fails silently               | Low         | Medium | QG-5C verifies dashboard on first start       |
| R-06 | Stage 4 demo fails because container name mismatch | Medium    | Medium | `NEXGUARD_ALLOWED_CONTAINERS` env var default matches `compose.yaml` |

---

## Change Log

| Date       | Change |
|------------|--------|
| 2026-07-14 | Approved plan; aligned stage boundaries, backup trigger, bind mounts, metrics, and recovery branches. |
| 2026-07-14 | Owner designated the current host Docker-free; Docker gates are deferred to CI/target-host verification. |
