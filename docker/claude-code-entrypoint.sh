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

# ── Auth guard ─────────────────────────────────────────────────────
# An empty ANTHROPIC_API_KEY forces Claude Code into "API Usage Billing"
# mode, overriding subscription-based auth.  Unset it if blank so
# Claude Code falls back to interactive login or CLAUDE_CODE_OAUTH_TOKEN.
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  unset ANTHROPIC_API_KEY 2>/dev/null || true
fi
if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  unset CLAUDE_CODE_OAUTH_TOKEN 2>/dev/null || true
fi

# ── Configuration ───────────────────────────────────────────────────
MAX_RETRIES=20
RETRY_INTERVAL=3

# Bypass proxy for internal Docker hostnames
export no_proxy="kali-forensics,winforensics,osint,threat-intel,binary-analysis,network-forensics,filesystem,db,redis,orchestrator,ollama,mcpo,open-webui,localhost,127.0.0.1"
export NO_PROXY="$no_proxy"

# MCP servers to verify — name:container:test_cmd triples.
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

check_service() {
  local container="$1"
  local test_cmd="$2"
  docker exec "$container" sh -c "$test_cmd" >/dev/null 2>&1
}

wait_for_service() {
  local name="$1"
  local container="$2"
  local test_cmd="$3"
  local optional="${4:-false}"

  printf "  %-24s " "$name"

  for i in $(seq 1 "$MAX_RETRIES"); do
    if check_service "$container" "$test_cmd"; then
      echo -e "[ ${CHECK} ]"
      return 0
    fi
    sleep "$RETRY_INTERVAL"
  done

  if [ "$optional" = "true" ]; then
    echo -e "[ ${WARN} ] (optional — skipped)"
  else
    echo -e "[ ${CROSS} ]"
  fi
  return 1
}

# ── Main ────────────────────────────────────────────────────────────

print_banner

# Show auth mode so the user knows what's happening
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo -e "  ${BOLD}Auth:${NC} API key ${DIM}(pay-per-use billing)${NC}"
elif [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  echo -e "  ${BOLD}Auth:${NC} OAuth token ${DIM}(subscription)${NC}"
else
  echo -e "  ${BOLD}Auth:${NC} Interactive login ${DIM}(will prompt on first use)${NC}"
  echo -e "  ${DIM}Credentials persist in the claude-config volume across restarts.${NC}"
fi
echo ""

echo -e "${BOLD}Checking MCP server containers (via docker exec)...${NC}"
echo -e "${DIM}Waiting up to $((MAX_RETRIES * RETRY_INTERVAL))s per service.${NC}"
echo ""

OK_COUNT=0
FAIL_COUNT=0

echo -e "  ${BOLD}MCP Servers (stdio via docker exec)${NC}"
for entry in "${MCP_SERVERS[@]}"; do
  IFS=':' read -r name container test_cmd <<< "$entry"
  if wait_for_service "$name" "$container" "$test_cmd"; then
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
echo -e "  ${CYAN}Analyze the memory dump in evidence/${NC}"
echo -e "  ${CYAN}Run a full OSINT sweep on user@example.com${NC}"
echo -e "${DIM}──────────────────────────────────────────────────────${NC}"
echo ""

exec claude "$@"
