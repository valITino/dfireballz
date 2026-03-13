# Incident Response Investigation

Conduct full incident response for [TARGET].

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

## Phase 1: Triage

1. Log chain of custody for all evidence
2. Identify scope of compromise
3. Classify incident type (malware, data breach, unauthorized access, insider threat)
4. Establish investigation timeline boundaries

## Phase 2: Containment Assessment

1. Identify compromised systems and accounts
2. Map network lateral movement
3. Assess data exfiltration risk
4. Document active threats still present

## Phase 3: Evidence Collection

Use **kali-forensics**, **winforensics**, **network-forensics**, and **filesystem** MCP servers:
1. **Disk forensics** — Sleuthkit, file carving with Foremost
2. **Memory forensics** — Volatility3 full analysis
3. **Windows artifacts** — Full Windows artifact suite (MFT, EVTX, Registry, etc.)
4. **Network forensics** — PCAP analysis with tshark
5. **Metadata** — ExifTool on relevant files

## Phase 4: Attack Chain Reconstruction

1. Initial access vector identification
2. Execution timeline (Prefetch, Amcache, EVTX)
3. Persistence mechanisms (Registry, Services, Scheduled Tasks)
4. Privilege escalation evidence
5. Lateral movement mapping
6. Data staging and exfiltration
7. Anti-forensics and cleanup attempts

## Phase 5: Threat Intelligence

Use **threat-intel** MCP server:
1. IoC enrichment via VirusTotal, ThreatFox, AbuseIPDB
2. Attribution indicators
3. MITRE ATT&CK technique mapping
4. Related campaign identification

## Phase 6: Impact Assessment

1. Data loss quantification
2. System compromise scope
3. Credential exposure assessment
4. Regulatory notification requirements

## Phase 7: Reporting

1. Full ForensicPayload with all sections populated
2. Attack chain with MITRE ATT&CK mapping
3. Containment, eradication, and recovery recommendations
4. Lessons learned and prevention measures
5. Generate report (both MD and PDF) and store in `/reports/<case-id>/`
6. Store timeline in `/cases/<case-id>/timelines/` or `/workspace/output/timelines/`
7. Finalize process log and issues log

## MCP Containers to Use

- ALL containers: kali-forensics, winforensics, network-forensics, binary-analysis, threat-intel, osint, filesystem
