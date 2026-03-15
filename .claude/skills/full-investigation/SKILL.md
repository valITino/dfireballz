---
name: full-investigation
description: Run a 6-phase forensic investigation — evidence intake, artifact collection, network analysis, threat intel, timeline reconstruction, and reporting.
---

Run the full forensic investigation workflow against the specified target.

**Usage:** `/full-investigation <target>`

Where `<target>` is the evidence path or subject — e.g. `/evidence/case001/`, `/evidence/disk.E01`.

If no target is provided, ask the user what they want to investigate.

## Instructions

1. Load the investigation template: call `get_template(name="full-investigation", target="$ARGUMENTS")`
2. Follow all 6 phases in order
3. Use the MCP servers for every phase — do not skip tool usage
4. Log chain of custody for every evidence access
5. Write findings incrementally to output directories
6. Generate the final report in `/reports/`
