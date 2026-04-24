# DFIReballz — Claude Code Instructions

Behavioral guidelines + project-specific rules. Read the whole file before touching anything.

---

## ⚠️ Mandatory Protocol — Read Before Touching Anything

Before making **any** fix, refactor, addition, or change — no matter how small it looks — you must complete all three phases below in order. **No exceptions.**

> **Note on tradeoffs:** Generic coding guidance often says "for trivial tasks, use judgment and skip the ceremony." That shortcut **does not apply here.** This platform is used in real cybercrime investigations, where a one-line change can break chain of custody, leak evidence, or produce output that won't hold up under legal scrutiny. Bias toward caution over speed, always.

### Phase 1: Web Research — Cast a Wide Net

Search the web for current, accurate information on **anything the task touches** that may have changed, broken, or gained known issues since your training cutoff. Err on the side of over-researching. The goal is to catch surprises *before* you write code, not after.

At minimum, research:

- **Every framework, library, package, runtime, or base image involved in the change** — current API, deprecations, breaking changes between versions, known CVEs, security advisories
- **Every external tool, CLI, flag, or forensic utility** whose behavior the change depends on — verify signatures, current output format, flag semantics, and any recent changes to evidence-handling behavior
- **Every upstream MCP server repo** the change interacts with — latest tagged version, open issues, breaking changes, unresolved bugs
- **Every protocol, spec, or standard** the change interacts with (MCP protocol, Docker APIs, file-format specs) — look for recent revisions
- **Forensic / legal / evidentiary context relevant to the task** — current best practices, admissibility considerations, known artifacts or anti-forensic techniques that affect correctness

Then broaden: is there a recent post-mortem, GitHub issue, or advisory describing a bug very similar to what you're about to fix or introduce? Check.

If your web research is inconclusive, contradicts your prior assumptions, or returns nothing relevant — **say so explicitly** before proceeding. Do not silently fill gaps with memory.

### Phase 2: Full Codebase Review — Understand the Blast Radius

Read the **actual current state** of the codebase. Do not rely on memory from previous sessions, and do not trust summaries — open the files.

Baseline reading (always, every session):

- `CLAUDE.md` (this file) and `README.md`
- Top-level configuration: build/orchestration files, dependency manifests, environment templates, any manifest that controls what the AI client sees (e.g., `.mcp.json`, `~/.mcphost.yml`)

Task-specific reading (scale to the change):

- **Every file you plan to modify — in full**, not just the region you're touching. Adjacent code often encodes invariants that aren't obvious from the target line alone.
- **Every file that imports or is imported by the files you're touching** — to see the blast radius
- **Related tests, schemas, fixtures, type definitions, and Pydantic models** — they describe the contract you're about to honor or break
- **Any chain-of-custody, logging, or audit code path** the change could cross — this is a legal-grade invariant in this codebase
- **Any documentation, playbook, or prompt template** that references the behavior you're changing
- **Any orchestration or glue layer** (compose files, Makefile targets, container entrypoints, `dfireballz/backends/docker.py` mappings, `tools_catalog.json`) that wires the touched component into the rest of the system

If mid-review you discover the change touches more than you thought, **expand the review** — do not push ahead with a partial picture.

### Phase 3: Understand Before Acting

Before writing code, answer these internally:

1. **Root cause** — not the symptom, the actual root cause?
2. **Blast radius** — which other files, modules, behaviors, or contracts does this change affect?
3. **Stable contracts** — does the fix break any stable internal contract that downstream consumers rely on? Examples include the **Chain of Custody contract** (every evidence access must create a `chain_of_custody_log` entry), MCP tool signatures, the `tools_catalog.json` schema, and any playbook/prompt contract.
4. **Security & evidentiary invariants** — does it violate any core safety rule? Shell-injection safety (`shell=False`), secret/API-key handling, Pydantic validation of MCP tool inputs, the read-only mount on evidence paths.
5. **Architecture invariants** — does it break the stdio-only MCP transport model, expose a port that must stay internal-only, add an HTTP/SSE surface where none should exist, or write output anywhere other than `/workspace/output`?
6. **Simplicity** — is there a simpler fix that achieves the same result?

