# NexGuard — Demo Scenarios

## Prerequisites

```bash
export DOCKER_GID="$(stat -c '%g' /var/run/docker.sock)"
export NEXGUARD_DATA_GID="$(stat -c '%g' data/gateway)"
docker compose up -d --build
docker compose ps   # all containers must be healthy
```

---

## Scenario A — Container Stop (Automatic Restart)

**What it demonstrates**: NexGuard detects a stopped container and automatically
restarts it after 3 failed health checks.

### Steps

```bash
# 1. Start demo
./scripts/demo-stop.sh

# 2. Watch controller logs in real-time
docker compose logs -f nexguard-controller

# 3. After ~35-40 seconds, verify recovery
./scripts/verify-demo.sh
```

### Expected Log Sequence

```
{"event_type":"health_check","level":"WARNING","ok":false,"reason":"network_error"}
{"event_type":"health_check","level":"WARNING","ok":false,"reason":"network_error"}
{"event_type":"health_check","level":"WARNING","ok":false,"reason":"network_error"}
{"event_type":"incident_opened","level":"ERROR","reason":"network_error"}
{"event_type":"recovery_started","level":"INFO"}
{"event_type":"container_restarted","level":"INFO","container":"gateway-simulator"}
{"event_type":"recovery_verified","level":"INFO","ok":true,"reason":"ok"}
```

Every real event also includes `timestamp` and `message`; fields are abbreviated above.

### Expected Metrics Changes

| Metric | Before | After |
|--------|--------|-------|
| `nexguard_gateway_up` | 1 | 0 → 1 |
| `nexguard_incidents_total` | N | N+1 |
| `nexguard_recoveries_total` | M | M+1 |
| `nexguard_consecutive_health_failures` | 0 | 3 → 0 |

---

## Scenario B — Config Corruption (Automatic Restore)

**What it demonstrates**: NexGuard detects an invalid YAML config, verifies the
SHA-256 of the backup, restores the config atomically, and restarts the gateway.

### Steps

```bash
# 1. Reset to clean state first
./scripts/reset-demo.sh

# 2. Start demo
./scripts/demo-corrupt-config.sh

# 3. Watch controller logs
docker compose logs -f nexguard-controller

# 4. After ~35-40 seconds, verify recovery
./scripts/verify-demo.sh
```

### Expected Log Sequence

```
{"event_type":"health_check","level":"WARNING","ok":false,"reason":"config_invalid"}
{"event_type":"health_check","level":"WARNING","ok":false,"reason":"config_invalid"}
{"event_type":"health_check","level":"WARNING","ok":false,"reason":"config_invalid"}
{"event_type":"incident_opened","level":"ERROR","reason":"config_invalid"}
{"event_type":"recovery_started","level":"INFO"}
{"event_type":"backup_verified","level":"INFO","backup":"<filename>"}
{"event_type":"config_restored","level":"INFO"}
{"event_type":"container_restarted","level":"INFO","container":"gateway-simulator"}
{"event_type":"recovery_verified","level":"INFO","ok":true,"reason":"ok"}
```

### Expected Metrics Changes

| Metric | Before | After |
|--------|--------|-------|
| `nexguard_config_integrity` | 1 | 0 → 1 |
| `nexguard_gateway_up` | 1 | 0 → 1 |
| `nexguard_incidents_total` | N | N+1 |
| `nexguard_recoveries_total` | M | M+1 |

---

## Full Verification Script Output

A successful `./scripts/verify-demo.sh` prints:

```
NexGuard demo verification: PASS
<last 100 nexguard-controller log lines>
```

---

## Reset Between Scenarios

```bash
./scripts/reset-demo.sh
```

This command:
1. Stops all containers: `docker compose down`
2. Restores `data/gateway/gateway.yaml` from the bundled known-good copy
3. Restarts and rebuilds the gateway and controller services required by the demo
4. Waits for gateway health and the initial verified backup

Prometheus and Grafana are intentionally not required by reset; start the complete
monitoring stack afterward with `docker compose up -d` when needed.
