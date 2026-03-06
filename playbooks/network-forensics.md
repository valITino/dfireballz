---
name: Network Forensics - PCAP Investigation
id: pb-network-forensics
description: >
  Network forensics playbook for comprehensive PCAP analysis using
  Wireshark/tshark. Covers protocol statistics, DNS extraction, HTTP
  transaction analysis, TLS certificate inspection, security auditing,
  and geographic IP resolution. Designed for investigating network
  captures from security incidents.
case_types:
  - network-forensics
  - incident-response
  - threat-hunting
  - data-exfiltration
tools_required:
  - network-forensics/wireshark
  - network-forensics/geoip
estimated_duration: 30-90 minutes
tags:
  - network-forensics
  - pcap
  - wireshark
  - dns
  - http
  - tls
  - protocol-analysis
steps:
  - id: analyze_pcap
    name: PCAP Overview Analysis
    tool: network-forensics/wireshark_analyze_pcap
    action: analyze_pcap
    description: >
      Perform an initial overview analysis of the PCAP file to determine
      capture duration, packet counts, conversation summaries, and
      high-level traffic patterns. Identify the top talkers, unusual
      protocols, and any immediate anomalies. Establish baseline for
      deeper analysis in subsequent steps.
    inputs:
      pcap_path: "{{evidence.pcap_path}}"
      analysis_type: overview
      include:
        - capture_info
        - conversations
        - endpoints
        - io_graph
      top_n: 20
      output_format: json
      output_dir: "{{case.working_dir}}/pcap_overview"

  - id: protocol_stats
    name: Protocol Statistics
    tool: network-forensics/wireshark_get_protocol_stats
    action: get_protocol_stats
    description: >
      Generate detailed protocol hierarchy statistics from the capture.
      Identify protocol distribution, unusual or unexpected protocols,
      encapsulated traffic, and protocol anomalies. Flag any non-standard
      port usage or protocol tunneling that may indicate evasion
      techniques or covert channels.
    inputs:
      pcap_path: "{{evidence.pcap_path}}"
      stats_type:
        - protocol_hierarchy
        - conversations
        - endpoints
        - packet_lengths
      filter: ""
      output_format: json

  - id: extract_dns
    name: DNS Query Extraction
    tool: network-forensics/wireshark_extract_dns
    action: extract_dns
    description: >
      Extract all DNS queries and responses from the capture. Identify
      suspicious lookups including DGA-generated domains, DNS tunneling
      indicators, unusual record types (TXT, NULL), high-frequency
      lookups, NXDOMAIN patterns, and queries to non-standard DNS
      servers. Build a domain resolution map for the capture period.
    inputs:
      pcap_path: "{{evidence.pcap_path}}"
      extract:
        - queries
        - responses
        - nxdomains
        - txt_records
      detect:
        - dga_domains
        - dns_tunneling
        - fast_flux
        - non_standard_servers
      output_format: json
      output_dir: "{{case.working_dir}}/dns_extraction"

  - id: extract_http
    name: HTTP Transaction Extraction
    tool: network-forensics/wireshark_extract_http
    action: extract_http
    description: >
      Extract and analyze all HTTP transactions from the capture. Recover
      requested URLs, POST data, uploaded files, downloaded content,
      cookies, and user agent strings. Identify suspicious patterns such
      as beaconing, data exfiltration via HTTP, web shell communications,
      and exploit kit traffic.
    inputs:
      pcap_path: "{{evidence.pcap_path}}"
      extract:
        - requests
        - responses
        - objects
        - post_data
        - cookies
        - user_agents
      export_objects: true
      export_dir: "{{case.working_dir}}/http_objects"
      detect:
        - beaconing
        - exfiltration
        - webshell
        - exploit_kit
      output_format: json

  - id: extract_tls
    name: TLS Certificate and Handshake Analysis
    tool: network-forensics/wireshark_extract_tls
    action: extract_tls
    description: >
      Extract TLS handshake data including client hello parameters,
      server certificates, cipher suites, and JA3/JA3S fingerprints.
      Identify self-signed certificates, expired certificates, known
      malicious JA3 hashes, and suspicious SNI values. Detect TLS
      connections to known malicious infrastructure.
    inputs:
      pcap_path: "{{evidence.pcap_path}}"
      extract:
        - certificates
        - handshakes
        - ja3_fingerprints
        - ja3s_fingerprints
        - sni_values
        - cipher_suites
      detect:
        - self_signed
        - expired_certs
        - known_malicious_ja3
        - certificate_anomalies
      output_format: json
      export_certs: true
      export_dir: "{{case.working_dir}}/tls_certs"

  - id: security_audit
    name: Security Audit
    tool: network-forensics/wireshark_security_audit
    action: audit_traffic
    description: >
      Perform a comprehensive security audit of the network capture.
      Detect port scans, brute force attempts, credential exposure in
      cleartext protocols, ARP spoofing, MITM indicators, lateral
      movement patterns, and policy violations. Generate security
      findings with severity ratings.
    inputs:
      pcap_path: "{{evidence.pcap_path}}"
      checks:
        - port_scanning
        - brute_force
        - cleartext_credentials
        - arp_spoofing
        - dns_poisoning
        - smb_attacks
        - lateral_movement
        - data_exfiltration
        - policy_violations
      severity_threshold: low
      output_format: json
      output_dir: "{{case.working_dir}}/security_audit"

  - id: geo_resolve
    name: Geographic IP Resolution
    tool: network-forensics/wireshark_geo_resolve
    action: resolve_geoip
    description: >
      Resolve all external IP addresses in the capture to geographic
      locations. Generate a connection map showing communication flows
      by country, ASN, and organization. Identify connections to
      high-risk geographies, unexpected foreign infrastructure, and
      known hosting providers used by threat actors.
    inputs:
      pcap_path: "{{evidence.pcap_path}}"
      geoip_database: /opt/geoip/GeoLite2-City.mmdb
      asn_database: /opt/geoip/GeoLite2-ASN.mmdb
      resolve:
        - country
        - city
        - asn
        - organization
      filter_private: true
      generate_map: true
      flag_countries: "{{case.high_risk_countries}}"
      output_format: json
      output_dir: "{{case.working_dir}}/geoip_results"
