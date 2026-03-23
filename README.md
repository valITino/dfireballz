```
╔═════════════════════════════════════════════════════════════════════════════════╗
║                                                                                 ║
║  ██████╗ ███████╗██╗██████╗   ███████╗██████╗  █████╗ ██╗     ██╗     ███████╗  ║
║  ██╔══██╗██╔════╝██║██╔══██╗  ██╔════╝██╔══██╗██╔══██╗██║     ██║     ╚══███╔╝  ║
║  ██║  ██║█████╗  ██║██████╔╝  █████╗  ██████╔╝███████║██║     ██║       ███╔╝   ║
║  ██║  ██║██╔══╝  ██║██╔══██╗  ██╔══╝  ██╔══██╗██╔══██║██║     ██║      ███╔╝    ║
║  ██████╔╝██║     ██║██║  ██║  ███████╗██████╔╝██║  ██║███████╗███████╗███████╗  ║
║  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝  ╚══════╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝  ║
║                                                                                 ║
╠═════════════════════════════════════════════════════════════════════════════════╣
║              Digital Forensics & Cybercrime Investigation Platform              ║
║              Chain of Custody  ·  Artifact Analysis  ·  MCP-Powered             ║
╠═════════════════════════════════════════════════════════════════════════════════╣
║                by valITino  ·  Docker · Python · FastMCP · Ollama               ║
╚═════════════════════════════════════════════════════════════════════════════════╝
```

<br>

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-25%2B-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/MCP-stdio-8A2BE2.svg)](https://modelcontextprotocol.io)

**MCP-based AI-native forensic investigation framework — everything runs in Docker.**

> This is **not** a pentesting tool. It is a professional forensic platform designed to produce court-admissible evidence.

---

## Table of Contents

**Overview**
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Components](#components)

**Getting Started**
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)

