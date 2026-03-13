# Full Forensic Investigation

Conduct a comprehensive digital forensic investigation of [TARGET].

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

## Phase 1: Evidence Intake

1. Log chain of custody for all evidence files
2. Verify evidence integrity (hash verification)
3. Identify evidence type (disk image, memory dump, PCAP, files)

## Phase 2: Artifact Collection

Use **kali-forensics**, **winforensics**, **binary-analysis**, and **filesystem** MCP servers:
1. **Disk analysis** — Use Sleuthkit to examine file systems, recover deleted files
2. **Memory analysis** — Use Volatility3 for process listing, DLL analysis, network connections
3. **Windows artifacts** — Parse MFT, EVTX, Registry, Prefetch, ShellBags, Amcache, USN Journal
4. **Metadata extraction** — Use ExifTool on documents, images, media files
5. **Malware scanning** — Run YARA rules, Capa for capability detection

## Phase 3: Network Analysis

Use **network-forensics** MCP server:
1. Analyze PCAPs with tshark — protocol analysis, stream extraction
2. Extract DNS queries, HTTP requests, TLS handshakes
3. Identify C2 communication patterns (JA3/JA3S fingerprints)
4. GeoIP lookup on suspicious external IPs

## Phase 4: Threat Intelligence

Use **threat-intel** MCP server:
1. Check file hashes against VirusTotal, MalwareBazaar
2. Look up suspicious IPs on AbuseIPDB, Shodan
3. Check domains on URLScan, ThreatFox
4. Correlate IoCs with known threat actor TTPs

## Phase 5: Timeline Reconstruction

1. Build unified timeline from all artifact timestamps
2. Identify initial access vector
3. Map lateral movement
4. Document data exfiltration indicators
5. Store timeline in `/cases/<case-id>/timelines/` or `/workspace/output/timelines/`

## Phase 6: Reporting

1. Call `get_payload_schema` to understand the expected format
2. Structure all findings into a ForensicPayload
3. Call `aggregate_results` to validate and persist
4. Call `generate_report` with format "both" for MD + PDF
5. Verify reports are written to `/reports/<case-id>/`
6. Finalize process log and issues log

## MCP Containers to Use

- kali-forensics, winforensics, network-forensics, binary-analysis, threat-intel, osint, filesystem
