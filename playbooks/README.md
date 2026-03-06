# DFIReballz Playbooks

Structured investigation playbooks for digital forensics, incident response, and OSINT operations. Each playbook contains YAML front matter with machine-readable step definitions and a Markdown body with analyst guidance.

## Playbook Index

| Playbook | ID | Description | Estimated Duration |
|---|---|---|---|
| [Malware Sample Analysis](malware-analysis.md) | `pb-malware-analysis` | Complete binary analysis workflow from hash computation through static analysis, capability detection, YARA matching, decompilation, and threat intel enrichment. | 45-90 min |
| [OSINT Person Investigation](osint-person-investigation.md) | `pb-osint-person-investigation` | Person of interest investigation covering username enumeration, email verification, SpiderFoot and theHarvester scanning, and IOC enrichment. | 30-60 min |
| [OSINT Domain Investigation](osint-domain-investigation.md) | `pb-osint-domain-investigation` | Domain infrastructure mapping with WHOIS, subdomain enumeration, typosquatting detection, web fingerprinting, passive DNS, Shodan, and VirusTotal. | 30-60 min |
| [Ransomware Investigation](ransomware-investigation.md) | `pb-ransomware-investigation` | Post-incident ransomware analysis using Volatility memory forensics, file recovery, disk analysis, YARA scanning, network C2 detection, and VT enrichment. | 90-180 min |
| [Phishing Investigation](phishing-investigation.md) | `pb-phishing-investigation` | Phishing email triage covering header analysis, domain reputation, URL redirect chain analysis, WHOIS, abuse IP checks, and HTML artifact extraction. | 20-45 min |
| [Network Forensics](network-forensics.md) | `pb-network-forensics` | PCAP investigation with protocol statistics, DNS extraction, HTTP transaction recovery, TLS analysis, security auditing, and geographic IP resolution. | 30-90 min |
| [Dark Web Trace](dark-web-trace.md) | `pb-dark-web-trace` | Threat actor tracking from an initial IOC through dark web and surface web OSINT pivoting, username correlation, and attribution analysis. | 60-120 min |
| [Mobile Artifact Analysis](mobile-artifact-analysis.md) | `pb-mobile-artifact-analysis` | Mobile device forensics covering SQLite extraction, location history, app usage analysis, contacts, and call log recovery for Android and iOS. | 60-120 min |
| [Chain of Custody](chain-of-custody.md) | `pb-chain-of-custody` | Evidence handling protocol template covering identification, forensic acquisition, hash verification, labeling, transfer documentation, and storage. | 15-30 min/item |

## Playbook Structure

Each playbook file uses the following structure:

### YAML Front Matter

```yaml
---
name: Playbook Name
id: pb-unique-identifier
description: What this playbook does
case_types:
  - applicable-case-type
tools_required:
  - tool-category/tool-name
estimated_duration: time range
tags:
  - relevant-tags
steps:
  - id: step_identifier
    name: Human-Readable Step Name
    tool: tool-category/tool-name
    action: action_to_invoke
    description: What this step does
    inputs:
      key: value
---
```

### Markdown Body

- **Overview** -- Purpose and scope of the playbook
- **Prerequisites** -- Tools, credentials, and access requirements
- **Workflow** -- Ordered summary of investigation steps
- **Decision Points** -- Conditional branching logic for analysts
- **Output Artifacts** -- Expected deliverables from the investigation

## Usage

Playbooks can be executed manually by following the step-by-step workflow, or programmatically by parsing the YAML front matter and invoking the specified tools with the defined inputs. Template variables (e.g., `{{evidence.sample_path}}`) are resolved at runtime from case and evidence metadata.

## Categories

- **Malware Analysis**: `malware-analysis.md`
- **OSINT**: `osint-person-investigation.md`, `osint-domain-investigation.md`
- **Incident Response**: `ransomware-investigation.md`, `phishing-investigation.md`
- **Network Forensics**: `network-forensics.md`
- **Dark Web**: `dark-web-trace.md`
- **Mobile Forensics**: `mobile-artifact-analysis.md`
- **Documentation**: `chain-of-custody.md`
