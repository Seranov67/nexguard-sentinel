# NexGuard — Security Considerations

## ⚠️ Docker Socket Access

NexGuard mounts `/var/run/docker.sock` inside the controller container.
This is functionally equivalent to **root access on the host machine**.

### Why it is acceptable for this MVP

This is a **local hackathon demo**, running on a single developer machine:
- No multi-tenant environment
- No network exposure outside localhost
- No sensitive data on the host

### Mitigations applied in the MVP

| Mitigation | Implementation |
|------------|----------------|
| Container allowlist | `NEXGUARD_ALLOWED_CONTAINERS` env var (comma-separated names) |
| Docker label guard | `io.nexguard.managed=true` must be present on the container |
| Minimal SDK calls | Only `container.start()` / `container.restart()` are used |
| Security block logging | All blocked restart attempts are logged as `SECURITY_BLOCK` events |

### Recommended production mitigations

**Option A — Docker Socket Proxy**

Use [Tecnativa/docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy)
to expose only specific API endpoints to the controller:

```yaml
# compose.yaml (production variant)
services:
  docker-socket-proxy:
    image: tecnativa/docker-socket-proxy
    environment:
      CONTAINERS: 1   # allow listing containers
      POST: 1         # allow POST (start/restart)
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    # expose only to nexguard-controller, not externally

  nexguard-controller:
    environment:
      DOCKER_HOST: tcp://docker-socket-proxy:2375
    # remove volume: /var/run/docker.sock
```

**Option B — Host Agent**

Deploy a minimal privileged agent on the host that accepts only:
```
POST /containers/{name}/restart
```
with a pre-shared API key, and have the controller call that instead of the
Docker API directly.

---

## Secrets Management

| Rule | Implementation |
|------|----------------|
| No secrets in repository | `.gitignore` excludes `.env`; CI checks for leaked tokens |
| `.env.example` contains no real values | All values are placeholders or empty |
| Telegram token is optional | Controller starts normally if token is absent |

---

## Network Isolation

All services communicate over the `nexguard-net` Docker bridge network.
No ports are exposed to external interfaces beyond localhost.

---

## File System

| Path | Access | Notes |
|------|--------|-------|
| `/data/gateway/gateway.yaml` | Read (simulator), Write (controller) | Config file |
| `/data/backups/` | Write (controller) | Backup files + SHA-256 checksums |
| `/var/run/docker.sock` | Read/Write (controller) | **High privilege — see above** |

---

## Dependency Security

- All Python dependencies are pinned in `requirements.txt` per service.
- `ruff` security rules (`S` prefix) are enabled and enforce safe practices.
- `mypy` strict mode prevents type confusion bugs.
