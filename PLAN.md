# DFIReballz — blhackbox Construct Adaptation Plan

## Overview

Adapt the blhackbox project structure 1:1 for dfireballz, transforming it from a
flat `orchestrator/` + `mcp-servers/` layout into a unified Python package with CLI,
MCP server, Pydantic models, report generators, prompt templates, and proper packaging.

**Key additions beyond 1:1 structural copy:**
1. UI gets evidence/file upload capability for autonomous forensic processing
2. Reports generated inside the Claude Code container are exported to the host via bind-mounted `./reports` volume
3. All `.md` documentation files updated to reflect the new architecture

---

## Phase 1: Create the `dfireballz/` Python Package (Core Construct)

### 1.1 Package skeleton
Create `dfireballz/` top-level Python package mirroring `blhackbox/`:

```
dfireballz/
├── __init__.py              # __version__ = "2.0.0"
├── main.py                  # Click CLI (version, catalog, run-tool, report, templates, mcp)
├── config.py                # pydantic-settings (DB, Redis, API keys, dirs)
├── exceptions.py            # DfireballzError, ReportingError, ChainOfCustodyError
├── mcp/
│   ├── __init__.py
│   └── server.py            # Unified MCP server (stdio) — forensic tools
├── models/
│   ├── __init__.py
│   ├── base.py              # ForensicSession, Finding, Evidence, Target
│   └── forensic_payload.py  # ForensicPayload (adapted from AggregatedPayload)
├── backends/
│   ├── __init__.py
│   ├── base.py              # ToolBackend, ToolResult (abstract)
│   └── docker.py            # DockerBackend — runs tools via docker exec
├── reporting/
│   ├── __init__.py
│   ├── html_generator.py    # DFIReballz-branded HTML forensic reports
│   ├── md_generator.py      # Markdown forensic reports
│   ├── pdf_generator.py     # PDF via WeasyPrint
│   └── paths.py             # Organized report path: reports/reports-DDMMYYYY/
├── prompts/
│   ├── __init__.py           # load_template, list_templates
│   ├── claude_playbook.md    # Forensic investigation playbook for MCP host
│   └── templates/
│       ├── README.md
│       ├── full-investigation.md
│       ├── malware-analysis.md
│       ├── ransomware-investigation.md
│       ├── phishing-investigation.md
│       ├── network-forensics.md
│       ├── osint-person.md
│       ├── osint-domain.md
│       ├── memory-forensics.md
│       └── incident-response.md
├── utils/
│   ├── __init__.py
│   ├── logger.py             # Rich logging + DFIReballz banner
│   └── catalog.py            # Forensic tool catalog loader
├── modules/
│   ├── __init__.py
│   └── base.py               # Base module for future extensions
└── data/
    ├── __init__.py
    └── tools_catalog.json     # Forensic tool metadata
```

### 1.2 `ForensicPayload` model (adapted from `AggregatedPayload`)
The critical data contract. Forensic-domain models instead of pentest:

- `ForensicPayload` (top-level)
  - `case_id`, `session_id`, `target` (evidence source), `investigation_timestamp`
  - `findings: ForensicFindings`
    - `artifacts: list[ArtifactEntry]` — files, registry keys, MFT entries
    - `timeline_events: list[TimelineEvent]` — timestamped events
    - `iocs: list[IoCEntry]` — Indicators of Compromise (IP, hash, domain, URL)
    - `network_connections: list[NetworkConnection]` — suspicious connections
    - `processes: list[ProcessEntry]` — from memory/volatile analysis
    - `user_accounts: list[UserAccountEntry]` — account activity
    - `malware_samples: list[MalwareSample]` — identified malware
    - `vulnerabilities: list[VulnerabilityEntry]` — exploited vulns
    - `dns_records: list[DNSRecordEntry]`
    - `whois: WhoisRecord`
    - `email_artifacts: list[EmailArtifact]` — phishing headers, etc.
  - `chain_of_custody: list[CoCEntry]` — every evidence access logged
  - `error_log: list[ErrorLogEntry]`
  - `executive_summary: ExecutiveSummary`
  - `recommendations: list[RecommendationEntry]`
  - `metadata: ForensicMetadata` (tools_run, model, duration, hashes)

### 1.3 MCP Server (`dfireballz/mcp/server.py`)
Unified stdio MCP server exposing forensic orchestration tools:

