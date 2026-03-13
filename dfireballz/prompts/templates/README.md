# Investigation Templates

These templates provide structured workflows for different forensic investigation types.
Each template instructs the AI to use the available MCP servers and their tools, and aggregate
results into a `ForensicPayload` for report generation.

Every template includes:
- **MCP server usage instructions** — explicit directions to use the MCP containers and their tools
- **Host directory layout** — where to read evidence and store output (`/cases/`, `/evidence/`, `/reports/`, `/workspace/output/`)
- **Documentation & logging requirements** — process logs, issues/errors logs, and incremental findings

## Available Templates

| Template | Use Case |
|----------|----------|
| `complete-investigation` | **All-in-one**: full investigation + response across every domain |
| `full-investigation` | End-to-end forensic investigation |
| `malware-analysis` | Static + dynamic malware analysis |
| `ransomware-investigation` | Ransomware incident response |
| `phishing-investigation` | Phishing email/site analysis |
| `network-forensics` | PCAP and network traffic analysis |
| `osint-person` | Person/username investigation |
| `osint-domain` | Domain/infrastructure investigation |
| `memory-forensics` | Memory dump analysis |
| `incident-response` | Full incident response workflow |

## Usage

Via MCP: `list_templates` then `get_template(name="malware-analysis", target="/evidence/sample.exe")`

Via CLI: `dfireballz templates show malware-analysis --target /evidence/sample.exe`
