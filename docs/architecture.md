# NexGuard Edge Resilience — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Default Docker Compose Network                │
│                                                                 │
│  ┌──────────────────────┐     health check / 10s               │
│  │  nexguard-controller │ ─────────────────────────────────►   │
│  │  (port 8081)         │                                       │
│  │                      │ ◄──── /health, /metrics ─────────── │
│  │  • Health monitor    │                                       │
│  │  • Incident manager  │     ┌──────────────────────┐         │
│  │  • Recovery manager  │     │  gateway-simulator   │         │
│  │  • Backup manager    │     │  (port 8080)         │         │
│  │  • Docker manager    │     │                      │         │
│  │  • Telegram notifier │     │  • /health           │         │
│  └──────────┬───────────┘     │  • /metrics          │         │
│             │                 │  • Reads gateway.yaml│         │
│             │ Docker Socket   └────────────┬─────────┘         │
│             ▼                              │                    │
│  /var/run/docker.sock                      │ bind mount         │
│  (restart gateway-simulator only)          ▼                    │
│                              /data/gateway/gateway.yaml         │
│                                            │                    │
│                              /data/backups/ (SHA-256 backups)   │
│                                                                 │
│  ┌──────────────────┐     ┌──────────────────────────────────┐  │
│  │   Prometheus     │     │            Grafana               │  │
│  │   (port 9090)    │     │            (port 3000)           │  │
│  │                  │     │                                  │  │
│  │  scrapes:        │     │  auto-provisioned dashboard      │  │
│  │  • controller    │────►│  UID: nexguard-main              │  │
│  │  • simulator     │     │                                  │  │
│  └──────────────────┘     └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

Optional (out-of-band):
  Telegram Bot API  ◄──── nexguard-controller (non-blocking, optional)
```

---

## Controller State Machine

```
          ┌─────────────────────┐
          │     MONITORING      │◄──────────────────────────┐
          │  (every 10 s)       │                           │
          └────────┬────────────┘                           │
                   │                                        │
          ┌────────▼────────────┐                  ┌────────┴────────────┐
          │  Health check OK?   │  YES (reset ctr)  │  Recovery verified? │
          │                     │──────────────────►│  (post-restart      │
          │                     │                   │   health check)     │
          └────────┬────────────┘                   └─────────────────────┘
                   │ NO (increment counter)                  ▲
          ┌────────▼────────────┐                           │
          │  3 consecutive      │                           │
          │  failures?          │                           │
          └────────┬────────────┘                           │
                   │ YES                                    │
          ┌────────▼────────────┐                           │
          │  INCIDENT OPENED    │                           │
          │                     │                           │
          │  Check config       │                           │
          │  integrity          │                           │
          └────────┬────────────┘                           │
                   │                                        │
          ┌────────▼────────────┐                           │
          │  cooldown OK?       │ NO ─ wait                │
          │  rate limit OK?     │                           │
          └────────┬────────────┘                           │
                   │ YES                                    │
          ┌────────▼────────────┐                           │
          │  RECOVERY BRANCH    │                           │
          │  config invalid:    │                           │
          │  verify + restore   │                           │
          │  config valid:      │                           │
          │  skip restore       │                           │
          │  restart + verify   │───────────────────────────┘
          └────────┬────────────┘
                   │ if 3 attempts in 10 min exceeded
          ┌────────▼────────────┐
          │  MANUAL INTERVENTION│
          │  REQUIRED           │
          └─────────────────────┘
```

---

## Data Flow: Scenario B (Config Corruption)

```
demo-corrupt-config.sh
        │
        ▼
gateway.yaml ← invalid YAML written

        │  next health check (≤10s)
        ▼
gateway /health → 503 unhealthy

        │  3 consecutive failures
        ▼
incident_opened event logged

        │  config integrity check
        ▼
config_checker detects invalid YAML

        │  cooldown & rate limit OK
        ▼
backup_manager verifies SHA-256 of latest backup

        │  verification passes
        ▼
config restored atomically (os.replace)

        │
        ▼
docker_manager restarts gateway-simulator
(only if label io.nexguard.managed=true AND in allowlist)

        │  wait up to 30s
        ▼
gateway /health → 200 healthy

        │
        ▼
nexguard_recoveries_total++ , recovery_verified logged
Telegram notification sent (if configured)
```

Scenario A follows the same incident and safety checks but skips backup restoration when
the current YAML remains valid; it performs only the guarded restart and post-recovery check.

---

## Port Reference

| Service             | Port | Protocol | Path       |
|---------------------|------|----------|------------|
| gateway-simulator   | 8080 | HTTP     | /health, /metrics |
| nexguard-controller | 8081 | HTTP     | /health, /metrics |
| Prometheus          | 9090 | HTTP     | /api/v1/*, /metrics |
| Grafana             | 3000 (configurable with `GRAFANA_PORT`) | HTTP | / (dashboard) |

---

## Security Model (MVP)

The Docker socket bind gives the controller root-equivalent host access.

**Mitigations in the MVP**:
1. **Allowlist**: `NEXGUARD_ALLOWED_CONTAINERS` env var (default: `gateway-simulator`)
2. **Label guard**: `io.nexguard.managed=true` required on every restartable container
3. **Minimal Docker SDK usage**: only `container.restart()` is called

**For production**: Replace with Docker Socket Proxy or a host-agent with a narrow API.
See `docs/security.md` for details.
