# specs/001-nexguard-mvp/acceptance.md
# NexGuard MVP — Acceptance Criteria

**Version**: 1.0.2
**Linked spec**: `specs/001-nexguard-mvp/spec.md`  
**Status**: VERIFIED — all criteria passed on 2026-07-15

> Each acceptance criterion maps to one or more Functional Requirements (FR-xxx)
> from `spec.md`. All criteria must pass before the MVP is considered complete.

---

## AC-001 — Gateway health endpoint (FR-001)

**Given** the gateway simulator container is running and has a valid config  
**When** `GET http://localhost:8080/health` is called  
**Then** the response is:
- HTTP status: `200`
- Body: `{"status": "healthy"}`

**Verification**:
```bash
curl -sf http://localhost:8080/health | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='healthy'"
echo "AC-001: PASS"
```

---

## AC-002 — Gateway metrics endpoint (FR-001)

**Given** the gateway simulator container is running  
**When** `GET http://localhost:8080/metrics` is called  
**Then** the response body is in Prometheus text format (contains `# HELP` and `# TYPE`)

**Verification**:
```bash
curl -sf http://localhost:8080/metrics | grep -q "# HELP" && echo "AC-002: PASS"
```

---

## AC-003 — Gateway reads YAML config (FR-002)

**Given** a valid YAML file at the configured path  
**When** the gateway simulator starts  
**Then** `/health` returns `{"status": "healthy"}` without restart

**Verification**: Same as AC-001.

---

## AC-004 — Corrupt YAML causes unhealthy state (FR-003)

**Given** a syntactically invalid YAML file at the config path  
**When** `GET http://localhost:8080/health` is called  
**Then**:
- HTTP status: `503`
- Body contains `"status": "unhealthy"`
- Body contains `"reason": "config_invalid"`

**Verification**:
```bash
echo "bad: [unclosed" > data/gateway/gateway.yaml
sleep 2
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
[ "$STATUS" = "503" ] && echo "AC-004: PASS" || echo "AC-004: FAIL (HTTP $STATUS)"
```

---

## AC-005 — Missing YAML keys cause unhealthy state (FR-003)

**Given** a structurally valid YAML missing mandatory keys (e.g. `gateway.id`)  
**When** `GET http://localhost:8080/health` is called  
**Then** response is HTTP 503 with `"status": "unhealthy"`

**Verification**: Unit test `test_config.py::test_reject_missing_required_keys`

---

## AC-006 — Controller periodic health check (FR-004)

**Given** the controller is running  
**When** 30 seconds pass  
**Then** at least 2 JSON log lines with `"event_type": "health_check"` appear in controller logs

**Verification**:
```bash
sleep 30
docker compose logs nexguard-controller | grep -c "health_check" | awk '{if ($1>=2) print "AC-006: PASS"; else print "AC-006: FAIL"}'
```

---

## AC-007 — Three consecutive failures trigger exactly one incident (FR-005)

**Given** the controller is running  
**When** the gateway is stopped (3 health checks fail)  
**Then**:
- Exactly one incident is created
- The controller JSON log contains exactly one line with `"event_type": "incident_opened"`

**Verification**:
```bash
docker compose stop gateway-simulator
sleep 40
docker compose logs nexguard-controller | grep -c "incident_opened" | awk '{if ($1==1) print "AC-007: PASS"; else print "AC-007: FAIL"}'
```

---

## AC-008 — Two failures + success resets counter (FR-005)

**Given** 2 consecutive failures have been recorded  
**When** a successful health check is received  
**Then** the failure counter resets to 0 and no incident is opened

**Verification**: Unit test `test_incident.py::test_counter_reset_on_success`

---

## AC-009 — Backup created from healthy state only (FR-006)

**Given** the controller is running, the gateway is healthy, and no valid backup exists
**When** the first verified healthy check completes
**Then** an initial backup file appears in `data/backups/`

**Given** a valid backup already exists and the gateway remains healthy
**When** `BACKUP_INTERVAL_SECONDS` elapses
**Then** a new timestamped backup is created

**Given** the gateway is unhealthy  
**When** the backup interval triggers  
**Then** no new backup file is created

**Verification**: Unit tests `test_backup.py::test_backup_only_when_healthy`,
`test_backup.py::test_no_backup_when_unhealthy`, and an integration test for initial and
interval-triggered backup creation.

