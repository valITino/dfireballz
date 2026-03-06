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

# ── Configuration ───────────────────────────────────────────────────
MAX_RETRIES=20
RETRY_INTERVAL=3

# MCP servers to verify — name:container pairs.
# Each container must be running and respond to "docker exec" before
# Claude Code starts, ensuring all MCP tools are reachable.
MCP_SERVERS=(
  "kali-forensics:dfireballz-kali-forensics-1"
  "winforensics:dfireballz-winforensics-1"
  "osint:dfireballz-osint-1"
  "threat-intel:dfireballz-threat-intel-1"
  "binary-analysis:dfireballz-binary-analysis-1"
  "network-forensics:dfireballz-network-forensics-1"
  "filesystem:dfireballz-filesystem-1"
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

# Check if a container is running and healthy via docker inspect.
check_container() {
  local container="$1"
  local status
  status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null) || return 1
  [ "$status" = "running" ]
}

# Wait for a container with retries. Prints status line.
wait_for_container() {
  local name="$1"
  local container="$2"
  local retries="${3:-$MAX_RETRIES}"

  printf "  %-24s " "$name"

  for i in $(seq 1 "$retries"); do
    if check_container "$container"; then
      echo -e "[ ${CHECK} ]"
      return 0
    fi
    sleep "$RETRY_INTERVAL"
  done

  echo -e "[ ${CROSS} ] (container $container not running)"
  return 1
}

# ── Main ────────────────────────────────────────────────────────────

print_banner

echo -e "${BOLD}Verifying MCP server containers...${NC}"
echo -e "${DIM}Waiting up to $((MAX_RETRIES * RETRY_INTERVAL))s for each service.${NC}"
echo ""

OK_COUNT=0
FAIL_COUNT=0

echo -e "  ${BOLD}MCP Servers (stdio via docker exec)${NC}"
for entry in "${MCP_SERVERS[@]}"; do
  name="${entry%%:*}"
  container="${entry#*:}"
  if wait_for_container "$name" "$container"; then
    OK_COUNT=$((OK_COUNT + 1))
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
done

echo ""
echo -e "${DIM}──────────────────────────────────────────────────────${NC}"

if [ "$FAIL_COUNT" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}  All $OK_COUNT MCP servers running.${NC}"
else
  echo -e "${YELLOW}${BOLD}  $OK_COUNT/$((OK_COUNT + FAIL_COUNT)) MCP servers running. $FAIL_COUNT unreachable.${NC}"
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

exec claude "$@"
