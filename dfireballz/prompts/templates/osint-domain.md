# OSINT Domain Investigation

Investigate the domain/infrastructure [TARGET].

---

## Important: Use MCP Servers and Their Tools

You MUST use the DFIReballz MCP servers and their tools to execute every phase below. Do NOT attempt manual analysis or skip tool usage. Call the tools provided by each MCP container — they are your primary instruments.

---

## Forensic Process Mapping

Canonical six-phase model from `docs/forensic-process.md`. Companion playbook: `playbooks/osint-domain-investigation.md`.

For OSINT, the "evidence" is the target itself (a domain/IP). Acquisition consists of fetching public records into the case directory; data fetches that parse public records are tagged Examination; reputation/correlation steps are tagged Analysis.

---

## Host Directory Layout

```
/cases/<case-id>/
  ├── 01-readiness/         ← Pre-flight
  ├── 02-identification/    ← Target record, scope, authority
  ├── 03-acquisition/       ← Raw fetched records (WHOIS, DNS, certs) + hashes
  ├── 04-examination/       ← Parsed extractions, subdomain map, fingerprints
  ├── 05-analysis/          ← Reputation, threat assessment, attribution
  └── 06-reporting/         ← Closure manifest

/reports/<case-id>/         ← Final deliverables
```

**Claude Code paths** are prefixed with `/workspace/`.

---

## Documentation & Logging Requirements

1. **Document every tool invocation** — `process-log.md`.
2. **Document errors and issues** — `issues-log.md`.
3. **Log chain of custody** for every record fetched. Original public records are immutable but each fetch is a discrete evidentiary act — log it.
4. **Write findings incrementally** under the relevant phase directory.

---

## Phase 1 — Readiness

1. Confirm case is open with documented investigation authority and scope
2. Health-check MCP servers: osint, threat-intel, filesystem
3. Verify API keys: Shodan, SecurityTrails, VirusTotal, Censys, URLScan
4. Pin tool versions (subfinder, DNSTwist, theHarvester) into `01-readiness/case-precondition.json`

## Phase 2 — Identification

1. Create the target record: domain, scope (subdomains, related infrastructure), investigation authority
2. Assign case-scoped evidence ID for the target
3. Log chain of custody (`identified`)

## Phase 3 — Acquisition

Fetch raw public records into `cases/<case-id>/03-acquisition/<evidence-id>/`:

1. WHOIS raw output
2. DNS records (A, AAAA, MX, NS, TXT, CNAME)
3. SSL certificate(s)
4. Hash each fetched artifact (SHA256)
5. Write acquisition manifest entry; log chain of custody (`acquired`)

## Phase 4 — Examination

Use **osint** and **threat-intel**:

1. **DNS & subdomain enumeration** — subfinder (passive), DNSTwist (typosquatting/homoglyph), theHarvester
2. **Web technology fingerprinting** — servers, frameworks, CMS, JS libraries, security headers
3. **Infrastructure** — Shodan for exposed services / vulns; URLScan for screenshot + behavior
4. **WHOIS parsing** — registrant, registrar, dates, name servers
5. **SSL certificate analysis** — issuer, SAN, validity, certificate transparency
6. **Passive DNS** — historical resolutions

## Phase 5 — Analysis

Use **threat-intel**:

1. **Reputation** — VirusTotal domain report, AbuseIPDB on hosting IPs, ThreatFox for IoC matches
2. **Historical analysis** — past resolutions, prior owners, known-bad associations
3. **Risk assessment** — correlate fingerprint, exposure, and reputation signals
4. **Attribution indicators** — shared infrastructure, registration patterns
5. Each finding cites: contributing examination artifact paths + SHA256 + audit IDs; fact vs. interpretation

## Phase 6 — Reporting

1. `get_payload_schema` → populate ForensicPayload (`dns_records`, `iocs`, `mitre_techniques` if applicable)
2. Include infrastructure map + risk assessment
3. `aggregate_results` → `generate_report` format `"both"`
4. Write `06-reporting/closure-manifest.json`; log `case_closed`
5. Finalize process + issues logs

## MCP Containers to Use

- osint (subfinder, DNSTwist, theHarvester, SpiderFoot, web fingerprint)
- threat-intel (Shodan, AbuseIPDB, URLScan, VirusTotal, ThreatFox)
- filesystem (case + report file access)
