# Phishing Investigation

Analyze a phishing incident targeting [TARGET].

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

## Phase 1: Email Analysis

1. Log chain of custody for the phishing email
2. Parse email headers (SPF, DKIM, DMARC results)
3. Identify true sender (X-Originating-IP, Received headers)
4. Extract URLs, attachments, and embedded content

## Phase 2: URL/Domain Investigation

Use **osint** and **threat-intel** MCP servers:
1. Check suspicious URLs on URLScan
2. DNSTwist for typosquatting detection
3. theHarvester for related infrastructure
4. WHOIS lookup on sender and phishing domains
5. Shodan for hosting infrastructure analysis

## Phase 3: Attachment Analysis

Use **kali-forensics** and **binary-analysis** MCP servers:
1. Hash all attachments (SHA256, MD5)
2. VirusTotal lookup for known malware
3. ExifTool for document metadata
4. YARA scan for malicious macros/scripts
5. If executable: Capa + Radare2 analysis

## Phase 4: Credential Harvesting Check

1. Screenshot the phishing page for evidence
2. Identify credential harvesting form fields
3. Check if credentials were submitted (browser artifacts)
4. Determine scope of compromised accounts

## Phase 5: Threat Intelligence

Use **threat-intel** MCP server:
1. Cross-reference IoCs with ThreatFox
2. Check sender IP on AbuseIPDB
3. MalwareBazaar for attachment hashes
4. Identify related phishing campaigns

## Phase 6: Reporting

1. Include email artifacts with header analysis
2. Document attack chain from delivery to potential impact
3. Provide user awareness recommendations
4. Generate report and store in `/reports/<case-id>/`
5. Finalize process log and issues log

## MCP Containers to Use

- osint (theHarvester, DNSTwist, subfinder, SpiderFoot)
- threat-intel (VirusTotal, URLScan, AbuseIPDB, ThreatFox, MalwareBazaar, Shodan)
- kali-forensics (ExifTool, YARA, bulk_extractor)
- binary-analysis (Capa, Radare2 — for attachments)
- filesystem (evidence file access)
