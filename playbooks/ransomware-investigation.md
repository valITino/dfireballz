---
name: Ransomware Investigation
id: pb-ransomware-investigation
description: >
  End-to-end ransomware investigation playbook covering memory forensics
  with Volatility, file recovery with Foremost, disk analysis with
  Sleuth Kit, YARA signature scanning, network forensics for C2 detection,
  and VirusTotal enrichment. Designed for post-incident analysis of
  ransomware-affected systems.
case_types:
  - ransomware
  - incident-response
  - malware-analysis
tools_required:
  - kali-forensics/volatility3
  - kali-forensics/foremost
  - kali-forensics/sleuthkit
  - binary-analysis/yara
  - network-forensics/wireshark
  - threat-intel/virustotal
estimated_duration: 90-180 minutes
tags:
  - ransomware
  - memory-forensics
  - disk-forensics
  - file-recovery
  - incident-response
  - c2-detection
steps:
  - id: volatility_pslist
    name: Memory Analysis - Process Listing
    tool: kali-forensics/volatility_run
    action: pslist
    description: >
      Analyze the memory dump to enumerate running processes at the time
      of capture. Identify suspicious processes, unusual parent-child
      relationships, processes running from temporary directories, and
      any process injection indicators. Cross-reference with known
      ransomware process names.
    inputs:
      memory_dump: "{{evidence.memory_dump_path}}"
      plugin: windows.pslist
      output_format: json
      additional_args:
        - "--pid"
        - "{{target.suspicious_pids}}"

  - id: volatility_netscan
    name: Memory Analysis - Network Connections
    tool: kali-forensics/volatility_run
    action: netscan
    description: >
      Extract active and recently closed network connections from the
      memory dump. Identify connections to known C2 infrastructure,
      unusual outbound connections, data exfiltration channels, and
      lateral movement indicators.
    inputs:
      memory_dump: "{{evidence.memory_dump_path}}"
      plugin: windows.netscan
      output_format: json
      filter_state:
        - ESTABLISHED
        - CLOSE_WAIT
        - SYN_SENT

  - id: volatility_malfind
    name: Memory Analysis - Malicious Code Detection
    tool: kali-forensics/volatility_run
    action: malfind
    description: >
      Scan process memory for injected code, hollowed processes, and
      suspicious memory regions with executable permissions. Dump
      identified regions for further analysis. Flag any process with
      PAGE_EXECUTE_READWRITE protections or unmapped executable sections.
    inputs:
      memory_dump: "{{evidence.memory_dump_path}}"
      plugin: windows.malfind
      output_format: json
      dump_dir: "{{case.working_dir}}/malfind_dumps"
      include_dump: true

  - id: foremost_recover
    name: File Recovery
    tool: kali-forensics/foremost_recover
    action: recover_files
    description: >
      Recover deleted files and file fragments from the disk image using
      Foremost. Focus on recovering ransom notes, encryption key files,
      original unencrypted files, dropped payloads, and any staging
      artifacts left by the ransomware operator.
    inputs:
      image_path: "{{evidence.disk_image_path}}"
      output_dir: "{{case.working_dir}}/recovered_files"
      file_types:
        - doc
        - pdf
        - txt
        - exe
        - dll
        - zip
        - png
        - jpg
      verbose: true
      audit_file: true

  - id: sleuthkit_analyze
    name: Disk Image Analysis
    tool: kali-forensics/sleuthkit_analyze
    action: analyze_image
    description: >
      Analyze the disk image using Sleuth Kit tools to examine the
      filesystem timeline, identify recently modified files, locate
      ransomware artifacts (encrypted files, ransom notes), and
      reconstruct the attack timeline. Focus on temp directories,
      startup locations, and user profile folders.
    inputs:
      image_path: "{{evidence.disk_image_path}}"
      operations:
        - timeline_creation
        - file_listing
        - deleted_file_recovery
        - metadata_analysis
      focus_paths:
        - "/Windows/Temp"
        - "/Users/*/AppData"
        - "/Users/*/Desktop"
        - "/ProgramData"
        - "/Windows/System32/Tasks"
      time_range:
        start: "{{case.incident_start}}"
        end: "{{case.incident_end}}"
      output_dir: "{{case.working_dir}}/sleuthkit_output"

  - id: yara_scan
    name: YARA Ransomware Scan
    tool: binary-analysis/yara_match
    action: scan_with_rules
    description: >
      Scan recovered files, memory dumps, and disk artifacts against
      ransomware-specific YARA rules. Match against known ransomware
      families, encryption routines, ransom note templates, and
      common ransomware behaviors.
    inputs:
      scan_paths:
        - "{{case.working_dir}}/malfind_dumps"
        - "{{case.working_dir}}/recovered_files"
      rule_paths:
        - /opt/yara-rules/ransomware
        - /opt/yara-rules/malware
        - /opt/yara-rules/crypto
      recursive: true
      timeout: 300
      output_format: json

  - id: network_c2_detection
    name: Network Forensics - C2 Detection
    tool: network-forensics/wireshark_analyze_pcap
    action: analyze_pcap
    description: >
      Analyze network packet captures for command-and-control communication
      patterns. Identify beaconing behavior, DNS tunneling, encrypted C2
      channels, data exfiltration, and lateral movement traffic. Correlate
      with IP addresses found in memory analysis.
    inputs:
      pcap_path: "{{evidence.pcap_path}}"
      analysis_type: security
      filters:
        - "ip.addr == {{steps.volatility_netscan.outputs.suspicious_ips}}"
      detect:
        - beaconing
        - dns_tunneling
        - encrypted_c2
        - data_exfiltration
        - lateral_movement
      output_format: json
      export_conversations: true

  - id: vt_enrichment
    name: VirusTotal Enrichment
    tool: threat-intel/vt_lookup
    action: bulk_lookup
    description: >
      Submit all identified hashes, IP addresses, and domains to
      VirusTotal for enrichment. Identify the ransomware family,
      obtain AV detection names, retrieve behavioral reports, and
      collect associated infrastructure. Map findings to known
      ransomware campaigns and threat actors.
    inputs:
      indicators:
        hashes: "{{steps.yara_scan.outputs.matched_hashes}}"
        ips: "{{steps.volatility_netscan.outputs.suspicious_ips}}"
        domains: "{{steps.network_c2_detection.outputs.contacted_domains}}"
      include_behavior: true
      include_relationships: true
      output_format: json
