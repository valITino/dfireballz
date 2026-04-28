# Memory Forensics Investigation

Analyze the memory dump from [TARGET].

---

## Important: Use MCP Servers and Their Tools

You MUST use the DFIReballz MCP servers and their tools to execute every phase below. Do NOT attempt manual analysis or skip tool usage. Call the tools provided by each MCP container — they are your primary instruments.

---

## Forensic Process Mapping

Canonical six-phase model from `docs/forensic-process.md`.

---

## Host Directory Layout

```
/cases/<case-id>/
  ├── 01-readiness/         ← Pre-flight
  ├── 02-identification/    ← Memory dump record, source system, authority
  ├── 03-acquisition/       ← Working copy + hashes
  ├── 04-examination/       ← Volatility plugin outputs, dumps, strings
  ├── 05-analysis/          ← IoC enrichment, ATT&CK mapping, timeline
  └── 06-reporting/         ← Closure manifest

/evidence/<case-id>/        ← READ-ONLY originals
/reports/<case-id>/         ← Final deliverables
```

**Claude Code paths** are prefixed with `/workspace/`.

---

## Documentation & Logging Requirements

1. **Document every tool invocation** — `process-log.md`.
2. **Document errors and issues** — `issues-log.md`.
3. **Log chain of custody** for every memory-dump access. **Original is read-only.**
4. **Write findings incrementally** under the relevant phase directory.

---

## Phase 1 — Readiness

1. Confirm case is open with authority for the source system
2. Health-check MCP servers: kali-forensics, threat-intel, filesystem
3. Verify Volatility3 symbol tables for the suspected OS profile are available
4. Pin Volatility3 + YARA rule-set versions into `01-readiness/case-precondition.json`

## Phase 2 — Identification

1. Create the memory-dump evidence record: source system, capture method, capture tool/version, time of capture
2. Identify OS profile (Volatility3 auto-detection)
3. Assign case-scoped evidence ID
4. Log chain of custody (`identified`)

## Phase 3 — Acquisition

1. Copy dump to `cases/<case-id>/03-acquisition/<evidence-id>/`
2. Compute SHA256 + MD5
3. Independently verify with `hashdeep`
4. Write acquisition manifest entry
5. Log chain of custody (`acquired`, `verified`)

## Phase 4 — Examination

Re-verify source hash before each major plugin run. Use **kali-forensics**:

1. **Process analysis** — pslist, pstree, psxview; detect hidden/unlinked processes; malfind for injection
2. **DLL analysis** — dlllist, ldrmodules; flag suspicious modules
3. **Handles** — open files, registry keys, network handles
4. **Network connections** — netscan (active TCP/UDP), DNS cache, listening ports / backdoor listeners
5. **Persistence artifacts** — registry Run keys, services, scheduled tasks from memory
6. **Command history** — cmdscan, consoles
7. **File objects** — filescan
8. **Clipboard** — clipboard contents
9. **Credentials** (if authorized) — hashdump, lsadump
10. **YARA across memory** — yarascan
11. **Strings + entropy** of suspicious processes
12. **bulk_extractor** carving — emails, URLs, credit-card numbers

## Phase 5 — Analysis

Use **threat-intel**:

1. **VirusTotal / ThreatFox** lookups on extracted hashes, IPs, domains
2. **Correlate** memory findings (processes ↔ network ↔ persistence) into an attack chain
3. **MITRE ATT&CK mapping** for identified techniques
4. **Timeline** of in-memory artifacts vs. external indicators
5. Each finding cites source-dump SHA256 + audit IDs; fact vs. interpretation

## Phase 6 — Reporting

1. `get_payload_schema` → populate ForensicPayload (`processes`, `network_connections`, `artifacts`, `iocs`, `mitre_techniques`)
2. Re-verify source-dump hash
3. `aggregate_results` → `generate_report` format `"both"`
4. Write `06-reporting/closure-manifest.json`; log `case_closed`
5. Finalize process + issues logs

## MCP Containers to Use

- kali-forensics (Volatility3, YARA, bulk_extractor, ExifTool, hashdeep)
- threat-intel (VirusTotal, ThreatFox)
- filesystem (evidence access)
