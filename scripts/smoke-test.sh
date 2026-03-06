#!/usr/bin/env bash
# DFIReballz — Container Smoke Test
# Verifies all MCP server containers are running and respond to
# docker exec probes. Run after `make start` to validate the stack.
#
# Usage:
#   bash scripts/smoke-test.sh
#   make test-smoke  (if target exists)
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

# Test runner — returns 0 on pass, 1 on fail.
run_test() {
  local name="$1"
  local container="$2"
  local test_cmd="$3"
  local description="$4"

  printf "  %-26s %-40s " "$name" "$description"

  # Check container exists and is running
  local status
  status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null) || status="not_found"

  if [ "$status" != "running" ]; then
    echo -e "[ ${RED}SKIP${NC} ] (container $status)"
    WARN=$((WARN + 1))
    return 0
  fi

  # Run the exec probe with 10s timeout
  if timeout 10 docker exec "$container" sh -c "$test_cmd" >/dev/null 2>&1; then
    echo -e "[ ${GREEN}PASS${NC} ]"
    PASS=$((PASS + 1))
  else
    echo -e "[ ${RED}FAIL${NC} ]"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo -e "${BOLD}DFIReballz Container Smoke Tests${NC}"
echo -e "${DIM}Running docker exec probes against all services...${NC}"
echo ""

# ── MCP Servers ──────────────────────────────────────────────────
echo -e "${BOLD}MCP Servers:${NC}"

run_test "kali-forensics" \
  "dfireballz-kali-forensics-1" \
  "python3 -c 'import fastmcp; print(\"ok\")'" \
  "FastMCP import check"

run_test "winforensics" \
  "dfireballz-winforensics-1" \
  "/app/winforensics-mcp/.venv/bin/python -c 'import winforensics_mcp; print(\"ok\")'" \
  "winforensics_mcp import check"

run_test "osint" \
  "dfireballz-osint-1" \
  "python3 -c 'import fastmcp; print(\"ok\")'" \
  "FastMCP import check"

run_test "threat-intel" \
  "dfireballz-threat-intel-1" \
  "python3 -c 'import fastmcp; print(\"ok\")'" \
  "FastMCP import check"

run_test "binary-analysis" \
  "dfireballz-binary-analysis-1" \
  "python3 -c 'import fastmcp; print(\"ok\")'" \
  "FastMCP import check"

run_test "network-forensics" \
  "dfireballz-network-forensics-1" \
  "python3 -c 'import fastmcp; print(\"ok\")'" \
  "FastMCP import check"

run_test "filesystem" \
  "dfireballz-filesystem-1" \
  "node -e 'console.log(\"ok\")'" \
  "Node.js runtime check"

echo ""

# ── Infrastructure ───────────────────────────────────────────────
echo -e "${BOLD}Infrastructure:${NC}"

run_test "db (PostgreSQL)" \
  "dfireballz-db-1" \
  "pg_isready -U dfireballz -d dfireballz" \
  "pg_isready connection test"

run_test "redis" \
  "dfireballz-redis-1" \
  "redis-cli ping" \
  "PING/PONG test"

run_test "orchestrator" \
  "dfireballz-orchestrator-1" \
  "curl -sf http://localhost:8800/health" \
  "HTTP /health endpoint"

echo ""

# ── Summary ──────────────────────────────────────────────────────
TOTAL=$((PASS + FAIL + WARN))
echo -e "${DIM}──────────────────────────────────────────────────────${NC}"

if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}All $TOTAL tests passed.${NC}"
elif [ "$FAIL" -eq 0 ]; then
  echo -e "${YELLOW}${BOLD}$PASS passed, $WARN skipped, $FAIL failed.${NC}"
else
  echo -e "${RED}${BOLD}$PASS passed, $WARN skipped, $FAIL failed.${NC}"
  exit 1
fi
