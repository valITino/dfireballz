#!/usr/bin/env bash
set -euo pipefail

# Parse arguments
MCP_HOST="claude-code"
while [[ $# -gt 0 ]]; do
    case $1 in
        --host) MCP_HOST="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Source .env if present (avoid process substitution for portability)
if [ -f .env ]; then
    set -a
    # shellcheck source=/dev/null
    . .env
    set +a
fi

MCP_HOST=${MCP_HOST:-${MCP_HOST_ENV:-claude-code}}

echo "Generating MCP configuration for: ${MCP_HOST}"
echo ""

MCP_CONFIG='{
  "mcpServers": {
    "kali-forensics": {
      "command": "docker",
      "args": ["exec", "-i", "-e", "PYTHONUNBUFFERED=1", "dfireballz-kali-forensics-1", "python3", "-u", "/app/server.py"],
      "description": "Kali forensics: Volatility3, bulk_extractor, tshark, YARA, dc3dd, Sleuthkit, foremost, binwalk, exiftool"
    },
    "winforensics": {
      "command": "docker",
      "args": ["exec", "-i", "dfireballz-winforensics-1", "/app/winforensics-mcp/.venv/bin/python", "-m", "winforensics_mcp.server"],
      "description": "Windows artifacts: MFT, ShellBags, LNK, Registry, EVTX, Prefetch, browser history, timestomping"
    },
    "osint": {
      "command": "docker",
      "args": ["exec", "-i", "-e", "PYTHONUNBUFFERED=1", "dfireballz-osint-1", "python3", "-u", "/app/server.py"],
      "description": "OSINT: Maigret, Sherlock, Holehe, SpiderFoot, theHarvester, DNSTwist, h8mail, subfinder"
    },
    "threat-intel": {
      "command": "docker",
      "args": ["exec", "-i", "-e", "PYTHONUNBUFFERED=1", "dfireballz-threat-intel-1", "python3", "-u", "/app/server.py"],
      "description": "Threat intel: VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan"
    },
    "binary-analysis": {
      "command": "docker",
      "args": ["exec", "-i", "-e", "PYTHONUNBUFFERED=1", "dfireballz-binary-analysis-1", "python3", "-u", "/app/server.py"],
      "description": "Binary/malware: Ghidra headless, Radare2, Capa, YARA, pefile, entropy analysis"
    },
    "network-forensics": {
      "command": "docker",
      "args": ["exec", "-i", "-e", "PYTHONUNBUFFERED=1", "dfireballz-network-forensics-1", "python3", "-u", "/app/server.py"],
      "description": "Network: 18-tool Wireshark/tshark suite, tcpdump capture, PCAP split/merge/carve, threat detection"
    },
    "filesystem": {
      "command": "docker",
      "args": ["exec", "-i", "dfireballz-filesystem-1", "npx", "-y", "@modelcontextprotocol/server-filesystem", "/cases", "/evidence", "/reports"],
      "description": "Scoped evidence filesystem"
    }
  }
}'

case $MCP_HOST in
    claude-code)
        echo "$MCP_CONFIG" > .mcp.json
        echo "Written .mcp.json to project root"
        echo ""
        echo "Claude Code will auto-discover these MCP servers when opened in this directory."
        echo ""
        echo "Alternatively, run Claude Code fully containerized:"
        echo "  make claude-code"
        echo ""
        echo "The containerized version waits for all MCP servers to be healthy"
        echo "before starting.  Auth options: API key, OAuth token, or interactive login."
        echo "See config/.env.example for details."
        ;;

    claude-desktop)
        echo "$MCP_CONFIG" > .mcp.json

        # Detect OS and suggest config location
        if [[ "$OSTYPE" == "darwin"* ]]; then
            CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
        elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
            CONFIG_PATH="$APPDATA/Claude/claude_desktop_config.json"
        else
            CONFIG_PATH="$HOME/.config/claude/claude_desktop_config.json"
        fi

        echo "Written .mcp.json to project root"
        echo ""
        echo "To use with Claude Desktop, merge the contents of .mcp.json into:"
        echo "  ${CONFIG_PATH}"
        echo ""
        echo "Then restart Claude Desktop."
        ;;

    mcphost)
        MCPHOST_CONFIG='mcpServers:
  kali-forensics:
    command: docker
    args: ["exec", "-i", "-e", "PYTHONUNBUFFERED=1", "dfireballz-kali-forensics-1", "python3", "-u", "/app/server.py"]
  winforensics:
    command: docker
    args: ["exec", "-i", "dfireballz-winforensics-1", "/app/winforensics-mcp/.venv/bin/python", "-m", "winforensics_mcp.server"]
  osint:
    command: docker
    args: ["exec", "-i", "-e", "PYTHONUNBUFFERED=1", "dfireballz-osint-1", "python3", "-u", "/app/server.py"]
  threat-intel:
    command: docker
    args: ["exec", "-i", "-e", "PYTHONUNBUFFERED=1", "dfireballz-threat-intel-1", "python3", "-u", "/app/server.py"]
  binary-analysis:
    command: docker
    args: ["exec", "-i", "-e", "PYTHONUNBUFFERED=1", "dfireballz-binary-analysis-1", "python3", "-u", "/app/server.py"]
  network-forensics:
    command: docker
    args: ["exec", "-i", "-e", "PYTHONUNBUFFERED=1", "dfireballz-network-forensics-1", "python3", "-u", "/app/server.py"]
  filesystem:
    command: docker
    args: ["exec", "-i", "dfireballz-filesystem-1", "npx", "-y", "@modelcontextprotocol/server-filesystem", "/cases", "/evidence", "/reports"]'

        echo "$MCPHOST_CONFIG" > "$HOME/.mcphost.yml"
        echo "Written ~/.mcphost.yml"
        echo ""
        echo "Start MCPHost with:"
        echo "  mcphost -m ollama/qwen3:8b --config ~/.mcphost.yml"
        echo ""
        echo "Recommended models:"
        echo "  qwen3:8b    — Excellent tool calling, 8GB RAM"
        echo "  qwen3:14b   — Excellent tool calling, 16GB RAM"
        echo "  llama3.1:8b — Good tool calling, 8GB RAM"
        ;;

    open-webui)
        echo "mcpo config at config/mcpo.json is ready"
        echo ""
        echo "Start with: make start-openwebui"
        echo ""
        echo "Then open http://localhost:8080 and register MCP tools:"
        echo "  Admin Panel > Settings > External Tools"
        echo "  Add each: http://mcpo:8000/<server-name>/"
        ;;

    *)
        echo "Unknown MCP host: ${MCP_HOST}"
        echo "Valid options: claude-code, claude-desktop, mcphost, open-webui"
        exit 1
        ;;
esac
