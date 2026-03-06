# Binary Analysis MCP Server

Malware and binary analysis combining Ghidra headless, Radare2, Capa, YARA, pefile, and lief.

## Tools

| Tool | Description |
|------|-------------|
| `static_analyze` | File type, hashes, PE/ELF headers, packed detection |
| `strings_extract` | String extraction (ASCII + Unicode) |
| `ghidra_decompile` | Ghidra headless decompilation |
| `radare2_analyze` | r2 analysis (functions, xrefs, disassembly) |
| `capa_detect` | MITRE ATT&CK capability detection |
| `yara_match` | YARA rule matching |
| `entropy_analysis` | Section entropy for packer/encryption detection |
| `import_export_table` | Parse import/export tables |

## Transport

stdio only — connect via `docker exec -i dfireballz-binary-analysis-1 python3 -m server`
