# NexGuard Sentinel — ETHOnline 2026

Testnet incident response using live The Graph data, structured AI classification,
durable pause-only execution, and inspectable incident evidence. DemoVault uses
valueless accounting credits; it holds no Ether or tokens.

## Verified status — 6 September 2026

- Guardian and DemoVault are deployed on Base Sepolia; 9 Solidity tests pass.
- Studio v0.1.0 returns live Withdrawal entities and healthy `_meta` information.
- ES302 safety repairs and ES401/ES402 implementation pass local gates. The CLI
  uses an explicitly configured Ollama model; missing or invalid AI cannot pause.
- SQLite preserves pending processing, atomic reservations, action limits, signed
  hashes, canonical incident references, classification traces and notification retries.
- Evidence API / MCP support incident inspection and payload integrity checks.
  Payment settlement is **not implemented**. Demo bypass requires server opt-in.
- Ledger descriptor passes the vendored official ERC-7730 v1 schema. Hardware
  Clear Signing and a Ledger-originated recovery have **not been demonstrated**.
- Final live AI rehearsal, real-model A/B comparison, video and Dashboard submission
  remain pending. Historical onchain receipts do not prove AI or hardware use.

See [current verification and blockers](docs/ethonline/FINAL_AUDIT_2026-09-06.md)
and the [submission and recording pack](docs/ethonline/SUBMISSION_PACK.md).

## Reproduce

Use Python 3.12:

```bash
git clone --branch feature/ethonline-sentinel https://github.com/Seranov67/nexguard-sentinel.git
cd nexguard-sentinel
python -m venv .venv
# Activate .venv using your shell's activation command.
python -m pip install -r sentinel/requirements.lock
python -m pip install --no-deps -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m mypy sentinel
```

The lock includes runtime and verification dependencies. Installed distributions
include Bazantic and Ledger modules plus their JSON assets. Tests require no keys.

## Operate

Copy `.env.ethonline.example` to ignored `.env.ethonline` and configure public
contract/Graph endpoints. Set `OLLAMA_URL` and `OLLAMA_MODEL` for classification.

```bash
python -m sentinel.cli status
python -m sentinel.cli run --once --dry-run
python -m sentinel.ledger.unpause_ledger --simulate --reason "Incident reviewed"
```

Dry-run uses isolated state and never signs. Live `run` requires the disposable
keeper key and the configured model. Reconcile unfinished intents before attributed
latch reset; reconciliation never resends. Notification delivery is at-least-once
structured stdout with durable retries; consumers deduplicate notification IDs.

For local evidence inspection set `SENTINEL_EVIDENCE_DEMO=1` on the API server:

```bash
python -m uvicorn sentinel.evidence_api:app --host 127.0.0.1 --port 8082
# Separate shell; point the MCP client at this API.
# EVIDENCE_API_URL=http://127.0.0.1:8082
python -m sentinel.bazantic.mcp_server
python -m sentinel.bazantic.benchmark_ab --model YOUR_INSTALLED_MODEL
```

A/B requires reachable services and records actual tool transcripts. It never
substitutes synthetic responses or predetermined improvement scores.

## Public evidence and provenance

- [Guardian](https://sepolia.basescan.org/address/0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3)
- [DemoVault](https://sepolia.basescan.org/address/0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13)
- [Historical pause](https://sepolia.basescan.org/tx/0xaa915ea5e86823ec63259d3573b05c4e243fbbaae3ae3a8003dbaf8582e29d75), block 46433932
- [Historical owner recovery](https://sepolia.basescan.org/tx/0x2f68bdd881089057139f38d1ce7585169d27ff793f5b7af5a34951def628b070), block 46434002
- [Prior-work disclosure](docs/ethonline/DISCLOSURE.md), [AI usage](docs/ethonline/AI_USAGE.md),
  [prompt archive](docs/ethonline/AI_PROMPTS.md), [SSD tasks](specs/002-ethonline-sentinel/tasks.md)
- Event baseline: `pre-ethonline-2026` / `fa202e994a77ea365061f6ac609daea1b5ad60dd`.

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
