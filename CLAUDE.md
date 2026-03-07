# DFIReballz — Claude Code Instructions

## ⚠️ Mandatory Protocol — Read Before Touching Anything

Before making **any** fix, refactor, addition, or change — no matter how small it looks — you must complete all three phases below in order. No exceptions.

**Phase 1: Web Research**
Search the web for current, accurate information relevant to the task. The MCP ecosystem, tool versions, and Docker APIs move fast. Research:
- The relevant MCP server repo (e.g. `github.com/x746b/winforensics-mcp`, `github.com/PreistlyPython/wireshark-mcp`, `github.com/FuzzingLabs/mcp-security-hub`) for latest versions and breaking changes
- FastMCP PyPI (`pypi.org/project/fastmcp`) for current API and version
- Any tool, library, or Docker base image you're touching — verify current signatures and known CVEs
- If the web research is inconclusive, say so explicitly before proceeding

**Phase 2: Full Codebase Review**
Read the following before writing a single line:
- `CLAUDE.md` (this file), `README.md`, `DFIREBALLZ_CLAUDE_CODE_PROMPT.md` (source of truth)
- `docker-compose.yml`, `Makefile`, `.env.example`
- Every file directly relevant to the task: `Dockerfile`, `server.py`, `init.sql`, workflow files — whatever applies
- Do not rely on memory from previous sessions. Read the actual current files.

**Phase 3: Understand Before Acting**
Before writing code, answer these internally:
1. What is the root cause — not the symptom, the actual root cause?
2. Does the fix conflict with anything else in the codebase?
3. Does it break the Chain of Custody contract? (Every evidence access must create a `chain_of_custody_log` entry.)
4. Does it violate the `shell=False` rule?
5. Does it expose a port that must stay internal-only?
6. Is there a simpler fix that achieves the same result?

Only after answering all six — write the fix.

---

## Project Purpose
DFIReballz is a digital forensics and cybercrime investigation platform. All code decisions
should reflect the context of a professional forensic investigator.

## Development Commands
- `make dev` — Start development environment (hot-reload)
- `make test` — Run all tests
- `make test-smoke` — Run container smoke tests (docker exec probes)
- `make test-security` — Security scan (Trivy + Bandit)
- `make mcp-health-check` — Check MCP server container health
- `make shell-kali` — Debug Kali forensics container
- `make shell-osint` — Debug OSINT container
- `make shell-netforensics` — Debug Wireshark/tcpdump container
- `make configure-mcp` — Regenerate `.mcp.json` / `~/.mcphost.yml` for your AI host
- `make start-openwebui` — Start with Open WebUI + Ollama (`--profile openwebui`)
- `make claude-code` — Run Claude Code in Docker (interactive, requires `ANTHROPIC_API_KEY`)

## Architecture
- **MCP Transport: stdio only.** Every MCP server runs `mcp.run(transport="stdio")`.
  The AI host (Claude Code / Claude Desktop / MCPHost) connects via `docker exec -i <container> <cmd>`.
  No HTTP ports, no proxy, no gateway for direct AI host connections.
- **Ollama note:** Ollama has NO native MCP support. Use MCPHost (`mark3labs/mcphost`) or
  Open WebUI + mcpo proxy as the bridge. MCPHost model syntax: `mcphost -m ollama/qwen3:8b --config ~/.mcphost.yml`
- **Containerized Claude Code** (`--profile claude-code`): Runs Claude Code inside Docker with
  all MCP servers pre-configured. Two-tier health check (running + responsive) before launch.
  Hardened with `cap_drop: ALL`, `no-new-privileges`, SUID stripping, pids_limit, tmpfs noexec.
- Orchestrator API (port 8800) manages cases, evidence, and playbooks
- UI (port 3000) is the investigator-facing dashboard
- For Open WebUI scenario: mcpo container (port 8812) exposes MCP servers as OpenAPI endpoints.
  The mcpo container needs `/var/run/docker.sock` mounted to run `docker exec` commands.

**Security Defaults (all containers):**
- `security_opt: no-new-privileges:true` on every container
- `ENTRYPOINT []` on all MCP containers (prevents inherited entrypoint interference)
- `.dockerignore` in every MCP server directory

**MCP Servers (stdio only — no exposed ports):**
| Container | Key Tools |
|-----------|-----------|
| `kali-forensics` | Volatility3, bulk_extractor, YARA, dc3dd, Sleuthkit, Foremost, ExifTool |
| `winforensics` | MFT, EVTX, Registry, Amcache, SRUM, ShellBags, USN Journal, WinRM remote |
| `osint` | Maigret, Sherlock, Holehe, SpiderFoot, theHarvester, subfinder, DNSTwist |
| `threat-intel` | VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan |
| `binary-analysis` | Ghidra headless, Radare2, Capa (MITRE ATT&CK), YARA, pefile, Binwalk |
| `network-forensics` | tshark (18 tools), tcpdump capture, PCAP carving, JA3/JA3S, GeoIP |
| `filesystem` | Scoped to /cases, /evidence, /reports — evidence always read-only |

## Code Standards
- All Python code must be type-annotated
- All MCP tool inputs must be validated with Pydantic
- All tool subprocess calls must use `subprocess.run(args_list, shell=False)`
- Every evidence access must create a `chain_of_custody_log` entry
- Never use `shell=True` in subprocess calls
- Never log API keys or secrets

## Adding a New MCP Server
1. Create `mcp-servers/new-server/` directory
2. Write Dockerfile (non-root user, health check required)
3. Write `server.py` using FastMCP
4. Register in `docker-compose.yml` and generate updated `.mcp.json` via `make configure-mcp`
5. Add service to `docker-compose.yml`
6. Document tools in README.md MCP reference table
7. Add unit tests

## Key Reference Links
| Resource | URL |
|----------|-----|
| FastMCP (Python MCP framework) | https://pypi.org/project/fastmcp |
| WinForensics MCP | https://github.com/x746b/winforensics-mcp |
| Wireshark MCP (18 tools) | https://github.com/PreistlyPython/wireshark-mcp |
| FuzzingLabs Security Hub | https://github.com/FuzzingLabs/mcp-security-hub |
| MCPHost (Ollama bridge) | https://github.com/mark3labs/mcphost |
| mcpo (Open WebUI proxy) | https://github.com/open-webui/mcpo |
| MCP Protocol spec | https://modelcontextprotocol.io |
| Chainsaw (EVTX/Sigma hunting) | https://github.com/WithSecureLabs/chainsaw |

---

*This platform will be used in real cybercrime investigations. Every decision must hold up under legal scrutiny. Research first. Understand fully. Then act.*
