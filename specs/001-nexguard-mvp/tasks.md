# specs/001-nexguard-mvp/tasks.md
# NexGuard MVP — Task Breakdown

**Format**: Each task has a unique ID, files, dependencies, acceptance criterion, and
verification command.  
**Status legend**: `[ ]` todo · `[/]` in-progress · `[x]` done · `[d]` Docker gate deferred

---

## Stage 0 — Analysis & SSD Documents

### T000 — Initialize repository structure
**Status**: `[x]`  
**Files**:
```
.gitignore
.env.example
pyproject.toml
docs/ssd/CONSTITUTION.md
docs/ssd/QUALITY_GATES.md
specs/001-nexguard-mvp/spec.md
specs/001-nexguard-mvp/plan.md
specs/001-nexguard-mvp/tasks.md       ← this file
specs/001-nexguard-mvp/acceptance.md
```
**Dependencies**: none  
**Acceptance criterion**: All files exist; no production code present.  
**Verification**: `ls docs/ssd/ specs/001-nexguard-mvp/`

---

## Stage 1 — Docker Compose + Gateway Simulator

### T001 — Project tooling config (`pyproject.toml`, `.env.example`, `.gitignore`)
**Status**: `[x]`
**Files**:
```
pyproject.toml
.env.example
.gitignore
```
**Dependencies**: T000  
**Acceptance criterion**: `ruff check .` and `mypy services` are runnable; no secrets in `.env.example`.  
**Verification**: `ruff check . && mypy --version`

---

### T002 — Gateway Simulator: FastAPI app
**Status**: `[x]`
**Files**:
```
services/gateway-simulator/app/__init__.py
services/gateway-simulator/app/main.py
services/gateway-simulator/app/config.py
services/gateway-simulator/app/schemas.py
```
**Dependencies**: T001  
**Acceptance criterion**:
- `GET /health` → `{"status": "healthy"}` 200 when YAML is valid.
- `GET /health` → `{"status": "unhealthy", "reason": "config_invalid"}` 503 when YAML is corrupt.
- `GET /metrics` → Prometheus text format.

**Verification**:
```bash
cd services/gateway-simulator
uvicorn app.main:app --port 8080 &
curl -sf http://localhost:8080/health
curl -sf http://localhost:8080/metrics
kill %1
```

---

### T003 — Gateway Simulator: Dockerfile
**Status**: `[d]` — implementation complete; Docker verification deferred to CI/target host
**Files**:
```
services/gateway-simulator/Dockerfile
services/gateway-simulator/requirements.txt
```
**Dependencies**: T002  
**Acceptance criterion**: `docker build -t gateway-sim .` succeeds; container runs as non-root.  
**Verification**: `docker build -t gateway-sim services/gateway-simulator && docker run --rm gateway-sim whoami`

---

### T004 — Docker Compose skeleton
**Status**: `[d]` — implementation complete; Docker verification deferred to CI/target host
**Files**:
```
compose.yaml
data/gateway/gateway.yaml
```
**Dependencies**: T003  
**Acceptance criterion**: `docker compose up -d gateway-simulator` → container healthy.  
**Verification**:
```bash
docker compose up -d gateway-simulator
docker compose ps
curl -sf http://localhost:8080/health
```

---

### T005 — Gateway Simulator unit tests
**Status**: `[x]`
**Files**:
```
services/gateway-simulator/tests/__init__.py
services/gateway-simulator/tests/test_health.py
services/gateway-simulator/tests/test_config.py
```
**Dependencies**: T002  
**Acceptance criterion**: Tests cover: healthy response, unhealthy on corrupt YAML, unhealthy on missing keys.  
**Verification**: `pytest services/gateway-simulator/tests/ -v`

---

## Stage 2 — Backup & Config Integrity

### T006 — Backup manager
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/app/__init__.py
services/nexguard-controller/app/backup.py
```
**Dependencies**: T007
**Acceptance criterion**:
- `create_backup()` refuses unhealthy or unknown gateway state.
- The source YAML is schema-valid before it can become a backup.
- `create_backup()` writes atomically.
- SHA-256 file is created alongside backup.
- `verify_backup()` detects tampered files.

**Verification**: `pytest services/nexguard-controller/tests/test_backup.py -v`

---

### T007 — Config checker
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/app/config_checker.py
```
**Dependencies**: T001  
**Acceptance criterion**:
- Returns `(False, "yaml_parse_error")` on syntactically invalid YAML.
- Returns `(False, "missing_required_key")` on valid YAML missing mandatory keys.
- Returns `(True, "ok")` on fully valid config.

