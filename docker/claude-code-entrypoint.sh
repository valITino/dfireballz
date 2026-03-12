#!/bin/bash
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

CHECK="${GREEN}OK${NC}"
CROSS="${RED}FAIL${NC}"
WARN="${YELLOW}WARN${NC}"

# ── Configuration ───────────────────────────────────────────────────
MAX_RETRIES=20
RETRY_INTERVAL=3

# MCP servers to verify — name:container:test_cmd triples.
# Each container must be running AND respond to a docker exec probe
# before Claude Code starts, ensuring all MCP tools are reachable.
MCP_SERVERS=(
  "kali-forensics:dfireballz-kali-forensics-1:python3 -c 'import fastmcp; print(\"ok\")'"
  "winforensics:dfireballz-winforensics-1:/app/winforensics-mcp/.venv/bin/python -c 'import winforensics_mcp; print(\"ok\")'"
  "osint:dfireballz-osint-1:python3 -c 'import fastmcp; print(\"ok\")'"
  "threat-intel:dfireballz-threat-intel-1:python3 -c 'import fastmcp; print(\"ok\")'"
  "binary-analysis:dfireballz-binary-analysis-1:python3 -c 'import fastmcp; print(\"ok\")'"
  "network-forensics:dfireballz-network-forensics-1:python3 -c 'import fastmcp; print(\"ok\")'"
  "filesystem:dfireballz-filesystem-1:node -e 'console.log(\"ok\")'"
)

# ── Functions ───────────────────────────────────────────────────────

print_banner() {
  echo ""
  echo -e "${CYAN}${BOLD} ╔══════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}${BOLD} ║     DFIReballz — Claude Code (containerized)    ║${NC}"
  echo -e "${CYAN}${BOLD} ║     Digital Forensics Investigation Platform     ║${NC}"
  echo -e "${CYAN}${BOLD} ╚══════════════════════════════════════════════════╝${NC}"
  echo ""
}

# Tier 1: Check container is running via docker inspect.
check_container_running() {
  local container="$1"
  local status
  status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null) || return 1
  [ "$status" = "running" ]
}

# Tier 2: Verify stdio connectivity via docker exec (like blhackbox's
# curl health probes, but adapted for stdio transport).
check_container_responsive() {
  local container="$1"
  local test_cmd="$2"
  docker exec "$container" sh -c "$test_cmd" >/dev/null 2>&1
}

# Two-tier wait: first check running, then verify exec responsiveness.
wait_for_container() {
  local name="$1"
  local container="$2"
  local test_cmd="$3"
  local retries="${4:-$MAX_RETRIES}"

  printf "  %-24s " "$name"

  # Tier 1: Wait for container to be running
  local running=false
  for i in $(seq 1 "$retries"); do
    if check_container_running "$container"; then
      running=true
      break
    fi
    sleep "$RETRY_INTERVAL"
  done

  if ! $running; then
    echo -e "[ ${CROSS} ] (container not running)"
    return 1
  fi

  # Tier 2: Verify docker exec connectivity (3 attempts)
  for attempt in 1 2 3; do
    if check_container_responsive "$container" "$test_cmd"; then
      echo -e "[ ${CHECK} ]"
      return 0
    fi
    sleep 2
  done

  # Container running but exec probe failed — still usable, warn only
  echo -e "[ ${WARN} ] (running, exec probe failed)"
  return 0
}

# ── Main ────────────────────────────────────────────────────────────

print_banner

echo -e "${BOLD}Verifying MCP server containers (two-tier check)...${NC}"
echo -e "${DIM}Tier 1: docker inspect (running?)  Tier 2: docker exec (responsive?)${NC}"
echo -e "${DIM}Waiting up to $((MAX_RETRIES * RETRY_INTERVAL))s for each service.${NC}"
echo ""

OK_COUNT=0
FAIL_COUNT=0

