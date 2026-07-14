#!/usr/bin/env sh
set -eu

printf '%s\n' 'bad: [unclosed' > data/gateway/gateway.yaml
echo "Gateway config corrupted; NexGuard should restore the latest verified backup."