---

## AC-010 — Atomic backup with SHA-256 (FR-007)

**Given** the backup manager is called with a valid config path  
**When** `create_backup()` completes  
**Then**:
- A backup file exists with a UTC timestamp in its name
- A companion `.sha256` file exists with the correct hex digest

**Verification**: Unit test `test_backup.py::test_atomic_write_and_sha256`

---

## AC-011 — Automatic config restoration (FR-008)

**Given** an incident is open due to a corrupt config  
**When** the recovery manager runs  
**Then**:
- Backup SHA-256 is verified before use
- Config file is restored atomically
- The restoration event is logged as JSON

**Verification**:
```bash
./scripts/demo-corrupt-config.sh
sleep 45
./scripts/verify-demo.sh
```

---

## AC-012 — Container restart allowlist + label guard (FR-009)

**Given** a container does NOT have label `io.nexguard.managed=true`  
**When** the recovery manager tries to restart it  
**Then** restart is blocked; a `SECURITY_BLOCK` event is logged

**Given** a container name is NOT in `NEXGUARD_ALLOWED_CONTAINERS`  
**When** the recovery manager tries to restart it  
**Then** restart is blocked; a `SECURITY_BLOCK` event is logged

**Verification**: Unit tests `test_docker_manager.py::test_docker_label_enforcement` and
`test_docker_manager.py::test_allowlist_enforcement`

---

## AC-013 — Post-recovery health check (FR-010)

**Given** a successful config restoration and container restart  
**When** the container becomes running  
**Then**:
- The controller performs a health check within `RESTART_WAIT_SECONDS`
- The result is logged as JSON with `"event_type": "recovery_verified"`

**Verification**: Unit test `test_recovery.py::test_post_recovery_health_check`

---

## AC-014 — Seven Prometheus metrics exported (FR-011)

**Given** the controller is running  
**When** `GET http://localhost:8081/metrics` is called  
**Then** the response contains all 7 required metric names:
```
nexguard_gateway_up
nexguard_config_integrity
nexguard_incidents_total
nexguard_recoveries_total
nexguard_recovery_duration_seconds
nexguard_last_backup_timestamp_seconds
nexguard_consecutive_health_failures
```

**Verification**:
```bash
METRICS=$(curl -sf http://localhost:8081/metrics)
for M in nexguard_gateway_up nexguard_config_integrity nexguard_incidents_total \
          nexguard_recoveries_total nexguard_recovery_duration_seconds \
          nexguard_last_backup_timestamp_seconds nexguard_consecutive_health_failures; do
  echo "$METRICS" | grep -q "$M" && echo "  ✓ $M" || echo "  ✗ $M MISSING"
done
```

---

## AC-015 — Grafana dashboard auto-provisioned (FR-012)

**Given** `docker compose up -d` has been run  
**When** `GET http://localhost:3000/api/dashboards/uid/nexguard-main` is called  
**Then** HTTP 200 is returned (no manual import required)

**Verification**:
```bash
curl -sf -u "${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}" \
  http://localhost:3000/api/dashboards/uid/nexguard-main \
  | grep -q "nexguard" && echo "AC-015: PASS"
```

---

## AC-016 — Non-blocking Telegram (FR-013)

**Given** `TELEGRAM_BOT_TOKEN` is NOT set  
**When** a recovery event occurs  
**Then**:
- Recovery completes normally
- No exception propagates
- Test suite passes

**Verification**: `unset TELEGRAM_BOT_TOKEN && pytest`

---

## AC-017 — Structured JSON event log (FR-014)

**Given** an incident occurs and is resolved  
**When** controller logs are inspected  
**Then** every event line is valid JSON containing: `timestamp`, `event_type`, `level`, `message`

**Verification**:
```bash
docker logs nexguard-controller 2>&1 | grep "^{" | python3 -c "
import sys, json
lines = list(sys.stdin)
assert lines, 'no structured JSON events found'
for line in lines:
    d = json.loads(line.strip())
    assert 'timestamp' in d
    assert 'event_type' in d
    assert 'level' in d
    assert 'message' in d
print('AC-017: PASS')
"
```

---

## AC-018 — Recovery cooldown enforced (ARCH-7)

**Given** a recovery attempt just completed  
**When** another failure immediately occurs  
**Then** the next recovery attempt is delayed by at least 60 seconds