**Setup Guides**
- [Claude Code in Docker (Recommended)](#tutorial-1--claude-code-in-docker-recommended)
- [Claude Code on Host](#tutorial-2--claude-code-on-host)
- [Claude Desktop](#tutorial-3--claude-desktop)
- [ChatGPT](#tutorial-4--chatgpt)
- [MCPHost + Ollama](#tutorial-5--mcphost--ollama)
- [Open WebUI + Ollama](#tutorial-6--open-webui--ollama)

**Skills & Templates**
- [Investigation Skills (Slash Commands)](#investigation-skills)
- [How Skills Work](#how-skills-work)

**Reference**
- [How Prompts Flow](#how-prompts-flow-through-the-system)
- [Host Directory Layout](#host-directory-layout)
- [MCP Servers Reference](#mcp-servers-reference)
- [Investigation Playbooks](#investigation-playbooks)
- [API Keys](#api-keys)
- [Makefile Shortcuts](#makefile-shortcuts)
- [Chain of Custody](#chain-of-custody)

**Advanced**
- [Advanced FAQ & Tutorials](#advanced-faq--tutorials)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Security Notes](#security-notes)
- [CI/CD Pipeline](#cicd-pipeline)
- [Contributing](#contributing)
- [License](#license)

---

## How It Works

Your AI client (Claude Code, Claude Desktop, ChatGPT, or MCPHost+Ollama) **is the orchestrator**:

1. **You type a prompt** — or use a `/skill` slash command (e.g. `/malware-analysis /evidence/sample.exe`)
2. **The AI selects tools** from 7 MCP servers (90+ forensic tools)
3. **Each tool executes** inside its Docker container via `docker exec -i` (stdio transport)
4. **The AI correlates findings** — timelines, MITRE ATT&CK mappings, IoC extraction
5. **The AI writes the forensic report** with chain of custody maintained throughout

Everything runs in Docker. No forensic tools on your host. All findings land in `./output/`.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     AI Host (Choose One)                      │
│  Claude Code  │  Claude Desktop  │  ChatGPT  │  MCPHost/WebUI│
└──────┬────────┴────────┬─────────┴─────┬─────┴────────┬──────┘
       │ docker exec -i  │               │  HTTP/SSE    │
       ▼                 ▼               ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                     MCP Servers (stdio)                       │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │ kali-forensics │  │  winforensics  │  │     osint      │  │
│  │ Volatility3    │  │ MFT, Registry  │  │ Maigret        │  │
│  │ YARA, tshark   │  │ EVTX, Prefetch │  │ Sherlock       │  │
│  └────────────────┘  └────────────────┘  └────────────────┘  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │  threat-intel  │  │binary-analysis │  │network-forensic│  │
│  │ VT, Shodan     │  │ Ghidra, r2     │  │ 18 tshark tools│  │
│  │ AbuseIPDB      │  │ Capa, YARA     │  │ tcpdump, PCAP  │  │
│  └────────────────┘  └────────────────┘  └────────────────┘  │
│  ┌────────────────┐                                          │
│  │   filesystem   │   All containers on dfireballz-net       │
│  │ /cases /evidence│  Evidence volumes: READ-ONLY            │
│  └────────────────┘                                          │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                      Infrastructure                          │
│  ┌──────────────┐  ┌───────────┐  ┌───────────┐             │
│  │ Orchestrator │  │ PostgreSQL│  │   Redis   │             │
│  │  FastAPI     │  │ pgcrypto  │  │   Cache   │             │
│  │  :8800       │  │   :5432   │  │   :6379   │             │
│  └──────────────┘  └───────────┘  └───────────┘             │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                  Host Machine (your computer)                 │
│                                                              │
│  ./evidence/   — Evidence files (read-only in containers)    │
│  ./cases/      — Working case files                          │
│  ./reports/    — Generated forensic reports                  │
│  ./output/     — Investigation findings, logs, exports       │
└──────────────────────────────────────────────────────────────┘
```

> **Transport:** stdio only. Every MCP server runs `mcp.run(transport="stdio")`. The AI host connects via `docker exec -i <container> <command>`. No HTTP ports exposed for direct AI connections.
>
> **Exception:** ChatGPT uses HTTP/SSE — the mcpo proxy bridges MCP servers as OpenAPI endpoints.

---

## Components

| Container | What It Does | Port | Profile |
|:--|:--|:--:|:--:|
| **kali-forensics** | Volatility3, bulk_extractor, tshark, YARA, dc3dd, Sleuthkit, foremost, binwalk, exiftool | — | default |
| **winforensics** | MFT, ShellBags, LNK, Registry, EVTX, Prefetch, Chainsaw | — | default |
| **osint** | Maigret, Sherlock, Holehe, theHarvester, DNSTwist, subfinder | — | default |
| **threat-intel** | VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan | — | default |
| **binary-analysis** | Ghidra headless, Radare2, Capa (MITRE ATT&CK), YARA, pefile, lief | — | default |
| **network-forensics** | 18 Wireshark/tshark tools, tcpdump, PCAP merge/split/carve, JA3/JA3S | — | default |
| **filesystem** | Scoped file access to /cases, /evidence (read-only), /reports, /output | — | default |
| **orchestrator** | FastAPI — cases, evidence, playbooks, chain of custody | `8800` | default |
| **db** | PostgreSQL with pgcrypto (encrypted API key storage) | — | default |
| **redis** | Redis cache | — | default |
| **claude-code** | Anthropic CLI in Docker (no host install needed) | — | `claude-code` |
| **ollama** | Local LLM inference (Open WebUI scenario) | `11434` | `openwebui` |
| **open-webui** | Web UI for Ollama models | `8080` | `openwebui` |
| **mcpo** | MCP-to-OpenAPI bridge for Open WebUI / ChatGPT | `8812` | `openwebui` |

---

## Prerequisites

| Requirement | Details |
|:--|:--|
| **Docker** | 25+ with Docker Compose v2 |
| **RAM** | 16 GB recommended (8 GB minimum) |
| **Disk** | 50 GB+ (Docker images are large) |
| **Docker GID** | Verify with: `getent group docker \| cut -d: -f3` — must match `DOCKER_GID` in `.env` (default `999`) |
| **GPU** *(optional)* | NVIDIA GPU + [Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) for Ollama |

### API Keys (Free Tiers Available)

| Service | Free Tier | Sign Up |
|:--|:--|:--|
| **VirusTotal** | 4 req/min | [virustotal.com/gui/my-apikey](https://www.virustotal.com/gui/my-apikey) |
| **Shodan** | Limited queries | [account.shodan.io](https://account.shodan.io/) |
| **AbuseIPDB** | 1,000 req/day | [abuseipdb.com/account/api](https://www.abuseipdb.com/account/api) |
| **URLScan.io** | 50 scans/day | [urlscan.io/user/signup](https://urlscan.io/user/signup) |
| **VulnCheck** | Free tier | [vulncheck.com](https://vulncheck.com/) |

> **Using Claude Code in Docker?** You also need an **Anthropic API key**: [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

```bash
bash scripts/check-requirements.sh   # Verify prerequisites
```

---

## Quick Start

All images are pre-built on [Docker Hub](https://hub.docker.com/r/crhacky/dfireballz). No local building required.

```bash
git clone https://github.com/valITino/dfireballz.git
cd dfireballz
make setup    # Interactive wizard: .env, images, MCP config
make start    # Starts 10 containers
```

### Verify

```bash
make status   # Container health table
make health   # MCP server responsiveness check
```

---

## Tutorial 1 — Claude Code in Docker (Recommended)

Run Claude Code entirely inside Docker — connects directly to MCP servers on the internal network.

```bash
make setup        # Select "Claude Code in Docker"
make start
make claude-code  # Launch interactive Claude Code
```

The entrypoint verifies all 7 MCP servers are responsive before launching. Once inside:

```
/malware-analysis /evidence/sample.exe
```

Claude Code autonomously calls binary-analysis (Ghidra, Radare2, Capa), kali-forensics (YARA, ExifTool), and threat-intel (VirusTotal), then writes a full forensic report.

### View results

```bash
ls output/findings/   # Analysis results
ls output/exports/    # Extracted artifacts
ls reports/           # Forensic reports
```

---

## Tutorial 2 — Claude Code on Host

If you already have Claude Code installed locally.

```bash
make setup    # Select "Claude Code on host"
make start
```

Open Claude Code in the DFIReballz directory. MCP tools are auto-discovered from `.mcp.json`. The SessionStart hook (`.claude/hooks/session-start.sh`) verifies Docker stack health automatically.

---

## Tutorial 3 — Claude Desktop

```bash
make setup    # Select "Claude Desktop"
make start
bash scripts/install-claude-desktop.sh   # Auto-merge MCP config
```

Restart Claude Desktop. MCP tools appear in the tool picker.

**Manual config?** Merge `.mcp.json` into your Claude Desktop config:

| OS | Config Path |
|:--|:--|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

---

## Tutorial 4 — ChatGPT

ChatGPT uses HTTP/SSE, not stdio. The mcpo proxy bridges MCP servers as HTTP endpoints.

```bash
make setup              # Select "ChatGPT"
make start-openwebui    # Starts mcpo proxy on port 8812
```

Expose your mcpo proxy to the internet (ChatGPT needs to reach it):

```bash
ngrok http 8812                              # Option A
cloudflared tunnel --url http://localhost:8812   # Option B
```

In **ChatGPT** → **Settings** → **Connectors** → **Developer Mode**, add your tunnel URL. Endpoints: `/kali-forensics/`, `/osint/`, `/threat-intel/`, `/winforensics/`, `/binary-analysis/`, `/network-forensics/`, `/filesystem/`.

---

## Tutorial 5 — MCPHost + Ollama

Ollama has no native MCP support. [MCPHost](https://github.com/mark3labs/mcphost) bridges the gap.

```bash
curl -fsSL https://ollama.ai/install.sh | sh
go install github.com/mark3labs/mcphost@latest
ollama pull qwen3:8b

make setup    # Select "MCPHost + Ollama"
make start
mcphost -m ollama/qwen3:8b --config ~/.mcphost.yml
```

| Model | RAM | Tool Calling | Notes |
|:--|:--|:--|:--|
| `qwen3:8b` | 8 GB | Excellent | **Recommended** |
| `qwen3:14b` | 16 GB | Excellent | Better reasoning |
| `llama3.1:8b` | 8 GB | Good | Widely tested |
| `llama3.3:70b` | 48 GB+ | Excellent | Best quality |

---

## Tutorial 6 — Open WebUI + Ollama

```bash
make setup
make start-openwebui
```

Open **http://localhost:8080** → **Admin Panel** → **Settings** → **External Tools**. Register each server at `http://mcpo:8000/<server-name>/`.

---

## Investigation Skills

DFIReballz includes 10 **Claude Code skills** — slash commands that launch structured investigation workflows. Each skill loads the corresponding investigation template, replaces `[TARGET]` with your input, and executes the full workflow.

### Available Skills

| Skill | What It Does | Example |
|:--|:--|:--|
| `/complete-investigation` | Full 11-phase investigation across all servers | `/complete-investigation /evidence/` |
| `/full-investigation` | 6-phase end-to-end forensic investigation | `/full-investigation /evidence/case001/` |
| `/malware-analysis` | Static analysis, YARA, Capa, VirusTotal | `/malware-analysis /evidence/sample.exe` |
| `/ransomware-investigation` | Ransomware triage, C2 detection, attack chain | `/ransomware-investigation /evidence/encrypted-host/` |
| `/phishing-investigation` | Email headers, URL analysis, credential checks | `/phishing-investigation /evidence/phish.eml` |
| `/network-forensics` | PCAP analysis, protocol dissection, JA3 | `/network-forensics /evidence/capture.pcap` |
| `/osint-person` | Username/email enumeration, digital footprint | `/osint-person suspect@example.com` |
| `/osint-domain` | DNS, subdomain, infrastructure mapping | `/osint-domain suspicious-site.com` |
| `/memory-forensics` | Volatility3 process/network/malware analysis | `/memory-forensics /evidence/memdump.raw` |
| `/incident-response` | 7-phase IR: triage to remediation | `/incident-response /evidence/compromised-host/` |

### How Skills Work

Skills live in `.claude/skills/<name>/SKILL.md`. Claude Code auto-discovers them when opened in the project directory.

```
.claude/skills/
├── complete-investigation/SKILL.md
├── full-investigation/SKILL.md
├── malware-analysis/SKILL.md
├── ransomware-investigation/SKILL.md
├── phishing-investigation/SKILL.md
├── network-forensics/SKILL.md
├── osint-person/SKILL.md
├── osint-domain/SKILL.md
├── memory-forensics/SKILL.md
└── incident-response/SKILL.md
```

**Skills vs. Templates vs. Playbooks:**

| | Skills | Templates | Playbooks |
|:--|:--|:--|:--|
| **Where** | `.claude/skills/` | `dfireballz/prompts/templates/` | `playbooks/` |
| **Loaded** | Auto by Claude Code | Via MCP or CLI | Via orchestrator API |
| **Invoked** | `/skill-name target` | `get_template(name, target)` | `POST /api/playbook/run` |
| **For** | Claude Code users | Any MCP client | API consumers |
| **UX** | Slash command | Function call | REST API |

All three share the same investigation workflows — skills are the Claude Code-native interface.

**Docker:** Skills are volume-mounted into the `claude-code` container at `/workspace/.claude/skills/` (read-only), and also baked into the image as a fallback.

---

## How Prompts Flow Through the System

```
STEP 1 ─ YOU TYPE A PROMPT (or /skill)
│  "/malware-analysis /evidence/sample.exe"
│
▼
STEP 2 ─ AI LOADS TEMPLATE & SELECTS TOOLS
│  Skill loads the malware-analysis template, AI picks tools:
│    · capa_analyze (binary-analysis)      → MITRE ATT&CK mapping
│    · yara_scan (kali-forensics)          → malware signature matching
│    · check_virustotal (threat-intel)     → hash reputation lookup
│
▼
STEP 3 ─ TOOLS EXECUTE IN DOCKER
│  docker exec -i dfireballz-binary-analysis-1 python3 -u /app/server.py
│  Each tool returns structured output via stdio.
│
▼
STEP 4 ─ AI CORRELATES & STRUCTURES RESULTS
│  Timeline, MITRE ATT&CK techniques, IoCs, severity
│
▼
STEP 5 ─ AI WRITES FORENSIC REPORT
│  Executive summary, evidence analysis, IoC table, chain of custody
│
▼
STEP 6 ─ OUTPUT ON HOST
   ./reports/  → HTML, PDF, Markdown
   ./output/   → findings, logs, exports, timelines
```

---

## Host Directory Layout

```
dfireballz/
├── evidence/           Evidence files — mounted READ-ONLY in all containers
├── cases/              Working case files — writable by containers
├── reports/            Generated forensic reports
├── results/            Session JSON data
└── output/             Investigation output (host-visible)
    ├── findings/       Analysis results & summaries
    ├── screenshots/    Visual evidence captures
    ├── logs/           Activity & audit logs
    ├── exports/        Carved files & extracted objects
    └── timelines/      Event timeline reconstructions
```

> **Why `output/`?** When Claude Code runs in a container, files it creates aren't visible on the host unless bind-mounted. `output/` ensures all artifacts are immediately accessible.

---

## MCP Servers Reference

| Server | Tools | Source |
|:--|:--|:--|
| **kali-forensics** | Volatility3, bulk_extractor, tshark, YARA, dc3dd, Sleuthkit, foremost, binwalk, exiftool | Custom |
| **winforensics** | MFT, ShellBags, LNK, Registry, EVTX, Prefetch, browser history, Chainsaw | [x746b/winforensics-mcp](https://github.com/x746b/winforensics-mcp) |
| **osint** | Maigret, Sherlock, Holehe, theHarvester, DNSTwist, subfinder, amass, h8mail | Custom |
| **threat-intel** | VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan, NVD | Custom |
| **binary-analysis** | Ghidra headless, Radare2, Capa, YARA, pefile, lief, entropy analysis | Adapted from [FuzzingLabs](https://github.com/FuzzingLabs/mcp-security-hub) |
| **network-forensics** | 18 Wireshark/tshark tools, tcpdump, PCAP merge/split/carve, JA3/JA3S, GeoIP | Adapted from [PreistlyPython](https://github.com/PreistlyPython/wireshark-mcp) |
| **filesystem** | Scoped file access (/cases, /evidence, /reports, /output) — evidence always read-only | [@modelcontextprotocol/server-filesystem](https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem) |

---

## Investigation Playbooks

| Playbook | Description |
|:--|:--|
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

## API Keys

Keys are entered during `make setup` and stored in `.env`.

**Add or change keys later:**

```bash
make setup-keys    # Interactive wizard — shows status, saves keys, restarts container, validates
```

This handles everything: prompts for each key, updates `.env`, restarts the threat-intel container, and validates connectivity.

| Service | Used By | Get Key |
|:--|:--|:--|
| **VirusTotal** | threat-intel | [virustotal.com/gui/my-apikey](https://www.virustotal.com/gui/my-apikey) |
| **Shodan** | threat-intel | [account.shodan.io](https://account.shodan.io/) |
| **AbuseIPDB** | threat-intel | [abuseipdb.com/account/api](https://www.abuseipdb.com/account/api) |
| **URLScan.io** | threat-intel | [urlscan.io/user/signup](https://urlscan.io/user/signup) |
| **VulnCheck** | threat-intel | [vulncheck.com](https://vulncheck.com/) |
| **Anthropic** | claude-code container | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |

> The Anthropic key is only needed for `make claude-code`. Host-installed Claude Code and Claude Desktop handle auth themselves.

---

## Makefile Shortcuts

### Setup & Running

```bash
make setup              # Interactive first-run wizard
make setup-keys         # Add/update threat intel API keys (with validation)
make start              # Start all services (10 containers)
make stop               # Stop all services
make restart            # Restart all services
make claude-code        # Launch Claude Code in Docker
make start-openwebui    # Start with Open WebUI + Ollama
make dev                # Dev mode (hot reload)
```

### Status & Monitoring

```bash
make status             # Container health status
make health             # MCP server health check
make logs               # Tail all logs
make log-<service>      # kali, osint, netforensics, winforensics,
                        # binary, threat, filesystem, orchestrator, db, redis
```

### Testing & Quality

```bash
make test               # Run all tests
make test-smoke         # Container smoke tests
make test-security      # Trivy + Bandit security scan
make lint               # Ruff linter
make format             # Auto-format
make typecheck          # mypy
```

### Utilities

```bash
make configure-mcp      # Regenerate MCP config
make report             # Generate report from last session
make shell-<service>    # Debug shell into any container
make clean              # Remove containers + local images
make nuke               # Remove EVERYTHING (containers, volumes, images)
```

---

## Chain of Custody

Every evidence interaction is logged in the immutable `chain_of_custody_log` table:

| Action | When |
|:--|:--|
| **Acquired** | Evidence uploaded, hashes computed |
| **Accessed** | Evidence file read by any tool |
| **Analyzed** | MCP tool invocation against evidence |
| **Exported** | Report generation or evidence transfer |

Database triggers prevent `UPDATE` and `DELETE` on chain of custody records, ensuring forensic integrity.

---

## Advanced FAQ & Tutorials

### How do I create a custom investigation skill?

Create a new directory in `.claude/skills/` with a `SKILL.md` file:

```bash
mkdir .claude/skills/my-investigation
```

Write `.claude/skills/my-investigation/SKILL.md`:

```markdown
---
name: my-investigation
description: Short description of what this skill does — Claude uses this to auto-invoke.
---

Instructions for Claude when this skill is invoked.

**Usage:** `/my-investigation <target>`

## Instructions

1. What Claude should do first
2. Which MCP servers to use
3. What output to produce
```

Claude Code auto-discovers it on next session. No config changes needed.

### How do skills differ from CLAUDE.md?

**CLAUDE.md** = passive rules. Always loaded, always enforced. "How to behave."
**Skills** = active workflows. Invoked on demand via `/slash-command`. "What to do."
**Subdirectory CLAUDE.md** = scoped rules. Loaded only when Claude touches files in that directory.

This repo uses all three:
- Root `CLAUDE.md` — global forensic rules (chain of custody, `shell=False`, etc.)
- `mcp-servers/CLAUDE.md` — rules for editing MCP server code
- `dfireballz/models/CLAUDE.md` — rules for editing data models
- `.claude/skills/` — 10 investigation workflows

### How do I run a skill inside the Docker container?

Skills are volume-mounted into the claude-code container. Just use them normally:

```bash
make claude-code
# Inside the container:
/malware-analysis /evidence/sample.exe
```

### Can I use skills AND MCP templates together?

Yes. Skills are the Claude Code interface. Templates are the MCP interface. They share the same underlying markdown files. Use whichever fits your client:

- **Claude Code** (host or Docker): `/malware-analysis /evidence/sample.exe`
- **Claude Desktop**: Call `get_template(name="malware-analysis", target="/evidence/sample.exe")`
- **ChatGPT**: Call the same MCP function through mcpo proxy
- **CLI**: `dfireballz templates show malware-analysis --target /evidence/sample.exe`

### How do subdirectory CLAUDE.md files work?

Claude Code loads a directory's `CLAUDE.md` when it reads or edits files in that directory. This repo has scoped rules in:

```
mcp-servers/CLAUDE.md        — shell=False, Pydantic validation, stdio transport
dfireballz/models/CLAUDE.md  — ForensicPayload contract, backward compatibility
dfireballz/backends/CLAUDE.md — _TOOL_COMMANDS mapping, Docker exec patterns
dfireballz/reporting/CLAUDE.md — report format requirements, output paths
```

These keep Claude focused on directory-specific constraints without bloating the root CLAUDE.md.

### How do I add a new MCP server?

1. Create `mcp-servers/new-server/` with `Dockerfile` + `server.py`
2. Register in `docker-compose.yml`
3. Run `make configure-mcp` to update `.mcp.json`
4. Add tools to `dfireballz/backends/docker.py` `_TOOL_COMMANDS` mapping
5. Add to `dfireballz/data/tools_catalog.json`
6. Optionally create a skill in `.claude/skills/`
7. Add tests

### How do I investigate something without a skill?

Just describe what you want in natural language:

```
Analyze the memory dump at /evidence/memdump.raw for signs of process injection.
Check any suspicious hashes against VirusTotal.
```

Claude Code picks the right MCP tools automatically. Skills are convenience shortcuts, not requirements.

### How do I view all available MCP tools?

```bash
dfireballz catalog              # CLI: list all 90+ tools
# Or inside Claude Code:
/mcp                            # Check MCP server status and tools
```

### How do I export investigation results?

All output is in bind-mounted directories visible on your host:

```bash
ls reports/            # Forensic reports (HTML, PDF, MD)
ls output/findings/    # Analysis summaries
ls output/exports/     # Carved files, extracted objects
ls output/timelines/   # Event timelines
ls results/            # Raw ForensicPayload JSON
```

---

## Troubleshooting

### Containers not starting

```bash
make health           # MCP server health check
make status           # Container status table
make restart-kali     # Restart specific service
```

### MCP tools not appearing in Claude Code

1. `make health` — ensure all containers are healthy
2. `make configure-mcp` — regenerate MCP config
3. Restart Claude Code

### Claude Code container issues

```bash
grep ANTHROPIC_API_KEY .env                             # Verify key is set
docker compose --profile claude-code logs claude-code   # Check logs
```

### SessionStart hook reports issues

```bash
bash .claude/mcp-health-check.sh           # Full diagnostic
bash .claude/mcp-health-check.sh --fix     # Auto-start stopped containers
```

### MCP servers "failed" in /mcp

1. Check Docker GID: `getent group docker | cut -d: -f3` must match `DOCKER_GID` in `.env`
2. `make restart` — picks up volume-mounted code changes
3. `claude --debug` — shows MCP connection errors
4. `make build && make restart` — last resort: rebuild images

---

## Project Structure

```
dfireballz/
├── .claude/
│   ├── settings.json              Claude Code hooks config
│   ├── hooks/session-start.sh     Auto-verify Docker stack health
│   ├── mcp-health-check.sh        MCP server health checker
│   └── skills/                    Investigation skills (10 slash commands)
│       ├── malware-analysis/SKILL.md
│       ├── network-forensics/SKILL.md
│       ├── osint-person/SKILL.md
│       └── ...
│
├── mcp-servers/
│   ├── kali-forensics/            Volatility3, YARA, Sleuthkit
│   ├── winforensics/              MFT, EVTX, Registry, Chainsaw
│   ├── osint/                     Maigret, Sherlock, theHarvester
│   ├── threat-intel/              VirusTotal, Shodan, AbuseIPDB
│   ├── binary-analysis/           Ghidra, Radare2, Capa
│   ├── network-forensics/         tshark (18 tools), tcpdump
│   └── filesystem/                Scoped file access
│
├── dfireballz/                    Python package (CLI, MCP server, reports)
│   ├── backends/                  Tool execution (Docker exec)
│   ├── models/                    Pydantic data models (ForensicPayload)
│   ├── mcp/                       MCP server implementation
│   ├── prompts/templates/         Investigation templates (10)
│   └── reporting/                 HTML, PDF, Markdown report generators
│
├── orchestrator/                  FastAPI backend (cases, evidence, playbooks)
├── database/                      PostgreSQL init (pgcrypto, chain of custody)
├── docker/                        Claude Code Dockerfile + entrypoint
├── playbooks/                     Investigation playbook definitions (9)
├── scripts/                       Setup wizard, MCP config generator
│
├── evidence/                      Evidence files (mounted read-only)
├── cases/                         Working case files
├── reports/                       Generated reports
├── output/                        Host-visible investigation output
│
├── docker-compose.yml             All services
├── Makefile                       50+ make targets
├── CLAUDE.md                      AI instructions (global rules)
└── .mcp.json                      MCP config for host Claude Code
```

---

## Security Notes

| Concern | How It's Handled |
|:--|:--|
| **Docker socket** | Mounted read-only. Never expose port `8800` publicly. |
| **Evidence integrity** | Read-only volumes in all MCP containers. Chain of custody at DB level. |
| **No `shell=True`** | All subprocess calls use `subprocess.run(args_list, shell=False)`. |
| **API key encryption** | Stored via PostgreSQL pgcrypto. |
| **Non-root containers** | All run with `no-new-privileges` (except network-forensics — needs packet capture caps). |
| **Network isolation** | Internal `dfireballz-net` bridge. Only orchestrator exposes a port. |

---

## CI/CD Pipeline

| Workflow | Trigger | Actions |
|:--|:--|:--|
| **CI** | Push / PR to main | Lint, test, pip-audit dependency scan |
| **Docker Build & Push** | CI pass on main, version tag (`v*`), manual | Build + push all images, Docker Scout CVE scan |
| **CodeQL** | Push / PR to main + weekly | Static security analysis |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

[MIT](LICENSE)
