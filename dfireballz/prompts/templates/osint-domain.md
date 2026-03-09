# OSINT Domain Investigation

Investigate the domain/infrastructure [TARGET].

## Phase 1: DNS & Subdomain Enumeration
1. **subfinder** — Passive subdomain discovery
2. **DNSTwist** — Typosquatting and phishing domain detection
3. **theHarvester** — Email and subdomain harvesting
4. DNS record enumeration (A, AAAA, MX, NS, TXT, CNAME)

## Phase 2: Infrastructure Analysis
1. **Shodan** — Exposed services, ports, technologies
2. **URLScan** — Web page analysis and screenshot
3. WHOIS lookup — Registration details, dates, registrant
4. SSL certificate analysis — Issuer, SAN, validity

## Phase 3: Threat Assessment
1. **AbuseIPDB** — Check hosting IPs for abuse reports
2. **ThreatFox** — IoC lookup for associated malware
3. **VirusTotal** — Domain reputation check
4. Historical DNS records analysis

## Phase 4: Web Presence
1. Technology detection
2. Security header analysis
3. Associated email addresses
4. Historical changes (if available)

## Phase 5: Reporting
1. Structure findings with dns_records, whois, IoCs
2. Include infrastructure map
3. Provide risk assessment
4. Generate report

## MCP Containers to Use
- osint (subfinder, DNSTwist, theHarvester, SpiderFoot)
- threat-intel (Shodan, AbuseIPDB, URLScan, VirusTotal, ThreatFox)
