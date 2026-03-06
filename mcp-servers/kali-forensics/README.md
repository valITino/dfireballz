# Kali Forensics MCP Server

Core forensic tooling based on Kali Linux with Volatility3, bulk_extractor, tshark, YARA, dc3dd, Sleuthkit, foremost, binwalk, and exiftool.

## Tools

| Tool | Description |
|------|-------------|
| `volatility_run` | Run Volatility3 plugins against memory images |
| `tshark_analyze` | PCAP analysis with display filters |
| `bulk_extract` | Extract artifacts from disk/memory images |
| `foremost_recover` | File carving from disk images |
| `binwalk_scan` | Firmware/binary scanning |
| `exiftool_read` | Metadata extraction |
| `yara_scan` | YARA rule scanning |
| `dc3dd_hash` | Forensic hashing for chain of custody |
| `sleuthkit_analyze` | TSK disk forensics commands |

## Transport

stdio only — connect via `docker exec -i dfireballz-kali-forensics-1 python3 -m server`