---

# Network Forensics - PCAP Investigation Playbook

## Overview

This playbook provides a systematic approach to analyzing network packet captures from security incidents. It progresses from high-level traffic overview through protocol-specific extraction to security auditing and geographic analysis.

## Prerequisites

- PCAP or PCAPNG file from the incident
- Wireshark/tshark installed (version 3.x or later)
- GeoIP databases (GeoLite2-City and GeoLite2-ASN)
- Sufficient disk space for extracted objects
- JA3/JA3S hash lookup database

## Workflow

1. **PCAP Overview** -- Establish capture parameters and identify top talkers
2. **Protocol Statistics** -- Analyze protocol distribution and anomalies
3. **DNS Extraction** -- Extract and analyze DNS queries for suspicious activity
4. **HTTP Extraction** -- Recover HTTP transactions and exported objects
5. **TLS Analysis** -- Inspect certificates, handshakes, and JA3 fingerprints
6. **Security Audit** -- Detect attacks, policy violations, and suspicious patterns
7. **Geographic Resolution** -- Map external connections to locations and ASNs

## Decision Points

- If DNS tunneling is detected, extract tunnel payload and pivot to malware analysis.
- If HTTP objects contain executables, submit to malware analysis playbook.
- If cleartext credentials are found, initiate credential compromise response.
- If C2 beaconing is detected, extract timing intervals and correlate with endpoint telemetry.
- If data exfiltration is confirmed, quantify data volume and escalate.

## Output Artifacts

- PCAP overview and capture statistics
- Protocol hierarchy and conversation analysis
- DNS query log with anomaly flags
- HTTP transaction log with extracted objects
- TLS certificate inventory and JA3 fingerprints
- Security audit findings with severity ratings
- Geographic connection map
