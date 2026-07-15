# NexGuard Edge Resilience — Quality Gates

> The IDE **does not proceed** to the next stage until every gate in the current
> stage is green. A failed gate must be fixed before moving forward.

**Docker-free development profile**: when explicitly approved by the owner, gates that
require a Docker runtime are marked `DEFERRED`, not `PASS`. Non-Docker stages and gates may
continue. Every deferred gate must pass in CI or on a Docker-capable target host before the
MVP can satisfy its Definition of Done.

---

## Stage 0 — Analysis & SSD Documents

**Deliverables**
- `docs/ssd/CONSTITUTION.md`
- `docs/ssd/QUALITY_GATES.md`
- `specs/001-nexguard-mvp/spec.md`
- `specs/001-nexguard-mvp/plan.md`
- `specs/001-nexguard-mvp/tasks.md`
- `specs/001-nexguard-mvp/acceptance.md`

**Gates**

| ID    | Check                                                      | Command / Method              |
|-------|------------------------------------------------------------|-------------------------------|
| QG-0A | All SSD documents exist and are non-empty                  | `ls -la docs/ssd/ specs/001-nexguard-mvp/` |
| QG-0B | No contradictions found in spec (cross-reference FR IDs)   | Manual review                 |
| QG-0C | All acceptance criteria map to an FR, NFR, ARCH, SEC, or System requirement | Manual review |
| QG-0D | No production code was written during this stage           | `git diff --name-only HEAD`   |

---

## Stage 1 — Docker Compose + Gateway Simulator

**Deliverables**
- `compose.yaml`
- `.env.example`
- `services/gateway-simulator/Dockerfile`
- `services/gateway-simulator/app/main.py`
- `services/gateway-simulator/app/config.py`
- `data/gateway/gateway.yaml` (initial config)

**Gates**

| ID    | Check                                                          | Command                                           |
|-------|----------------------------------------------------------------|---------------------------------------------------|
| QG-1A | Stack builds without errors                                    | `docker compose build`                            |
| QG-1B | Gateway simulator starts and is healthy                        | `docker compose up -d && docker compose ps`       |
| QG-1C | `/health` returns `200 OK` with JSON `{"status": "healthy"}`   | `curl -sf http://localhost:8080/health`            |
| QG-1D | `/metrics` returns Prometheus text format                      | `curl -sf http://localhost:8080/metrics`           |
| QG-1E | Corrupt YAML makes `/health` return `{"status": "unhealthy"}`  | `echo "bad: [unclosed" > data/gateway/gateway.yaml && sleep 2 && curl http://localhost:8080/health` |
| QG-1F | No secrets in repo                                             | `grep -rI "token\|password\|secret" .env.example` → only placeholders |

---

## Stage 2 — Backup & Config Integrity

**Deliverables**
- `services/nexguard-controller/app/backup.py`
- `services/nexguard-controller/app/config_checker.py`
- Unit tests for backup and config checker

**Gates**

| ID    | Check                                                          | Command                                           |
|-------|----------------------------------------------------------------|---------------------------------------------------|
| QG-2A | Backup is written atomically (temp → replace)                  | Code review: `os.replace` used                    |
| QG-2B | SHA-256 checksum file exists alongside backup                  | Unit test `test_atomic_write_and_sha256`          |
| QG-2C | Backup is created only from verified healthy state             | Unit test `test_backup_only_when_healthy`         |
| QG-2D | Config checker detects corrupt YAML                            | Unit test `test_detect_corrupt_yaml`              |
| QG-2E | Config checker validates SHA-256 of backup                     | Unit test `test_sha256_validation`                |
| QG-2F | Tests pass                                                     | `pytest services/nexguard-controller/tests/ -v`   |

---

## Stage 3 — Incident Detection

**Deliverables**
- `services/nexguard-controller/app/health_monitor.py`
- `services/nexguard-controller/app/incident.py`
- Unit tests for incident lifecycle

**Gates**

| ID    | Check                                                              | Command                                               |
|-------|--------------------------------------------------------------------|-------------------------------------------------------|
| QG-3A | Three consecutive failures (and only 3) trigger one incident       | Unit test `test_incident_after_3_failures`            |
| QG-3B | Two failures then a success resets the counter                     | Unit test `test_counter_reset_on_success`             |
| QG-3C | Incident is logged as structured JSON to stdout                    | Unit test `test_incident_json_log`                    |
| QG-3D | `nexguard_consecutive_health_failures` metric increments correctly | Unit test `test_metric_consecutive_failures`          |
| QG-3E | `nexguard_incidents_total` increments on each incident             | Unit test `test_metric_incidents_total`               |
| QG-3F | Health loop cadence stays within ±1 s of the configured interval    | Unit test `test_health_loop_cadence`                  |

---

## Stage 4 — Restore & Docker Restart

**Deliverables**
- `services/nexguard-controller/app/recovery.py`
- `services/nexguard-controller/app/docker_manager.py`
- Integration tests (container restart with mock Docker)

**Gates**

