---
name: phishing-investigation
description: Investigate a phishing campaign — email header analysis, URL/domain investigation, attachment analysis, credential harvesting checks, and threat intel.
---

Investigate the phishing incident involving the specified target.

**Usage:** `/phishing-investigation <target>`

Where `<target>` is the phishing email, URL, or evidence path — e.g. `/evidence/phish-email.eml`, `suspicious-login.example.com`.

If no target is provided, ask the user for the phishing evidence.

## Instructions

1. Load the investigation template: call `get_template(name="phishing-investigation", target="$ARGUMENTS")`
2. Follow all 6 phases: Email Analysis, URL/Domain Investigation, Attachment Analysis, Credential Harvesting Check, Threat Intelligence, Reporting
3. Use these MCP servers: osint, threat-intel, kali-forensics, binary-analysis, filesystem
4. Check URLs against URLScan and VirusTotal
5. Log chain of custody for every evidence access
6. Generate report with IoC table and takedown recommendations
