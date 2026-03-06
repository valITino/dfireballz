---
name: Dark Web Trace Investigation
id: pb-dark-web-trace
description: >
  Dark web trace investigation playbook for tracking threat actor activity
  starting from an IOC. Covers OSINT pivoting across surface and dark web,
  username correlation across marketplaces and forums, and threat
  intelligence enrichment to link personas, infrastructure, and campaigns.
case_types:
  - dark-web-investigation
  - threat-actor-profiling
  - osint
  - threat-hunting
tools_required:
  - osint/spiderfoot
  - osint/username_search
  - osint/theharvester
  - threat-intel/ioc_enrichment
  - threat-intel/virustotal
  - osint/domain_reputation
estimated_duration: 60-120 minutes
tags:
  - dark-web
  - osint
  - threat-actor
  - underground-forums
  - marketplace
  - attribution
steps:
  - id: ioc_pivot
    name: Initial IOC Pivot
    tool: threat-intel/enrich_ioc
    action: deep_enrich
    description: >
      Start from the initial IOC (hash, IP, domain, email, or wallet
      address) and enrich across all available threat intelligence
      sources. Identify related infrastructure, campaigns, threat actor
      aliases, and any dark web mentions. Build an initial pivot graph
      of related indicators.
    inputs:
      ioc: "{{evidence.initial_ioc}}"
      ioc_type: "{{evidence.ioc_type}}"
      sources:
        - virustotal
        - otx
        - threatfox
        - malwarebazaar
        - urlhaus
        - abuse_ch
        - inquest
      include_dark_web: true
      include_paste_sites: true
      depth: 2
      output_format: json

  - id: osint_surface_pivot
    name: Surface Web OSINT Pivot
    tool: osint/spiderfoot_scan
    action: run_scan
    description: >
      Conduct broad OSINT scanning on indicators discovered in the
      initial pivot. Search across surface web sources including social
      media, code repositories, paste sites, forums, and breach
      databases. Identify any surface web presence linked to the
      dark web activity.
    inputs:
      scan_name: "darkweb_trace_{{case.id}}"
      target_identifiers: "{{steps.ioc_pivot.outputs.related_identifiers}}"
      modules:
        - sfp_social
        - sfp_paste
        - sfp_breach
        - sfp_github
        - sfp_bitcoin
        - sfp_darknet
        - sfp_email
        - sfp_dns
      max_threads: 10
      timeout: 900

  - id: username_correlation
    name: Username Correlation
    tool: osint/username_search
    action: search_platforms
    description: >
      Search for usernames, aliases, and handles discovered during
      the investigation across surface web platforms and known dark
      web forum indices. Correlate accounts by registration patterns,
      writing style indicators, timezone activity, and shared
      infrastructure. Build a persona map linking aliases.
    inputs:
      usernames: "{{steps.ioc_pivot.outputs.associated_usernames}}"
      platforms: all
      include_archived: true
      check_dark_web_indices: true
      correlation_checks:
        - registration_timing
        - shared_email
        - shared_infrastructure
        - language_patterns
      output_format: json

  - id: infrastructure_mapping
    name: Infrastructure Mapping
    tool: osint/theharvester
    action: run_harvester
    description: >
      Map all infrastructure associated with discovered domains, IPs,
      and email addresses. Enumerate related hosts, subdomains, and
      services. Identify hosting patterns, bulletproof hosting
      providers, and infrastructure reuse across campaigns.
    inputs:
      targets: "{{steps.ioc_pivot.outputs.related_domains}}"
      sources:
        - shodan
        - censys
        - crtsh
        - dnsdumpster
        - securitytrails
      limit: 1000
      output_format: json

  - id: threat_intel_enrichment
    name: Consolidated Threat Intel Enrichment
    tool: threat-intel/enrich_ioc
    action: bulk_enrich
    description: >
      Perform final enrichment of all indicators, personas, and
      infrastructure discovered throughout the investigation. Cross-
      reference against known APT groups, cybercrime campaigns, and
      threat actor databases. Generate attribution confidence scores
      and identify links to prior investigations.
    inputs:
      iocs:
        domains: "{{steps.infrastructure_mapping.outputs.domains}}"
        ips: "{{steps.infrastructure_mapping.outputs.ips}}"
        emails: "{{steps.osint_surface_pivot.outputs.emails}}"
        usernames: "{{steps.username_correlation.outputs.confirmed_accounts}}"
        crypto_wallets: "{{steps.ioc_pivot.outputs.wallet_addresses}}"
      sources:
        - virustotal
        - otx
        - threatfox
        - malwarebazaar
        - misp
        - recorded_future
        - mandiant
      correlate_campaigns: true
      attribution_analysis: true
      confidence_threshold: 30
      output_format: json
---

# Dark Web Trace Investigation Playbook

## Overview

This playbook provides a structured methodology for tracing threat actor activity from an initial indicator of compromise through dark web and surface web OSINT, username correlation, and threat intelligence enrichment. It is designed for investigators tracking criminal infrastructure and personas.

## Prerequisites

- Initial IOC (hash, IP, domain, email, cryptocurrency wallet, or username)
- SpiderFoot instance with dark web modules configured
- Access to dark web forum indices and marketplace databases
- Threat intelligence platform subscriptions
- Tor access for manual verification (if needed)
- Legal authorization for the investigation scope

## Workflow

1. **IOC Pivot** -- Enrich the starting IOC and identify related indicators
2. **Surface Web OSINT** -- Scan for surface web presence linked to dark web activity
3. **Username Correlation** -- Link personas across platforms and forums
4. **Infrastructure Mapping** -- Map hosting, domains, and services
5. **Threat Intel Enrichment** -- Final correlation and attribution analysis

## Decision Points

- If cryptocurrency wallets are found, initiate blockchain analysis.
- If multiple personas are confirmed as the same actor, consolidate and re-run enrichment.
- If infrastructure links to known APT or cybercrime group, reference existing threat profiles.
- If active operations are discovered, coordinate with law enforcement before further action.
- If PGP keys are found, extract and cross-reference across key servers.

## Operational Security

- Use isolated analysis infrastructure for all dark web interactions.
- Route all lookups through anonymization layers where appropriate.
- Do not interact with threat actors or access criminal marketplaces directly.
- Document all access and collection for legal defensibility.

## Output Artifacts

- IOC pivot graph with related indicators
- Surface web OSINT scan results
- Persona correlation map
- Infrastructure topology map
- Threat intelligence enrichment report
- Attribution assessment with confidence levels
