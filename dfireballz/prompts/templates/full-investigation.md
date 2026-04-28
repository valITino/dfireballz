# Full Forensic Investigation

Conduct a comprehensive digital forensic investigation of [TARGET].

---

## Important: Use MCP Servers and Their Tools

You MUST use the DFIReballz MCP servers and their tools to execute every phase below. Do NOT attempt manual analysis or skip tool usage. Call the tools provided by each MCP container — they are your primary instruments.

---

## Forensic Process Mapping

Canonical six-phase model from `docs/forensic-process.md`. This template covers all six phases at a general-purpose level; for highly specialized investigations use `complete-investigation` (deeper) or a domain-specific template.

---

## Host Directory Layout

```
/cases/<case-id>/
  ├── 01-readiness/         ← Pre-flight: MCP health, tool versions, API keys, time
  ├── 02-identification/    ← Evidence records, scope, authority
  ├── 03-acquisition/       ← Working copies + verified hashes + manifest
  ├── 04-examination/       ← Per-evidence extracted artifacts
  ├── 05-analysis/          ← Findings, IoCs, timelines, ATT&CK mapping
  └── 06-reporting/         ← Closure manifest, sealed audit-log digest

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

1. Confirm the case is open with documented authority
2. Health-check the MCP servers required for the case
3. Verify required API keys for the planned tooling
4. Confirm UTC time sync; pin tool versions into `01-readiness/case-precondition.json`

## Phase 2 — Identification

1. Enumerate evidence sources: disk images, memory dumps, PCAPs, document/email files, malware samples
2. Apply RFC 3227 order of volatility — volatile sources first
3. Assign case-scoped evidence IDs
4. Document the legal authority and scope per item
5. Log chain of custody (`identified`)

## Phase 3 — Acquisition

1. Copy each evidence item into `cases/<case-id>/03-acquisition/<evidence-id>/`
2. Compute SHA256 + MD5 with `dc3dd_hash` or `hashdeep`
3. Independently verify with a second tool
4. Write the acquisition manifest entry
5. Log chain of custody (`acquired`, `verified`)

## Phase 4 — Examination

Re-verify source hash before each major tool. Use **kali-forensics**, **winforensics**, **binary-analysis**, **filesystem**:

1. **Disk** — Sleuthkit (file systems, deleted recovery), Foremost (carving), bulk_extractor (emails/URLs/cards/domains)
2. **Memory** — Volatility3 (pslist/pstree/psxview/malfind, dlllist, netscan, registry-from-memory)
3. **Windows artifacts** — MFT, EVTX (Security/System/PowerShell/RDP/logon), Registry (run keys, USB), Prefetch, Amcache, ShellBags, USN Journal, SRUM, Browser history
4. **Metadata** — ExifTool on documents, images, media
5. **Malware** — YARA scan, Capa capability detection (ATT&CK mapped), Radare2, Ghidra headless decompile

## Phase 5 — Analysis

Use **network-forensics**, **threat-intel**, **osint**:

1. **Network analysis** — tshark for DNS, HTTP, TLS (JA3/JA3S), beaconing, exfiltration, GeoIP
2. **Threat-intel enrichment** — VirusTotal, MalwareBazaar, AbuseIPDB, Shodan, URLScan, ThreatFox
3. **OSINT** — Maigret/Sherlock/Holehe/theHarvester/DNSTwist if attribution leads
4. **Timeline reconstruction** — unified across disk, memory, network, EVTX
5. **Attack chain** — initial access → execution → persistence → privilege escalation → lateral movement → collection → exfiltration → impact
6. **MITRE ATT&CK mapping**
7. Each finding cites evidence ID + source SHA256 + audit IDs; fact vs. interpretation

## Phase 6 — Reporting

1. `get_payload_schema` → populate ForensicPayload (every applicable section)
2. Re-verify all source-evidence hashes
3. `aggregate_results` → `generate_report` format `"both"`
4. Write `06-reporting/closure-manifest.json`; log `case_closed`
5. Finalize process + issues logs

## MCP Containers to Use

- kali-forensics, winforensics, network-forensics, binary-analysis, threat-intel, osint, filesystem
