#!/bin/zsh
set -euo pipefail

secrets_file="${LOCAL_AI_SECRETS:-$HOME/Documents/AI/Local-AI/.secrets}"

if [[ -f "$secrets_file" ]]; then
  set -a
  source "$secrets_file"
  set +a
fi

exec "$@"
