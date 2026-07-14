#!/usr/bin/env sh
set -eu

attempt=0
while [ "$attempt" -lt 60 ]; do
  if curl -sf http://localhost:8080/health >/dev/null; then
    echo "NexGuard demo verification: PASS"
    docker compose logs --tail=100 nexguard-controller
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep 1
done

echo "NexGuard demo verification: FAIL" >&2
docker compose logs --tail=100 nexguard-controller >&2
exit 1
