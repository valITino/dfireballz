# Ransomware Investigation

Investigate a ransomware incident affecting [TARGET].

## Phase 1: Initial Triage
1. Log chain of custody for all evidence
2. Identify the ransomware variant (ransom note analysis, file extensions)
3. Document encryption scope (affected directories, file types)

## Phase 2: Artifact Analysis
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
1. YARA scan for ransomware signatures
2. Capa for capability detection
3. Radare2/Ghidra for static analysis of the ransomware binary
4. VirusTotal for variant identification

## Phase 5: Network Forensics
1. Analyze PCAPs for C2 communication
2. DNS queries to malicious domains
3. Data exfiltration indicators (large outbound transfers)
4. JA3 fingerprints for known C2 frameworks

## Phase 6: Reporting
1. Structure findings with attack chain reconstruction
2. Include MITRE ATT&CK technique mapping
3. Provide containment and recovery recommendations
4. Generate report

## MCP Containers to Use
- kali-forensics, winforensics, binary-analysis, network-forensics, threat-intel
