# Threat Intelligence MCP Server

Aggregates VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan.io, and NVD for IOC enrichment.

## Tools

| Tool | Description |
|------|-------------|
| `vt_lookup` | VirusTotal lookup (file hash, URL, domain, IP) |
| `shodan_host` | Shodan host information |
| `shodan_search` | Shodan dork search |
| `abuse_ip_check` | AbuseIPDB IP reputation |
| `malware_bazaar_lookup` | MalwareBazaar sample search |
| `threatfox_lookup` | ThreatFox IOC database |
| `urlscan_lookup` | URLScan.io analysis |
| `cve_lookup` | NVD CVE details |
| `enrich_ioc` | Multi-source IOC enrichment with confidence score |

## API Keys Required

Set in environment: `VIRUSTOTAL_API_KEY`, `SHODAN_API_KEY`, `ABUSEIPDB_API_KEY`, `URLSCAN_API_KEY`

## Transport

stdio only — connect via `docker exec -i dfireballz-threat-intel-1 python3 -m server`