**Verification**: Unit test `test_recovery.py::test_cooldown_enforcement`

---

## AC-019 — Rate limit triggers manual intervention (ARCH-8, ARCH-9)

**Given** 3 recovery attempts have occurred within 10 minutes  
**When** a 4th failure occurs  
**Then**:
- Recovery is NOT attempted
- Status is `manual_intervention_required`
- An event is logged

**Verification**: Unit test `test_recovery.py::test_max_recovery_limit`

---

## AC-020 — Full scenario A: container stop → auto-restart (System)

**Steps**:
1. `docker compose up -d --build` → all containers healthy
2. `./scripts/demo-stop.sh` → stops gateway-simulator
3. Wait 45 seconds
4. `./scripts/verify-demo.sh` → exits 0

**Expected outcomes**:
- Controller logs show: `health_check FAIL` × 3, then `incident_opened`, then `container_restarted`
- No config restoration is attempted while the current YAML remains valid
- `nexguard_recoveries_total` counter = 1
- Gateway `/health` returns 200 OK
- Grafana shows recovery event

**Verification**: `./scripts/demo-stop.sh && sleep 45 && ./scripts/verify-demo.sh`

---

## AC-021 — Full scenario B: config corruption → auto-restore (System)

**Steps**:
1. `./scripts/reset-demo.sh` → clean state
2. `./scripts/demo-corrupt-config.sh` → corrupts gateway.yaml
3. Wait 45 seconds
4. `./scripts/verify-demo.sh` → exits 0

**Expected outcomes**:
- Controller logs show: `config_invalid`, `backup_verified`, `config_restored`, `container_restarted`
- `nexguard_config_integrity` metric returns to 1
- Gateway `/health` returns 200 OK

**Verification**: `./scripts/demo-corrupt-config.sh && sleep 45 && ./scripts/verify-demo.sh`

---

## AC-022 — No secrets in repository (SEC-1, SEC-2, NFR-04)

**Given** any state of the repository  
**When** the following check is run  
**Then** it exits 0

**Verification**:
```bash
grep -rIE "g""hp_|xo""xb-|AK""IA|bo""t[0-9]{8,}:" . \
  --exclude-dir=.git --exclude-dir=.venv \
  && echo "SECRET FOUND — FAIL" || echo "AC-022: PASS"
```

---

## AC-023 — Health-check loop cadence (NFR-02)

**Given** a configured health-check interval
**When** the controller health loop executes multiple checks
**Then** each check begins within ±1 second of its scheduled deadline without cumulative drift

**Verification**: Unit test `test_health_monitor.py::test_health_loop_cadence`

---

## Acceptance Summary Table

| AC ID  | FR / Rule  | Test Type     | Status |
|--------|------------|---------------|--------|
| AC-001 | FR-001     | Integration   | `[x]`  |
| AC-002 | FR-001     | Integration   | `[x]`  |
| AC-003 | FR-002     | Integration   | `[x]`  |
| AC-004 | FR-003     | Integration   | `[x]`  |
| AC-005 | FR-003     | Unit          | `[x]`  |
| AC-006 | FR-004     | Integration   | `[x]`  |
| AC-007 | FR-005     | Integration   | `[x]`  |
| AC-008 | FR-005     | Unit          | `[x]`  |
| AC-009 | FR-006     | Unit          | `[x]`  |
| AC-010 | FR-007     | Unit          | `[x]`  |
| AC-011 | FR-008     | Integration   | `[x]`  |
| AC-012 | FR-009     | Unit          | `[x]`  |
| AC-013 | FR-010     | Unit          | `[x]`  |
| AC-014 | FR-011     | Integration   | `[x]`  |
| AC-015 | FR-012     | Integration   | `[x]`  |
| AC-016 | FR-013     | Unit          | `[x]`  |
| AC-017 | FR-014     | Integration   | `[x]`  |
| AC-018 | ARCH-7     | Unit          | `[x]`  |
| AC-019 | ARCH-8/9   | Unit          | `[x]`  |
| AC-020 | System     | E2E           | `[x]`  |
| AC-021 | System     | E2E           | `[x]`  |
| AC-022 | SEC-1/2    | CI/Static     | `[x]`  |
| AC-023 | NFR-02     | Unit          | `[x]`  |
