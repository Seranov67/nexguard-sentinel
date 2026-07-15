# specs/001-nexguard-mvp/spec.md
# NexGuard Edge Resilience — MVP Specification

**Version**: 1.1.0
**Status**: FINAL HARDENING — owner-requested audit 2026-07-15
**Stage**: Stage 9

---

## 1. Background & Problem Statement

IoT gateways deployed in remote regions with unstable power and limited technician
access suffer extended downtime when containers crash or configuration files become
corrupted. Manual intervention is slow and expensive.

**NexGuard** is a lightweight supervisor that runs alongside the gateway, continuously
monitors its health, and autonomously restores service using a known-good backup.

---

## 2. Functional Requirements

### FR-001 — Gateway Simulator: HTTP endpoints
- The gateway simulator **must** expose a `/health` HTTP endpoint.
- Response body: `{"status": "healthy"}` with HTTP 200 when healthy.
- Response body: `{"status": "unhealthy", "reason": "<string>"}` with HTTP 503 when unhealthy.
- The simulator **must** expose `/metrics` in Prometheus text format.

### FR-002 — Gateway Simulator: YAML configuration
- The simulator **must** read a YAML configuration file from a path specified by the
  environment variable `GATEWAY_CONFIG_PATH` (default: `/data/gateway/gateway.yaml`).
- The simulator **must** reload the config on every `/health` request (or on a configurable
  interval), so that changes on disk are detected without restart.

### FR-003 — Unhealthy state on corrupt config
- If the YAML file is **missing**, **empty**, or **syntactically invalid**, the simulator
  **must** return `{"status": "unhealthy", "reason": "config_invalid"}` with HTTP 503.
- A structurally valid YAML with missing mandatory keys **must** also produce `unhealthy`.

### FR-004 — Controller: periodic health check
- The controller **must** check the gateway's `/health` endpoint at a configurable
  interval (env `HEALTH_CHECK_INTERVAL_SECONDS`, default `10`).
- Each check result (success or failure) **must** be logged as a structured JSON line.

### FR-005 — Incident creation after 3 consecutive failures
- The controller **must** count consecutive `/health` failures.
- After **exactly 3** consecutive failures the controller **must** open a single incident.
- A successful health check **must** reset the consecutive-failure counter to 0.
- Opening a duplicate incident while an existing one is open is **not allowed**.

### FR-006 — Backup from healthy state only
- The controller **must** create a config backup only when:
  - The gateway's `/health` returns 200 OK, **and**
  - The current config YAML passes schema validation.
- Backups are **never** created from an unhealthy or unknown state.
- The first verified healthy check **must** create an initial backup when no valid backup
  exists. Later healthy checks refresh the backup no more often than
  `BACKUP_INTERVAL_SECONDS` (default: 60 seconds).

### FR-007 — Atomic backup with SHA-256
- Backup **must** be written atomically: write to a `.tmp` file in the same directory,
  then call `os.replace()` to rename it.
- A companion `<backup-name>.sha256` file **must** be written atomically in the same
  operation, containing the hex SHA-256 of the backup content.
- The backup filename **must** include a UTC ISO-8601 timestamp.

### FR-008 — Automatic config restoration
- When the controller opens an incident and detects a corrupt/invalid config, it
  **must** attempt restoration using the latest valid backup.
- Restoration **must** also be atomic (`os.replace`).
- Before restoring, the controller **must** verify the backup's SHA-256 checksum.
  If verification fails, restoration is aborted and an error is logged.

### FR-009 — Controlled container restart
- After config restoration, the controller **must** restart the gateway container.
- When an incident is caused by an unavailable or stopped container while the current
  config remains valid, recovery **must** skip config restoration and perform a guarded
  restart directly.
- The controller **must only** restart a container that satisfies **both** conditions:
  1. Container name is in `NEXGUARD_ALLOWED_CONTAINERS` (comma-separated env var).
  2. Container has the Docker label `io.nexguard.managed=true`.
- If either condition fails, the restart is skipped and a `SECURITY_BLOCK` event is logged.

### FR-010 — Post-recovery health check
- After restarting the container, the controller **must** wait for the container to
  reach a running state (up to `RESTART_WAIT_SECONDS`, default 30 s), then perform
  a health check.
- The result (success or failure) **must** be logged and reflected in metrics.

### FR-011 — Prometheus metrics
- The controller **must** expose a `/metrics` endpoint (default port `8081`) in
  Prometheus text format.
- All 7 required metrics must be present (see Section 4).

### FR-012 — Grafana dashboard
- A pre-built Grafana dashboard **must** be provisioned automatically on first start.
- The dashboard **must** contain panels for: gateway status, incidents total,
  recoveries total, recovery duration, consecutive failures, config integrity, and
  last backup time.

### FR-013 — Non-blocking Telegram
- Telegram notifications are **optional**; if `TELEGRAM_BOT_TOKEN` is not set the
  notifier **must** be skipped silently.
- Telegram calls **must** be made asynchronously (e.g. in a background thread/task)
  and any exception **must** be caught and logged without propagating.

### FR-014 — Structured JSON event log
- All incidents, recovery attempts, backup events, and security blocks **must** be
  logged as JSON lines to stdout.
- Required fields: `timestamp` (ISO-8601 UTC), `event_type`, `level`, `message`,
  and any relevant additional context.

