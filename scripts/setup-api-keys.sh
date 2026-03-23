#!/usr/bin/env bash
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

CHECK="${GREEN}✓${NC}"
CROSS="${RED}✗${NC}"
WARN="${YELLOW}!${NC}"
DOT="${DIM}·${NC}"

# Portable sed -i
_sed_i() {
    if [[ "${OSTYPE:-linux}" == "darwin"* ]]; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}

echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║     DFIReballz — Threat Intel API Key Setup          ║${NC}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Check .env exists ────────────────────────────────────────────────
if [ ! -f .env ]; then
    echo -e "  ${CROSS} No .env file found. Run ${BOLD}make setup${NC} first."
    exit 1
fi

# ── Show current status ─────────────────────────────────────────────
echo -e "  ${BOLD}Current API Key Status:${NC}"
echo ""

KEYS_CONFIGURED=0
KEYS_TOTAL=5

_show_status() {
    local env_var="$1" label="$2"
    local val
    val=$(grep "^${env_var}=" .env 2>/dev/null | cut -d= -f2- || echo "")
    if [ -n "$val" ]; then
        # Mask the key: show first 8 chars + ****
        local masked="${val:0:8}****"
        echo -e "  ${CHECK} ${label}: ${DIM}${masked}${NC}"
        KEYS_CONFIGURED=$((KEYS_CONFIGURED + 1))
    else
        echo -e "  ${DOT} ${label}: ${DIM}not configured${NC}"
    fi
}

_show_status "VIRUSTOTAL_API_KEY" "VirusTotal"
_show_status "SHODAN_API_KEY"     "Shodan"
_show_status "ABUSEIPDB_API_KEY"  "AbuseIPDB"
_show_status "URLSCAN_API_KEY"    "URLScan.io"
_show_status "VULNCHECK_API_KEY"  "VulnCheck"

echo ""
echo -e "  ${DIM}${KEYS_CONFIGURED}/${KEYS_TOTAL} configured — press Enter to skip any key${NC}"
echo ""

# ── Prompt for each key ─────────────────────────────────────────────
CHANGED=0

_prompt_key() {
    local label="$1" env_var="$2" url="$3"
    local current
    current=$(grep "^${env_var}=" .env 2>/dev/null | cut -d= -f2- || echo "")

    if [ -n "$current" ]; then
        local masked="${current:0:8}****"
        echo -e "  ${BOLD}${label}${NC} ${DIM}(current: ${masked})${NC}"
    else
        echo -e "  ${BOLD}${label}${NC}"
    fi
    echo -e "  ${DIM}${url}${NC}"

    local prompt_text
    if [ -n "$current" ]; then
        prompt_text="  New key (Enter = keep current): "
    else
        prompt_text="  API Key (Enter = skip): "
    fi
    read -rp "$prompt_text" KEY_VALUE

    if [ -n "$KEY_VALUE" ]; then
        # Check if the env_var already exists (uncommented) in .env
        if grep -q "^${env_var}=" .env 2>/dev/null; then
            _sed_i "s|^${env_var}=.*|${env_var}=${KEY_VALUE}|" .env
        elif grep -q "^# *${env_var}=" .env 2>/dev/null; then
            # Uncomment and set
            _sed_i "s|^# *${env_var}=.*|${env_var}=${KEY_VALUE}|" .env
        else
            # Append
            echo "${env_var}=${KEY_VALUE}" >> .env
        fi
        echo -e "  ${CHECK} Saved"
        CHANGED=$((CHANGED + 1))
    else
        if [ -n "$current" ]; then
            echo -e "  ${DIM}  Kept existing${NC}"
        else
            echo -e "  ${DIM}  Skipped${NC}"
        fi
    fi
    echo ""
}

