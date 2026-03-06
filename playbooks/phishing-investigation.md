---
name: Phishing Investigation
id: pb-phishing-investigation
description: >
  Phishing email investigation playbook covering email header analysis,
  sender domain reputation assessment, URL chain analysis through redirects,
  WHOIS lookups on suspicious domains, IP abuse checks, and HTML artifact
  extraction from phishing kits. Designed for SOC analysts triaging
  reported phishing emails.
case_types:
  - phishing
  - email-security
  - incident-response
tools_required:
  - email-forensics/header_analyzer
  - osint/domain_reputation
  - email-forensics/url_chain_analyzer
  - osint/whois
  - threat-intel/abuseipdb
  - email-forensics/html_extractor
estimated_duration: 20-45 minutes
tags:
  - phishing
  - email-forensics
  - url-analysis
  - social-engineering
  - incident-response
steps:
  - id: email_header_analysis
    name: Email Header Analysis
    tool: email-forensics/header_analyzer
    action: analyze_headers
    description: >
      Parse and analyze the full email headers to trace the message path
      from origin to delivery. Validate SPF, DKIM, and DMARC authentication
      results. Identify the true sending IP, relay chain, and any header
      forgery or spoofing indicators. Extract Message-ID, timestamps, and
      X-headers for forensic correlation.
    inputs:
      email_source: "{{evidence.email_file_path}}"
      parse_mode: full
      validate_auth:
        - spf
        - dkim
        - dmarc
      extract_fields:
        - from
        - to
        - reply-to
        - return-path
        - received
        - message-id
        - x-originating-ip
        - x-mailer
      output_format: json

  - id: domain_reputation
    name: Sender Domain Reputation Check
    tool: osint/domain_reputation
    action: check_reputation
    description: >
      Assess the reputation of the sending domain and any domains found
      in the email body. Check against blocklists, phishing databases,
      domain age, registration patterns, and threat intelligence feeds.
      Flag newly registered domains, disposable email services, and
      known phishing infrastructure.
    inputs:
      domains:
        - "{{steps.email_header_analysis.outputs.sender_domain}}"
        - "{{steps.email_header_analysis.outputs.reply_to_domain}}"
        - "{{steps.email_header_analysis.outputs.return_path_domain}}"
      checks:
        - blocklist
        - phishing_database
        - domain_age
        - dns_records
        - ssl_certificate
      sources:
        - google_safe_browsing
        - phishtank
        - openphish
        - urlhaus
        - virustotal
      output_format: json

  - id: url_chain_analysis
    name: URL Redirect Chain Analysis
    tool: email-forensics/url_chain_analyzer
    action: follow_chain
    description: >
      Follow all URLs found in the email body through their complete
      redirect chain to identify the final landing page. Capture
      screenshots at each hop, record HTTP status codes, identify
      cloaking mechanisms, and detect credential harvesting forms or
      malware download endpoints.
    inputs:
      urls: "{{steps.email_header_analysis.outputs.body_urls}}"
      max_redirects: 15
      capture_screenshots: true
      capture_dom: true
      user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      timeout_per_url: 30
      sandbox_mode: true
      output_dir: "{{case.working_dir}}/url_analysis"
      output_format: json

  - id: whois_lookup
    name: WHOIS Lookup on Suspicious Domains
    tool: osint/whois_lookup
    action: query_whois
    description: >
      Perform WHOIS lookups on all suspicious domains identified in the
      email, including sender domain, reply-to domain, and all domains
      in URL chains. Record registrant details, creation dates, registrar,
      and name servers. Flag domains registered within the last 30 days
      as high-risk indicators.
    inputs:
      domains:
        - "{{steps.email_header_analysis.outputs.sender_domain}}"
        - "{{steps.url_chain_analysis.outputs.final_domains}}"
      follow_referrals: true
      flag_age_threshold_days: 30
      output_format: json

  - id: abuse_ip_check
    name: Abuse IP Check
    tool: threat-intel/abuse_ip_check
    action: check_ips
    description: >
      Check the sending IP address and all IPs in the email relay chain
      against abuse databases. Retrieve abuse confidence scores, report
      counts, ISP information, geographic location, and usage type.
      Identify IPs associated with known spam, phishing, or malware
      distribution infrastructure.
    inputs:
      ip_addresses:
        - "{{steps.email_header_analysis.outputs.originating_ip}}"
        - "{{steps.email_header_analysis.outputs.relay_ips}}"
      sources:
        - abuseipdb
        - spamhaus
        - barracuda
        - sorbs
      max_age_days: 90
      confidence_threshold: 25
      output_format: json

  - id: html_artifact_extraction
    name: HTML Artifact Extraction
    tool: email-forensics/html_extractor
    action: extract_artifacts
    description: >
      Extract and analyze HTML artifacts from the email body and any
      phishing landing pages. Identify embedded forms, credential
      harvesting fields, hidden iframes, JavaScript payloads, tracking
      pixels, encoded content, and brand impersonation elements.
      Deobfuscate any encoded or obfuscated scripts.
    inputs:
      sources:
        - "{{evidence.email_file_path}}"
        - "{{steps.url_chain_analysis.outputs.captured_pages}}"
      extract:
        - forms
        - iframes
        - scripts
        - tracking_pixels
        - embedded_objects
        - meta_tags
        - hidden_fields
      deobfuscate_js: true
      identify_brand_impersonation: true
      output_dir: "{{case.working_dir}}/html_artifacts"
      output_format: json
---

# Phishing Investigation Playbook

## Overview

This playbook provides a structured approach to investigating reported phishing emails. It covers the complete investigation lifecycle from header analysis through URL detonation and artifact extraction.

## Prerequisites

- Original email in EML or MSG format (not forwarded)
- Sandboxed environment for URL analysis
- API keys for reputation services and threat intelligence
- Screenshot capture capability for URL chain analysis

## Workflow

1. **Email Header Analysis** -- Trace message origin and validate authentication
2. **Domain Reputation** -- Assess sender and linked domain reputations
3. **URL Chain Analysis** -- Follow redirect chains to final landing pages
4. **WHOIS Lookup** -- Investigate domain registration details
5. **Abuse IP Check** -- Check sending infrastructure against abuse databases
6. **HTML Artifact Extraction** -- Extract forms, scripts, and phishing kit artifacts

## Decision Points

- If SPF/DKIM/DMARC all pass and domain is legitimate, investigate possible account compromise.
- If URL chain leads to credential harvesting, immediately block the domain and check for successful submissions.
- If newly registered domains are detected, pivot to OSINT domain investigation playbook.
- If malware download is detected in URL chain, pivot to malware analysis playbook.
- If brand impersonation is confirmed, initiate takedown procedures.

## Immediate Response Actions

- Block sender domain and IP at the email gateway.
- Block phishing URLs at the web proxy.
- Search mailboxes for additional recipients of the same campaign.
- Reset credentials for any users who interacted with the phish.

## Output Artifacts

- Email header analysis report with authentication results
- Domain reputation assessment
- URL chain analysis with screenshots
- WHOIS registration details
- Abuse IP check results
- HTML artifact extraction report
- IOC list for blocking (domains, IPs, URLs, hashes)
