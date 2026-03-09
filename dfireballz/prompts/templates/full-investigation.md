# Full Forensic Investigation

Conduct a comprehensive digital forensic investigation of [TARGET].

## Phase 1: Evidence Intake
1. Log chain of custody for all evidence files
2. Verify evidence integrity (hash verification)
3. Identify evidence type (disk image, memory dump, PCAP, files)

## Phase 2: Artifact Collection
1. **Disk analysis** — Use Sleuthkit to examine file systems, recover deleted files
2. **Memory analysis** — Use Volatility3 for process listing, DLL analysis, network connections
3. **Windows artifacts** — Parse MFT, EVTX, Registry, Prefetch, ShellBags, Amcache, USN Journal
4. **Metadata extraction** — Use ExifTool on documents, images, media files
5. **Malware scanning** — Run YARA rules, Capa for capability detection

## Phase 3: Network Analysis
1. Analyze PCAPs with tshark — protocol analysis, stream extraction
2. Extract DNS queries, HTTP requests, TLS handshakes
3. Identify C2 communication patterns (JA3/JA3S fingerprints)
4. GeoIP lookup on suspicious external IPs

## Phase 4: Threat Intelligence
1. Check file hashes against VirusTotal, MalwareBazaar
2. Look up suspicious IPs on AbuseIPDB, Shodan
3. Check domains on URLScan, ThreatFox
4. Correlate IoCs with known threat actor TTPs

## Phase 5: Timeline Reconstruction
1. Build unified timeline from all artifact timestamps
2. Identify initial access vector
3. Map lateral movement
4. Document data exfiltration indicators

## Phase 6: Reporting
1. Call `get_payload_schema` to understand the expected format
2. Structure all findings into a ForensicPayload
3. Call `aggregate_results` to validate and persist
4. Call `generate_report` with format "both" for MD + PDF
5. Reports will be available on the host at ./reports/

## MCP Containers to Use
- kali-forensics, winforensics, network-forensics, binary-analysis, threat-intel, osint, filesystem