### FR-015 — Bounded backup retention and manifest
- The controller **must** retain at most `BACKUP_RETENTION_COUNT` complete backups
  (default: 10, minimum: 1).
- Each successful backup **must** atomically refresh `backup-manifest.json` with the
  retained filenames, SHA-256 values, and latest backup name.
- Pruning **must** remove both the YAML backup and its companion checksum.

### FR-016 — Compose-wired Telegram configuration
- `docker compose up` **must** pass `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from
  `.env` into the controller without storing credentials in the repository.

---

## 3. Non-Functional Requirements

| ID     | Requirement                                                               |
|--------|---------------------------------------------------------------------------|
| NFR-01 | The full stack starts from cold with `docker compose up -d --build` in < 2 min on a modern laptop |
| NFR-02 | Health check loop must not drift more than ±1 s from the configured interval |
| NFR-03 | Config restoration must complete within 5 seconds                          |
| NFR-04 | No plaintext secrets in repository (enforced by CI)                       |
| NFR-05 | All Python code passes `ruff check` with zero errors                      |
| NFR-06 | All Python code passes `mypy` with zero errors (strict mode per service)  |
| NFR-07 | Test suite runs successfully with `TELEGRAM_BOT_TOKEN` unset              |

---

## 4. Required Prometheus Metrics

| Metric name                              | Type    | Description                                               |
|------------------------------------------|---------|-----------------------------------------------------------|
| `nexguard_gateway_up`                    | Gauge   | 1 if last health check was OK, 0 otherwise                |
| `nexguard_config_integrity`              | Gauge   | 1 if config is valid, 0 if corrupt/missing                |
| `nexguard_incidents_total`               | Counter | Total number of incidents opened                          |
| `nexguard_recoveries_total`              | Counter | Total successful recoveries                               |
| `nexguard_recovery_duration_seconds`     | Histogram | Time taken for each recovery                            |
| `nexguard_last_backup_timestamp_seconds` | Gauge   | Unix timestamp of the most recent successful backup       |
| `nexguard_consecutive_health_failures`   | Gauge   | Current count of consecutive health-check failures        |

---

## 5. Recovery Safety Rules

| Rule                    | Value              |
|-------------------------|--------------------|
| Cooldown between attempts | 60 seconds       |
| Max attempts per window | 3                  |
| Window duration         | 10 minutes         |
| Behaviour after limit   | `manual_intervention_required` status; recovery loop paused |
| Container restart guard | Label `io.nexguard.managed=true` **AND** name in allowlist |

---

## 6. Configuration Reference

### Gateway Simulator environment variables

| Variable             | Default                        | Required |
|----------------------|--------------------------------|----------|
| `GATEWAY_CONFIG_PATH`| `/data/gateway/gateway.yaml`   | No       |
| `PORT`               | `8080`                         | No       |

### Controller environment variables

| Variable                        | Default        | Required |
|---------------------------------|----------------|----------|
| `GATEWAY_HEALTH_URL`            | `http://gateway-simulator:8080/health` | No |
| `HEALTH_CHECK_INTERVAL_SECONDS` | `10`           | No       |
| `FAILURE_THRESHOLD`             | `3`            | No       |
| `CONFIG_PATH`                   | `/data/gateway/gateway.yaml` | No |
| `BACKUP_DIR`                    | `/data/backups` | No      |
| `BACKUP_INTERVAL_SECONDS`       | `60`           | No       |
| `BACKUP_RETENTION_COUNT`        | `10`           | No       |
| `NEXGUARD_ALLOWED_CONTAINERS`   | `gateway-simulator` | No  |
| `RECOVERY_COOLDOWN_SECONDS`     | `60`           | No       |
| `MAX_RECOVERIES_PER_WINDOW`     | `3`            | No       |
| `RECOVERY_WINDOW_SECONDS`       | `600`          | No       |
| `RESTART_WAIT_SECONDS`          | `30`           | No       |
| `METRICS_PORT`                  | `8081`         | No       |
| `TELEGRAM_BOT_TOKEN`            | *(unset)*      | No       |
| `TELEGRAM_CHAT_ID`              | *(unset)*      | No       |

### Docker Compose host variables

| Variable             | Default                | Purpose |
|----------------------|------------------------|---------|
| `DOCKER_SOCKET`      | `/var/run/docker.sock` | Host socket bind source |
| `DOCKER_GID`         | `0`                    | Supplementary group for socket access |
| `NEXGUARD_DATA_GID`  | `1000`                 | Supplementary group for bind-mounted data |
| `GRAFANA_PORT`       | `3000`                 | Grafana host port |

---

## 7. Gateway Config YAML Schema

```yaml
# Mandatory keys for a "valid" gateway config
gateway:
  id: string          # required
  name: string        # required
  location: string    # required
  sensors:
    - id: string      # at least one sensor required
      type: string
      unit: string
  reporting_interval_seconds: integer  # required, > 0
```

---

## 8. Out of Scope

See `docs/ssd/CONSTITUTION.md` § 3.2 for the complete exclusion list.

---

## 9. Resolved Design Decisions

| ID    | Decision                                                               |
|-------|------------------------------------------------------------------------|
| OQ-01 | Reload on every `/health` request.                                      |
| OQ-02 | Store a full YAML copy, not a diff.                                     |
| OQ-03 | Use Grafana dashboard UID `nexguard-main`.                              |
| OQ-04 | Write structured application logs to stdout only.                       |

These decisions were accepted with the specification on 2026-07-14.
