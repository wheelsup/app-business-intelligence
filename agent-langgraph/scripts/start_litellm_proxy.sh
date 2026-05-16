#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${LITELLM_HOST:=0.0.0.0}"
: "${LITELLM_PORT:=4500}"

if [[ -f ".env.litellm" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env.litellm"
  set +a
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY is required. Create agent-langgraph/.env.litellm from .env.litellm.example or export it in your shell." >&2
  exit 1
fi

if [[ -z "${LITELLM_MASTER_KEY:-}" ]]; then
  echo "LITELLM_MASTER_KEY is required. Create agent-langgraph/.env.litellm from .env.litellm.example or export it in your shell." >&2
  exit 1
fi

exec uvx 'litellm[proxy]' \
  --config litellm_config.yaml \
  --host "$LITELLM_HOST" \
  --port "$LITELLM_PORT"
