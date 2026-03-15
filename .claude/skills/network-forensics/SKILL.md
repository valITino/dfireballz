---
name: network-forensics
description: Analyze network traffic — PCAP triage, protocol analysis, anomaly detection, IoC extraction, stream reconstruction, and reporting.
---

Perform network forensics analysis on the specified target.

**Usage:** `/network-forensics <target>`

Where `<target>` is the PCAP file or capture path — e.g. `/evidence/capture.pcap`, `/evidence/network-dump/`.

If no target is provided, ask the user for the PCAP location.

## Instructions

1. Load the investigation template: call `get_template(name="network-forensics", target="$ARGUMENTS")`
2. Follow all 6 phases: PCAP Triage, Protocol Analysis, Anomaly Detection, IoC Extraction, Stream Reconstruction, Reporting
3. Use these MCP servers: network-forensics (18 tshark tools, tcpdump), threat-intel, osint, filesystem
4. Extract JA3/JA3S fingerprints for TLS analysis
5. Log chain of custody for every evidence access
6. Generate report with traffic analysis and IoC correlation
