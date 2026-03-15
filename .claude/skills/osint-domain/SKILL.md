---
name: osint-domain
description: Investigate a domain — DNS/subdomain enumeration, infrastructure analysis, threat assessment, web presence mapping, and reporting.
---

Conduct an OSINT investigation on the specified domain.

**Usage:** `/osint-domain <target>`

Where `<target>` is a domain name — e.g. `suspicious-site.com`, `example.org`.

If no target is provided, ask the user for the domain.

## Instructions

1. Load the investigation template: call `get_template(name="osint-domain", target="$ARGUMENTS")`
2. Follow all 5 phases: DNS & Subdomain Enumeration, Infrastructure Analysis, Threat Assessment, Web Presence, Reporting
3. Use these MCP servers: osint (theHarvester, subfinder, DNSTwist, amass), threat-intel (Shodan, AbuseIPDB, URLScan, VirusTotal), filesystem
4. Map the full infrastructure footprint
5. Check for domain typosquatting variants
6. Generate report with DNS map and threat indicators
