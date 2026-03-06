#!/usr/bin/env bash
# DFIReballz — MCP Server Pre-Flight Health Check
# Verifies all MCP server containers are running and responsive.
#
# Usage:
#   bash .claude/mcp-health-check.sh           # Full diagnostic output
#   bash .claude/mcp-health-check.sh --quiet   # Summary only
#   bash .claude/mcp-health-check.sh --fix     # Auto-start stopped containers
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
QUIET=false
FIX=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --quiet) QUIET=true; shift ;;
    --fix)   FIX=true; shift ;;
    *)       shift ;;
  esac
done

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# MCP server containers to check
CONTAINERS=(
  "kali-forensics:dfireballz-kali-forensics-1"
  "winforensics:dfireballz-winforensics-1"
  "osint:dfireballz-osint-1"
  "threat-intel:dfireballz-threat-intel-1"
  "binary-analysis:dfireballz-binary-analysis-1"
  "network-forensics:dfireballz-network-forensics-1"
  "filesystem:dfireballz-filesystem-1"
)

OK=0
WARN=0
FAIL=0

check_container() {
  local name="$1"
  local container="$2"

  local status health
  status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null) || status="not_found"
  health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no_healthcheck{{end}}' "$container" 2>/dev/null) || health="unknown"

  if [ "$status" = "running" ] && [ "$health" = "healthy" ]; then
    $QUIET || printf "  %-22s ${GREEN}healthy${NC}\n" "$name"
    OK=$((OK + 1))
    return 0
  elif [ "$status" = "running" ]; then
    $QUIET || printf "  %-22s ${YELLOW}running (health: %s)${NC}\n" "$name" "$health"
    WARN=$((WARN + 1))
    return 0
  elif [ "$status" = "not_found" ]; then
    $QUIET || printf "  %-22s ${RED}not found${NC}\n" "$name"
    FAIL=$((FAIL + 1))
    return 1
  else
    $QUIET || printf "  %-22s ${RED}%s${NC}\n" "$name" "$status"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

# ── Check Docker prerequisites ────────────────────────────────────
if ! docker info &>/dev/null 2>&1; then
  echo -e "${RED}Docker daemon is not running.${NC}"
  exit 1
fi

# ── Check .mcp.json ───────────────────────────────────────────────
if [ -f "$PROJECT_DIR/.mcp.json" ]; then
  SERVER_COUNT=$(python3 -c "import json; print(len(json.load(open('$PROJECT_DIR/.mcp.json')).get('mcpServers', {})))" 2>/dev/null || echo "?")
  $QUIET || echo -e "${DIM}.mcp.json found — $SERVER_COUNT servers configured${NC}"
else
  echo -e "${YELLOW}.mcp.json not found — run: make configure-mcp${NC}"
fi

# ── Check each container ─────────────────────────────────────────
$QUIET || echo ""
$QUIET || echo -e "${BOLD}MCP Server Status:${NC}"

for entry in "${CONTAINERS[@]}"; do
  name="${entry%%:*}"
  container="${entry#*:}"
  check_container "$name" "$container" || true
done

# ── Summary ──────────────────────────────────────────────────────
TOTAL=$((OK + WARN + FAIL))

if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}All $TOTAL MCP servers reachable.${NC}"
elif $FIX; then
  echo ""
  echo -e "${YELLOW}Attempting to start missing containers...${NC}"
  cd "$PROJECT_DIR"
  docker compose up -d 2>/dev/null || true
  echo -e "${DIM}Containers starting. Re-run this check in ~30s.${NC}"
else
  echo ""
  echo -e "${YELLOW}$OK/$TOTAL healthy, $FAIL unreachable.${NC}"
  echo -e "${DIM}Start the stack: make start${NC}"
  echo -e "${DIM}Auto-fix: bash .claude/mcp-health-check.sh --fix${NC}"
fi
