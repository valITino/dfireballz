# Ransomware Investigation

Investigate a ransomware incident affecting [TARGET].

---

## Important: Use MCP Servers and Their Tools

You MUST use the DFIReballz MCP servers and their tools to execute every phase below. Do NOT attempt manual analysis or skip tool usage. Call the tools provided by each MCP container — they are your primary instruments.

---

## Forensic Process Mapping

Canonical six-phase model from `docs/forensic-process.md`. Companion playbook: `playbooks/ransomware-investigation.md`.

---

## Host Directory Layout

```
/cases/<case-id>/
  ├── 01-readiness/         ← Pre-flight
  ├── 02-identification/    ← Affected systems, evidence records
  ├── 03-acquisition/       ← Memory dumps, disk images, PCAPs (working copies + hashes)
  ├── 04-examination/       ← Volatility/Sleuthkit/Foremost/YARA outputs
  ├── 05-analysis/          ← C2 detection, attack chain, VT enrichment, timelines
  └── 06-reporting/         ← Closure manifest, sealed audit-log digest

/evidence/<case-id>/        ← READ-ONLY originals
/reports/<case-id>/         ← Final deliverables
```

**Claude Code paths** are prefixed with `/workspace/`.

---

## Documentation & Logging Requirements

1. **Document the process** — every tool invocation logged in `process-log.md`.
2. **Document errors and issues** — `issues-log.md`.
3. **Log chain of custody** for every evidence access. **Originals are read-only.**
4. **Write findings incrementally** to the appropriate phase directory.

---

## Phase 1 — Readiness

1. Confirm case is open with authority for the affected systems
2. Health-check MCP servers: kali-forensics, winforensics, binary-analysis, network-forensics, threat-intel, filesystem
3. Verify API keys (VirusTotal, MalwareBazaar, Shodan, AbuseIPDB)
4. Pin tool + symbol-table versions (Volatility3 profiles, YARA rule sets, Sleuthkit) into `01-readiness/case-precondition.json`

## Phase 2 — Identification

1. Identify the ransomware variant via ransom note + extension patterns
2. Document encryption scope (affected dirs, file types, hostnames)
3. Identify and create evidence records for: memory dump(s), disk image(s), PCAP(s), ransom notes
4. Assign case-scoped evidence IDs
5. Log chain of custody (`identified`)

## Phase 3 — Acquisition

1. Copy each evidence item to `cases/<case-id>/03-acquisition/<evidence-id>/`
2. Compute SHA256 + MD5 with `dc3dd_hash` or `hashdeep`
3. Independently verify with a second tool
4. Write acquisition + verification logs and the manifest
5. Log chain of custody (`acquired`, `verified`)

## Phase 4 — Examination

Re-verify source hash before each major tool. Use **kali-forensics**, **winforensics**, **binary-analysis**:

1. **Memory — Volatility3**: pslist, pstree, psxview, malfind, netscan, dlllist, ldrmodules; dump suspicious processes
2. **Disk — Sleuthkit**: timeline creation, file listing, deleted-file recovery; focus `/Windows/Temp`, `/Users/*/AppData`, `/Users/*/Desktop`, `/ProgramData`, `/Windows/System32/Tasks`
3. **File recovery — Foremost**: ransom notes, encryption-key files, dropped payloads, unencrypted originals
4. **Windows artifacts — winforensics**: EVTX (RDP brute force, lateral movement, privilege escalation, logon events), Registry (Run keys, Services), Prefetch/Amcache (execution timeline), USN Journal (mass-encryption events), ShellBags
5. **Ransom note IoCs**: extract Bitcoin/Monero addresses, Tor URLs, email contacts
6. **YARA**: scan recovered files + memory dumps + disk artifacts against ransomware/crypto/malware rule sets
7. **Binary analysis** (if ransomware sample recovered): Capa, Radare2, Ghidra; identify packing, anti-analysis, encryption routines

## Phase 5 — Analysis

Use **network-forensics** and **threat-intel**:

1. **C2 detection — wireshark**: beaconing, DNS tunneling, encrypted C2, data exfiltration, lateral movement; correlate with `volatility netscan` IPs
2. **JA3/JA3S fingerprints** for known C2 frameworks
3. **VirusTotal bulk lookup**: hashes, IPs, domains; identify ransomware family + campaign
4. **MalwareBazaar / ThreatFox**: family-specific IoC sets
5. **Attack chain reconstruction**: initial access → execution → persistence → privilege escalation → lateral movement → collection → exfiltration → encryption (impact)
6. **Timeline** unified across memory, disk, network, EVTX
7. **MITRE ATT&CK mapping** across all techniques
8. **Decryptor check** (NoMoreRansom.org) once family is identified
9. Each finding cites evidence ID + source SHA256 + audit IDs; fact vs. interpretation

## Phase 6 — Reporting

1. `get_payload_schema` → populate ForensicPayload (`malware_samples`, `network_connections`, `processes`, `artifacts`, `iocs`, `timeline_events`, `mitre_techniques`)
2. Containment, eradication, recovery recommendations
3. Re-verify all source-evidence hashes
4. `aggregate_results` → `generate_report` format `"both"`
5. Write `06-reporting/closure-manifest.json`; log `case_closed`
6. Finalize process + issues logs

## MCP Containers to Use

- kali-forensics (Volatility3, Foremost, Sleuthkit, YARA, bulk_extractor, hashdeep)
- winforensics (MFT, EVTX, Registry, Prefetch, Amcache, USN Journal, ShellBags)
- binary-analysis (Ghidra, Radare2, Capa)
- network-forensics (tshark, tcpdump, JA3/JA3S)
- threat-intel (VirusTotal, MalwareBazaar, ThreatFox, AbuseIPDB, Shodan)
- filesystem (evidence access)
