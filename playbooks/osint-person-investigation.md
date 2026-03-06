---
name: OSINT Person Investigation
id: pb-osint-person-investigation
description: >
  Open-source intelligence playbook for investigating a person of interest.
  Covers username enumeration across platforms, email verification, automated
  OSINT scanning with SpiderFoot and theHarvester, and IOC enrichment for
  any discovered infrastructure.
case_types:
  - osint
  - person-investigation
  - threat-actor-profiling
tools_required:
  - osint/sherlock
  - osint/holehe
  - osint/spiderfoot
  - osint/theharvester
  - threat-intel/ioc_enrichment
estimated_duration: 30-60 minutes
tags:
  - osint
  - person-investigation
  - username-enumeration
  - email-verification
  - social-media
steps:
  - id: username_search
    name: Username Enumeration
    tool: osint/username_search
    action: search_platforms
    description: >
      Search for the target username across hundreds of social media platforms,
      forums, and web services. Identify confirmed accounts, collect profile
      URLs, and note any variations or aliases discovered during enumeration.
    inputs:
      username: "{{target.username}}"
      platforms: all
      check_nsfw: false
      output_format: json
      timeout_per_site: 10
      export_path: "{{case.working_dir}}/username_results"

  - id: email_check
    name: Email Verification and Account Discovery
    tool: osint/email_check
    action: check_email
    description: >
      Verify whether the target email address is registered on known platforms.
      Check for breached credentials, associated accounts, and linked services.
      Validate email deliverability and extract mail server information.
    inputs:
      email: "{{target.email}}"
      check_breaches: true
      check_registrations: true
      check_deliverability: true
      output_format: json

  - id: spiderfoot_scan
    name: SpiderFoot Automated OSINT Scan
    tool: osint/spiderfoot_scan
    action: run_scan
    description: >
      Execute a SpiderFoot scan against all known target identifiers (name,
      email, username, phone) to perform automated OSINT collection. Modules
      include social media, DNS, WHOIS, dark web, paste sites, and breach
      databases. Correlate findings into a unified entity graph.
    inputs:
      scan_name: "person_investigation_{{case.id}}"
      target_identifiers:
        - type: username
          value: "{{target.username}}"
        - type: email
          value: "{{target.email}}"
        - type: name
          value: "{{target.full_name}}"
      modules:
        - sfp_social
        - sfp_email
        - sfp_dns
        - sfp_whois
        - sfp_darkweb
        - sfp_paste
        - sfp_breach
      max_threads: 10
      timeout: 600

  - id: harvester_scan
    name: theHarvester Scan
    tool: osint/harvester_scan
    action: run_harvester
    description: >
      Run theHarvester to collect emails, subdomains, hosts, employee names,
      and open ports from public sources associated with the target. Sources
      include search engines, PGP key servers, Shodan, and social media APIs.
    inputs:
      domain: "{{target.associated_domain}}"
      search_term: "{{target.full_name}}"
      sources:
        - google
        - bing
        - linkedin
        - twitter
        - pgp
        - shodan
        - dnsdumpster
        - crtsh
      limit: 500
      output_format: json

  - id: ioc_enrich
    name: Enrich Discovered IOCs
    tool: threat-intel/enrich_ioc
    action: bulk_enrich
    description: >
      Enrich all infrastructure indicators discovered during the investigation
      including domains, IP addresses, and email addresses. Cross-reference
      against threat intelligence feeds, abuse databases, and reputation
      services to identify malicious or suspicious associations.
    inputs:
      iocs:
        domains: "{{steps.harvester_scan.outputs.domains}}"
        ips: "{{steps.harvester_scan.outputs.ips}}"
        emails: "{{steps.email_check.outputs.associated_emails}}"
      sources:
        - virustotal
        - abuseipdb
        - otx
        - shodan
        - greynoise
      confidence_threshold: 40
---

# OSINT Person Investigation Playbook

## Overview

This playbook provides a structured approach to investigating a person of interest using open-source intelligence techniques. It progresses from targeted identifier lookups to broad automated scanning and concludes with threat intelligence enrichment.

## Prerequisites

- Target identifiers: at least one of username, email, or full name
- SpiderFoot instance running and configured with API keys
- theHarvester installed with data source API keys
- Threat intelligence API credentials configured
- Legal authorization for the investigation scope

## Workflow

1. **Username Enumeration** -- Search for the target username across platforms
2. **Email Verification** -- Validate email and discover linked accounts
3. **SpiderFoot Scan** -- Automated broad OSINT collection and correlation
4. **theHarvester Scan** -- Gather associated infrastructure and contacts
5. **IOC Enrichment** -- Correlate discovered indicators with threat intel

## Decision Points

- If username enumeration reveals aliases, re-run steps 1-3 with each alias.
- If email check reveals breach data, document and pivot on leaked credentials.
- If SpiderFoot discovers dark web mentions, escalate for threat assessment.

## Legal and Ethical Considerations

- Ensure all collection activities are within authorized scope.
- Do not interact with or log into discovered accounts.
- Document all sources and methods for evidentiary purposes.
- Comply with applicable privacy regulations (GDPR, CCPA, etc.).

## Output Artifacts

- Username enumeration report with confirmed accounts
- Email verification and breach check results
- SpiderFoot scan report with entity graph
- theHarvester collection results
- Consolidated enriched IOC report
