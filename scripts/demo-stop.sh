#!/usr/bin/env sh
set -eu

docker compose stop gateway-simulator
echo "Gateway simulator stopped; NexGuard should open an incident after three failed checks."