**Verification**: `pytest services/nexguard-controller/tests/test_config_checker.py -v`

---

### T008 — Backup and config checker tests
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/tests/__init__.py
services/nexguard-controller/tests/test_backup.py
services/nexguard-controller/tests/test_config_checker.py
```
**Dependencies**: T006, T007  
**Acceptance criterion**: All tests pass; covers atomic write, SHA-256, verification failure, schema checks.  
**Verification**: `pytest services/nexguard-controller/tests/test_backup.py services/nexguard-controller/tests/test_config_checker.py -v`

---

## Stage 3 — Incident Detection

### T009 — Health monitor
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/app/health_monitor.py
services/nexguard-controller/app/models.py
```
**Dependencies**: T001  
**Acceptance criterion**:
- `check_once()` makes HTTP GET and returns `HealthResult(ok=True/False, reason=...)`.
- Timeout is configurable (default 5 s).
- Network errors are treated as failures (not exceptions).

**Verification**: `pytest services/nexguard-controller/tests/test_health_monitor.py -v`

---

### T010 — Incident manager
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/app/incident.py
```
**Dependencies**: T009  
**Acceptance criterion**:
- Incident created on 3rd consecutive failure, not before.
- Counter resets on success.
- No duplicate incidents opened.
- `nexguard_incidents_total` and `nexguard_consecutive_health_failures` metrics updated.

**Verification**: `pytest services/nexguard-controller/tests/test_incident.py -v`

---

### T011 — Incident + health monitor tests
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/tests/test_health_monitor.py
services/nexguard-controller/tests/test_incident.py
```
**Dependencies**: T009, T010  
**Acceptance criterion**: Tests cover all state transitions; use `pytest-asyncio` for async code.  
Tests also verify that loop scheduling stays within ±1 second of the configured interval.
**Verification**: `pytest services/nexguard-controller/tests/test_health_monitor.py services/nexguard-controller/tests/test_incident.py -v`

---

## Stage 4 — Restore & Docker Restart

### T012 — Docker manager
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/app/docker_manager.py
```
**Dependencies**: T001  
**Acceptance criterion**:
- `restart_container("gateway-simulator")` succeeds only when label is present AND name is in allowlist.
- Raises `SecurityBlockError` otherwise.
- `wait_for_running()` polls up to `timeout` seconds.

**Verification**: `pytest services/nexguard-controller/tests/test_docker_manager.py -v`

---

### T013 — Recovery manager
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/app/recovery.py
```
**Dependencies**: T006, T007, T012  
**Acceptance criterion**:
- Valid config + unavailable container: guarded restart → health-check.
- Invalid config: verify backup SHA → restore config → guarded restart → health-check.
- Cooldown of 60 s enforced.
- Rate limit of 3 per 10 min enforced.
- `manual_intervention_required` status after limit exceeded.
- All events logged as JSON.

**Verification**: `pytest services/nexguard-controller/tests/test_recovery.py -v`

---

### T014 — Controller main loop
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/app/main.py
services/nexguard-controller/app/metrics.py
```
**Dependencies**: T009, T010, T013  
**Acceptance criterion**:
- FastAPI app starts on port 8081.
- `/health` returns controller health.
- `/metrics` returns Prometheus metrics.
- Background task runs health-check loop.
- The first verified healthy check creates an initial backup; later backups respect
  `BACKUP_INTERVAL_SECONDS` (default 60 s).

**Verification**:
```bash
docker compose up -d nexguard-controller
curl -sf http://localhost:8081/health
curl -sf http://localhost:8081/metrics | grep nexguard_gateway_up
```

---

### T015 — Controller Dockerfile
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/Dockerfile
services/nexguard-controller/requirements.txt
```
**Dependencies**: T014  
**Acceptance criterion**: `docker build` succeeds; container mounts Docker socket correctly in compose.yaml.  
**Verification**: `docker compose build nexguard-controller`

---

### T016 — Demo scripts: Scenario A & B
**Status**: `[ ]`  
**Files**:
```
scripts/demo-stop.sh
scripts/demo-corrupt-config.sh
scripts/reset-demo.sh
scripts/verify-demo.sh
```
**Dependencies**: T014, T015  
**Acceptance criterion**: Both scenarios pass `./scripts/verify-demo.sh`.  
**Verification**:
```bash
# Scenario A
docker compose up -d --build
./scripts/demo-stop.sh
sleep 45
./scripts/verify-demo.sh

# Scenario B
./scripts/reset-demo.sh
./scripts/demo-corrupt-config.sh
sleep 45
./scripts/verify-demo.sh
```

