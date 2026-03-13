# OSINT Domain Investigation

Investigate the domain/infrastructure [TARGET].

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

## Phase 1: DNS & Subdomain Enumeration

Use **osint** MCP server:
1. **subfinder** — Passive subdomain discovery
2. **DNSTwist** — Typosquatting and phishing domain detection
3. **theHarvester** — Email and subdomain harvesting
4. DNS record enumeration (A, AAAA, MX, NS, TXT, CNAME)

## Phase 2: Infrastructure Analysis

Use **threat-intel** MCP server:
1. **Shodan** — Exposed services, ports, technologies
2. **URLScan** — Web page analysis and screenshot
3. WHOIS lookup — Registration details, dates, registrant
4. SSL certificate analysis — Issuer, SAN, validity

## Phase 3: Threat Assessment

Use **threat-intel** MCP server:
1. **AbuseIPDB** — Check hosting IPs for abuse reports
2. **ThreatFox** — IoC lookup for associated malware
3. **VirusTotal** — Domain reputation check
4. Historical DNS records analysis

## Phase 4: Web Presence

Use **osint** MCP server:
1. Technology detection
2. Security header analysis
3. Associated email addresses
4. Historical changes (if available)

## Phase 5: Reporting

1. Structure findings with dns_records, whois, IoCs
2. Include infrastructure map
3. Provide risk assessment
4. Generate report and store in `/reports/<case-id>/`
5. Finalize process log and issues log

## MCP Containers to Use

- osint (subfinder, DNSTwist, theHarvester, SpiderFoot)
- threat-intel (Shodan, AbuseIPDB, URLScan, VirusTotal, ThreatFox)
- filesystem (evidence and report file access)