| ID    | Check                                                              | Command                                               |
|-------|--------------------------------------------------------------------|-------------------------------------------------------|
| QG-4A | Restore writes correct file atomically from backup                 | Unit test `test_restore_atomic`                       |
| QG-4B | Controller only restarts containers with label `io.nexguard.managed=true` | Unit test `test_allowlist_enforcement`         |
| QG-4C | Controller only restarts containers in allowlist                   | Unit test `test_docker_label_enforcement`             |
| QG-4D | Cooldown of 60 s is enforced between recovery attempts             | Unit test `test_cooldown_enforcement`                 |
| QG-4E | Max 3 recoveries per 10 min; afterwards status is `manual_intervention_required` | Unit test `test_max_recovery_limit`  |
| QG-4F | **Scenario A** passes end-to-end: stop container → auto-restart → `/health` 200 OK | `./scripts/demo-stop.sh && ./scripts/verify-demo.sh` |
| QG-4G | **Scenario B** passes end-to-end: corrupt config → restore → `/health` 200 OK      | `./scripts/demo-corrupt-config.sh && ./scripts/verify-demo.sh` |
| QG-4H | Post-recovery health-check is executed and logged                  | Check JSON logs after scenario run                    |

---

## Stage 5 — Prometheus & Grafana

**Deliverables**
- `monitoring/prometheus.yml`
- `monitoring/grafana/provisioning/datasources/prometheus.yml`
- `monitoring/grafana/provisioning/dashboards/nexguard.yml`
- `monitoring/grafana/dashboards/nexguard.json`

**Gates**

| ID    | Check                                                              | Command                                               |
|-------|--------------------------------------------------------------------|-------------------------------------------------------|
| QG-5A | All 7 required metrics are exported by controller                  | `curl -s http://localhost:9090/metrics \| grep nexguard` |
| QG-5B | Prometheus scrapes controller metrics successfully                 | Check Prometheus UI targets page                      |
| QG-5C | Grafana dashboard loads automatically on first start               | `curl -sf http://localhost:3000/api/dashboards/home`  |
| QG-5D | Dashboard panels are non-empty after running a demo scenario       | Manual visual check                                   |

---

## Stage 6 — Telegram (Optional)

**Deliverables**
- `services/nexguard-controller/app/notifier.py`

**Gates**

| ID    | Check                                                              | Command                                               |
|-------|--------------------------------------------------------------------|-------------------------------------------------------|
| QG-6A | Tests pass **without** `TELEGRAM_BOT_TOKEN` set                    | `unset TELEGRAM_BOT_TOKEN && pytest`                  |
| QG-6B | Notifier failure does not block or crash recovery pipeline         | Unit test `test_notifier_failure_is_non_blocking`     |
| QG-6C | Notifier is skipped gracefully when token is absent                | Unit test `test_notifier_skipped_without_token`       |

---

## Stage 7 — Tests & CI

**Deliverables**
- `.github/workflows/ci.yml`
- Full test coverage for all modules

**Gates**

| ID    | Check                                                              | Command                                               |
|-------|--------------------------------------------------------------------|-------------------------------------------------------|
| QG-7A | All unit tests pass                                                | `pytest`                                              |
| QG-7B | Ruff finds no errors                                               | `ruff check .`                                        |
| QG-7C | MyPy finds no errors                                               | Run strict MyPy once per service source root          |
| QG-7D | Compose config is valid                                            | `docker compose config --quiet`                       |
| QG-7E | CI pipeline passes on push to `main`                               | GitHub Actions green                                  |

---

## Stage 8 — README & Demo

**Deliverables**
- `README.md`
- `AGENTS.md`
- `docs/architecture.md`
- `docs/demo-scenario.md`
- `docs/security.md`
- `scripts/demo-stop.sh`
- `scripts/demo-corrupt-config.sh`
- `scripts/reset-demo.sh`
- `scripts/verify-demo.sh`

**Gates**

| ID    | Check                                                              | Method                                                |
|-------|--------------------------------------------------------------------|-------------------------------------------------------|
| QG-8A | `README.md` contains: quick-start, architecture section, demo section | Manual review                                    |
| QG-8B | A new user can reach a running stack in under 10 minutes           | Time the full sequence from `git clone` to healthy UI |
| QG-8C | `scripts/reset-demo.sh` returns the environment to a clean state   | Run after each scenario                               |
| QG-8D | Security warning about Docker socket is prominent in README        | Manual review                                         |

---

## Stage 9 — Final Delivery Hardening

**Deliverables**
- Bounded backup retention and atomic manifest
- Compose-wired optional Telegram credentials
- Public presentation assets and final repository metadata

**Gates**

| ID    | Check                                                              | Method                                                |
|-------|--------------------------------------------------------------------|-------------------------------------------------------|
| QG-9A | Backup count never exceeds configured retention                    | Unit test `test_retention_and_manifest`               |
| QG-9B | Manifest is atomically replaced and matches retained backups       | Unit test `test_retention_and_manifest`               |
| QG-9C | Telegram values from `.env` reach the controller                   | `docker compose config`                               |
| QG-9D | README, architecture PNG, and monitoring screenshots are present   | Manual review                                         |
| QG-9E | Public repository uses the required name and `main` default branch | GitHub repository metadata                            |

---

## Global Non-Regression Gates (run before every commit)

Run every gate that is applicable to the files available at the current stage. The
Per-service strict MyPy gates become mandatory once T002 creates Python sources. The
`docker compose config --quiet` gate becomes mandatory once T004 creates `compose.yaml`.

```bash
ruff check .
mypy services/gateway-simulator
mypy services/nexguard-controller
pytest
docker compose config --quiet
grep -rIE "g""hp_|xo""xb-|AK""IA|bo""t[0-9]{8,}:" . \
  --exclude-dir=.git --exclude-dir=.venv \
  && echo "SECRET FOUND" || echo "Clean"
```
