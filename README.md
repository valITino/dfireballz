```
    ____  ____________  ______  __    __
   / __ \/ ____/  _/ / / / __ )/ /   / /
  / / / / /_   / // /_/ / __  / /   / /
 / /_/ / __/ _/ // __  / /_/ / /___/ /___
/_____/_/   /___/_/ /_/_____/_____/_____/
                                     ______
    DFIReballz                      |______|
```

# DFIReballz — Digital Forensics & Cybercrime Investigation Platform

A fully containerized, AI-native forensic investigation platform that orchestrates MCP (Model Context Protocol) servers for structured, reproducible, legally defensible investigations.

---

## What is DFIReballz?

DFIReballz is a **digital forensics and cybercrime investigation** platform built for:

- **Malware reverse engineering** — Static analysis, decompilation, YARA matching, MITRE ATT&CK mapping
- **OSINT investigations** — Username/email tracing, domain recon, dark web correlation
- **Network forensics** — PCAP analysis, C2 detection, DNS tunneling identification
- **Windows artifact analysis** — MFT, Registry, EVTX, Prefetch, browser history
- **Memory forensics** — Volatility3 analysis of Windows and Linux memory dumps
- **Threat intelligence** — VirusTotal, Shodan, AbuseIPDB, MalwareBazaar enrichment
- **Chain of custody** — Immutable audit trail for every evidence interaction

This is **not** a pentesting tool. It is a professional forensic platform designed to produce court-admissible evidence.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI Host (Choose One)                   │
│  Claude Code │ Claude Desktop │ MCPHost+Ollama │ OpenWebUI│
└──────┬───────┴───────┬────────┴───────┬────────┴────┬────┘
       │ docker exec -i│                │             │
       ▼               ▼                ▼             ▼
┌──────────────────────────────────────────────────────────┐
│                   MCP Servers (stdio)                     │
│ ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐ │
│ │kali-forensics│ │ winforensics │ │      osint         │ │
│ │Volatility3   │ │MFT, Registry │ │Maigret, Sherlock   │ │
│ │tshark, YARA  │ │EVTX, Prefetch│ │Holehe, theHarvester│ │
│ └──────────────┘ └──────────────┘ └────────────────────┘ │
│ ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐ │
│ │ threat-intel │ │binary-analysis│ │ network-forensics  │ │
│ │VT, Shodan    │ │Ghidra, r2    │ │18 Wireshark tools  │ │
│ │AbuseIPDB     │ │Capa, YARA    │ │tcpdump, PCAP carve │ │
│ └──────────────┘ └──────────────┘ └────────────────────┘ │
│ ┌──────────────┐                                         │
│ │ filesystem   │  All containers on dfireballz-net       │
│ │/cases /evidence│ Evidence volumes: READ-ONLY           │
│ └──────────────┘                                         │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│              Infrastructure                               │
│ ┌──────────────┐ ┌──────────┐ ┌────────┐ ┌────────────┐ │
│ │ Orchestrator │ │    UI    │ │ Postgres│ │   Redis    │ │
│ │  FastAPI     │ │  React   │ │pgcrypto │ │  Cache     │ │
│ │  :8800       │ │  :3000   │ │  :5432  │ │  :6379     │ │
│ └──────────────┘ └──────────┘ └────────┘ └────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- **Docker** 25+ with Docker Compose v2
- **RAM:** 16GB minimum (8GB absolute minimum, limited functionality)
- **Disk:** 50GB+ recommended (Docker images are large)
- **Optional:** NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) for GPU-accelerated inference

```bash
# Verify prerequisites
bash scripts/check-requirements.sh
```

---

## Quick Start

```bash
git clone https://github.com/crhacky/dfireballz.git
cd dfireballz
make setup    # Interactive setup wizard
make start    # Start all services
```

Dashboard: http://localhost:3000 | API: http://localhost:8800

---

## Installation Guide

### Scenario A: Claude Code as MCP Host (host-installed)

1. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
2. Start DFIReballz:
   ```bash
   make setup
   make start
   make configure-mcp  # Generates .mcp.json
   ```
