#!/usr/bin/env sh
set -eu

docker compose down
temp_file="data/gateway/.gateway.yaml.reset.tmp"
git show HEAD:data/gateway/gateway.yaml > "$temp_file"
python -c "import os; os.replace(r'$temp_file', 'data/gateway/gateway.yaml')"
rm -f data/backups/*.yaml data/backups/*.sha256
docker compose up -d --build
