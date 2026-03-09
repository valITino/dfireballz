# OSINT Person Investigation

Conduct an open-source intelligence investigation on [TARGET].

## Phase 1: Username/Email Enumeration
1. **Maigret** — Search username across 2500+ platforms
2. **Sherlock** — Social media platform search
3. **Holehe** — Check email registration on services
4. **h8mail** — Breach database lookup (if configured)

## Phase 2: Domain/Infrastructure
1. **theHarvester** — Harvest emails, subdomains, names from public sources
2. **SpiderFoot** — Automated OSINT collection and correlation
3. **subfinder** — Discover associated subdomains

## Phase 3: Threat Intelligence
1. Check known IPs on AbuseIPDB
2. Shodan search for associated infrastructure
3. URLScan for web presence analysis

## Phase 4: Correlation
1. Cross-reference usernames across platforms
2. Map the digital footprint
3. Identify potential aliases
4. Document timeline of online activity

## Phase 5: Reporting
1. Structure findings with IoCs and user_accounts
2. Include platform presence map
3. Generate report

## MCP Containers to Use
- osint (Maigret, Sherlock, Holehe, SpiderFoot, theHarvester, subfinder)
- threat-intel (AbuseIPDB, Shodan, URLScan)
