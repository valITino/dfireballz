# Network Forensics Investigation

Analyze network traffic from [TARGET] for forensic evidence.

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

## Phase 1: PCAP Triage

1. Log chain of custody for all PCAP files
2. Get PCAP overview — protocol statistics, conversation list, endpoints
3. Identify time range and data volume

## Phase 2: Protocol Analysis

Use **network-forensics** MCP server:
1. **DNS** — Extract all DNS queries, identify suspicious domains, DNS tunneling
2. **HTTP/HTTPS** — Request/response analysis, file downloads, POST data
3. **TLS** — JA3/JA3S fingerprints, certificate analysis, suspicious handshakes
4. **SMB** — Lateral movement, file transfers, authentication attempts
5. **RDP** — Remote access sessions, brute force attempts

## Phase 3: Anomaly Detection

Use **network-forensics** MCP server:
1. Identify beaconing patterns (regular interval C2 communication)
2. Detect data exfiltration (large outbound transfers, DNS tunneling)
3. Find port scanning and reconnaissance activity
4. Identify use of non-standard ports for common protocols

## Phase 4: IoC Extraction

Use **threat-intel** and **osint** MCP servers:
1. Extract all unique external IPs and domains
2. Look up IPs on AbuseIPDB, Shodan
3. Check domains on URLScan, ThreatFox
4. GeoIP analysis for suspicious destinations

## Phase 5: Stream Reconstruction

Use **network-forensics** MCP server:
1. Follow TCP streams for suspicious conversations
2. Extract transferred files (HTTP objects, SMB files)
3. Reconstruct credential submissions
4. Document encrypted vs. unencrypted traffic

## Phase 6: Reporting

1. Include network connections, IoCs, and timeline
2. Attach JA3/JA3S fingerprint analysis
3. Provide network segmentation recommendations
4. Generate report and store in `/reports/<case-id>/`
5. Store extracted files in `/cases/<case-id>/artifacts/` or `/workspace/output/exports/`
6. Finalize process log and issues log

## MCP Containers to Use

- network-forensics (tshark — 18 tools, tcpdump, PCAP carving, JA3/JA3S, GeoIP)
- threat-intel (AbuseIPDB, Shodan, URLScan, ThreatFox)
- osint (subfinder, DNSTwist)
- filesystem (evidence file access)
