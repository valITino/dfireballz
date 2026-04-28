# Phishing Investigation

Analyze a phishing incident targeting [TARGET].

---

## Important: Use MCP Servers and Their Tools

You MUST use the DFIReballz MCP servers and their tools to execute every phase below. Do NOT attempt manual analysis or skip tool usage. Call the tools provided by each MCP container — they are your primary instruments.

---

## Forensic Process Mapping

This template follows the canonical six-phase forensic process model defined in `docs/forensic-process.md`: **Readiness → Identification → Acquisition → Examination → Analysis → Reporting**. Phase headers below correspond to that model. The phase-tagged playbook companion is `playbooks/phishing-investigation.md`.

---

## Host Directory Layout

All MCP containers share these mounted directories:

```
/cases/                     ← Case working directories (read/write)
  └── <case-id>/
      ├── 01-readiness/         ← Pre-flight: MCP health, tool versions, API keys, time
      ├── 02-identification/    ← Evidence records, photos, authority
      ├── 03-acquisition/       ← Working copies, hashes, manifests
      ├── 04-examination/       ← Extracted artifacts (per evidence-id)
      ├── 05-analysis/          ← Findings, IOCs, timelines, hypotheses
      └── 06-reporting/         ← Closure manifest, sealed audit-log digest

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
4. **Write findings incrementally** to the appropriate phase directory under `cases/<case-id>/0N-<phase>/` or `/workspace/output/findings/`.

---

## Phase 1 — Readiness

1. Confirm the case is open with documented authority for handling the email
2. Health-check the MCP servers needed: osint, threat-intel, kali-forensics, filesystem
3. Verify required API keys are present: URLScan, VirusTotal, AbuseIPDB
4. Confirm host time source is UTC-synced
5. Pin tool versions for the playbook into `cases/<case-id>/01-readiness/case-precondition.json`

## Phase 2 — Identification

1. Classify the report as phishing
2. Create the evidence record for the email: source, format (EML/MSG only — never forwarded), reporting party, authority reference
3. Assign a case-scoped evidence ID
4. Log chain of custody (`identified` action)

## Phase 3 — Acquisition

1. Copy the email to `cases/<case-id>/03-acquisition/<evidence-id>/`
2. Compute SHA-256 + MD5; record in the acquisition log
3. Independently re-verify with a second hashing tool (`hashdeep`)
4. Write the acquisition manifest entry
5. Log chain of custody (`acquired`, `verified`)

## Phase 4 — Examination

Operates on the working copy from Phase 3 — never on the original.

Use **kali-forensics**, **osint**, **threat-intel**, **binary-analysis**, **filesystem**:

1. **Email headers** — parse SPF, DKIM, DMARC; identify true sender (X-Originating-IP, Received chain)
2. **URL extraction** — pull all URLs and embedded content
3. **URL/Domain investigation** — URLScan, DNSTwist (typosquatting), theHarvester, WHOIS, Shodan
4. **Attachment analysis** — SHA256 + MD5 of every attachment; VirusTotal lookup; ExifTool metadata; YARA scan; Capa + Radare2 if executable
5. **Credential harvesting check** — screenshot the phishing page; identify form fields; trace whether credentials were submitted
6. **HTML artifact extraction** — forms, iframes, scripts, tracking pixels, brand impersonation

## Phase 5 — Analysis

Use **threat-intel** MCP server:

1. Cross-reference IoCs with ThreatFox; sender IP on AbuseIPDB; attachment hashes on MalwareBazaar
2. Identify related phishing campaigns
3. Build the consolidated IoC list (domains, IPs, URLs, hashes)
4. Each finding must cite evidence ID + source-image SHA-256 + AI invocation audit ID
5. Distinguish fact vs. interpretation; confirm or refute hypotheses (sender_spoofing, account_compromise, credential_harvesting, malware_delivery, brand_impersonation)

## Phase 6 — Reporting

1. Call `get_payload_schema` for the ForensicPayload format
2. Populate every applicable section with citations
3. Document the attack chain from delivery to potential impact
4. Provide user-awareness recommendations
5. Re-verify the source-email hash one last time
6. Call `aggregate_results`, then `generate_report` with format `"both"` (MD + PDF)
7. Write closure manifest to `cases/<case-id>/06-reporting/closure-manifest.json`
8. Log chain of custody (`case_closed`)
9. Finalize process log and issues log

## MCP Containers to Use

- osint (theHarvester, DNSTwist, subfinder, SpiderFoot)
- threat-intel (VirusTotal, URLScan, AbuseIPDB, ThreatFox, MalwareBazaar, Shodan)
- kali-forensics (ExifTool, YARA, bulk_extractor, hashdeep)
- binary-analysis (Capa, Radare2 — for attachments)
- filesystem (evidence file access)
