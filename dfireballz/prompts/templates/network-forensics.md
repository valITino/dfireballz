# Network Forensics Investigation

Analyze network traffic from [TARGET] for forensic evidence.

---

## Important: Use MCP Servers and Their Tools

You MUST use the DFIReballz MCP servers and their tools to execute every phase below. Do NOT attempt manual analysis or skip tool usage. Call the tools provided by each MCP container — they are your primary instruments.

---

## Forensic Process Mapping

Canonical six-phase model from `docs/forensic-process.md`. Companion playbook: `playbooks/network-forensics.md`.

---

## Host Directory Layout

```
/cases/<case-id>/
  ├── 01-readiness/         ← Pre-flight
  ├── 02-identification/    ← PCAP records, capture authority, time range
  ├── 03-acquisition/       ← PCAP working copies + hashes
  ├── 04-examination/       ← Protocol stats, DNS/HTTP/TLS extractions, exported objects
  ├── 05-analysis/          ← Anomaly detection, IoCs, GeoIP, attack chain, timelines
  └── 06-reporting/         ← Closure manifest, segmentation recommendations

/evidence/<case-id>/        ← READ-ONLY originals
/reports/<case-id>/         ← Final deliverables
```

**Claude Code paths** are prefixed with `/workspace/`.

---

## Documentation & Logging Requirements

1. **Document every tool invocation** — `process-log.md`.
2. **Document errors and issues** — `issues-log.md`.
3. **Log chain of custody** for every PCAP access. **Originals are read-only.**
4. **Write findings incrementally** under the relevant phase directory.

---

## Phase 1 — Readiness

1. Confirm case is open with capture authority documented
2. Health-check MCP servers: network-forensics, threat-intel, osint, filesystem
3. Verify GeoIP databases present (GeoLite2-City, GeoLite2-ASN) and recent
4. Verify API keys (AbuseIPDB, Shodan, URLScan, ThreatFox)
5. Pin tshark version into `01-readiness/case-precondition.json`

## Phase 2 — Identification

1. Create the PCAP evidence record(s): capture point, time range, capture authority, packet count
2. Identify capture format (PCAP / PCAPNG) and validate integrity
3. Assign case-scoped evidence IDs
4. Log chain of custody (`identified`)

## Phase 3 — Acquisition

1. Copy PCAPs to `cases/<case-id>/03-acquisition/<evidence-id>/`
2. Compute SHA256 + MD5
3. Independently verify with a second tool
4. Write acquisition manifest entry
5. Log chain of custody (`acquired`, `verified`)

## Phase 4 — Examination

Use **network-forensics** MCP server:

1. **PCAP overview** — capture parameters, top talkers, conversations, endpoints, IO graph
2. **Protocol statistics** — protocol hierarchy, distribution, anomalies, non-standard port usage
3. **DNS** — extract queries/responses, NXDOMAINs, TXT records; flag DGA candidates, DNS tunneling, fast-flux
4. **HTTP/HTTPS** — requests/responses, POST data, cookies, user agents; export objects to `04-examination/<evidence-id>/http_objects/`
5. **TLS** — handshakes, certificates, JA3/JA3S fingerprints, SNI; export certs
6. **SMB / RDP** — auth attempts, file transfers, lateral movement evidence
7. **Stream reconstruction** — follow TCP streams for suspicious conversations; extract transferred files

## Phase 5 — Analysis

Use **network-forensics**, **threat-intel**, **osint**:

1. **Security audit** — port scans, brute force, cleartext credentials, ARP/DNS spoofing, lateral movement, exfiltration; classify severity
2. **Beaconing detection** — regular-interval C2 patterns; extract intervals + destinations
3. **Data exfiltration indicators** — large outbound transfers, DNS encoding
4. **IoC enrichment** — AbuseIPDB, Shodan, URLScan, ThreatFox, VirusTotal for IPs/domains
5. **GeoIP** — resolve external IPs to country/ASN/org; flag high-risk geographies
6. **Timeline** — chronological reconstruction
7. **MITRE ATT&CK mapping** for identified techniques
8. Each finding cites: source PCAP SHA256 + audit IDs; fact vs. interpretation

## Phase 6 — Reporting

1. `get_payload_schema` → populate ForensicPayload (`network_connections`, `dns_records`, `iocs`, `timeline_events`, `mitre_techniques`)
2. Attach JA3/JA3S fingerprint analysis + protocol breakdown
3. Provide network segmentation / blocking recommendations
4. Re-verify source PCAP hashes
5. `aggregate_results` → `generate_report` format `"both"`
6. Store extracted files in `cases/<case-id>/04-examination/<evidence-id>/` (working set) and a deliverable copy under `/reports/<case-id>/exports/`
7. Write `06-reporting/closure-manifest.json`; log `case_closed`
8. Finalize process + issues logs

## MCP Containers to Use

- network-forensics (tshark — 18 tools, tcpdump, PCAP carving, JA3/JA3S, GeoIP)
- threat-intel (AbuseIPDB, Shodan, URLScan, ThreatFox, VirusTotal)
- osint (subfinder, DNSTwist)
- filesystem (evidence access)
