#!/bin/bash
set -euo pipefail

# Resolve project root from this script's location (.claude/ -> project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
  python3 -m venv .venv >&2
fi

# Ensure package is installed (entry point must exist)
if [ ! -f ".venv/bin/dfireballz" ]; then
  .venv/bin/pip install -e . --quiet >&2
fi

# Load .env if present (for DB, API keys, etc.)
# Auth vars (ANTHROPIC_API_KEY, CLAUDE_CODE_OAUTH_TOKEN) are commented out
# by default in .env.example.  See config/.env.example for auth options.
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
  # Unset empty auth vars — an empty value forces Claude Code into
  # "API Usage Billing" mode, overriding subscription-based auth.
  if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    unset ANTHROPIC_API_KEY 2>/dev/null || true
  fi
  if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
    unset CLAUDE_CODE_OAUTH_TOKEN 2>/dev/null || true
  fi
fi

exec .venv/bin/dfireballz mcp
