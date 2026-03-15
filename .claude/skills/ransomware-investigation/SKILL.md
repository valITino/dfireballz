---
name: ransomware-investigation
description: Investigate a ransomware incident — triage, artifact analysis, attack chain reconstruction, malware analysis, network forensics, and reporting.
---

Investigate the ransomware incident affecting the specified target.

**Usage:** `/ransomware-investigation <target>`

Where `<target>` is the evidence path or affected system — e.g. `/evidence/encrypted-host/`, `/evidence/ransom-note.txt`.

If no target is provided, ask the user for the evidence location.

## Instructions

1. Load the investigation template: call `get_template(name="ransomware-investigation", target="$ARGUMENTS")`
2. Follow all 6 phases: Initial Triage, Artifact Analysis, Attack Chain Reconstruction, Malware Analysis, Network Forensics, Reporting
3. Use these MCP servers: kali-forensics, winforensics, binary-analysis, network-forensics, threat-intel, filesystem
4. Identify the ransomware family and C2 infrastructure
5. Log chain of custody for every evidence access
6. Generate report with MITRE ATT&CK mapping and remediation steps