---

### T017 — Recovery, Docker manager tests
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/tests/test_recovery.py
services/nexguard-controller/tests/test_docker_manager.py
```
**Dependencies**: T012, T013  
**Acceptance criterion**: Mock Docker client used; no real container required for unit tests.  
**Verification**: `pytest services/nexguard-controller/tests/test_recovery.py services/nexguard-controller/tests/test_docker_manager.py -v`

---

## Stage 5 — Prometheus & Grafana

### T018 — Prometheus configuration
**Status**: `[ ]`  
**Files**:
```
monitoring/prometheus.yml
```
**Dependencies**: T014  
**Acceptance criterion**: Prometheus scrapes both services successfully.  
**Verification**: `curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool`

---

### T019 — Grafana provisioning and dashboard
**Status**: `[ ]`  
**Files**:
```
monitoring/grafana/provisioning/datasources/prometheus.yaml
monitoring/grafana/provisioning/dashboards/nexguard.yaml
monitoring/grafana/dashboards/nexguard.json
```
**Dependencies**: T018  
**Acceptance criterion**: Dashboard visible in Grafana after `docker compose up -d`; all 7 metrics have panels.  
**Verification**: `curl -sf http://localhost:3000/api/dashboards/uid/nexguard-main`

---

### T020 — Add Prometheus + Grafana to compose.yaml
**Status**: `[ ]`  
**Files**:
```
compose.yaml   ← add prometheus, grafana services
```
**Dependencies**: T018, T019  
**Acceptance criterion**: `docker compose up -d` starts all 4 services; all healthy.  
**Verification**: `docker compose ps`

---

## Stage 6 — Telegram (Optional)

### T021 — Telegram notifier
**Status**: `[ ]`  
**Files**:
```
services/nexguard-controller/app/notifier.py
services/nexguard-controller/tests/test_notifier.py
```
**Dependencies**: T014  
**Acceptance criterion**:
- Skipped silently without token.
- Failure does not propagate to recovery pipeline.
- Tests pass with `TELEGRAM_BOT_TOKEN` unset.

**Verification**: `unset TELEGRAM_BOT_TOKEN && pytest services/nexguard-controller/tests/test_notifier.py -v`

---

## Stage 7 — Tests & CI

### T022 — Full test suite
**Status**: `[ ]`  
**Files**:
```
services/gateway-simulator/tests/
services/nexguard-controller/tests/
```
**Dependencies**: all previous tasks  
**Acceptance criterion**: `pytest` exits 0.  
**Verification**: `pytest --tb=short`

---

### T023 — CI pipeline
**Status**: `[ ]`  
**Files**:
```
.github/workflows/ci.yml
```
**Dependencies**: T022  
**Acceptance criterion**: Pipeline runs on push to `main`; all jobs green.  
**Verification**: GitHub Actions UI or `act` local runner

---

## Stage 8 — Documentation & Demo

### T024 — README
**Status**: `[ ]`  
**Files**:
```
README.md
```
**Dependencies**: all previous tasks  
**Acceptance criterion**: Covers quick-start (≤ 10 min), architecture, demo A & B, security note.  
**Verification**: Manual review by a new reader

---

### T025 — Supporting documentation
**Status**: `[ ]`  
**Files**:
```
AGENTS.md
docs/architecture.md
docs/demo-scenario.md
docs/security.md
```
**Dependencies**: T024  
**Acceptance criterion**: All files non-empty and accurate.  
**Verification**: Manual review

---

## Task Dependency Graph

```
T000
 └─ T001
     ├─ T002 ──► T003 ──► T004
     │    └─ T005
     ├─ T007 ──► T006 ──► T008
     ├─ T009 ──► T010 ──► T011
     ├─ T012 ──► T017
     └─ T013 ──► T017
          T013 depends on: T006, T007, T012
          T014 depends on: T009, T010, T013
          T015 depends on: T014
          T016 depends on: T014, T015
          T018 depends on: T014
          T019 depends on: T018
          T020 depends on: T018, T019
          T021 depends on: T014
          T022 depends on: all tests
          T023 depends on: T022
          T024 depends on: T023
          T025 depends on: T024
```
