---
name: OSINT Domain Investigation
id: pb-osint-domain-investigation
description: >
  Comprehensive domain investigation playbook for mapping infrastructure,
  identifying ownership, enumerating subdomains, detecting typosquatting,
  fingerprinting web technologies, and enriching findings through passive
  DNS, Shodan, and VirusTotal.
case_types:
  - osint
  - domain-investigation
  - infrastructure-analysis
  - threat-hunting
tools_required:
  - osint/whois
  - osint/subfinder
  - osint/dnstwist
  - osint/whatweb
  - osint/passive_dns
  - osint/shodan
  - threat-intel/virustotal
estimated_duration: 30-60 minutes
tags:
  - osint
  - domain
  - dns
  - infrastructure
  - reconnaissance
  - typosquatting
steps:
  - id: whois_lookup
    name: WHOIS Lookup
    tool: osint/whois_lookup
    action: query_whois
    description: >
      Perform a WHOIS lookup on the target domain to retrieve registration
      details including registrant information, registrar, creation and
      expiration dates, name servers, and registration status. Identify
      privacy protection services and note any exposed contact data.
    inputs:
      domain: "{{target.domain}}"
      follow_referrals: true
      include_raw: true
      output_format: json

  - id: subdomain_enum
    name: Subdomain Enumeration
    tool: osint/subdomain_enum
    action: enumerate_subdomains
    description: >
      Enumerate subdomains of the target domain using certificate
      transparency logs, DNS brute-forcing, search engine dorking, and
      passive DNS sources. Resolve discovered subdomains to IP addresses
      and flag any that point to cloud services or CDNs.
    inputs:
      domain: "{{target.domain}}"
      sources:
        - crtsh
        - dnsdumpster
        - virustotal
        - shodan
        - censys
        - securitytrails
      wordlist: /opt/wordlists/subdomains-top1mil.txt
      resolve: true
      timeout: 300
      output_format: json

  - id: dns_twist
    name: DNS Typosquatting Detection
    tool: osint/dns_twist
    action: detect_typosquats
    description: >
      Generate and check domain permutations to detect typosquatting,
      homoglyph attacks, and brand impersonation domains. Check each
      permutation for active DNS records, web content, and mail servers.
      Flag domains that appear to be actively impersonating the target.
    inputs:
      domain: "{{target.domain}}"
      checks:
        - addition
        - bitsquatting
        - homoglyph
        - hyphenation
        - insertion
        - omission
        - repetition
        - replacement
        - subdomain
        - transposition
        - vowel_swap
      resolve_dns: true
      check_mx: true
      check_whois: true
      output_format: json

  - id: web_fingerprint
    name: Web Technology Fingerprinting
    tool: osint/web_fingerprint
    action: fingerprint
    description: >
      Fingerprint web technologies in use on the target domain and
      discovered subdomains. Identify web servers, frameworks, CMS
      platforms, JavaScript libraries, analytics tools, and security
      headers. Note any outdated or vulnerable component versions.
    inputs:
      targets:
        - "https://{{target.domain}}"
        - "http://{{target.domain}}"
      follow_redirects: true
      aggressive: false
      check_headers: true
      check_cookies: true
      check_scripts: true
      output_format: json

  - id: passive_dns
    name: Passive DNS Analysis
    tool: osint/passive_dns
    action: query_pdns
    description: >
      Query passive DNS databases to retrieve historical DNS resolution
      data for the target domain. Identify infrastructure changes over
      time, shared hosting relationships, and domains historically
      resolving to the same IP addresses.
    inputs:
      query: "{{target.domain}}"
      query_type: domain
      sources:
        - circl
        - securitytrails
        - farsight
        - riskiq
      time_range: 365d
      output_format: json

  - id: shodan_host
    name: Shodan Host Intelligence
    tool: osint/shodan_host
    action: search_host
    description: >
      Query Shodan for intelligence on IP addresses associated with the
      target domain. Retrieve open ports, running services, banners,
      SSL certificate details, known vulnerabilities, and organization
      information. Identify exposed or misconfigured services.
    inputs:
      targets: "{{steps.subdomain_enum.outputs.resolved_ips}}"
      include_history: true
      include_vulns: true
      facets:
        - port
        - org
        - os
        - product
      output_format: json

  - id: vt_domain_check
    name: VirusTotal Domain Report
    tool: threat-intel/vt_lookup
    action: lookup_domain
    description: >
      Query VirusTotal for the domain reputation report including
      community votes, detected URLs, communicating files, downloaded
      files, and historical WHOIS data. Identify any malicious
      associations or detections by security vendors.
    inputs:
      domain: "{{target.domain}}"
      include_relationships: true
      relationships:
        - communicating_files
        - downloaded_files
        - referrer_files
        - resolutions
        - subdomains
        - urls
      output_format: json
---

# OSINT Domain Investigation Playbook

## Overview

This playbook provides a structured methodology for investigating a domain from initial WHOIS registration through full infrastructure mapping, typosquatting detection, and threat intelligence enrichment.

## Prerequisites

- Target domain name
- API keys for Shodan, SecurityTrails, VirusTotal, and Censys
- Passive DNS service access
- dnstwist installed and operational
- Subfinder or equivalent subdomain enumeration tool

## Workflow

1. **WHOIS Lookup** -- Identify domain ownership and registration details
2. **Subdomain Enumeration** -- Map the full subdomain landscape
3. **DNS Typosquatting Detection** -- Find impersonation and brand abuse domains
4. **Web Fingerprinting** -- Identify technologies and potential vulnerabilities
5. **Passive DNS** -- Analyze historical DNS and infrastructure relationships
6. **Shodan Host Intelligence** -- Assess exposed services and vulnerabilities
7. **VirusTotal Domain Report** -- Check community reputation and malicious associations

## Decision Points

- If WHOIS reveals privacy protection, pivot to passive DNS and certificate transparency data.
- If typosquatting domains are actively serving content, capture evidence and escalate.
- If Shodan reveals critical vulnerabilities, notify the appropriate remediation team.
- If VT shows malicious associations, correlate with active case IOCs.

## Output Artifacts

- WHOIS registration report
- Subdomain enumeration map with resolved IPs
- Typosquatting detection results
- Web technology fingerprint report
- Passive DNS timeline
- Shodan host intelligence report
- VirusTotal domain reputation report
