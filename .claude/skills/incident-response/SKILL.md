---
name: incident-response
description: Run a 7-phase incident response — triage, containment assessment, evidence collection, attack chain reconstruction, threat intel, impact assessment, and reporting.
---

Execute the incident response workflow for the specified target.

**Usage:** `/incident-response <target>`

Where `<target>` is the affected system, evidence path, or incident description — e.g. `/evidence/compromised-host/`, `192.168.1.50`.

If no target is provided, ask the user to describe the incident.

## Instructions

1. Load the investigation template: call `get_template(name="incident-response", target="$ARGUMENTS")`
2. Follow all 7 phases: Triage, Containment Assessment, Evidence Collection, Attack Chain Reconstruction, Threat Intelligence, Impact Assessment, Reporting
3. Use all relevant MCP servers based on the incident type
4. Prioritize containment recommendations
5. Log chain of custody for every evidence access
6. Generate report with timeline, MITRE ATT&CK mapping, and remediation plan