3. Open Claude Code in the DFIReballz directory — all MCP tools auto-discovered
4. The SessionStart hook (`.claude/hooks/session-start.sh`) automatically verifies Docker stack health
5. Start investigating:
   ```
   > Analyze the malware sample at /evidence/sample.exe — run static analysis,
     extract strings, check YARA rules, and look up the hash on VirusTotal.
   ```

### Scenario A2: Claude Code Containerized (no host install needed)

Run Claude Code entirely inside Docker — no local Node.js or Claude Code installation required.

1. Start DFIReballz:
   ```bash
   make setup
   make start
   ```
2. Launch containerized Claude Code:
   ```bash
   make claude-code    # Requires ANTHROPIC_API_KEY in .env
   ```
3. The entrypoint verifies all 7 MCP servers are healthy (two-tier check: running + responsive) before launching the Claude CLI
4. All MCP tools are pre-configured via stdio over `docker exec -i`

The containerized Claude Code container includes:
- `tini` for proper signal handling (clean `docker stop`)
- DNS configuration for reliable Anthropic API access
- `CLAUDE.md` mounted read-only at `/workspace` for project context
- Evidence mounted read-only for chain-of-custody compliance

### Scenario B: Claude Desktop as MCP Host

1. Install [Claude Desktop](https://claude.ai/desktop)
2. Start DFIReballz:
   ```bash
   make setup
   make start
   make configure-mcp MCP_HOST=claude-desktop
   ```
3. Merge generated config into Claude Desktop's config file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
4. Restart Claude Desktop

### Scenario C: MCPHost + Ollama as MCP Host

> **Important:** Ollama has NO native MCP support. MCPHost is the required bridge.

1. Install Ollama and MCPHost:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   go install github.com/mark3labs/mcphost@latest
   ```
2. Pull a model with tool calling support:
   ```bash
   ollama pull qwen3:8b
   ```
3. Start DFIReballz:
   ```bash
   make setup
   make start
   make configure-mcp MCP_HOST=mcphost
   ```
4. Launch MCPHost:
   ```bash
   mcphost -m ollama/qwen3:8b --config ~/.mcphost.yml
   ```

#### Model Selection Guide

| Model | RAM | GPU VRAM | Tool Calling | Notes |
|-------|-----|----------|--------------|-------|
| `qwen3:8b` | 8GB | 6GB | Excellent | **Recommended default** |
| `qwen3:14b` | 16GB | 12GB | Excellent | Better reasoning |
| `qwen2.5:14b` | 16GB | 12GB | Excellent | Great for analysis |
| `llama3.1:8b` | 8GB | 8GB | Good | Widely tested |
| `llama3.3:70b` | 48GB+ | 40GB+ | Excellent | Best quality, high-end hardware |
| `llama3.2:3b` | 4GB | 4GB | Limited | Minimal hardware |

Verify tool calling: `ollama show <model> | grep capabilities`

### Scenario D: Open WebUI + Ollama

1. Start everything:
   ```bash
   make setup
   make start-openwebui
   ```
2. Open http://localhost:8080
3. Go to **Admin Panel > Settings > External Tools**
4. Register each MCP server:
   - `http://mcpo:8000/kali-forensics/`
   - `http://mcpo:8000/osint/`
   - `http://mcpo:8000/threat-intel/`
   - etc.
5. Select your Ollama model and start chatting

---

## Playbooks

| Playbook | Description |
|----------|-------------|
| `malware-analysis` | Complete static analysis of malware samples |
| `osint-person-investigation` | Person investigation via username/email tracing |
| `osint-domain-investigation` | Domain/website reconnaissance |
| `ransomware-investigation` | Ransomware artifact analysis and C2 detection |
| `phishing-investigation` | Phishing email/infrastructure investigation |
| `network-forensics` | PCAP analysis with threat detection |
| `dark-web-trace` | Dark web IOC tracing and correlation |
| `mobile-artifact-analysis` | Mobile device forensics |
| `chain-of-custody` | Evidence handling documentation template |

---

## MCP Servers Reference

| Server | Tools | Source |
|--------|-------|--------|
| **kali-forensics** | Volatility3, bulk_extractor, tshark, YARA, dc3dd, Sleuthkit, foremost, binwalk, exiftool | Custom |
| **winforensics** | MFT, ShellBags, LNK, Registry, EVTX, Prefetch, browser history, Chainsaw | [x746b/winforensics-mcp](https://github.com/x746b/winforensics-mcp) |
| **osint** | Maigret, Sherlock, Holehe, theHarvester, DNSTwist, subfinder, amass, h8mail | Custom |
| **threat-intel** | VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan, NVD | Custom |
| **binary-analysis** | Ghidra headless, Radare2, Capa, YARA, pefile, lief, entropy analysis | Adapted from [FuzzingLabs](https://github.com/FuzzingLabs/mcp-security-hub) |
| **network-forensics** | 18 Wireshark/tshark tools, tcpdump, PCAP merge/split/carve | Adapted from [PreistlyPython](https://github.com/PreistlyPython/wireshark-mcp) |
| **filesystem** | Scoped file access (/cases, /evidence, /reports) | [@modelcontextprotocol/server-filesystem](https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem) |

---

## API Keys Setup

| Service | Free Tier | Get Key |
|---------|-----------|---------|
| VirusTotal | 4 req/min | https://www.virustotal.com/gui/my-apikey |
| Shodan | Limited queries | https://account.shodan.io/ |
| AbuseIPDB | 1000 req/day | https://www.abuseipdb.com/account/api |
| URLScan.io | 50 scans/day | https://urlscan.io/user/signup |
| VulnCheck | Free tier | https://vulncheck.com/ |

API keys are stored encrypted in PostgreSQL (pgcrypto). Set them during `make setup` or in the Settings page.

---

## Development

```bash
make dev              # Start with hot-reload
make test             # Run unit tests
make test-security    # Trivy + Bandit scan
make mcp-health-check # Check MCP server container health
make shell-kali       # Shell into Kali container
make shell-osint      # Shell into OSINT container
```

### Claude Code SessionStart Hook

When Claude Code opens this project on the host, the `.claude/hooks/session-start.sh` hook runs automatically:
- Checks Docker daemon is running
- Ensures `.env` and `.mcp.json` exist (creates them if missing)
- Runs the MCP health check to verify all 7 containers are responsive

The health check script supports three modes:
```bash
bash .claude/mcp-health-check.sh           # Full diagnostic output
bash .claude/mcp-health-check.sh --quiet   # Summary only
bash .claude/mcp-health-check.sh --fix     # Auto-start stopped containers
```

---

## Chain of Custody

Every evidence interaction is logged in the immutable `chain_of_custody_log` table:

- **Acquired** — Evidence uploaded, hashes computed
- **Accessed** — Evidence file read by any tool
- **Analyzed** — MCP tool invocation against evidence
- **Exported** — Report generation or evidence transfer
- **Transferred** — Evidence moved between systems

Database triggers prevent UPDATE and DELETE on CoC records, ensuring forensic integrity.

---

## CI/CD Pipeline

| Workflow | Trigger | Actions |
|----------|---------|---------|
| **CI** | Push/PR to main/develop | Lint, type check, unit tests, Bandit, Docker build, Trivy scan |
| **Docker Build & Push** | Version tag (v*.*.*) | Build multi-arch, push to `crhacky/dfireballz` |
| **CodeQL** | Push/PR to main + weekly | Static security analysis |
| **Dependabot** | Weekly | Auto-update pip, npm, Docker, GitHub Actions dependencies |

---

## Docker Hub

```bash
docker pull crhacky/dfireballz:latest
docker pull crhacky/dfireballz:v1.0.0
```

---

## Legal Notice

DFIReballz is designed for **authorized cybercrime investigation and digital forensics** use only. Users must comply with all applicable laws and regulations. The developers assume no liability for misuse.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## License

[MIT](LICENSE)
