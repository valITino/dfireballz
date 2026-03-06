# OSINT MCP Server

OSINT aggregator wrapping Maigret, Sherlock, Holehe, theHarvester, DNSTwist, subfinder, amass, and more.

## Tools

| Tool | Description |
|------|-------------|
| `username_search` | Search username across 500+ platforms (Maigret + Sherlock) |
| `email_check` | Email platform registration + breach check (Holehe + h8mail) |
| `harvester_scan` | Find emails, subdomains, hosts, employee names |
| `subdomain_enum` | Subdomain enumeration (subfinder + amass) |
| `dns_twist` | Detect typosquatting / phishing domains |
| `whois_lookup` | WHOIS + RDAP lookup |
| `web_fingerprint` | Web technology fingerprinting (whatweb) |
| `passive_dns` | Passive DNS history |

## Transport

stdio only — connect via `docker exec -i dfireballz-osint-1 python3 -m server`
