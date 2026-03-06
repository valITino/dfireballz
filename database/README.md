# DFIReballz Database

PostgreSQL 16 with pgcrypto extension for encrypted API key storage.

## Schema

- **cases** — Investigation cases with metadata
- **evidence** — Evidence files with forensic hashes
- **chain_of_custody_log** — Immutable audit log (UPDATE/DELETE blocked by trigger)
- **iocs** — Indicators of Compromise with enrichment data
- **findings** — Investigation findings with MITRE ATT&CK mapping
- **playbook_runs** — Playbook execution log
- **api_keys** — Encrypted API key storage

## Chain of Custody Immutability

The `chain_of_custody_log` table has database-level triggers that prevent any UPDATE or DELETE operations. This ensures forensic integrity of the audit trail.