- `run_tool` — execute forensic tool via docker exec backend
- `list_tools` — discover available forensic tools across containers
- `aggregate_results` — validate & persist ForensicPayload
- `get_payload_schema` — return ForensicPayload JSON schema
- `generate_report` — produce HTML/PDF/MD forensic reports
- `list_templates` — discover investigation templates
- `get_template` — load investigation template with placeholders
- `query_case` — retrieve case data from orchestrator API
- `log_chain_of_custody` — record CoC entry

### 1.4 CLI (`dfireballz/main.py`)
Click-based CLI mirroring blhackbox:
- `dfireballz version`
- `dfireballz catalog`
- `dfireballz run-tool --category forensics --tool volatility3 --params '{"target":"..."}'`
- `dfireballz report --session <id> --format pdf`
- `dfireballz templates list` / `dfireballz templates show <name>`
- `dfireballz mcp` — start stdio MCP server

### 1.5 Config (`dfireballz/config.py`)
pydantic-settings with:
- Database (PostgreSQL URL, user, password, db)
- Redis URL
- API keys (VirusTotal, Shodan, AbuseIPDB, etc.)
- Orchestrator URL (internal: http://orchestrator:8800)
- Results/reports/evidence directories
- Log level, max iterations

---

## Phase 2: Python Packaging (`pyproject.toml`, `setup.py`, `requirements.txt`)

### 2.1 `pyproject.toml`
```toml
[project]
name = "dfireballz"
version = "2.0.0"
requires-python = ">=3.11"
dependencies = [
    "click==8.1.8",
    "httpx==0.28.1",
    "pydantic>=2.11.0",
    "pydantic-settings>=2.10.1",
    "rich==13.9.4",
    "mcp>=1.23.0",
    "weasyprint==68.1",
    "jinja2==3.1.6",
    "aiofiles==24.1.0",
    "python-dotenv==1.0.1",
    "tenacity==9.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.4", "pytest-asyncio==0.25.2", "pytest-cov==6.0.0",
    "ruff==0.9.6", "mypy==1.14.1", "respx==0.22.0",
]

[project.scripts]
dfireballz = "dfireballz.main:cli"
```

### 2.2 `setup.py` (minimal, delegates to pyproject.toml)
### 2.3 `requirements.txt` (for pip-audit compatibility)

---

## Phase 3: Report Generation & Host Export

### 3.1 Report generators
Adapt blhackbox's HTML/PDF/MD generators for forensic context:
- DFIReballz branding, forensic-specific sections
- Chain of custody section in every report
- IoC table, timeline view, MITRE ATT&CK mapping
- Organized output: `reports/reports-DDMMYYYY/report-<case>-DDMMYYYY.<ext>`

### 3.2 Host export mechanism
The `./reports` directory is already bind-mounted into both the Claude Code container
and the orchestrator. Reports written to `/reports` inside any container automatically
appear on the host at `./reports/`.

**docker-compose.yml** already has:
```yaml
claude-code:
  volumes:
    - ./reports:/reports
```

We enhance this:
1. Add a `results/` bind-mount to claude-code for session JSON files
2. Add `make export-reports` command that copies latest reports to a user-friendly location
3. MCP `generate_report` tool writes to `/reports/` → automatically on host
4. UI gets a "Download Report" button that serves files from `/reports/`

---

## Phase 4: `.claude/` Integration (Claude Code Web + Docker)

### 4.1 `.mcp.json`
```json
{
  "mcpServers": {
    "dfireballz": {
      "command": "bash",
      "args": [".claude/mcp-start.sh"],
      "description": "dfireballz core MCP server — forensic tools, case management, report generation"
    }
  }
}
```

### 4.2 `.claude/mcp-start.sh`
- Create .venv if needed
- Install dfireballz package (editable mode)
- Load .env
- Exec `dfireballz mcp`

### 4.3 `.claude/hooks/session-start.sh`
- Remote-only (CLAUDE_CODE_REMOTE=true)
- Install [dev] deps
- Copy .env.example → .env
- Export venv to PATH
- Run health check

---

## Phase 5: UI Enhancement — Evidence Upload

### 5.1 New `EvidenceUpload` component
Add to the UI:
- Drag-and-drop file upload zone
- Supports any file type (disk images, PCAPs, memory dumps, documents, etc.)
- Computes SHA256 hash client-side before upload
- Uploads to orchestrator API: `POST /evidence/upload`
- Creates chain of custody entry automatically
- Shows upload progress and hash verification

### 5.2 New route: `/evidence`
- Evidence management page
- List uploaded evidence with hashes, timestamps, CoC log
- Download evidence, view metadata
- Link evidence to cases

### 5.3 Orchestrator API enhancement
- `POST /evidence/upload` — accept multipart file upload
- Compute SHA256/MD5/SHA1 hashes
- Store in `./evidence/<case_id>/` (read-only mount to MCP containers)
- Create chain_of_custody_log entry
- Return evidence metadata

---

## Phase 6: Testing (`tests/`)

### 6.1 Test suite mirroring source structure
```
tests/
├── __init__.py
├── conftest.py
├── test_cli.py
├── test_config.py
├── test_forensic_payload.py
├── test_mcp_server.py
├── test_models.py
├── test_reporting.py
├── test_backends.py
├── test_catalog.py
├── test_prompts.py
└── test_paths.py
```

---

## Phase 7: Makefile Expansion

Add blhackbox-style targets:
- `make up` — alias for `make start`
- `make lint` — `ruff check dfireballz/ tests/`
- `make format` — `ruff format dfireballz/ tests/`
- `make health` — health check all MCP servers
- `make nuke` — full cleanup (containers + volumes + images)
- `make push-all` — build & push all images
- `make report SESSION=<id>` — generate report via CLI
- `make wordlists` — download common forensic wordlists/signatures
- Per-service log targets: `make logs-kali`, `make logs-winforensics`, etc.
- Per-service restart targets

---

## Phase 8: CI/CD Updates

### 8.1 `.github/workflows/ci.yml`
- Add Python package install: `pip install -e ".[dev]"`
- Lint: `ruff check dfireballz/ tests/`
- Test: `pytest tests/ -v --tb=short`
- pip-audit security scan

### 8.2 `.github/workflows/build-and-push.yml`
Update matrix to build all dfireballz services:
- kali-forensics, winforensics, osint, threat-intel, binary-analysis, network-forensics, filesystem
- orchestrator, ui, db, claude-code

---

## Phase 9: Documentation Updates

### 9.1 Files to update:
- `CLAUDE.md` — reference new `dfireballz/` package, ForensicPayload contract, mcp server path
- `README.md` — full rewrite reflecting new architecture, unified package, CLI, templates
- `CONTRIBUTING.md` — update development workflow with new package structure
- `SECURITY.md` — add ForensicPayload schema contract, report export security
- `DOCKER.md` — new file documenting Docker architecture (mirroring blhackbox)
- `playbooks/README.md` — update with template system reference

---

## Phase 10: Volume & Export Architecture

### Reports export (containerized Claude Code → host):
```
Container path:    /reports/reports-DDMMYYYY/report-*.pdf
                        ↕ (bind mount)
Host path:         ./reports/reports-DDMMYYYY/report-*.pdf
```

### Results/session export:
```
Container path:    /results/session-<id>.json
                        ↕ (bind mount)
Host path:         ./results/session-<id>.json
```

### docker-compose.yml changes:
```yaml
claude-code:
  volumes:
    - ./cases:/cases
    - ./evidence:/evidence:ro
    - ./reports:/reports        # ← already exists
    - ./results:/results        # ← ADD: session JSON files
```

---

## Execution Order

1. Phase 1 — Python package (core construct)
2. Phase 2 — pyproject.toml, setup.py, requirements.txt
3. Phase 3 — Report generators + host export
4. Phase 4 — .claude/ integration
5. Phase 5 — UI evidence upload
6. Phase 6 — Tests
7. Phase 7 — Makefile
8. Phase 8 — CI/CD
9. Phase 9 — Documentation
10. Phase 10 — Volume architecture (docker-compose.yml)

---

## What stays unchanged
- All 7 MCP server containers (kali-forensics, winforensics, osint, etc.) — they keep their existing Dockerfiles and server.py files
- PostgreSQL database schema and init.sql
- Redis
- The existing orchestrator FastAPI app (keeps running alongside the new package)
- UI framework (React + Vite + Tailwind) — we only add evidence upload
- Docker security hardening (no-new-privileges, cap_drop, etc.)
- Claude Code Dockerfile and entrypoint (only minor volume updates)
