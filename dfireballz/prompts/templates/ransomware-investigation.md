# Ransomware Investigation

Investigate a ransomware incident affecting [TARGET].

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

## Phase 1: Initial Triage

1. Log chain of custody for all evidence
2. Identify the ransomware variant (ransom note analysis, file extensions)
3. Document encryption scope (affected directories, file types)

## Phase 2: Artifact Analysis

Use **winforensics** and **kali-forensics** MCP servers:
1. **Ransom note** — Extract IoCs (Bitcoin addresses, Tor URLs, email contacts)
2. **Windows artifacts** — EVTX for RDP brute force, lateral movement, privilege escalation
3. **Registry** — Persistence mechanisms, run keys, services
4. **Prefetch/Amcache** — Execution timeline of malicious binaries
5. **USN Journal** — File system changes (mass encryption events)

## Phase 3: Attack Chain Reconstruction

1. Identify initial access vector (phishing, RDP, exploit)
2. Map lateral movement via event logs and network connections
3. Identify privilege escalation techniques
4. Document data exfiltration before encryption
5. Timeline the encryption event

## Phase 4: Malware Analysis

Use **binary-analysis** and **kali-forensics** MCP servers:
1. YARA scan for ransomware signatures
2. Capa for capability detection
3. Radare2/Ghidra for static analysis of the ransomware binary
4. VirusTotal for variant identification

## Phase 5: Network Forensics

Use **network-forensics** and **threat-intel** MCP servers:
1. Analyze PCAPs for C2 communication
2. DNS queries to malicious domains
3. Data exfiltration indicators (large outbound transfers)
4. JA3 fingerprints for known C2 frameworks
5. Look up IoCs on AbuseIPDB, Shodan, ThreatFox

## Phase 6: Reporting

1. Structure findings with attack chain reconstruction
2. Include MITRE ATT&CK technique mapping
3. Provide containment and recovery recommendations
4. Generate report and store in `/reports/<case-id>/`
5. Store timeline in `/cases/<case-id>/timelines/` or `/workspace/output/timelines/`
6. Finalize process log and issues log

## MCP Containers to Use

- kali-forensics (YARA, bulk_extractor, ExifTool)
- winforensics (MFT, EVTX, Registry, Prefetch, Amcache, USN Journal)
- binary-analysis (Ghidra, Radare2, Capa)
- network-forensics (tshark, tcpdump, JA3/JA3S)
- threat-intel (VirusTotal, MalwareBazaar, ThreatFox, AbuseIPDB, Shodan)
- filesystem (evidence file access)