_prompt_key "VirusTotal"  "VIRUSTOTAL_API_KEY" "https://www.virustotal.com/gui/my-apikey  (free: 4 req/min)"
_prompt_key "Shodan"      "SHODAN_API_KEY"     "https://account.shodan.io/               (free: limited)"
_prompt_key "AbuseIPDB"   "ABUSEIPDB_API_KEY"  "https://www.abuseipdb.com/account/api    (free: 1000/day)"
_prompt_key "URLScan.io"  "URLSCAN_API_KEY"    "https://urlscan.io/user/signup           (free: 50/day)"
_prompt_key "VulnCheck"   "VULNCHECK_API_KEY"  "https://vulncheck.com/                   (free tier)"

# ── Restart containers if keys changed ──────────────────────────────
if [ "$CHANGED" -gt 0 ]; then
    echo -e "  ${BOLD}${CHANGED} key(s) updated.${NC}"
    echo ""

    # Check if threat-intel container is running
    if docker compose ps --status running 2>/dev/null | grep -q "threat-intel"; then
        echo -e "  ${BOLD}Restarting threat-intel container to pick up new keys...${NC}"
        docker compose restart threat-intel
        echo ""

        # Brief pause for container to become healthy
        echo -e "  ${DIM}Waiting for container to become healthy...${NC}"
        sleep 3

        # ── Validate keys ────────────────────────────────────────
        echo ""
        echo -e "  ${BOLD}Validating API keys...${NC}"
        echo ""

        _validate_key() {
            local label="$1" env_var="$2" test_cmd="$3"
            local val
            val=$(grep "^${env_var}=" .env 2>/dev/null | cut -d= -f2- || echo "")
            if [ -z "$val" ]; then
                echo -e "  ${DOT} ${label}: ${DIM}not configured — skipped${NC}"
                return
            fi
            # Run the test command inside the threat-intel container
            local result
            result=$(docker exec dfireballz-threat-intel-1 python3 -c "$test_cmd" 2>&1) || true
            if echo "$result" | grep -qi "error\|fail\|unauthorized\|forbidden\|invalid"; then
                echo -e "  ${CROSS} ${label}: ${RED}key may be invalid${NC}"
                echo -e "     ${DIM}${result:0:120}${NC}"
            else
                echo -e "  ${CHECK} ${label}: ${GREEN}connected${NC}"
            fi
        }

        _validate_key "VirusTotal" "VIRUSTOTAL_API_KEY" \
            "import os,requests; r=requests.get('https://www.virustotal.com/api/v3/users/me',headers={'x-apikey':os.environ.get('VIRUSTOTAL_API_KEY','')},timeout=10); print('OK' if r.status_code==200 else f'HTTP {r.status_code}')"

        _validate_key "Shodan" "SHODAN_API_KEY" \
            "import os,requests; r=requests.get('https://api.shodan.io/api-info',params={'key':os.environ.get('SHODAN_API_KEY','')},timeout=10); print('OK' if r.status_code==200 else f'HTTP {r.status_code}')"

        _validate_key "AbuseIPDB" "ABUSEIPDB_API_KEY" \
            "import os,requests; r=requests.get('https://api.abuseipdb.com/api/v2/check',headers={'Key':os.environ.get('ABUSEIPDB_API_KEY',''),'Accept':'application/json'},params={'ipAddress':'8.8.8.8','maxAgeInDays':'1'},timeout=10); print('OK' if r.status_code==200 else f'HTTP {r.status_code}')"

        _validate_key "URLScan.io" "URLSCAN_API_KEY" \
            "import os,requests; r=requests.get('https://urlscan.io/user/quotas/',headers={'API-Key':os.environ.get('URLSCAN_API_KEY','')},timeout=10); print('OK' if r.status_code==200 else f'HTTP {r.status_code}')"

        echo ""
    else
        echo -e "  ${WARN} threat-intel container is not running."
        echo -e "  ${DIM}  Keys are saved in .env — they'll be used on next ${BOLD}make start${NC}"
        echo ""
    fi
else
    echo -e "  ${DIM}No changes made.${NC}"
    echo ""
fi

echo -e "${GREEN}${BOLD}  Done!${NC}"
echo ""
