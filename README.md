# NexGuard Edge Resilience

> **Hackathon MVP** — Specification-Driven Development  
> Status: Stages 1–8 implemented; local Docker runtime gates and GitHub Actions pass.

---

## What is NexGuard?

NexGuard is a lightweight supervisor that monitors an IoT gateway simulator,
automatically detects failures, restores last-known-good configuration, and
restarts supervised containers — all without human intervention.

**Business scenario**: reduce IoT gateway downtime in regions with unstable power
and limited access to technical personnel.

---

## Quick Start (< 10 minutes)

```bash
# Prerequisites: Docker + Docker Compose v2, Python 3.12 (for tests)
cp .env.example .env
# Set a local GF_SECURITY_ADMIN_PASSWORD in .env.
# Telegram variables may remain empty.

# Linux: grant the non-root controller access to the Docker socket and bind-mounted data.
export DOCKER_GID="$(stat -c '%g' /var/run/docker.sock)"
export NEXGUARD_DATA_GID="$(stat -c '%g' data/gateway)"
chmod g+w data/backups data/gateway

# Optional when host port 3000 is already occupied:
# export GRAFANA_PORT=3002

docker compose up -d --build  # starts all 4 containers

# Verify everything is healthy
docker compose ps
curl http://localhost:8080/health    # gateway simulator
curl http://localhost:8081/health    # nexguard controller
```

Open Grafana at [http://localhost:3000](http://localhost:3000), or at the port selected
with `GRAFANA_PORT`, using `GF_SECURITY_ADMIN_USER` and `GF_SECURITY_ADMIN_PASSWORD`
from `.env`.

All published ports bind to `127.0.0.1` only.

---

## Demo Scenarios

### Scenario A — Container stop
```bash
./scripts/demo-stop.sh
sleep 45
./scripts/verify-demo.sh
```

### Scenario B — Config corruption
```bash
./scripts/reset-demo.sh  # waits for the initial healthy backup
./scripts/demo-corrupt-config.sh
sleep 45
./scripts/verify-demo.sh
```

### Reset
```bash
./scripts/reset-demo.sh
```

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full diagram.

---

## ⚠️ Security Warning: Docker Socket

The controller mounts `/var/run/docker.sock` to manage containers.
This grants **root-equivalent privileges** on the host.

For this hackathon demo this is acceptable because:
- Access is restricted to the explicitly named allowlist (`NEXGUARD_ALLOWED_CONTAINERS`)
- Only containers with label `io.nexguard.managed=true` can be restarted
- Everything runs on a local development machine

**For production**, replace the Docker socket bind mount with:
- A dedicated **Docker Socket Proxy** (e.g. [Tecnativa/docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy)) exposing only container start/stop, or
- A separate **host-agent** with a minimal privileged API that the controller calls over HTTP.

---

## Repository Layout

```
nexguard-edge/
├── AGENTS.md                        # IDE agent instructions
├── README.md                        # This file
├── LICENSE                          # MIT license
├── compose.yaml                     # Docker Compose stack
├── .env.example                     # Environment variable template
├── pyproject.toml                   # Python tooling config
│
├── docs/
│   ├── architecture.md
│   ├── demo-scenario.md
│   ├── security.md
│   └── ssd/
│       ├── CONSTITUTION.md          # Inviolable rules
│       └── QUALITY_GATES.md         # Per-stage pass/fail criteria
│
├── specs/001-nexguard-mvp/
│   ├── spec.md                      # Functional requirements
│   ├── plan.md                      # Stage-by-stage implementation plan
│   ├── tasks.md                     # Task breakdown with acceptance criteria
│   └── acceptance.md                # Acceptance criteria (AC-xxx)
│
├── services/
│   ├── gateway-simulator/           # FastAPI IoT gateway simulator
│   └── nexguard-controller/         # FastAPI resilience controller
│
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│
├── data/
│   ├── gateway/                     # Live gateway config
│   └── backups/                     # Automatic config backups
│
└── scripts/                         # Demo and verification scripts
```

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy services/gateway-simulator
mypy services/nexguard-controller
```

## License

This project is licensed under the [MIT License](LICENSE).
