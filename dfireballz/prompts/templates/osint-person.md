# OSINT Person Investigation

Conduct an open-source intelligence investigation on [TARGET].

---

## Important: Use MCP Servers and Their Tools

You MUST use the DFIReballz MCP servers and their tools to execute every phase below. Do NOT attempt manual analysis or skip tool usage. Call the tools provided by each MCP container — they are your primary instruments.

---

## Host Directory Layout

All MCP containers share these mounted directories:

```
/cases/                     ← Case working directories (read/write)
  └── <case-id>/
      ├── notes/            ← Investigator notes
      ├── artifacts/        ← Extracted artifacts
      └── timelines/        ← Case-specific timelines

/evidence/                  ← Evidence files (READ-ONLY — never modify originals)
  └── <case-id>/

/reports/                   ← Final reports and deliverables (read/write)
  └── <case-id>/
```

**Claude Code paths** are prefixed with `/workspace/`:
`/workspace/cases/`, `/workspace/evidence/` (read-only), `/workspace/reports/`, `/workspace/results/`
`/workspace/output/` — host-visible output: `findings/`, `screenshots/`, `logs/`, `exports/`, `timelines/`

---

## Documentation & Logging Requirements

1. **Document the process thoroughly** — log every tool invocation, parameters, and result summary. Store process logs in `/reports/<case-id>/process-log.md` (or `/workspace/output/logs/process-log.md`).
2. **Document every issue, error, warning, and problem thoroughly** — record full details including error messages, the tool/container involved, and remediation steps. Store in `/reports/<case-id>/issues-log.md` (or `/workspace/output/logs/issues-log.md`).
3. **Log chain of custody** for every evidence access. **Never modify original evidence.**
4. **Write findings incrementally** to `/cases/<case-id>/artifacts/` or `/workspace/output/findings/`.

---

## Phase 1: Username/Email Enumeration

Use **osint** MCP server:
1. **Maigret** — Search username across 2500+ platforms
2. **Sherlock** — Social media platform search
3. **Holehe** — Check email registration on services
4. **h8mail** — Breach database lookup (if configured)

## Phase 2: Domain/Infrastructure

Use **osint** MCP server:
1. **theHarvester** — Harvest emails, subdomains, names from public sources
2. **SpiderFoot** — Automated OSINT collection and correlation
3. **subfinder** — Discover associated subdomains

## Phase 3: Threat Intelligence

Use **threat-intel** MCP server:
1. Check known IPs on AbuseIPDB
2. Shodan search for associated infrastructure
3. URLScan for web presence analysis

## Phase 4: Correlation

1. Cross-reference usernames across platforms
2. Map the digital footprint
3. Identify potential aliases
4. Document timeline of online activity

## Phase 5: Reporting

1. Structure findings with IoCs and user_accounts
2. Include platform presence map
3. Generate report and store in `/reports/<case-id>/`
4. Finalize process log and issues log

## MCP Containers to Use

- osint (Maigret, Sherlock, Holehe, SpiderFoot, theHarvester, subfinder)
- threat-intel (AbuseIPDB, Shodan, URLScan)
- filesystem (evidence and report file access)
