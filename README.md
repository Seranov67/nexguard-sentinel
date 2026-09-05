# NexGuard Sentinel — ETHOnline 2026

An in-progress, testnet-only onchain incident-response module developed alongside
the pre-existing **NexGuard Edge Resilience** IoT MVP. This repository preserves
the full history of [the original repository](https://github.com/Seranov67/nexguard-edge-resilience) under its MIT license.
Submission: Security / Continuity. Intended partner prize: The Graph AI Use Case
(Continuity); final partner selection is not yet verified.

## Sentinel status — 5 September 2026

| Component | Verified status |
|---|---|
| Guardian / DemoVault | Deployed on Base Sepolia; pause-only keeper and owner-only unpause; 9 Solidity tests |
| The Graph | Studio `nexguard-sentinel` v0.1.0 returns a real Withdrawal; 1 Matchstick test |
| SQLite core | Durable events, cursor, reservations, nonce/hash, outcomes, latch and outbox storage; 19 tests |
| Python regression | 74 tests, Ruff and strict MyPy passed locally |
| Ingestion / executor / AI | End-to-end integration pending; automatic protection is not enabled |
| Video / final submission | Pending |

Planned flow: live Graph data → AI classification → deterministic policy →
durable reservation → pause → confirmation and state verification. The full AI
prize use case is not yet demonstrated. DemoVault holds no Ether or tokens.
Sentinel is not yet integrated with the old IoT controller.

## Review and reproduce the event work

- Branch: `feature/ethonline-sentinel`.
- Baseline: `pre-ethonline-2026` at `fa202e994a77ea365061f6ac609daea1b5ad60dd`.
- [Event diff](https://github.com/Seranov67/nexguard-sentinel/compare/pre-ethonline-2026...feature/ethonline-sentinel).
- [Prior work](docs/ethonline/DISCLOSURE.md), [AI usage](docs/ethonline/AI_USAGE.md),
  [prompt record](docs/ethonline/AI_PROMPTS.md), [specification](specs/002-ethonline-sentinel/spec.md).
- [Contract evidence](docs/ethonline/deployments/base-sepolia.json) and
  [live Graph evidence](docs/ethonline/deployments/subgraph-studio.json).

Use Python 3.12; these tests require no signing credentials:

```bash
git clone --branch feature/ethonline-sentinel https://github.com/Seranov67/nexguard-sentinel.git
cd nexguard-sentinel
python -m pip install -e ".[dev]"
python -m pytest --tb=short
python -m ruff check .
python -m mypy sentinel --exclude tests
```

See [contracts](contracts/README.md), [Subgraph](subgraph/README.md), and
[durable core](sentinel/README.md) for component checks. Deployment is not needed
to inspect the existing evidence. Never commit `.env.ethonline`. A full dependency
lock and final clean-clone/end-to-end validation remain submission work.

## Pre-existing NexGuard Edge Resilience

The sections below describe the pre-event IoT MVP. Their completion claims and
DoraHacks placeholders refer to that older project, not the Sentinel submission.

[![CI](https://github.com/Seranov67/nexguard-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/Seranov67/nexguard-sentinel/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-0b7285)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-d97706.svg)](LICENSE)

Automated monitoring, configuration backup, and self-recovery for remote IoT gateways
and smart-city infrastructure.

[Architecture](docs/architecture.png) | [Demo Video](#demo-video) | [Demo Runbook](docs/demo-scenario.md) |
[Video Script](docs/video-script.md) | [Security Model](docs/security.md)

> Hackathon MVP status: implementation and automated recovery are complete. Add the
> [DoraHacks submission URL](#dorahacks-submission) after the BUIDL is published.

## Demo Video

**Watch the 2–3 minute walkthrough:** *URL pending — publish to YouTube, Loom, or Vimeo
(unlisted or public) using [docs/video-script.md](docs/video-script.md), then replace this
line with the link.*

Recording checklist: 1080p, no secrets on screen (`.env`, tokens, passwords), opens in an
incognito window without sign-in.

## Problem

Remote IoT gateways support environmental monitoring, traffic management, utilities,
and other smart-city services. When a container stops or its configuration becomes
corrupted, limited access to on-site technicians can turn a small fault into prolonged
downtime and expensive manual recovery.

## Solution

NexGuard runs beside an IoT gateway and checks its health every 10 seconds. It validates
the gateway configuration, creates SHA-256-protected last-known-good backups, opens an
incident after three consecutive failures, restores a valid configuration when needed,
restarts only an explicitly managed container, and verifies that service is healthy again.

## Key Features

- Dockerized IoT gateway simulator with `/health` and `/metrics` endpoints
- Automatic failure detection after exactly three consecutive failed checks
- Atomic configuration backup and restore using `os.replace`
- SHA-256 verification, atomic manifest, and configurable retention of 10 backups
- Label and allowlist guards for every Docker restart
- Recovery cooldown and sliding-window rate limit
- Seven Prometheus metrics and an auto-provisioned Grafana dashboard
- Structured JSON incident and recovery logs
- Optional, non-blocking Telegram incident and recovery notifications
- Automated unit, type, lint, Compose, and end-to-end CI checks

## Architecture

![NexGuard architecture](docs/architecture.png)

The controller polls the gateway, manages verified backups, and performs guarded Docker
restarts. Prometheus scrapes both application services, Grafana visualizes the controller
metrics, and Telegram notifications run out-of-band so messaging failures cannot block
recovery. See [the detailed architecture notes](docs/architecture.md).

## Technology Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.12, FastAPI, uvicorn |
| Containers | Docker, Docker Compose V2 |
| Configuration | YAML, Pydantic |
| Integrity | SHA-256, atomic filesystem replacement |
| Recovery | Docker SDK for Python |
| Monitoring | Prometheus, Grafana |
| Notifications | Telegram Bot API via async HTTP |
| Quality | Pytest, Ruff, strict MyPy, GitHub Actions |

## Demo Scenario

The demo starts with a healthy gateway and a verified backup. A presenter then stops the
gateway container or corrupts its YAML configuration. NexGuard records three failed health
checks, opens an incident, selects the safe recovery path, restarts the gateway, performs a
post-recovery health check, and updates metrics and logs.

The complete presenter flow is in [docs/demo-scenario.md](docs/demo-scenario.md), and the
2–3 minute recording outline is in [docs/video-script.md](docs/video-script.md).

## Quick Start

Prerequisites: Docker with Compose V2. Python 3.12 is needed only for local test commands.

```bash
git clone https://github.com/Seranov67/nexguard-sentinel.git
cd nexguard-sentinel
cp .env.example .env
```

Set a local `GF_SECURITY_ADMIN_PASSWORD` in `.env`. Telegram values may remain empty.
On Linux, expose the host group IDs needed by the non-root controller:

```bash
export DOCKER_GID="$(stat -c '%g' /var/run/docker.sock)"
export NEXGUARD_DATA_GID="$(stat -c '%g' data/gateway)"
chmod g+w data/backups data/gateway
```

Start and verify the complete stack:

```bash
docker compose up -d --build --wait
docker compose ps
curl http://localhost:8080/health
curl http://localhost:8081/health
```

Open Grafana at [http://localhost:3000](http://localhost:3000) and Prometheus at
[http://localhost:9090](http://localhost:9090). Set `GRAFANA_PORT` when port 3000 is in use.
All published ports bind to `127.0.0.1` only.

## Failure Simulation

Scenario A stops the gateway and demonstrates restart-only recovery:

```bash
./scripts/demo-stop.sh
sleep 45
./scripts/verify-demo.sh
```

Scenario B corrupts the live config and demonstrates verified restore plus restart:

```bash
./scripts/reset-demo.sh
./scripts/demo-corrupt-config.sh
sleep 45
./scripts/verify-demo.sh
```

Return to a clean state at any time with `./scripts/reset-demo.sh`.

## Monitoring

Prometheus scrapes the gateway and controller. The provisioned Grafana dashboard shows
gateway status, configuration integrity, incident and recovery counts, p95 recovery
duration, consecutive failures, and last backup time.

![Grafana dashboard](docs/screenshots/grafana-dashboard.png)

![Prometheus targets](docs/screenshots/prometheus-targets.png)

The exported dashboard is committed at
[monitoring/grafana/dashboards/nexguard.json](monitoring/grafana/dashboards/nexguard.json).

## Telegram Notifications

Telegram is optional and disabled when either value is empty. To enable it, set these only
in the ignored `.env` file:

```dotenv
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

The controller schedules notifications without awaiting Telegram. Network or API failures
are logged as `notification_failed` and never interrupt recovery. No real token or chat ID
belongs in this repository.

## Security Considerations

The MVP mounts `/var/run/docker.sock`, which grants root-equivalent host privileges. Every
restart is restricted by both `NEXGUARD_ALLOWED_CONTAINERS` and the
`io.nexguard.managed=true` label, but production deployments should replace direct socket
access with a Docker Socket Proxy or a narrow host-agent API. Read
[docs/security.md](docs/security.md) before deployment.

## Project Impact

NexGuard reduces gateway downtime, limits the need for on-site intervention, and makes
failure handling observable and repeatable. The MVP demonstrates a practical resilience
pattern for distributed infrastructure where connectivity, power, and technician access
cannot be assumed.

## Future Development

- Replace direct Docker socket access with a least-privilege host agent
- Add signed backup metadata and configurable off-device backup replication
- Integrate a log backend for dashboard-visible incident history
- Add support for multiple gateways through isolated controller instances
- Package deployment profiles for additional edge Linux distributions

These are post-MVP directions; Kubernetes, cloud infrastructure, databases, authentication,
and AI/ML remain outside this repository's current scope.

## DoraHacks Submission

**BUIDL URL:** *pending — add the public DoraHacks project link after submission.*

## Team

Maintained by [Seranov67](https://github.com/Seranov67). The final DoraHacks team roster
should be added here before submission.

## Running Tests

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy services/gateway-simulator
mypy services/nexguard-controller
pytest
docker compose config --quiet
```

## License

Licensed under the [MIT License](LICENSE).
