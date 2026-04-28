# OSINT Person Investigation

Conduct an open-source intelligence investigation on [TARGET].

---

## Important: Use MCP Servers and Their Tools

You MUST use the DFIReballz MCP servers and their tools to execute every phase below. Do NOT attempt manual analysis or skip tool usage. Call the tools provided by each MCP container — they are your primary instruments.

---

## Forensic Process Mapping

Canonical six-phase model from `docs/forensic-process.md`. Companion playbook: `playbooks/osint-person-investigation.md`.

The "evidence" is the target identifiers (username, email, name). Acquisition fetches public records into the case directory; parsed extractions are Examination; correlation/attribution is Analysis.

---

## Host Directory Layout

```
/cases/<case-id>/
  ├── 01-readiness/         ← Pre-flight
  ├── 02-identification/    ← Target record, identifiers, scope, authority
  ├── 03-acquisition/       ← Raw fetched records + hashes
  ├── 04-examination/       ← Username/email enumeration, harvester output
  ├── 05-analysis/          ← Persona correlation, IoC enrichment, footprint
  └── 06-reporting/         ← Closure manifest

/reports/<case-id>/         ← Final deliverables
```

**Claude Code paths** are prefixed with `/workspace/`.

---

## Documentation & Logging Requirements

1. **Document every tool invocation** — `process-log.md`.
2. **Document errors and issues** — `issues-log.md`.
3. **Log chain of custody** for every record fetched.
4. **Write findings incrementally** under the relevant phase directory.
5. **Legal scope** — every fetch must be within authorized scope. Do not interact with or log into discovered accounts. Comply with GDPR / CCPA / local privacy law.

---

## Phase 1 — Readiness

1. Confirm case is open with documented investigation authority and the legal scope (jurisdiction + privacy regime)
2. Health-check MCP servers: osint, threat-intel, filesystem
3. Verify SpiderFoot is configured with API keys; theHarvester data sources keyed
4. Pin tool versions (Maigret, Sherlock, Holehe) into `01-readiness/case-precondition.json`

## Phase 2 — Identification

1. Create the target record: identifiers (at least one of username, email, full name, phone), scope, authority
2. Assign case-scoped evidence ID
3. Log chain of custody (`identified`)

## Phase 3 — Acquisition

Fetch raw public records into `cases/<case-id>/03-acquisition/<evidence-id>/`:

1. Maigret/Sherlock raw outputs (per-platform)
2. Holehe raw output
3. theHarvester raw output
4. SpiderFoot scan exports
5. Hash each fetched artifact (SHA256)
6. Write acquisition manifest entry; log chain of custody (`acquired`)

## Phase 4 — Examination

Use **osint**:

1. **Username enumeration** — Maigret (2500+ platforms), Sherlock (social media), Holehe (email registration)
2. **Email verification** — deliverability, breach checks, associated services
3. **Domain / infrastructure** — theHarvester (emails, subdomains, hosts), subfinder
4. **SpiderFoot scan** — broad OSINT correlation across social, paste, breach, dns, whois, darkweb modules
5. **h8mail** breach lookup (if configured)

## Phase 5 — Analysis

Use **threat-intel** + osint correlation:

1. **Persona correlation** — link aliases, registration timing, shared infrastructure, language patterns
2. **IoC enrichment** — domains/IPs/emails against VirusTotal, AbuseIPDB, OTX, Shodan, GreyNoise
3. **Digital footprint map** — confirmed accounts + timeline of online activity
4. **Attribution indicators** if applicable
5. Each finding cites: source artifact + SHA256 + audit IDs; fact vs. interpretation

## Phase 6 — Reporting

1. `get_payload_schema` → populate ForensicPayload (`user_accounts`, `iocs`)
2. Include the platform-presence map and persona graph
3. Document scope adherence and legal basis
4. `aggregate_results` → `generate_report` format `"both"`
5. Write `06-reporting/closure-manifest.json`; log `case_closed`
6. Finalize process + issues logs

## MCP Containers to Use

- osint (Maigret, Sherlock, Holehe, SpiderFoot, theHarvester, subfinder)
- threat-intel (VirusTotal, AbuseIPDB, Shodan, URLScan, GreyNoise)
- filesystem (case + report file access)
