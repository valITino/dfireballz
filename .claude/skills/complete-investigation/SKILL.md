---
name: complete-investigation
description: Run a full 11-phase forensic investigation across all MCP servers — disk, memory, Windows artifacts, malware, network, OSINT, threat intel, timeline, and reporting.
---

Run the complete forensic investigation workflow against the specified target.

**Usage:** `/complete-investigation <target>`

Where `<target>` is the evidence path or subject — e.g. `/evidence/disk.dd`, `/evidence/memdump.raw`, `suspicious-domain.com`.

If no target is provided, ask the user what they want to investigate.

## Instructions

1. Load the investigation template: call `get_template(name="complete-investigation", target="$ARGUMENTS")`
2. Follow all 11 phases in order — do NOT skip any phase
3. Use the MCP servers and their tools for every phase (kali-forensics, winforensics, osint, threat-intel, binary-analysis, network-forensics, filesystem)
4. Log chain of custody for every evidence access
5. Write findings incrementally to `/workspace/output/findings/` (containerized) or `./output/findings/` (host)
6. Generate the final report in `/reports/`
