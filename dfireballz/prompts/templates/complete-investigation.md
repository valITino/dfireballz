# Complete Investigation — All-In-One

Perform a full end-to-end digital forensic investigation of [TARGET], including evidence intake, multi-domain analysis, threat intelligence correlation, timeline reconstruction, incident response assessment, and final report generation. This template covers every investigative domain in a single workflow.

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

## Host Directory Layout

All MCP containers share these mounted directories. Use them for reading evidence and storing output:

```
/cases/                     ← Case working directories (read/write)
  └── <case-id>/            ← Per-case folder
      ├── notes/            ← Investigator notes
      ├── artifacts/        ← Extracted artifacts
      └── timelines/        ← Case-specific timelines

/evidence/                  ← Evidence files (READ-ONLY — never modify originals)
  └── <case-id>/            ← Evidence scoped by case
      ├── disk-images/
      ├── memory-dumps/
      ├── pcaps/
      ├── malware-samples/
      └── documents/

/reports/                   ← Final reports and deliverables (read/write)
  └── <case-id>/
      ├── report.md
      └── report.pdf
```

**If running via Claude Code**, the paths are prefixed with `/workspace/`:
- `/workspace/cases/`, `/workspace/evidence/` (read-only), `/workspace/reports/`
- `/workspace/output/` — host-visible output with subdirectories:
  - `findings/` — analysis results and summaries
  - `screenshots/` — visual evidence captures
  - `logs/` — activity and audit logs
  - `exports/` — carved files and extracted objects
  - `timelines/` — event timeline reconstructions

---

## Documentation & Logging Requirements

Throughout the ENTIRE investigation, you MUST:

1. **Document the process thoroughly** — log every tool invocation, its parameters, and a summary of what it returned. Store process logs in `/reports/<case-id>/process-log.md` (or `/workspace/output/logs/` if using Claude Code).
2. **Document every issue, error, warning, and problem thoroughly** — if a tool fails, returns unexpected results, times out, or produces warnings, record the full details including the error message, the tool/container involved, and what you did next. Store error/issue logs in `/reports/<case-id>/issues-log.md` (or `/workspace/output/logs/issues-log.md` if using Claude Code).
3. **Log chain of custody** — use `log_chain_of_custody` for EVERY evidence access without exception.
4. **Never modify original evidence** — evidence at `/evidence/` is read-only.
5. **Write findings incrementally** — do not wait until the end; write partial findings as you go to `/cases/<case-id>/artifacts/` or `/workspace/output/findings/`.

---

## Phase 1: Evidence Intake & Triage

1. Log chain of custody for ALL evidence files
2. Verify evidence integrity — compute and record SHA256 hashes
3. Identify evidence types (disk image, memory dump, PCAP, files, email, malware sample)
4. Classify incident type (malware, ransomware, data breach, unauthorized access, phishing, insider threat)
5. Establish investigation timeline boundaries
6. Create a case directory under `/cases/<case-id>/`

## Phase 2: Disk & Filesystem Analysis

Use **kali-forensics** and **filesystem** MCP servers:
1. Examine file systems with Sleuthkit — partition layout, file listing, deleted file recovery
2. Carve files with Foremost — recover deleted/fragmented files
3. Extract metadata with ExifTool — documents, images, media files
4. Forensic imaging verification with dc3dd (if applicable)
5. Bulk data carving with bulk_extractor — emails, URLs, credit cards, domains

## Phase 3: Memory Forensics

Use **kali-forensics** MCP server:
1. Identify OS profile (Volatility3 auto-detection)
2. Process analysis — pslist, pstree, psxview, malfind for injection
3. DLL analysis — dlllist, ldrmodules for suspicious modules
4. Network connections — netscan for active connections, DNS cache
5. Persistence artifacts — registry run keys, services, scheduled tasks from memory
6. Credential extraction — hashdump, lsadump (if authorized)
7. YARA scan across memory — yarascan for malware signatures
8. String extraction from suspicious processes

## Phase 4: Windows Artifact Analysis

