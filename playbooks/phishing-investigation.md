---
name: Phishing Investigation
id: pb-phishing-investigation
description: >
  Phishing email investigation playbook organized by the canonical
  forensic process phases (Readiness → Identification → Acquisition →
  Examination → Analysis → Reporting). Covers email header analysis,
  sender domain reputation assessment, URL chain analysis through
  redirects, WHOIS lookups on suspicious domains, IP abuse checks, and
  HTML artifact extraction from phishing kits. Designed for SOC analysts
  triaging reported phishing emails.
case_types:
  - phishing
  - email-security
  - incident-response
tools_required:
  - documentation/coc_generator
  - kali-forensics/hashdeep
  - email-forensics/header_analyzer
  - osint/domain_reputation
  - email-forensics/url_chain_analyzer
  - osint/whois
  - threat-intel/abuseipdb
  - email-forensics/html_extractor
  - reporting/md_generator
estimated_duration: 20-45 minutes
process_model: dfireballz/forensic-process-v1
phases:
  - readiness
  - identification
  - acquisition
  - examination
  - analysis
  - reporting
tags:
  - phishing
  - email-forensics
  - url-analysis
  - social-engineering
  - incident-response
steps:
  # ── Phase 1 — Readiness ─────────────────────────────────────────────
  - id: case_precondition_check
    phase: readiness
    name: Case Precondition Check
    tool: documentation/coc_generator
    action: write_precondition
    description: >
      Confirm the platform is ready before any evidence is touched.
      Verify the case is open with documented authority, the relevant
      MCP servers are healthy (osint, threat-intel, kali-forensics,
      filesystem), required API keys are present (URLScan, VirusTotal,
      AbuseIPDB), and the host time source is UTC-synced. Pin the
      versions of every tool the playbook will invoke. Write the
      precondition record so reviewers can later reproduce the
      environment.
    inputs:
      case_id: "{{case.id}}"
      required_mcp_servers:
        - osint
        - threat-intel
        - kali-forensics
        - filesystem
      required_api_keys:
        - urlscan
        - virustotal
        - abuseipdb
      pin_tool_versions:
        - email-forensics/header_analyzer
        - osint/whois_lookup
        - threat-intel/urlscan
      output_path: "{{case.dir}}/01-readiness/case-precondition.json"
      coc_action: case_opened

  # ── Phase 2 — Identification ────────────────────────────────────────
  - id: evidence_intake
    phase: identification
    name: Phishing Evidence Intake
    tool: documentation/coc_generator
    action: create_evidence_record
    description: >
      Classify the report as phishing and create an evidence record
      for the original email. Capture source (mail gateway, user
      forward, threat intel feed), reporting party, original headers
      preserved (EML/MSG only — never forwarded copies), and the
      authority basis for handling user mail. Assign a stable evidence
      ID under the case scheme.
    inputs:
      case_id: "{{case.id}}"
      evidence_type: phishing-email
      evidence_fields:
        evidence_id: "{{evidence.assigned_id}}"
        source: "{{evidence.report_source}}"
        reporting_party: "{{evidence.reporting_party}}"
        format: "{{evidence.email_format}}"  # eml | msg
        original_path: "{{evidence.email_file_path}}"
        authority_reference: "{{case.authority_reference}}"
        received_datetime: "{{timestamp.now}}"
      output_path: "{{case.dir}}/02-identification/evidence-records/{{evidence.assigned_id}}.json"
      coc_action: identified

  # ── Phase 3 — Acquisition ───────────────────────────────────────────
  - id: email_acquisition
    phase: acquisition
    name: Email Acquisition and Hash Verification
    tool: kali-forensics/hashdeep
    action: hash_and_copy
    description: >
      Copy the original email file into the case acquisition directory
      and compute SHA-256 + MD5. Independently re-verify with a second
      tool invocation. Write the acquisition manifest entry. Originals
      remain read-only in /evidence; all subsequent work uses the
      working copy under the case directory.
    inputs:
      source: "{{evidence.email_file_path}}"
      destination: "{{case.dir}}/03-acquisition/{{evidence.assigned_id}}/{{evidence.assigned_id}}.{{evidence.email_format}}"
      hash_algorithms:
        - sha256
        - md5
      acquisition_log: "{{case.dir}}/03-acquisition/{{evidence.assigned_id}}/{{evidence.assigned_id}}_acquisition.log"
      verification_log: "{{case.dir}}/03-acquisition/{{evidence.assigned_id}}/{{evidence.assigned_id}}_verification.log"
      manifest_path: "{{case.dir}}/03-acquisition/acquisition-manifest.json"
      examiner: "{{analyst.name}}"
      coc_actions:
        - acquired
        - verified

  # ── Phase 4 — Examination ───────────────────────────────────────────
  - id: email_header_analysis
    phase: examination
    name: Email Header Analysis
    tool: email-forensics/header_analyzer
    action: analyze_headers
    description: >
      Parse and analyze the full email headers to trace the message path
      from origin to delivery. Validate SPF, DKIM, and DMARC authentication
      results. Identify the true sending IP, relay chain, and any header
      forgery or spoofing indicators. Extract Message-ID, timestamps, and
      X-headers for forensic correlation. Operates on the working copy
      from Phase 3 — the original file is never opened in this step.
    inputs:
      email_source: "{{steps.email_acquisition.outputs.destination}}"
      source_evidence_id: "{{evidence.assigned_id}}"
      source_sha256: "{{steps.email_acquisition.outputs.sha256}}"
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
      output_path: "{{case.dir}}/04-examination/{{evidence.assigned_id}}/headers.json"

  - id: domain_reputation
    phase: examination
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
      output_path: "{{case.dir}}/04-examination/{{evidence.assigned_id}}/domain-reputation.json"

  - id: url_chain_analysis
    phase: examination
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
      output_dir: "{{case.dir}}/04-examination/{{evidence.assigned_id}}/url-analysis"
      output_format: json

  - id: whois_lookup
    phase: examination
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
      output_path: "{{case.dir}}/04-examination/{{evidence.assigned_id}}/whois.json"

  - id: abuse_ip_check
    phase: examination
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
      output_path: "{{case.dir}}/04-examination/{{evidence.assigned_id}}/abuse-ip.json"

  - id: html_artifact_extraction
    phase: examination
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
        - "{{steps.email_acquisition.outputs.destination}}"
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
      output_dir: "{{case.dir}}/04-examination/{{evidence.assigned_id}}/html-artifacts"
      output_format: json

  # ── Phase 5 — Analysis ──────────────────────────────────────────────
  - id: findings_synthesis
    phase: analysis
    name: Findings Synthesis and IOC Consolidation
    tool: documentation/coc_generator
    action: write_findings
    description: >
      Correlate all examination outputs into a single findings record.
      Each finding cites the contributing examination artifact paths,
      their source-evidence SHA-256, and the AI-invocation audit IDs
      (from output/logs/ai_invocations.jsonl). Distinguish fact (e.g.
      "DKIM failed") from interpretation (e.g. "consistent with
      sender-spoofing attack"). Build the consolidated IOC list
      (domains, IPs, URLs, file hashes) for downstream blocking and
      threat-intel sharing. Confirm or refute each starting hypothesis
      with rationale.
    inputs:
      case_id: "{{case.id}}"
      evidence_id: "{{evidence.assigned_id}}"
      contributing_examination_outputs:
        - "{{steps.email_header_analysis.outputs.path}}"
        - "{{steps.domain_reputation.outputs.path}}"
        - "{{steps.url_chain_analysis.outputs.summary_path}}"
        - "{{steps.whois_lookup.outputs.path}}"
        - "{{steps.abuse_ip_check.outputs.path}}"
        - "{{steps.html_artifact_extraction.outputs.summary_path}}"
      findings_path: "{{case.dir}}/05-analysis/findings.json"
      ioc_list_path: "{{case.dir}}/05-analysis/iocs.json"
      hypothesis_set:
        - sender_spoofing
        - account_compromise
        - credential_harvesting
        - malware_delivery
        - brand_impersonation

  # ── Phase 6 — Reporting / Closure ───────────────────────────────────
  - id: report_generation
    phase: reporting
    name: Report Generation and Case Closure
    tool: reporting/md_generator
    action: generate_report
    description: >
      Generate the formal report from the analysis output. Include
      executive summary, methodology (citing this playbook and the
      DFIReballz forensic process model), evidence list with hashes,
      findings with citations, IoC table, full chain-of-custody log,
      audit-log digest, and a final hash re-verification of the source
      email. Write the closure manifest and append the case_closed
      chain-of-custody entry. Mark the case status closed.
    inputs:
      case_id: "{{case.id}}"
      report_formats:
        - md
        - html
        - pdf
      report_dir: "/reports/{{case.id}}"
      include:
        - executive_summary
        - methodology
        - evidence_list
        - findings
        - ioc_table
        - chain_of_custody_log
        - audit_log_digest
        - timeline
      reverify_source_hashes:
        - "{{steps.email_acquisition.outputs.destination}}"
      closure_manifest_path: "{{case.dir}}/06-reporting/closure-manifest.json"
      coc_action: case_closed
---

# Phishing Investigation Playbook

## Overview

This playbook investigates a reported phishing email, organized by the
canonical six-phase forensic process model defined in
[`docs/forensic-process.md`](../docs/forensic-process.md). It is the
worked reference example for that model — every other playbook will be
migrated to the same structure in a follow-up slice.

The investigation moves through Readiness → Identification → Acquisition
→ Examination → Analysis → Reporting. Each phase has explicit entry and
exit criteria; the on-disk layout under `cases/<case-id>/0N-<phase>/`
mirrors the phases so the directory tree itself is the audit trail.

## Prerequisites

- Original email in EML or MSG format (not forwarded — forwarded copies
  alter headers).
- Sandboxed environment for URL detonation.
- API keys for URLScan, VirusTotal, AbuseIPDB validated by the
  Readiness phase.
- Screenshot capture capability for URL chain analysis.
- Case opened via the orchestrator with documented authority for
  handling user mail.

## Workflow

### Phase 1 — Readiness

**Entry.** Case opened, authority documented.
**Exit.** `01-readiness/case-precondition.json` written; chain-of-custody
entry `case_opened` recorded.

1. **Case Precondition Check** — verify MCP servers, API keys, time
   source, pin tool versions.

### Phase 2 — Identification

**Entry.** Readiness exit met.
**Exit.** Evidence record exists with assigned ID; chain-of-custody
entry `identified` recorded.

2. **Phishing Evidence Intake** — classify the report, create the
   evidence record, capture source/format/authority.

### Phase 3 — Acquisition

**Entry.** Evidence record exists.
**Exit.** Working copy hashed and independently verified; manifest entry
written; chain-of-custody entries `acquired` and `verified` recorded.

3. **Email Acquisition and Hash Verification** — copy the email into
   the case directory, compute SHA-256 + MD5, re-verify with a second
   tool. Originals remain read-only in `/evidence`.

### Phase 4 — Examination

**Entry.** Acquisition exit met (verified working copy exists).
**Exit.** Extracted artifacts manifest written; pre/post hashes of
the source copy match (no mutation).

4. **Email Header Analysis** — trace message origin, validate SPF/DKIM/DMARC.
5. **Sender Domain Reputation** — assess sender and linked domains.
6. **URL Redirect Chain Analysis** — follow URLs to final landing pages.
7. **WHOIS Lookup** — registration details for suspicious domains.
8. **Abuse IP Check** — sending and relay IPs against abuse databases.
9. **HTML Artifact Extraction** — forms, scripts, phishing-kit artifacts.

### Phase 5 — Analysis

**Entry.** Examination exit met.
**Exit.** `05-analysis/findings.json` and `iocs.json` written; every
finding cites contributing artifacts and audit IDs; every hypothesis
supported or refuted.

10. **Findings Synthesis and IOC Consolidation** — correlate the six
    examination outputs, distinguish fact from interpretation, build
    the IOC list, evaluate hypotheses.

### Phase 6 — Reporting / Closure

**Entry.** Analysis exit met.
**Exit.** Report in `reports/<case-id>/`; closure manifest written;
final hash re-verification passes; `case_closed` chain-of-custody
entry recorded; case status closed.

11. **Report Generation and Case Closure** — generate md/html/pdf,
    seal audit log, re-verify hashes, close the case.

## Decision Points

- If SPF/DKIM/DMARC all pass and domain is legitimate, treat as
  possible account compromise; pivot to incident-response playbook for
  the affected mailbox.
- If URL chain leads to credential harvesting, immediately block the
  domain at the web proxy and check mail logs for successful
  submissions before completing analysis.
- If newly registered domains are detected, pivot to OSINT domain
  investigation playbook for infrastructure mapping.
- If malware download is detected in the URL chain, pivot to malware
  analysis playbook for the dropped sample.
- If brand impersonation is confirmed, initiate takedown procedures
  alongside the investigation.

Each pivot is a loopback or a related-case spawn — both must be logged
in the chain of custody per the loopback policy in
[`docs/forensic-process.md`](../docs/forensic-process.md).

## Immediate Response Actions

These are operational responses that run in parallel with the
investigation, not part of the forensic process. They are tracked
separately on the case record:

- Block sender domain and IP at the email gateway.
- Block phishing URLs at the web proxy.
- Search mailboxes for additional recipients of the same campaign.
- Reset credentials for any users who interacted with the phish.

## Output Artifacts

By phase:

| Phase | Artifact |
|---|---|
| 01 Readiness | `case-precondition.json` |
| 02 Identification | Evidence record JSON for the email |
| 03 Acquisition | Working copy, acquisition log, verification log, manifest entry |
| 04 Examination | `headers.json`, `domain-reputation.json`, `url-analysis/`, `whois.json`, `abuse-ip.json`, `html-artifacts/` |
| 05 Analysis | `findings.json`, `iocs.json` |
| 06 Reporting | Report (md/html/pdf), `closure-manifest.json`, sealed audit-log digest |
