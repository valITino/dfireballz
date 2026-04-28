# Complete Investigation — All-In-One

Perform a full end-to-end digital forensic investigation of [TARGET], including evidence intake, multi-domain analysis, threat intelligence correlation, timeline reconstruction, incident response assessment, and final report generation. This template covers every investigative domain in a single workflow, organized under the canonical six-phase forensic process model.

---

## Important: Use MCP Servers and Their Tools

You MUST use the DFIReballz MCP servers and their tools to execute every phase of this investigation. Do NOT attempt manual analysis or skip tool usage. Call the tools provided by each MCP container listed below — they are your primary instruments.

**Available MCP Containers & Tools:**

| Container | Tools |
|-----------|-------|
| `kali-forensics` | Volatility3, bulk_extractor, YARA, dc3dd, Sleuthkit, Foremost, ExifTool |
| `winforensics` | MFT parser, EVTX parser, Registry parser, Prefetch, ShellBags, Amcache, USN Journal, SRUM, Browser history |
| `osint` | Maigret, Sherlock, Holehe, SpiderFoot, theHarvester, subfinder, DNSTwist |
| `threat-intel` | VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan |
| `binary-analysis` | Ghidra headless, Radare2, Capa (MITRE ATT&CK), YARA, pefile, Binwalk |
| `network-forensics` | tshark (18 analysis tools), tcpdump, PCAP carving, JA3/JA3S fingerprinting, GeoIP |
| `filesystem` | Scoped file access to /cases, /evidence (read-only), /reports, /output |

---

## Forensic Process Mapping

Canonical six-phase model from `docs/forensic-process.md`. Every operational activity in this template is mapped to one of: **Readiness → Identification → Acquisition → Examination → Analysis → Reporting**.

---

## Host Directory Layout

```
/cases/<case-id>/
  ├── 01-readiness/         ← Pre-flight: MCP health, tool versions, API keys, time
  ├── 02-identification/    ← Evidence records, scope, authority, photographs
  ├── 03-acquisition/       ← Working copies + verified hashes + manifest
  ├── 04-examination/       ← Per-evidence extractions (disk, memory, win artifacts, malware)
  ├── 05-analysis/          ← Network analysis, threat-intel, OSINT, timelines, attack chain, impact
  └── 06-reporting/         ← Closure manifest, sealed audit-log digest, recommendations

/evidence/<case-id>/        ← READ-ONLY originals (disk-images, memory-dumps, pcaps, malware-samples, documents)
/reports/<case-id>/         ← Final deliverables (report.md, report.pdf, process-log.md, issues-log.md)
```

**Claude Code paths** are prefixed with `/workspace/`:
- `/workspace/cases/`, `/workspace/evidence/` (read-only), `/workspace/reports/`
- `/workspace/output/` — host-visible output: `findings/`, `screenshots/`, `logs/`, `exports/`, `timelines/`

---

## Documentation & Logging Requirements

Throughout the ENTIRE investigation, you MUST:

1. **Document the process thoroughly** — every tool invocation, parameters, result summary in `/reports/<case-id>/process-log.md` (or `/workspace/output/logs/process-log.md`).
2. **Document every issue, error, warning, and problem** — full details, tool/container, remediation in `/reports/<case-id>/issues-log.md` (or `/workspace/output/logs/issues-log.md`).
3. **Log chain of custody** — `log_chain_of_custody` for every evidence access, no exceptions.
4. **Never modify originals** — `/evidence/` is read-only.
5. **Write findings incrementally** under the relevant phase directory.

---

## Phase 1 — Readiness

1. Confirm case is open with documented authority
2. Health-check all seven MCP servers (`kali-forensics`, `winforensics`, `osint`, `threat-intel`, `binary-analysis`, `network-forensics`, `filesystem`)
3. Verify API keys: VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan, SecurityTrails, Censys
4. Confirm UTC time sync; pin every relevant tool/symbol-table/rule-set version into `01-readiness/case-precondition.json`
5. Log chain of custody (`case_opened`)

## Phase 2 — Identification

1. Enumerate evidence sources: disk images, memory dumps, PCAPs, malware samples, documents, email
2. Apply RFC 3227 order of volatility for the acquisition order
3. Photograph physical evidence in situ before handling
4. Document make/model/serial/condition/location for physical items
5. Classify the incident type (malware, ransomware, data breach, unauthorized access, phishing, insider threat, OSINT)
6. Establish timeline boundaries (first signal, current state)
7. Assign case-scoped evidence IDs (`<case-number>-E<NNN>`)
8. Document legal authority and scope per item
9. Log chain of custody (`identified`) for each item

## Phase 3 — Acquisition

For each evidence item:

1. Engage write-blocker where applicable
2. Copy / image into `cases/<case-id>/03-acquisition/<evidence-id>/`
3. Compute SHA256 + MD5 (SHA256 primary; MD5/SHA1 secondary for legacy threat-intel feeds)
4. Independently verify with a second tool (`hashdeep`)
5. Record acquisition method, tool, version, write-blocker, examiner, timestamps
6. Write the acquisition manifest entry
7. Log chain of custody (`acquired`, `verified`)
8. Any hash mismatch is a stop-the-world event — document and escalate

