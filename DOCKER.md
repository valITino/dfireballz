# DFIReballz — Docker Hub

[![Docker](https://img.shields.io/badge/docker-crhacky%2Fdfireballz-2496ED.svg?logo=docker&logoColor=white)](https://hub.docker.com/r/crhacky/dfireballz)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AI-native forensic investigation framework using MCP (Model Context Protocol). Everything runs in Docker.**

> Not a pentesting tool. A professional forensic platform designed to produce court-admissible evidence.

---

## Quick Start

```bash
git clone https://github.com/valITino/dfireballz.git
cd dfireballz
make setup    # Interactive wizard: .env, images, MCP config
make start    # Starts 10 containers
```

Or pull images directly:

```bash
docker compose pull
```

---

## Images

| Image | Description | Size |
|:--|:--|:--:|
| `crhacky/dfireballz:kali-forensics` | Volatility3, bulk_extractor, YARA, dc3dd, Sleuthkit, foremost, exiftool | ~3 GB |
| `crhacky/dfireballz:winforensics` | MFT, EVTX, Registry, ShellBags, Prefetch, Chainsaw | ~1 GB |
| `crhacky/dfireballz:osint` | Maigret, Sherlock, Holehe, theHarvester, DNSTwist, subfinder | ~2 GB |
| `crhacky/dfireballz:threat-intel` | VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan | ~500 MB |
| `crhacky/dfireballz:binary-analysis` | Ghidra headless, Radare2, Capa (MITRE ATT&CK), YARA, pefile | ~3 GB |
| `crhacky/dfireballz:network-forensics` | 18 Wireshark/tshark tools, tcpdump, PCAP merge/split/carve, JA3 | ~500 MB |
| `crhacky/dfireballz:filesystem` | Scoped file access to /cases, /evidence (read-only), /reports | ~200 MB |
| `crhacky/dfireballz:orchestrator` | FastAPI — cases, evidence, playbooks, chain of custody | ~300 MB |
| `crhacky/dfireballz:claude-code` | Claude Code CLI + investigation skills (no host install needed) | ~500 MB |
| `crhacky/dfireballz:db` | PostgreSQL with pgcrypto for encrypted API key storage | ~300 MB |

---

## Architecture

```
AI Client (Claude Code / Claude Desktop / ChatGPT / Ollama)
    │
    │  docker exec -i (stdio transport)
    ▼
┌─ MCP Servers (7 containers) ─────────────────────────────────┐
│  kali-forensics │ winforensics │ osint                        │
│  threat-intel   │ binary-analysis │ network-forensics         │
│  filesystem                                                   │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Infrastructure ──────────────────────────────────────────────┐
│  orchestrator (FastAPI :8800) │ PostgreSQL │ Redis             │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Host Volumes ────────────────────────────────────────────────┐
│  ./evidence/ (read-only) │ ./cases/ │ ./reports/ │ ./output/  │
└───────────────────────────────────────────────────────────────┘
```

---

## Volume Mounts

| Host Path | Container Path | Access | Purpose |
|:--|:--|:--:|:--|
| `./evidence/` | `/evidence` | Read-only | Disk images, memory dumps, PCAPs |
| `./cases/` | `/cases` | Read-write | Working case files, tool output |
| `./reports/` | `/reports` | Read-write | Generated forensic reports |
| `./output/` | `/workspace/output` | Read-write | Investigation findings (host-visible) |
| `./.claude/skills/` | `/workspace/.claude/skills` | Read-only | Investigation skills for Claude Code |
| `./CLAUDE.md` | `/workspace/CLAUDE.md` | Read-only | AI instructions |

---

## Investigation Skills

The `claude-code` image includes 10 pre-built investigation skills as `/slash-commands`:

| Skill | What It Does |
|:--|:--|
| `/malware-analysis` | Static analysis, YARA, Capa, VirusTotal lookup |
| `/ransomware-investigation` | Ransomware triage, C2 detection, attack chain |
| `/phishing-investigation` | Email headers, URL analysis, credential checks |
| `/network-forensics` | PCAP analysis, protocol dissection, JA3 |
| `/osint-person` | Username/email enumeration, digital footprint |
| `/osint-domain` | DNS, subdomain, infrastructure mapping |
| `/memory-forensics` | Volatility3 process/network/malware analysis |
| `/incident-response` | 7-phase IR: triage to remediation |
| `/complete-investigation` | Full 11-phase investigation across all servers |
| `/full-investigation` | 6-phase end-to-end forensic investigation |

Skills are baked into the image at `/workspace/.claude/skills/` and also volume-mounted from the host at runtime for live updates.

---

## Supported AI Hosts

| Host | Transport | Setup |
|:--|:--:|:--|
| **Claude Code (Docker)** | stdio | `make claude-code` — zero install, fully containerized |
| **Claude Code (Host)** | stdio | Auto-discovers `.mcp.json` in project directory |
| **Claude Desktop** | stdio | `bash scripts/install-claude-desktop.sh` |
| **ChatGPT** | HTTP/SSE | `make start-openwebui` (mcpo proxy on port 8812) |
| **MCPHost + Ollama** | stdio | `~/.mcphost.yml` config |
| **Open WebUI** | HTTP | `make start-openwebui` |

---

## Environment Variables

| Variable | Required | Purpose |
|:--|:--:|:--|
| `VIRUSTOTAL_API_KEY` | No | VirusTotal file/hash/URL lookups |
| `SHODAN_API_KEY` | No | Shodan host/search queries |
| `ABUSEIPDB_API_KEY` | No | AbuseIPDB IP reputation |
| `URLSCAN_API_KEY` | No | URLScan.io URL analysis |
| `ANTHROPIC_API_KEY` | For Docker Claude Code | Claude Code container auth |

All keys are set during `make setup` or edited directly in `.env`.

---

## Requirements

| Requirement | Details |
|:--|:--|
| **Docker** | 25+ with Docker Compose v2 |
| **RAM** | 16 GB recommended (8 GB minimum) |
| **Disk** | 50 GB+ |
| **GPU** *(optional)* | NVIDIA GPU for Ollama acceleration |

---

## Security

| Concern | How It's Handled |
|:--|:--|
| **Evidence integrity** | Volumes mounted read-only in all MCP containers |
| **Command injection** | All subprocess calls use `shell=False` |
| **API key storage** | Encrypted via PostgreSQL pgcrypto |
| **Container privileges** | Non-root with `no-new-privileges` |
| **Audit trail** | Chain of custody enforced at database level (immutable log) |

---

## Links

| Resource | URL |
|:--|:--|
| **GitHub** | [github.com/valITino/dfireballz](https://github.com/valITino/dfireballz) |
| **Documentation** | [README.md](https://github.com/valITino/dfireballz/blob/main/README.md) |
| **Issues** | [github.com/valITino/dfireballz/issues](https://github.com/valITino/dfireballz/issues) |

---

## License

[MIT](LICENSE)
