# WinForensics MCP Server

Windows artifact parsing from Linux — built from [x746b/winforensics-mcp](https://github.com/x746b/winforensics-mcp).

## Capabilities

- MFT parsing and timestomping detection ($SI vs $FN analysis)
- USN Journal analysis
- ShellBags, LNK files, Prefetch, UserAssist
- Amcache and SRUM (System Resource Usage Monitor)
- Registry hive parsing (SAM, SYSTEM, SOFTWARE, SECURITY, NTUSER.DAT)
- Windows Event Log (EVTX) analysis with pre-built security queries
- Browser artifacts (Chrome, Firefox, Edge)
- `hunt_ioc` meta-tool — searches across all artifact types
- Eric Zimmerman CSV import
- Remote collection via WinRM
- Chainsaw for fast Sigma-based EVTX hunting
- Optional VirusTotal integration

## Transport

stdio only — connect via `docker exec -i dfireballz-winforensics-1 uv run python -m winforensics_mcp.server`