Use **winforensics** MCP server:
1. MFT parsing — file creation/modification/access timestamps
2. EVTX analysis — Security, System, PowerShell, RDP, logon events
3. Registry analysis — persistence keys, user activity, USB history
4. Prefetch files — program execution history
5. Amcache — application execution and installation records
6. ShellBags — folder access history
7. USN Journal — file system change journal
8. SRUM — network usage, application resource consumption
9. Browser history — visited URLs, downloads, cached credentials

## Phase 5: Malware & Binary Analysis

Use **binary-analysis** and **kali-forensics** MCP servers:
1. YARA scanning — match against known malware signatures
2. Capa — capability detection with MITRE ATT&CK technique mapping
3. Static analysis with Radare2 — imports, exports, sections, strings
4. Decompilation with Ghidra headless — pseudocode for key functions
5. Binwalk — firmware/embedded file extraction
6. Identify packing, obfuscation, and anti-analysis techniques
7. Extract embedded C2 addresses, configuration data

## Phase 6: Network Forensics

Use **network-forensics** MCP server:
1. PCAP overview — protocol statistics, conversations, endpoints
2. DNS analysis — all queries, suspicious domains, DNS tunneling indicators
3. HTTP/HTTPS analysis — requests, responses, file downloads, POST data
4. TLS analysis — JA3/JA3S fingerprints, certificate anomalies
5. SMB/RDP analysis — lateral movement, file transfers, brute force
6. Beaconing detection — regular-interval C2 communication patterns
7. Data exfiltration indicators — large outbound transfers, encoding in DNS
8. Stream reconstruction — follow TCP streams, extract transferred files
9. GeoIP analysis on all external IPs

## Phase 7: OSINT & Reconnaissance

Use **osint** MCP server:
1. Username/email enumeration — Maigret, Sherlock, Holehe
2. Domain/infrastructure — theHarvester, SpiderFoot, subfinder
3. DNS investigation — DNSTwist for typosquatting
4. Map the attacker's digital footprint if attribution indicators exist

## Phase 8: Threat Intelligence Enrichment

Use **threat-intel** MCP server:
1. File hash lookups — VirusTotal, MalwareBazaar
2. IP reputation — AbuseIPDB, Shodan
3. Domain/URL reputation — URLScan, ThreatFox
4. Cross-reference all IoCs with known threat actor TTPs
5. Identify related campaigns and threat groups
6. Full MITRE ATT&CK technique mapping across all findings

## Phase 9: Timeline Reconstruction & Attack Chain

1. Build a unified timeline from ALL artifact timestamps across all phases
2. Identify the initial access vector
3. Map the full attack chain: initial access → execution → persistence → privilege escalation → lateral movement → collection → exfiltration → impact
4. Document anti-forensics and cleanup attempts
5. Store the timeline in `/cases/<case-id>/timelines/` or `/workspace/output/timelines/`

## Phase 10: Impact Assessment & Response

1. Quantify data loss and exposure
2. Assess system compromise scope (number of affected hosts, accounts)
3. Evaluate credential exposure
4. Determine regulatory notification requirements (GDPR, HIPAA, PCI-DSS, etc.)
5. Provide containment recommendations
6. Provide eradication and recovery steps
7. Document lessons learned and prevention measures

## Phase 11: Reporting & Deliverables

1. Call `get_payload_schema` to retrieve the expected ForensicPayload format
2. Structure ALL findings into a complete ForensicPayload with every section populated:
   - `malware_samples`, `network_connections`, `processes`, `artifacts`, `user_accounts`, `dns_records`, `iocs`, `timeline_events`, `mitre_techniques`
3. Call `aggregate_results` to validate and persist the payload
4. Call `generate_report` with format `"both"` for MD + PDF output
5. Verify the report is written to `/reports/<case-id>/`
6. Ensure the process log and issues log are finalized and stored

---

## MCP Containers to Use

ALL containers: `kali-forensics`, `winforensics`, `network-forensics`, `binary-analysis`, `threat-intel`, `osint`, `filesystem`

Skip any phase that does not apply to the evidence type — but document WHY it was skipped in the process log.
