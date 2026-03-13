# DFIReballz — Digital Forensics & Cybercrime Investigation Platform

**AI-native forensic investigation framework using MCP (Model Context Protocol). Everything runs in Docker.**

> Not a pentesting tool. A professional forensic platform designed to produce court-admissible evidence.

## What Is DFIReballz?

DFIReballz connects AI clients (Claude Code, Claude Desktop, ChatGPT, or Ollama) to 7 specialized forensic MCP servers running inside Docker containers. The AI selects and orchestrates tools autonomously — you just describe what you want to investigate.

**90+ forensic tools** across 7 containers, zero host-side installation.

## Quick Start

```bash
git clone https://github.com/valITino/dfireballz.git
cd dfireballz
make setup    # Interactive wizard: generates .env, pulls images, configures MCP
make start    # Starts all 10 containers
```

Or pull images directly:

```bash
docker compose pull
```

## Images

| Image | Description | Size |
|-------|-------------|------|
| `crhacky/dfireballz:kali-forensics` | Volatility3, bulk_extractor, YARA, dc3dd, Sleuthkit, foremost, exiftool | ~3 GB |
| `crhacky/dfireballz:winforensics` | MFT, EVTX, Registry, ShellBags, Prefetch, Chainsaw, browser history | ~1 GB |
| `crhacky/dfireballz:osint` | Maigret, Sherlock, Holehe, theHarvester, DNSTwist, subfinder | ~2 GB |
| `crhacky/dfireballz:threat-intel` | VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan | ~500 MB |
| `crhacky/dfireballz:binary-analysis` | Ghidra headless, Radare2, Capa (MITRE ATT&CK), YARA, pefile | ~3 GB |
| `crhacky/dfireballz:network-forensics` | 18 Wireshark/tshark tools, tcpdump, PCAP merge/split/carve, JA3 | ~500 MB |
| `crhacky/dfireballz:filesystem` | Scoped file access to /cases, /evidence (read-only), /reports | ~200 MB |
| `crhacky/dfireballz:orchestrator` | FastAPI backend — cases, evidence, playbooks, chain of custody | ~300 MB |
| `crhacky/dfireballz:claude-code` | Anthropic Claude Code CLI client (no host install needed) | ~500 MB |
| `crhacky/dfireballz:db` | PostgreSQL with pgcrypto for encrypted API key storage | ~300 MB |

## Architecture

```
AI Client (Claude Code / Claude Desktop / ChatGPT / Ollama)
    │
    │  docker exec -i (stdio transport)
    ▼
┌─ MCP Servers (7 containers) ──────────────────────────┐
│  kali-forensics  │  winforensics  │  osint            │
│  threat-intel    │  binary-analysis│  network-forensics│
│  filesystem                                           │
└───────────────────────────────────────────────────────┘
    │
    ▼
┌─ Infrastructure ──────────────────────────────────────┐
│  orchestrator (FastAPI :8800)  │  PostgreSQL  │  Redis│
└───────────────────────────────────────────────────────┘
    │
    ▼
┌─ Host Volumes ────────────────────────────────────────┐
│  ./evidence/ (read-only)  │  ./cases/  │  ./reports/  │
│  ./output/findings/  │  ./output/exports/  │  ...     │
└───────────────────────────────────────────────────────┘
```

## Volume Mounts

| Host Path | Container Path | Access | Purpose |
|-----------|---------------|--------|---------|
| `./evidence/` | `/evidence` | Read-only | Evidence files (disk images, memory dumps, PCAPs) |
| `./cases/` | `/cases` | Read-write | Working case files and tool output |
| `./reports/` | `/reports` | Read-write | Generated forensic reports |
| `./output/` | `/workspace/output` | Read-write | Investigation findings visible on host |

## Supported AI Hosts

| Host | Transport | Setup |
|------|-----------|-------|
| **Claude Code (Docker)** | stdio | `make claude-code` — zero install, fully containerized |
| **Claude Code (Host)** | stdio | Auto-discovers `.mcp.json` in project directory |
| **Claude Desktop** | stdio | `bash scripts/install-claude-desktop.sh` to auto-configure |
| **ChatGPT** | HTTP/SSE | Requires mcpo proxy: `make start-openwebui` |
| **MCPHost + Ollama** | stdio | Config at `~/.mcphost.yml` |
| **Open WebUI** | HTTP | `make start-openwebui` |

## Environment Variables

API keys for threat intelligence (optional but recommended):

| Variable | Service |
|----------|---------|
| `VIRUSTOTAL_API_KEY` | VirusTotal file/hash/URL lookups |
| `SHODAN_API_KEY` | Shodan host/search queries |
| `ABUSEIPDB_API_KEY` | AbuseIPDB IP reputation |
| `URLSCAN_API_KEY` | URLScan.io URL analysis |
| `ANTHROPIC_API_KEY` | Claude Code container auth |

All keys are set during `make setup` or edited directly in `.env`.

## Requirements

- Docker 25+ with Docker Compose v2
- 16 GB RAM recommended (8 GB minimum)
- 50 GB disk space
- Optional: NVIDIA GPU for Ollama acceleration

## Security

- Evidence volumes are mounted **read-only** in all MCP containers
- All subprocess calls use `shell=False` (no command injection)
- API keys stored encrypted via PostgreSQL pgcrypto
- Non-root containers with `no-new-privileges`
- Chain of custody enforced at database level (immutable audit log)

## Links

- **GitHub:** [github.com/valITino/dfireballz](https://github.com/valITino/dfireballz)
- **Documentation:** See [README.md](https://github.com/valITino/dfireballz/blob/main/README.md) for full setup guides
- **Issues:** [github.com/valITino/dfireballz/issues](https://github.com/valITino/dfireballz/issues)

## License

MIT
