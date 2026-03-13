# Memory Forensics Investigation

Analyze the memory dump from [TARGET].

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

## Phase 1: Evidence Handling

1. Log chain of custody for the memory dump
2. Verify memory dump integrity (SHA256 hash)
3. Identify OS profile (Volatility3 auto-detection)

## Phase 2: Process Analysis

Use **kali-forensics** MCP server:
1. **Process listing** — List all processes (pslist, pstree, psxview)
2. **Hidden processes** — Detect hidden/unlinked processes
3. **Process injection** — Identify injected code (malfind)
4. **DLL analysis** — Loaded modules, suspicious DLLs (dlllist, ldrmodules)
5. **Handles** — Open handles to files, registry keys, network

## Phase 3: Network Analysis

Use **kali-forensics** MCP server:
1. **Network connections** — Active TCP/UDP connections (netscan)
2. **DNS cache** — Cached DNS lookups
3. **Listening ports** — Identify backdoor listeners

## Phase 4: Persistence & Artifacts

Use **kali-forensics** MCP server:
1. **Registry** — Run keys, services, scheduled tasks
2. **Command history** — Console/PowerShell history (cmdscan, consoles)
3. **File objects** — Files mapped in memory (filescan)
4. **Clipboard** — Clipboard contents
5. **User credentials** — Cached credentials (hashdump, lsadump)

## Phase 5: Malware Detection

Use **kali-forensics** MCP server:
1. **YARA** — Scan memory with YARA rules (yarascan)
2. **Strings** — Extract strings from suspicious processes
3. **Entropy** — Identify packed/encrypted regions
4. **bulk_extractor** — Carve email addresses, URLs, credit card numbers

## Phase 6: Reporting

1. Structure findings with processes, network_connections, artifacts
2. Include memory-specific IoCs
3. Map to MITRE ATT&CK techniques
4. Generate report and store in `/reports/<case-id>/`
5. Finalize process log and issues log

## MCP Containers to Use

- kali-forensics (Volatility3, YARA, bulk_extractor, ExifTool)
- threat-intel (VirusTotal for hash lookups, ThreatFox for IoCs)
- filesystem (evidence and report file access)
