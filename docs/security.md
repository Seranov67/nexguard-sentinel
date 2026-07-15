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
| Minimal SDK calls | Only `container.restart()` is used |
| Security block logging | All blocked restart attempts are logged as `SECURITY_BLOCK` events |
| Non-root controller | Docker socket and data access use explicit supplementary group IDs |

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

Services communicate over the default project-scoped Docker Compose network.
Published ports are explicitly bound to `127.0.0.1` and are not exposed on other host interfaces.

---

## File System

| Path | Access | Notes |
|------|--------|-------|
| `/data/gateway/gateway.yaml` | Read (simulator), Write (controller) | Config file |
| `/data/backups/` | Write (controller) | Backup files + SHA-256 checksums |
| `/var/run/docker.sock` | Read/Write (controller) | **High privilege — see above** |

On Linux, set `DOCKER_GID` to the socket group and `NEXGUARD_DATA_GID` to the bind-mounted
data group, then grant that group write access with
`chmod g+w data/backups data/gateway`. This keeps the controller non-root while allowing
atomic backup and restore writes. Backups are created as `0640`; restored configs retain
their prior mode and data-group ownership so host-side demo tools remain usable.

---

## Dependency Security

- Python dependencies use bounded major-version ranges in each service `requirements.txt`.
- `ruff` security rules (`S` prefix) are enabled and enforce safe practices.
- `mypy` strict mode prevents type confusion bugs.
