# Memory Forensics Investigation

Analyze the memory dump from [TARGET].

## Phase 1: Evidence Handling
1. Log chain of custody for the memory dump
2. Verify memory dump integrity (SHA256 hash)
3. Identify OS profile (Volatility3 auto-detection)

## Phase 2: Process Analysis
1. **Process listing** — List all processes (pslist, pstree, psxview)
2. **Hidden processes** — Detect hidden/unlinked processes
3. **Process injection** — Identify injected code (malfind)
4. **DLL analysis** — Loaded modules, suspicious DLLs (dlllist, ldrmodules)
5. **Handles** — Open handles to files, registry keys, network

## Phase 3: Network Analysis
1. **Network connections** — Active TCP/UDP connections (netscan)
2. **DNS cache** — Cached DNS lookups
3. **Listening ports** — Identify backdoor listeners

## Phase 4: Persistence & Artifacts
1. **Registry** — Run keys, services, scheduled tasks
2. **Command history** — Console/PowerShell history (cmdscan, consoles)
3. **File objects** — Files mapped in memory (filescan)
4. **Clipboard** — Clipboard contents
5. **User credentials** — Cached credentials (hashdump, lsadump)

## Phase 5: Malware Detection
1. **YARA** — Scan memory with YARA rules (yarascan)
2. **Strings** — Extract strings from suspicious processes
3. **Entropy** — Identify packed/encrypted regions
4. **bulk_extractor** — Carve email addresses, URLs, credit card numbers

## Phase 6: Reporting
1. Structure findings with processes, network_connections, artifacts
2. Include memory-specific IoCs
3. Map to MITRE ATT&CK techniques
4. Generate report

## MCP Containers to Use
- kali-forensics (Volatility3, YARA, bulk_extractor)
- threat-intel (VirusTotal for hash lookups, ThreatFox for IoCs)