Only after answering all six — write the fix.

---

## Implementation Principles

These govern *how* you write code once the mandatory protocol is complete. They complement Phase 3, not replace it.

### 1. Think Before Coding
**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First
**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: *"Would a senior engineer say this is overcomplicated?"* If yes, simplify.

### 3. Surgical Changes
**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that **your** changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution
**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## Project Purpose

DFIReballz is a digital forensics and cybercrime investigation platform. All code decisions should reflect the context of a professional forensic investigator: evidence integrity, reproducibility, chain of custody, and admissibility come before convenience.

---

## Architecture

Hard architectural rules. Breaking any of these is a bug, not a tradeoff.

- **MCP Transport: stdio only.** Every MCP server runs `mcp.run(transport="stdio")`. The AI host (Claude Code / Claude Desktop / MCPHost) connects via `docker exec -i <container> <cmd>`. **No HTTP ports, no proxy, no gateway for direct AI host connections.**
- **ChatGPT note:** ChatGPT uses HTTP/SSE transport. Use mcpo proxy (port 8812) as the bridge.
- **Ollama note:** Ollama has no native MCP support. Use MCPHost (`mark3labs/mcphost`) or Open WebUI + mcpo proxy as the bridge. MCPHost model syntax: `mcphost -m ollama/qwen3:8b --config ~/.mcphost.yml`.
- **Orchestrator API** (port 8800) manages cases, evidence, and playbooks.
- **Open WebUI / ChatGPT scenario:** the mcpo container (port 8812) exposes MCP servers as OpenAPI endpoints. The mcpo container needs `/var/run/docker.sock` mounted to run `docker exec` commands.
- **Host output directory:** `./output/` is bind-mounted to the Claude Code container at `/workspace/output`, containing `findings/`, `screenshots/`, `logs/`, `exports/`, `timelines/`. **All investigation output must be written here** so it's visible on the host.
- **Evidence paths are read-only.** The filesystem MCP server is scoped to `/cases`, `/evidence`, `/reports`, `/output` — evidence is *always* mounted read-only.

### MCP Servers (stdio only — no exposed ports)

| Container | Key Tools |
|-----------|-----------|
| `kali-forensics` | Volatility3, bulk_extractor, tshark, YARA, dc3dd, Sleuthkit, Foremost, Binwalk, ExifTool |
| `winforensics` | MFT, EVTX, Registry, Amcache, SRUM, ShellBags, USN Journal, WinRM remote |
| `osint` | Maigret, Sherlock, Holehe, theHarvester, subfinder, amass, DNSTwist |
| `threat-intel` | VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan |
| `binary-analysis` | Ghidra headless, Radare2, Capa (MITRE ATT&CK), YARA, pefile, lief |
| `network-forensics` | tshark (18 tools), tcpdump capture, PCAP carving, JA3/JA3S, GeoIP |
| `filesystem` | Scoped to `/cases`, `/evidence`, `/reports`, `/output` — evidence always read-only |

---

## Code Standards

- All Python code must be type-annotated
- All MCP tool inputs must be validated with Pydantic
- All tool subprocess calls must use `subprocess.run(args_list, shell=False)`
- **Every evidence access must create a `chain_of_custody_log` entry** — this is a legal-grade invariant, not a nice-to-have
- Never use `shell=True` in subprocess calls
- Never log API keys or secrets
- Never expose an MCP server over anything other than stdio for the direct AI-host path

---

## Development Commands

### Core
- `make start` / `make up` — Start all services
- `make stop` / `make down` — Stop all services
- `make dev` — Start development environment (hot-reload)
- `make status` / `make ps` — Show container health status

