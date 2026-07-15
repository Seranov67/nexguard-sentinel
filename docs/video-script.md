# NexGuard Demo Video Script

Target length: 2–3 minutes. Record at 1080p and publish through YouTube, Loom, or Vimeo
with public or unlisted access.

## 0:00–0:20 — Problem

Narration:

> Smart-city and IoT gateways often operate in remote locations. When a configuration
> becomes corrupted or a service fails, manual recovery increases downtime and
> operational costs.

Show the project title and the problem statement from the README.

## 0:20–0:40 — Solution

Narration:

> NexGuard Edge Resilience continuously monitors an IoT gateway, verifies its
> configuration, creates protected backups, and automatically restores service after a
> failure.

Show `docs/architecture.png` and briefly trace the gateway, controller, backup,
Prometheus, Grafana, and optional Telegram flow.

## 0:40–1:00 — Healthy Stack

Show:

```bash
docker compose ps
curl http://localhost:8080/health
```

Open the Grafana dashboard and point out the healthy gateway, valid configuration, and
last backup timestamp.

## 1:00–1:30 — Create an Incident

Run one scenario:

```bash
./scripts/demo-corrupt-config.sh
```

In a second terminal, show:

```bash
docker compose logs -f nexguard-controller
```

Point out the failed health checks, `incident_opened`, and the changing Grafana metrics.
If Telegram is configured, show the incident notification without exposing credentials.

## 1:30–2:00 — Automatic Recovery

Keep the logs visible while NexGuard verifies the backup checksum, restores the config,
restarts the managed gateway, and completes the post-recovery health check. Highlight this
event sequence:

```text
incident_opened
backup_verified
config_restored
container_restarted
recovery_verified
```

## 2:00–2:30 — Result

Show the gateway healthy again, the Grafana recovery count, and the recovery notification.
Run the automated verifier:

```bash
./scripts/verify-demo.sh
```

Closing narration:

> NexGuard reduces infrastructure downtime by automatically detecting failures, restoring
> valid configurations, and verifying that the affected service is operational again.

## Publication Checklist

- Ensure the video opens in an incognito window without requesting access.
- Do not show `.env`, bot tokens, passwords, personal keys, or private IP addresses.
- Add the public video URL near the top of `README.md` and to the DoraHacks BUIDL.
- Add the final DoraHacks submission URL to `README.md` after the BUIDL is published.
