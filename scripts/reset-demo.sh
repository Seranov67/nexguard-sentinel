#!/usr/bin/env sh
set -eu

docker compose down
temp_file="data/gateway/.gateway.yaml.reset.tmp"
git show HEAD:data/gateway/gateway.yaml > "$temp_file"
python3 -c "import os; os.replace(r'$temp_file', 'data/gateway/gateway.yaml')"
rm -f data/backups/*.yaml data/backups/*.sha256
docker compose up -d --build gateway-simulator nexguard-controller

attempt=0
while [ "$attempt" -lt 60 ]; do
  if curl -sf http://localhost:8080/health >/dev/null \
    && find data/backups -maxdepth 1 -name 'gateway-*.yaml' -print -quit | grep -q .; then
    echo "Demo reset complete; gateway is healthy and an initial backup exists."
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep 1
done

echo "Demo reset failed: healthy gateway/initial backup not ready" >&2
exit 1
