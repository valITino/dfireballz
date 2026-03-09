# Network Forensics Investigation

Analyze network traffic from [TARGET] for forensic evidence.

## Phase 1: PCAP Triage
1. Log chain of custody for all PCAP files
2. Get PCAP overview — protocol statistics, conversation list, endpoints
3. Identify time range and data volume

## Phase 2: Protocol Analysis
1. **DNS** — Extract all DNS queries, identify suspicious domains, DNS tunneling
2. **HTTP/HTTPS** — Request/response analysis, file downloads, POST data
3. **TLS** — JA3/JA3S fingerprints, certificate analysis, suspicious handshakes
4. **SMB** — Lateral movement, file transfers, authentication attempts
5. **RDP** — Remote access sessions, brute force attempts

## Phase 3: Anomaly Detection
1. Identify beaconing patterns (regular interval C2 communication)
2. Detect data exfiltration (large outbound transfers, DNS tunneling)
3. Find port scanning and reconnaissance activity
4. Identify use of non-standard ports for common protocols

## Phase 4: IoC Extraction
1. Extract all unique external IPs and domains
2. Look up IPs on AbuseIPDB, Shodan
3. Check domains on URLScan, ThreatFox
4. GeoIP analysis for suspicious destinations

## Phase 5: Stream Reconstruction
1. Follow TCP streams for suspicious conversations
2. Extract transferred files (HTTP objects, SMB files)
3. Reconstruct credential submissions
4. Document encrypted vs. unencrypted traffic

## Phase 6: Reporting
1. Include network connections, IoCs, and timeline
2. Attach JA3/JA3S fingerprint analysis
3. Provide network segmentation recommendations
4. Generate report

## MCP Containers to Use
- network-forensics (tshark — 18 tools, tcpdump)
- threat-intel (AbuseIPDB, Shodan, URLScan, ThreatFox)
- osint (subfinder, DNSTwist)
