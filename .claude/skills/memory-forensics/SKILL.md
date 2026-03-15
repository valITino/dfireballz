---
name: memory-forensics
description: Analyze a memory dump — process analysis, network connections, persistence mechanisms, malware detection with Volatility3, and reporting.
---

Perform memory forensics analysis on the specified target.

**Usage:** `/memory-forensics <target>`

Where `<target>` is the memory dump path — e.g. `/evidence/memdump.raw`, `/evidence/memory.dmp`.

If no target is provided, ask the user for the memory dump location.

## Instructions

1. Load the investigation template: call `get_template(name="memory-forensics", target="$ARGUMENTS")`
2. Follow all 6 phases: Evidence Handling, Process Analysis, Network Analysis, Persistence & Artifacts, Malware Detection, Reporting
3. Use these MCP servers: kali-forensics (Volatility3, YARA, bulk_extractor), threat-intel, filesystem
4. Scan for injected processes and hidden modules
5. Log chain of custody before accessing the memory dump
6. Generate report with process tree, network connections, and IoCs
