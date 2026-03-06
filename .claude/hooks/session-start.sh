#!/usr/bin/env bash
# DFIReballz — Claude Code SessionStart hook
# Runs automatically when Claude Code opens this project on the host.
# Verifies the Docker stack is running and MCP servers are reachable.
set -euo pipefail

# Skip when running inside the containerized Claude Code
if [ "${DFIREBALLZ_CONTAINER:-}" = "1" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}DFIReballz — Session Start${NC}"
echo -e "${DIM}Checking Docker stack and MCP server health...${NC}"
echo ""

# ── Check Docker is running ──────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo -e "${YELLOW}Docker CLI not found. MCP servers require Docker.${NC}"
  echo -e "${DIM}Install Docker: https://docs.docker.com/get-docker/${NC}"
  exit 0
fi

if ! docker info &>/dev/null 2>&1; then
  echo -e "${YELLOW}Docker daemon not running. Start Docker first.${NC}"
  exit 0
fi

# ── Check .env exists ────────────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/.env" ]; then
  if [ -f "$PROJECT_DIR/config/.env.example" ]; then
    echo -e "${YELLOW}.env not found. Copying from config/.env.example${NC}"
    cp "$PROJECT_DIR/config/.env.example" "$PROJECT_DIR/.env"
    echo -e "${DIM}Edit .env to add your API keys, then run: make setup${NC}"
  else
    echo -e "${YELLOW}.env not found. Run: make setup${NC}"
  fi
fi

# ── Check .mcp.json exists ──────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/.mcp.json" ]; then
  echo -e "${YELLOW}.mcp.json not found. Generating...${NC}"
  bash "$PROJECT_DIR/scripts/configure_mcp.sh" --host claude-code 2>/dev/null || true
fi

# ── Run MCP health check ────────────────────────────────────────────
if [ -f "$PROJECT_DIR/.claude/mcp-health-check.sh" ]; then
  bash "$PROJECT_DIR/.claude/mcp-health-check.sh" --quiet
else
  echo -e "${DIM}MCP health check script not found, skipping.${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}Session ready.${NC} Run ${CYAN}make start${NC} if services aren't running."
echo ""
