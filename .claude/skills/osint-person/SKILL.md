---
name: osint-person
description: Investigate a person via OSINT — username/email enumeration with Maigret/Sherlock/Holehe, infrastructure analysis, threat intel correlation, and digital footprint mapping.
---

Conduct an OSINT investigation on the specified person.

**Usage:** `/osint-person <target>`

Where `<target>` is a username, email, or identifier — e.g. `johndoe`, `suspect@example.com`, `@username`.

If no target is provided, ask the user for the username or email.

## Instructions

1. Load the investigation template: call `get_template(name="osint-person", target="$ARGUMENTS")`
2. Follow all 5 phases: Username/Email Enumeration, Domain/Infrastructure, Threat Intelligence, Correlation, Reporting
3. Use these MCP servers: osint (Maigret, Sherlock, Holehe, theHarvester), threat-intel (AbuseIPDB, Shodan, URLScan), filesystem
4. Cross-reference usernames across platforms
5. Map the complete digital footprint
6. Generate report with platform presence map and timeline
