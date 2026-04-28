# Incident Response Investigation

Conduct full incident response for [TARGET].

---

## Important: Use MCP Servers and Their Tools

You MUST use the DFIReballz MCP servers and their tools to execute every phase below. Do NOT attempt manual analysis or skip tool usage. Call the tools provided by each MCP container — they are your primary instruments.

---

## Forensic Process Mapping

Canonical six-phase model from `docs/forensic-process.md`. Incident response touches all six phases; this template structures the IR-specific activities (containment assessment, attack chain, impact) under Examination and Analysis.

---

## Host Directory Layout

```
/cases/<case-id>/
  ├── 01-readiness/         ← Pre-flight + IR-specific authority (incident scope, contacts)
  ├── 02-identification/    ← Affected systems, evidence records, classification
  ├── 03-acquisition/       ← Working copies + verified hashes
  ├── 04-examination/       ← Forensic extractions
  ├── 05-analysis/          ← Attack chain, threat-intel, impact assessment, timeline
  └── 06-reporting/         ← Closure manifest, containment/eradication/recovery plan

/evidence/<case-id>/        ← READ-ONLY originals
/reports/<case-id>/         ← Final deliverables
```

**Claude Code paths** are prefixed with `/workspace/`.

---

## Documentation & Logging Requirements

1. **Document every tool invocation** — `process-log.md`.
2. **Document errors and issues** — `issues-log.md`.
3. **Log chain of custody** for every evidence access. **Originals are read-only.**
4. **Write findings incrementally** under the relevant phase directory.

---

## Phase 1 — Readiness

1. Confirm IR authorization is documented (incident commander, scope, legal contacts)
2. Health-check all relevant MCP servers
3. Verify API keys for threat-intel
4. Pin tool versions; record IR start timestamp into `01-readiness/case-precondition.json`

## Phase 2 — Identification

1. **Triage** — initial scope of compromise (affected hosts, accounts, services)
2. **Classify** the incident (malware, ransomware, data breach, unauthorized access, insider threat)
3. **Establish** timeline boundaries (first signal, current state)
4. **Containment-relevant identification** — compromised systems and accounts; map any active threats still present
5. Assign evidence IDs for every artifact to be collected (disk, memory, EVTX, PCAPs)
6. Log chain of custody (`identified`)

## Phase 3 — Acquisition

Use **kali-forensics**, **winforensics**, **network-forensics**, **filesystem**:

1. Memory captures first (volatile), then disk images, then logs, then PCAPs
2. Copy into `cases/<case-id>/03-acquisition/<evidence-id>/`
3. Compute SHA256 + MD5; independently verify with a second tool
4. Write acquisition manifest entries
5. Log chain of custody (`acquired`, `verified`)

## Phase 4 — Examination

Re-verify source hash before each major tool:

1. **Disk forensics** — Sleuthkit, Foremost (carving)
2. **Memory forensics** — Volatility3 full suite
3. **Windows artifacts** — MFT, EVTX, Registry, Prefetch, Amcache, ShellBags, USN Journal, SRUM, Browser history
4. **Network forensics** — tshark on captured PCAPs
5. **Metadata** — ExifTool

## Phase 5 — Analysis

Use **threat-intel**, **osint**, **network-forensics**:

1. **Attack chain reconstruction** — initial access → execution → persistence → privilege escalation → lateral movement → collection → exfiltration → impact (incl. anti-forensics / cleanup attempts)
2. **Threat-intel enrichment** — IoCs against VirusTotal, ThreatFox, AbuseIPDB
3. **Attribution indicators** if applicable
4. **MITRE ATT&CK technique mapping**
5. **Related-campaign identification**
6. **Timeline** unified across all evidence
7. **Impact assessment** — data loss / exposure quantification, system compromise scope, credential exposure, regulatory notification requirements (GDPR / HIPAA / PCI-DSS / etc.)
8. Each finding cites evidence ID + SHA256 + audit IDs; fact vs. interpretation

## Phase 6 — Reporting

1. `get_payload_schema` → populate full ForensicPayload (every applicable section)
2. Attach attack chain (with ATT&CK mapping), impact assessment, IoC table
3. Provide containment / eradication / recovery recommendations + lessons learned
4. Re-verify all source-evidence hashes
5. `aggregate_results` → `generate_report` format `"both"`
6. Write `06-reporting/closure-manifest.json`; log `case_closed`
7. Finalize process + issues logs

## MCP Containers to Use

- ALL containers: kali-forensics, winforensics, network-forensics, binary-analysis, threat-intel, osint, filesystem