### Python Package (`dfireballz/`)
- `make venv` — Create Python venv and install package
- `make install-dev` — Install dfireballz with dev dependencies
- `make test-pkg` — Run dfireballz package tests
- `make lint` — Run ruff linter on `dfireballz/` and `tests/`
- `make format` — Auto-format code with ruff
- `make typecheck` — Run mypy type checking
- `make audit` — Run pip-audit on dependencies
- `make version` — Show dfireballz package version

### Testing & Security
- `make test` — Run all tests (package + orchestrator)
- `make test-smoke` — Run container smoke tests
- `make test-security` — Trivy + Bandit security scan

### Container Debug
- `make shell-kali` — Debug Kali forensics container
- `make shell-osint` — Debug OSINT container
- `make shell-netforensics` — Debug network forensics container
- `make shell-winforensics` — Debug Windows forensics container
- `make shell-binary` — Debug binary analysis container
- `make shell-threat` — Debug threat-intel container
- `make shell-filesystem` — Debug filesystem container
- `make shell-orchestrator` — Debug orchestrator container

### Per-Service Operations
- `make log-<service>` — Tail logs (kali, osint, netforensics, winforensics, binary, threat, filesystem, orchestrator, db, redis)
- `make restart-<service>` — Restart a specific service

### Utilities
- `make setup-keys` — Add/update threat intel API keys (interactive, with validation)
- `make health` — Check MCP server container health
- `make configure-mcp` — Regenerate `.mcp.json` / `~/.mcphost.yml` for your AI host
- `make start-openwebui` — Start with Open WebUI + Ollama (`--profile openwebui`)
- `make report` — Generate report from last session
- `make clean` — Remove containers and local images
- `make nuke` — Remove EVERYTHING (containers, volumes, images)

---

## Adding a New MCP Server

Follow the existing conventions in the repo — don't invent new patterns. Before you start, read at least one existing server end-to-end to match its structure.

1. Create `mcp-servers/new-server/` directory alongside existing ones
2. Write a Dockerfile matching project conventions (non-root user, health check required, minimal base image)
3. Implement `server.py` using the same MCP framework and **stdio transport** the other servers use
4. Register in `docker-compose.yml` and regenerate `.mcp.json` via `make configure-mcp`
5. Register the exec command in `dfireballz/backends/docker.py` `_TOOL_COMMANDS` mapping
6. Add tools to `dfireballz/data/tools_catalog.json`
7. Document the exposed tools in the README MCP reference table
8. Add unit tests — at minimum, Pydantic validation tests for every tool input, and a chain-of-custody test for any tool that touches evidence

---

## Key Reference Links

| Resource | URL |
|----------|-----|
| MCP Protocol spec | https://modelcontextprotocol.io |
| FastMCP (Python MCP framework) | https://pypi.org/project/fastmcp |
| WinForensics MCP | https://github.com/x746b/winforensics-mcp |
| Wireshark MCP (18 tools) | https://github.com/PreistlyPython/wireshark-mcp |
| FuzzingLabs Security Hub | https://github.com/FuzzingLabs/mcp-security-hub |
| MCPHost (Ollama bridge) | https://github.com/mark3labs/mcphost |
| mcpo (Open WebUI proxy) | https://github.com/open-webui/mcpo |
| Chainsaw (EVTX/Sigma hunting) | https://github.com/WithSecureLabs/chainsaw |

---

## Self-Check — Are These Guidelines Working?

These guidelines are working if:
- Diffs contain fewer unnecessary changes
- Fewer rewrites due to overcomplication
- Clarifying questions come **before** implementation, not after mistakes
- Every Phase 3 question is answered before code is written
- No `shell=True`, no missing `chain_of_custody_log` entries, no MCP server exposed over HTTP/SSE on the direct AI-host path, no evidence mount that isn't read-only, no output written outside `/workspace/output`
- When research is inconclusive or the codebase review surfaces a surprise, it's named explicitly instead of papered over

---

*This platform will be used in real cybercrime investigations. Every decision must hold up under legal scrutiny. Research first. Understand fully. Then act.*