echo -e "  ${BOLD}MCP Servers (stdio via docker exec)${NC}"
for entry in "${MCP_SERVERS[@]}"; do
  IFS=':' read -r name container test_cmd <<< "$entry"
  if wait_for_container "$name" "$container" "$test_cmd"; then
    OK_COUNT=$((OK_COUNT + 1))
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
done

echo ""
echo -e "${DIM}──────────────────────────────────────────────────────${NC}"

if [ "$FAIL_COUNT" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}  All $OK_COUNT MCP servers verified.${NC}"
else
  echo -e "${YELLOW}${BOLD}  $OK_COUNT/$((OK_COUNT + FAIL_COUNT)) MCP servers verified. $FAIL_COUNT unreachable.${NC}"
  echo -e "${DIM}  Claude Code will start — unreachable servers show as 'failed' in /mcp.${NC}"
  echo -e "${DIM}  Use 'docker compose ps' in another terminal to check container health.${NC}"
fi

echo ""
echo -e "${DIM}──────────────────────────────────────────────────────${NC}"
echo -e "  ${BOLD}MCP servers (connected via stdio / docker exec):${NC}"
echo -e "  kali-forensics     ${DIM}Volatility3, bulk_extractor, YARA, dc3dd, Sleuthkit${NC}"
echo -e "  winforensics       ${DIM}MFT, EVTX, Registry, ShellBags, Amcache, USN Journal${NC}"
echo -e "  osint              ${DIM}Maigret, Sherlock, Holehe, SpiderFoot, theHarvester${NC}"
echo -e "  threat-intel       ${DIM}VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, URLScan${NC}"
echo -e "  binary-analysis    ${DIM}Ghidra headless, Radare2, Capa, YARA, pefile${NC}"
echo -e "  network-forensics  ${DIM}tshark (18 tools), tcpdump, PCAP carving, JA3${NC}"
echo -e "  filesystem         ${DIM}Scoped to /cases, /evidence, /reports${NC}"
echo ""
echo -e "  ${BOLD}Quick start:${NC}"
echo -e "  ${CYAN}/mcp${NC}                          ${DIM}Check MCP server status${NC}"
echo -e "  ${CYAN}Analyze the memory dump in /evidence${NC}"
echo -e "  ${CYAN}Run a full OSINT sweep on user@example.com${NC}"
echo -e "${DIM}──────────────────────────────────────────────────────${NC}"
echo ""

# ── Auth method detection ──────────────────────────────────────
# Check for persisted account login (OAuth) in the claude-config volume
HAS_ACCOUNT_AUTH=false
if [ -d "$HOME/.claude" ] && [ -n "$(find "$HOME/.claude" -name '*.json' -newer /proc/1/cmdline 2>/dev/null || find "$HOME/.claude" -name '*.json' 2>/dev/null)" ]; then
  HAS_ACCOUNT_AUTH=true
fi

# Unset ANTHROPIC_API_KEY if it's empty — an empty string causes Claude Code
# to attempt API auth (and fail) instead of falling through to OAuth login.
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  unset ANTHROPIC_API_KEY
fi

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo -e "  ${BOLD}Auth:${NC} ${GREEN}API key${NC} ${DIM}(from ANTHROPIC_API_KEY env var)${NC}"
elif $HAS_ACCOUNT_AUTH; then
  echo -e "  ${BOLD}Auth:${NC} ${GREEN}Account login${NC} ${DIM}(persisted in claude-config volume)${NC}"
else
  echo -e "  ${BOLD}Auth:${NC} ${YELLOW}Not configured${NC}"
  echo -e "  ${DIM}Claude Code will prompt you to log in via your Anthropic account.${NC}"
  echo -e "  ${DIM}Your login is persisted across restarts in the claude-config volume.${NC}"
  echo ""
  echo -e "  ${DIM}Alternatively, set ANTHROPIC_API_KEY in .env to use an API key.${NC}"
fi
echo ""

exec claude "$@"