---

# Ransomware Investigation Playbook

## Overview

This playbook guides investigators through a structured ransomware incident investigation, from memory forensics through disk analysis, file recovery, and threat intelligence enrichment. It is designed for post-compromise analysis of systems affected by ransomware.

## Prerequisites

- Memory dump from the affected system (raw or crashdump format)
- Forensic disk image (E01, dd, or raw format)
- Network packet captures from the incident timeframe
- Volatility 3 with appropriate symbol tables
- Ransomware-specific YARA rule sets
- VirusTotal API key configured
- Isolated analysis workstation

## Workflow

1. **Process Listing** -- Enumerate and analyze running processes from memory
2. **Network Connections** -- Extract network connections and identify C2
3. **Malicious Code Detection** -- Find injected code and hollowed processes
4. **File Recovery** -- Recover deleted files including ransom notes and payloads
5. **Disk Analysis** -- Timeline analysis and artifact recovery from disk image
6. **YARA Scan** -- Match artifacts against ransomware signatures
7. **C2 Detection** -- Analyze network traffic for C2 and exfiltration
8. **VirusTotal Enrichment** -- Identify ransomware family and campaign

## Decision Points

- If malfind identifies injected processes, dump and submit to sandbox analysis.
- If file recovery yields encryption keys or decryption tools, preserve and escalate.
- If C2 infrastructure is active, coordinate with network team for blocking.
- If ransomware family is identified, check for available decryptors (NoMoreRansom.org).
- If data exfiltration is confirmed, escalate to legal and compliance teams.

## Evidence Preservation

- Maintain chain of custody for all evidence items.
- Hash all artifacts before and after analysis.
- Document all tools, versions, and commands used.
- Preserve original evidence in read-only state.

## Output Artifacts

- Process listing and analysis report
- Network connection map with C2 indicators
- Malfind dump files and analysis
- Recovered files inventory
- Filesystem timeline
- YARA match report
- Network forensics report with C2 indicators
- VirusTotal enrichment report with ransomware family identification
