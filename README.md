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

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**MCP-based AI-native forensic investigation framework — everything runs in Docker.**

> This is **not** a pentesting tool. It is a professional forensic platform designed to produce court-admissible evidence.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Components](#components)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Tutorial 1: Claude Code (Docker) — Recommended](#tutorial-1-claude-code-docker--recommended)
- [Tutorial 2: Claude Code (Host-Installed)](#tutorial-2-claude-code-host-installed)
- [Tutorial 3: Claude Desktop](#tutorial-3-claude-desktop)
- [Tutorial 4: MCPHost + Ollama](#tutorial-4-mcphost--ollama)
- [Tutorial 5: Open WebUI + Ollama](#tutorial-5-open-webui--ollama)
- [How Prompts Flow Through the System](#how-prompts-flow-through-the-system)
- [MCP Servers Reference](#mcp-servers-reference)
- [Investigation Playbooks](#investigation-playbooks)
- [Report Export](#report-export)
- [API Keys Setup](#api-keys-setup)
- [Troubleshooting](#troubleshooting)
- [Makefile Shortcuts](#makefile-shortcuts)
- [Chain of Custody](#chain-of-custody)
- [Project Structure](#project-structure)
- [Security Notes](#security-notes)
- [License](#license)

---

## How It Works

Your AI client (Claude Code, Claude Desktop, or MCPHost+Ollama) **is the orchestrator**. The workflow:

1. **You input a prompt** in your AI client (e.g. "Analyze the malware sample at /evidence/sample.exe").
2. **The AI selects tools** from 7 MCP servers: Kali forensics, Windows forensics, OSINT, threat-intel, binary analysis, network forensics, and filesystem.
3. **Each MCP server executes the tool** inside its Docker container via `docker exec -i` (stdio transport) and returns results to the AI.
4. **The AI structures the results** — correlating findings, building timelines, mapping MITRE ATT&CK techniques.
5. **The AI writes the forensic report** with chain of custody maintained throughout.

Everything runs inside Docker containers. No forensic tools are installed on your host machine.

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
│ ┌──────────────┐ ┌─────────┐ ┌────────────┐              │
│ │ Orchestrator │ │ Postgres│ │   Redis    │              │
│ │  FastAPI     │ │pgcrypto │ │  Cache     │              │
│ │  :8800       │ │  :5432  │ │  :6379     │              │
│ └──────────────┘ └─────────┘ └────────────┘              │
└──────────────────────────────────────────────────────────┘
```

**Transport: stdio only.** Every MCP server runs `mcp.run(transport="stdio")`. The AI host connects via `docker exec -i <container> <command>`. No HTTP ports, no proxy, no gateway for direct AI connections.

---

## Components

| Container | What it does | Exposed Port | Profile |
|-----------|-------------|:---:|:---:|
| **kali-forensics** | Volatility3, bulk_extractor, YARA, dc3dd, Sleuthkit, foremost, exiftool | — | default |
| **winforensics** | MFT, ShellBags, LNK, Registry, EVTX, Prefetch, Chainsaw | — | default |
| **osint** | Maigret, Sherlock, Holehe, theHarvester, DNSTwist, subfinder | — | default |
| **threat-intel** | VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan | — | default |
| **binary-analysis** | Ghidra headless, Radare2, Capa (MITRE ATT&CK), YARA, pefile, binwalk | — | default |
| **network-forensics** | 18 Wireshark/tshark tools, tcpdump, PCAP merge/split/carve, JA3/JA3S | — | default |
| **filesystem** | Scoped file access to /cases, /evidence (read-only), /reports | — | default |
| **orchestrator** | FastAPI backend — cases, evidence, playbooks, chain of custody | 8800 | default |
| **db** | PostgreSQL with pgcrypto (encrypted API key storage) | — | default |
| **redis** | Redis cache | — | default |
| **claude-code** | Anthropic CLI client in Docker (no host install needed) | — | `claude-code` |
| **ollama** | Local LLM inference (Open WebUI scenario) | 11434 | `openwebui` |
| **open-webui** | Web UI for Ollama models | 8080 | `openwebui` |
| **mcpo** | MCP-to-OpenAPI bridge for Open WebUI | 8812 | `openwebui` |

---

## Prerequisites

- **Docker** 25+ with Docker Compose v2
- **RAM:** 16 GB recommended (8 GB absolute minimum, limited functionality)
- **Disk:** 50 GB+ recommended (Docker images are large)
- **Docker GID:** The orchestrator and Claude Code containers need access to `/var/run/docker.sock`. Verify your Docker group ID matches `DOCKER_GID` in `.env` (default 999). Run `getent group docker | cut -d: -f3` to check.
- **Optional:** NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) for GPU-accelerated inference with Ollama

### Required Accounts (Free Tiers Available)

The threat intelligence tools require API keys. **Create accounts before running setup** so you have your keys ready:

| Service | What It Does | Free Tier | Sign Up |
|---------|-------------|-----------|---------|
| **VirusTotal** | File/hash/URL reputation lookups | 4 req/min | [virustotal.com/gui/my-apikey](https://www.virustotal.com/gui/my-apikey) |
| **Shodan** | Internet-connected device search | Limited queries | [account.shodan.io](https://account.shodan.io/) |
| **AbuseIPDB** | IP address reputation checks | 1,000 req/day | [abuseipdb.com/account/api](https://www.abuseipdb.com/account/api) |
| **URLScan.io** | URL scanning and analysis | 50 scans/day | [urlscan.io/user/signup](https://urlscan.io/user/signup) |
| **VulnCheck** | Vulnerability intelligence | Free tier | [vulncheck.com](https://vulncheck.com/) |

> **Using Claude Code in Docker?** You also need an **Anthropic API key**: [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

```bash
# Verify prerequisites
bash scripts/check-requirements.sh
```

---

## Installation

All images are pre-built and published on [Docker Hub](https://hub.docker.com/r/crhacky/dfireballz). **No local building required.**

```bash
# 1. Clone the repo
git clone https://github.com/valITino/dfireballz.git
cd dfireballz

# 2. Run interactive setup (generates .env, pulls images, configures MCP — all in one)
make setup

# 3. Start all services (10 containers)
make start
```

That's it. The setup wizard will:
1. Generate `.env` with secure random secrets
2. Ask you to choose your AI host (Claude Code, Claude Desktop, MCPHost, or Open WebUI)
3. Collect your API keys (VirusTotal, Shodan, AbuseIPDB, URLScan.io)
4. Pull all pre-built Docker images from Docker Hub
5. Auto-generate the MCP configuration for your chosen host

> **Want to build from source instead?** Run `make build` before `make start`.
> This is only needed if you've modified Dockerfiles or server code locally.

**Verify everything is running:**

```bash
make status     # Container status table
make health     # MCP server health check
```

You should see 10 containers running:
- 7 MCP servers (kali-forensics, winforensics, osint, threat-intel, binary-analysis, network-forensics, filesystem)
- 3 infrastructure services (orchestrator, db, redis)

**Orchestrator API:** http://localhost:8800

---

## Tutorial 1: Claude Code (Docker) — Recommended

Run Claude Code entirely inside Docker — no local Node.js or Claude Code installation required. The container connects directly to all MCP servers on the internal Docker network.

### Step 1: Start the stack

Follow [Installation](#installation) above. Make sure `ANTHROPIC_API_KEY` is set in your `.env` file. All core containers must be healthy (`make health`).

### Step 2: Launch Claude Code

```bash
make claude-code
```

Or manually:

```bash
docker compose --profile claude-code run --rm claude-code
```

The entrypoint script checks each MCP server (two-tier: running + responsive) and shows status before launching the Claude CLI.

### Step 3: Run your first investigation

```
Analyze the malware sample at /evidence/sample.exe — run static analysis,
extract strings, check YARA rules, and look up the hash on VirusTotal.
```

Claude Code will autonomously:
1. Call binary-analysis tools (Ghidra, Radare2, Capa, YARA)
2. Extract metadata with kali-forensics (exiftool, strings, binwalk)
3. Look up the hash via threat-intel (VirusTotal, MalwareBazaar)
4. Correlate findings and map to MITRE ATT&CK techniques
5. Write a forensic report with full chain of custody

### What's in the container

- DNS configured for reliable Anthropic API access
- Docker CLI for stdio transport to MCP containers via `docker exec`
- Evidence mounted read-only for chain-of-custody compliance
- Reports and results exported to host via bind mounts

### Monitoring (separate terminal)

```bash
make log-kali              # Kali forensics activity
make log-binary            # Binary analysis activity
make log-threat            # Threat-intel lookups
make log-orchestrator      # Orchestrator API activity
```

---

## Tutorial 2: Claude Code (Host-Installed)

If you already have Claude Code installed on your host machine:

### Step 1: Start the stack

```bash
make setup      # Setup wizard — generates .env, pulls images, auto-generates .mcp.json
make start      # Start all containers (also regenerates .mcp.json)
```

### Step 2: Open Claude Code

Open Claude Code in the DFIReballz directory. All MCP tools are auto-discovered from `.mcp.json` (generated automatically during setup). The SessionStart hook (`.claude/hooks/session-start.sh`) automatically verifies Docker stack health.

### Step 3: Investigate

```
> Analyze the malware sample at /evidence/sample.exe — run static analysis,
  extract strings, check YARA rules, and look up the hash on VirusTotal.
```

---

## Tutorial 3: Claude Desktop

### Step 1: Start the stack

```bash
make setup      # Select "Claude Desktop" when prompted for MCP host
make start
```

> If you already ran setup with a different host, regenerate: `make configure-mcp MCP_HOST=claude-desktop`

### Step 2: Configure Claude Desktop

Merge the generated config into Claude Desktop's config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

### Step 3: Restart Claude Desktop

Restart the app. MCP tools should appear and be available.

---

## Tutorial 4: MCPHost + Ollama

> **Important:** Ollama has NO native MCP support. [MCPHost](https://github.com/mark3labs/mcphost) is the required bridge.

### Step 1: Install Ollama and MCPHost

```bash
curl -fsSL https://ollama.ai/install.sh | sh
go install github.com/mark3labs/mcphost@latest
```

### Step 2: Pull a model with tool-calling support

```bash
ollama pull qwen3:8b
```

### Step 3: Start DFIReballz

```bash
make setup      # Select "MCPHost + Ollama" when prompted for MCP host
make start
```

> If you already ran setup with a different host, regenerate: `make configure-mcp MCP_HOST=mcphost`

### Step 4: Launch MCPHost

```bash
mcphost -m ollama/qwen3:8b --config ~/.mcphost.yml
```

### Model Selection Guide

| Model | RAM | GPU VRAM | Tool Calling | Notes |
|-------|-----|----------|--------------|-------|
| `qwen3:8b` | 8 GB | 6 GB | Excellent | **Recommended default** |
| `qwen3:14b` | 16 GB | 12 GB | Excellent | Better reasoning |
| `qwen2.5:14b` | 16 GB | 12 GB | Excellent | Great for analysis |
| `llama3.1:8b` | 8 GB | 8 GB | Good | Widely tested |
| `llama3.3:70b` | 48 GB+ | 40 GB+ | Excellent | Best quality, high-end hardware |
| `llama3.2:3b` | 4 GB | 4 GB | Limited | Minimal hardware |

Verify tool calling: `ollama show <model> | grep capabilities`

---

## Tutorial 5: Open WebUI + Ollama

### Step 1: Start everything

```bash
make setup
make start-openwebui
```

### Step 2: Configure

1. Open http://localhost:8080
2. Go to **Admin Panel > Settings > External Tools**
3. Register each MCP server:
   - `http://mcpo:8000/kali-forensics/`
   - `http://mcpo:8000/osint/`
   - `http://mcpo:8000/threat-intel/`
   - `http://mcpo:8000/winforensics/`
   - `http://mcpo:8000/binary-analysis/`
   - `http://mcpo:8000/network-forensics/`
   - `http://mcpo:8000/filesystem/`

### Step 3: Investigate

Select your Ollama model and start chatting. The mcpo proxy bridges MCP servers as OpenAPI endpoints.

---

## How Prompts Flow Through the System

```
STEP 1: YOU TYPE A PROMPT
  "Analyze the memory dump at /evidence/memdump.raw for signs of injection"
        |
        v
STEP 2: AI DECIDES WHICH TOOLS TO USE
  The AI picks tools from the 7 MCP servers:
    - volatility3_analyze (kali-forensics) → process listing, DLL injection scan
    - yara_scan (kali-forensics)           → match against malware signatures
    - check_virustotal (threat-intel)      → hash lookup for suspicious processes
    - read_file (filesystem)               → access evidence (logged to chain of custody)
        |
        v
STEP 3: TOOLS EXECUTE IN DOCKER CONTAINERS
  AI host runs: docker exec -i -e PYTHONUNBUFFERED=1 dfireballz-kali-forensics-1 python3 -u /app/server.py
  Each tool runs inside its container and returns structured output via stdio.
        |
        v
STEP 4: AI STRUCTURES THE RESULTS
  The AI correlates findings across tools:
    - Timeline reconstruction
    - MITRE ATT&CK technique mapping
    - IoC extraction (hashes, IPs, domains)
    - Severity classification
        |
        v
STEP 5: AI WRITES THE FORENSIC REPORT
  Executive summary, evidence analysis, IoC table, timeline,
  MITRE ATT&CK mapping, remediation, chain of custody log.
        |
        v
STEP 6: REPORT EXPORTED TO HOST
  ./reports/ → HTML, PDF, Markdown reports
  ./results/ → Session JSON, structured forensic data
```

---

## MCP Servers Reference

| Server | Tools | Source |
|--------|-------|--------|
| **kali-forensics** | Volatility3, bulk_extractor, tshark, YARA, dc3dd, Sleuthkit, foremost, binwalk, exiftool | Custom |
| **winforensics** | MFT, ShellBags, LNK, Registry, EVTX, Prefetch, browser history, Chainsaw | [x746b/winforensics-mcp](https://github.com/x746b/winforensics-mcp) |
| **osint** | Maigret, Sherlock, Holehe, theHarvester, DNSTwist, subfinder, amass, h8mail | Custom |
| **threat-intel** | VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan, NVD | Custom |
| **binary-analysis** | Ghidra headless, Radare2, Capa, YARA, pefile, lief, entropy analysis | Adapted from [FuzzingLabs](https://github.com/FuzzingLabs/mcp-security-hub) |
| **network-forensics** | 18 Wireshark/tshark tools, tcpdump, PCAP merge/split/carve, JA3/JA3S, GeoIP | Adapted from [PreistlyPython](https://github.com/PreistlyPython/wireshark-mcp) |
| **filesystem** | Scoped file access (/cases, /evidence, /reports) — evidence always read-only | [@modelcontextprotocol/server-filesystem](https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem) |

---

## Investigation Playbooks

| Playbook | Description |
|----------|-------------|
| `malware-analysis` | Complete static analysis of malware samples |
| `ransomware-investigation` | Ransomware artifact analysis and C2 detection |
| `phishing-investigation` | Phishing email and infrastructure investigation |
| `network-forensics` | PCAP analysis with threat detection |
| `osint-person-investigation` | Person investigation via username/email tracing |
| `osint-domain-investigation` | Domain/website reconnaissance |
| `dark-web-trace` | Dark web IOC tracing and correlation |
| `mobile-artifact-analysis` | Mobile device forensics |
| `chain-of-custody` | Evidence handling documentation template |

---

## Report Export

Reports generated inside containers are automatically available on the host via bind mounts:

```
./reports/     → /reports inside containers  (HTML, PDF, Markdown reports)
./results/     → /results inside containers  (session JSON, ForensicPayload data)
```

Reports are organized by date: `reports/reports-DDMMYYYY/report-<case-id>-DDMMYYYY.<format>`

---

## API Keys Setup

API keys are entered during `make setup` and stored in `.env`. They are injected into MCP server containers as environment variables.

| Service | Used By | Free Tier | Get Key |
|---------|---------|-----------|---------|
| VirusTotal | threat-intel | 4 req/min | [virustotal.com/gui/my-apikey](https://www.virustotal.com/gui/my-apikey) |
| Shodan | threat-intel | Limited queries | [account.shodan.io](https://account.shodan.io/) |
| AbuseIPDB | threat-intel | 1,000 req/day | [abuseipdb.com/account/api](https://www.abuseipdb.com/account/api) |
| URLScan.io | threat-intel | 50 scans/day | [urlscan.io/user/signup](https://urlscan.io/user/signup) |
| VulnCheck | threat-intel | Free tier | [vulncheck.com](https://vulncheck.com/) |
| Anthropic | claude-code container | Pay-per-use | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |

> **Note:** The Anthropic API key is only needed if you use `make claude-code` (containerized Claude Code). If you use host-installed Claude Code or Claude Desktop, authentication is handled by those apps directly.

---

## Troubleshooting

### Containers not starting or unhealthy

```bash
make health           # Quick health check of all MCP servers
make status           # Container status table
docker compose logs   # Full logs
```

If a service shows unhealthy, restart it:

```bash
make restart-kali             # Restart Kali forensics
docker compose restart osint  # Or use docker compose directly
```

### MCP tools not appearing in Claude Code

1. Ensure all containers are healthy: `make health`
2. Regenerate MCP config: `make configure-mcp`
3. Restart Claude Code

### Claude Code container won't start

```bash
# Check ANTHROPIC_API_KEY is set
grep ANTHROPIC_API_KEY .env

# Check dependent services are healthy
make health

# Check container logs
docker compose --profile claude-code logs claude-code
```

### Evidence not accessible

Evidence is mounted read-only inside containers at `/evidence`. Ensure files exist on the host:

```bash
ls -la ./evidence/
```

### Container keeps restarting

Check its logs for the specific error:

```bash
docker compose logs <service-name>    # e.g., kali-forensics, orchestrator
```

Common causes:
- Insufficient memory (16 GB recommended)
- Port conflict on the host (8800)
- Missing or invalid `.env` configuration

### MCP servers show "failed" in Claude Code `/mcp`

If `make health` shows all containers as healthy but Claude Code's `/mcp` shows servers as failed:

1. **Check Docker GID:** Run `getent group docker | cut -d: -f3` and ensure it matches `DOCKER_GID` in `.env` (default 999)
2. **Restart containers:** `make restart` — picks up volume-mounted server.py changes and environment variables
3. **Run with debug:** `claude --debug` — shows actual MCP connection error logs
4. **Rebuild images** (if all else fails): `make build && make restart` — rebuilds with pinned `fastmcp<3`

The MCP servers use `PYTHONUNBUFFERED=1` and `python3 -u` to ensure unbuffered stdio transport. Server code is volume-mounted from `./mcp-servers/<name>/server.py`, so local edits take effect on container restart without rebuilding images.

### SessionStart hook reports issues

The `.claude/hooks/session-start.sh` hook runs automatically when Claude Code opens the project:

```bash
bash .claude/mcp-health-check.sh           # Full diagnostic output
bash .claude/mcp-health-check.sh --quiet   # Summary only
bash .claude/mcp-health-check.sh --fix     # Auto-start stopped containers
```

---

## Makefile Shortcuts

```bash
# Setup
make setup              # Interactive first-run setup wizard
make pull               # Pull pre-built images from Docker Hub
make build              # Build images locally from source (only if you modified Dockerfiles)

# Running
make start / make up    # Start all services (10 containers)
make stop / make down   # Stop all services
make restart            # Restart all services
make claude-code        # Launch Claude Code in Docker (interactive)
make start-openwebui    # Start with Open WebUI + Ollama
make dev                # Start in dev mode (hot reload)

# Status & Monitoring
make status / make ps   # Container health status
make health             # MCP server health check
make logs               # Tail all logs
make logs s=<svc>       # Tail specific service logs
make log-<service>      # Tail logs (kali, osint, netforensics, winforensics,
                        #   binary, threat, filesystem, orchestrator, db, redis)

# Per-Service Restart
make restart-<service>  # Restart a specific service

# Debug Containers
make shell-kali         # Shell into Kali forensics
make shell-osint        # Shell into OSINT
make shell-netforensics # Shell into network forensics
make shell-winforensics # Shell into Windows forensics
make shell-binary       # Shell into binary analysis
make shell-threat       # Shell into threat-intel
make shell-filesystem   # Shell into filesystem
make shell-orchestrator # Shell into orchestrator

# Testing & Security
make test               # Run all tests
make test-smoke         # Container smoke tests
make test-security      # Trivy + Bandit security scan
make lint               # Run ruff linter
make format             # Auto-format code
make typecheck          # Run mypy type checking

# Utilities
make configure-mcp      # Generate MCP config for chosen host
make report             # Generate report from last session
make case-new           # Create a new case (interactive)
make playbook-list      # List available playbooks
make check-gpu          # Check NVIDIA GPU availability
make clean              # Remove containers and local images
make nuke               # Remove EVERYTHING (containers, volumes, images)
```

---

## Chain of Custody

Every evidence interaction is logged in the immutable `chain_of_custody_log` table:

| Action | When |
|--------|------|
| **Acquired** | Evidence uploaded, hashes computed |
| **Accessed** | Evidence file read by any tool |
| **Analyzed** | MCP tool invocation against evidence |
| **Exported** | Report generation or evidence transfer |
| **Transferred** | Evidence moved between systems |

Database triggers prevent UPDATE and DELETE on chain of custody records, ensuring forensic integrity. This is critical — every evidence access must create a log entry.

---

## Project Structure

```
dfireballz/
├── mcp-servers/
│   ├── kali-forensics/          # Volatility3, YARA, Sleuthkit, etc.
│   │   ├── Dockerfile
│   │   └── server.py
│   ├── winforensics/            # MFT, EVTX, Registry, Chainsaw
│   ├── osint/                   # Maigret, Sherlock, theHarvester
│   ├── threat-intel/            # VirusTotal, Shodan, AbuseIPDB
│   ├── binary-analysis/         # Ghidra, Radare2, Capa
│   ├── network-forensics/       # tshark (18 tools), tcpdump
│   └── filesystem/              # Scoped file access
├── orchestrator/                # FastAPI backend (cases, evidence, playbooks)
├── database/                    # PostgreSQL init (pgcrypto, chain of custody)
├── docker/
│   ├── claude-code.Dockerfile   # Containerized Claude Code client
│   ├── claude-code-entrypoint.sh
│   └── mcp.json                 # MCP config for containerized Claude Code
├── dfireballz/                  # Python package (CLI, MCP server, reports)
├── config/
│   └── .env.example             # Environment variable template
├── scripts/
│   ├── setup.sh                 # Interactive setup wizard
│   ├── configure_mcp.sh         # MCP config generator
│   ├── check-requirements.sh    # Prerequisite checker
│   └── smoke-test.sh            # Container smoke tests
├── playbooks/                   # Investigation playbook definitions
├── cases/                       # Case files (created at runtime)
├── evidence/                    # Evidence files (mounted read-only)
├── reports/                     # Generated reports (bind-mounted to host)
├── results/                     # Session data (bind-mounted to host)
├── .claude/
│   ├── settings.json            # Claude Code hooks config
│   ├── hooks/
│   │   └── session-start.sh     # Auto-verify Docker stack health
│   └── mcp-health-check.sh      # MCP server health checker
├── docker-compose.yml           # All services defined here
├── Makefile                     # All commands via make
├── CLAUDE.md                    # Project instructions for AI
└── .mcp.json                    # MCP config for host-installed Claude Code
```

---

## Security Notes

- **Docker socket**: The orchestrator and Claude Code container mount `/var/run/docker.sock` read-only. Never expose port 8800 to the public internet.
- **Evidence integrity**: Evidence volumes are mounted read-only in all MCP containers. Chain of custody is enforced at the database level.
- **No `shell=True`**: All subprocess calls in MCP servers use `subprocess.run(args_list, shell=False)` to prevent command injection.
- **API key encryption**: Threat-intel API keys are stored encrypted via PostgreSQL pgcrypto.
- **Non-root containers**: All MCP server containers run as non-root users with `no-new-privileges` security opt.
- **Network isolation**: All containers communicate on the internal `dfireballz-net` bridge network. Only the orchestrator (8800) exposes a port to the host.

---

## CI/CD Pipeline

| Workflow | Trigger | Actions |
|----------|---------|---------|
| **CI** | Push/PR to main/develop | Package lint/test, orchestrator test, Docker build, Trivy scan |
| **Docker Build & Push** | Version tag (v*.*.*) | Build multi-arch, push to Docker Hub |
| **CodeQL** | Push/PR to main + weekly | Static security analysis |
| **Dependabot** | Weekly | Auto-update pip, npm, Docker, GitHub Actions dependencies |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## License

[MIT](LICENSE)