## Phase 4 — Examination

Re-verify source-image hash before each major examination tool. Operate exclusively on working copies. Use **kali-forensics**, **winforensics**, **binary-analysis**, **filesystem**:

### 4a. Disk & Filesystem
1. Sleuthkit — partition layout, file listing, deleted file recovery
2. Foremost — file carving (deleted/fragmented)
3. ExifTool — metadata (documents, images, media)
4. dc3dd — forensic-imaging verification (if applicable)
5. bulk_extractor — emails, URLs, credit cards, domains

### 4b. Memory
1. Volatility3 with auto-detection: pslist, pstree, psxview, malfind
2. DLL analysis: dlllist, ldrmodules
3. Network from memory: netscan, DNS cache
4. Persistence: registry run keys, services, scheduled tasks from memory
5. Credential extraction: hashdump, lsadump (if authorized)
6. YARA across memory: yarascan
7. String extraction from suspicious processes

### 4c. Windows Artifacts
1. MFT parsing — file creation/modification/access timestamps
2. EVTX — Security, System, PowerShell, RDP, logon events
3. Registry — persistence keys, user activity, USB history
4. Prefetch — program execution history
5. Amcache — application execution + installation
6. ShellBags — folder access history
7. USN Journal — file-system changes
8. SRUM — network usage, application resource consumption
9. Browser history — visited URLs, downloads, cached creds

### 4d. Malware & Binary
1. YARA scanning against known malware signatures
2. Capa — capability detection with MITRE ATT&CK mapping
3. Radare2 — imports, exports, sections, strings
4. Ghidra headless — pseudocode for key functions
5. Binwalk — firmware/embedded file extraction
6. Identify packing, obfuscation, anti-analysis techniques
7. Extract embedded C2 addresses, configuration data

## Phase 5 — Analysis

Use **network-forensics**, **threat-intel**, **osint**:

### 5a. Network Forensics
1. PCAP overview — protocol stats, conversations, endpoints
2. DNS — queries, suspicious domains, DNS tunneling
3. HTTP/HTTPS — requests, downloads, POST data
4. TLS — JA3/JA3S fingerprints, certificate anomalies
5. SMB / RDP — lateral movement, file transfers, brute force
6. Beaconing detection — regular-interval C2 patterns
7. Data exfiltration indicators — large outbound transfers, DNS encoding
8. Stream reconstruction — follow TCP streams, extract transferred files
9. GeoIP on external IPs

### 5b. OSINT (if attribution leads exist)
1. Username/email enumeration — Maigret, Sherlock, Holehe
2. Domain/infrastructure — theHarvester, SpiderFoot, subfinder
3. DNSTwist for typosquatting
4. Map attacker digital footprint

### 5c. Threat Intelligence Enrichment
1. Hash lookups — VirusTotal, MalwareBazaar
2. IP reputation — AbuseIPDB, Shodan
3. Domain/URL reputation — URLScan, ThreatFox
4. Cross-reference all IoCs with known threat-actor TTPs
5. Identify related campaigns and threat groups
6. Full MITRE ATT&CK technique mapping across all findings

### 5d. Timeline Reconstruction & Attack Chain
1. Build a unified timeline from ALL artifact timestamps
2. Identify the initial access vector
3. Map: initial access → execution → persistence → privilege escalation → lateral movement → collection → exfiltration → impact
4. Document anti-forensics and cleanup attempts
5. Store the timeline in `cases/<case-id>/05-analysis/timelines/`

### 5e. Impact Assessment
1. Quantify data loss and exposure
2. Assess system compromise scope (affected hosts, accounts)
3. Evaluate credential exposure
4. Determine regulatory notification requirements (GDPR / HIPAA / PCI-DSS / etc.)
5. Provide containment, eradication, recovery recommendations
6. Document lessons learned and prevention measures

Each finding cites: evidence ID + source SHA256 + audit IDs; mark fact vs. interpretation.

## Phase 6 — Reporting

1. `get_payload_schema` → ForensicPayload format
2. Populate every applicable section: `malware_samples`, `network_connections`, `processes`, `artifacts`, `user_accounts`, `dns_records`, `iocs`, `timeline_events`, `mitre_techniques`
3. Re-verify every source-evidence hash one last time and attach the result
4. Sign / seal the audit log: capture SHA-256 of the JSONL trail; pin into report and into chain-of-custody log
5. `aggregate_results` → `generate_report` format `"both"` (MD + PDF)
6. Verify the report is written to `/reports/<case-id>/`
7. Write `06-reporting/closure-manifest.json`
8. Log chain of custody (`case_closed`)
9. Finalize the process log and issues log

---

## MCP Containers to Use

ALL containers: `kali-forensics`, `winforensics`, `network-forensics`, `binary-analysis`, `threat-intel`, `osint`, `filesystem`.

Skip any sub-step that does not apply to the evidence type — but document WHY it was skipped in the process log.
