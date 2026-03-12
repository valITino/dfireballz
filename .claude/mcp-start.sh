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
# API keys (ANTHROPIC_API_KEY) are intentionally commented out in .env.example
# — Claude Code provides its own authentication via OAuth.
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
  # Unset ANTHROPIC_API_KEY if empty — an empty value can force Claude Code
  # into "API Usage Billing" mode, overriding account-based authentication.
  if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    unset ANTHROPIC_API_KEY 2>/dev/null || true
  fi
fi

exec .venv/bin/dfireballz mcp
