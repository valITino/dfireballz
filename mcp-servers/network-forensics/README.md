# Network Forensics MCP Server

18-tool Wireshark/tshark suite with tcpdump capture, PCAP analysis, and automated threat detection.

## Tools

| Tool | Description |
|------|-------------|
| `wireshark_system_info` | List interfaces, capabilities, version |
| `wireshark_live_capture` | Live tshark capture with BPF filter |
| `wireshark_analyze_pcap` | Comprehensive PCAP analysis |
| `wireshark_get_protocol_stats` | Protocol hierarchy statistics |
| `wireshark_get_conversations` | TCP/UDP conversation flows |
| `wireshark_follow_stream` | Reconstruct TCP/UDP/HTTP streams |
| `wireshark_apply_filter` | Filter PCAP by display filter |
| `wireshark_export_objects` | Carve HTTP/SMB/FTP files from PCAP |
| `wireshark_split_pcap` | Split PCAP by size/time/packets |
| `wireshark_merge_pcaps` | Merge multiple PCAPs chronologically |
| `wireshark_security_audit` | Automated threat detection |
| `wireshark_generate_filter` | Natural language to display filter |
| `wireshark_geo_resolve` | GeoIP resolution of external IPs |
| `wireshark_extract_dns` | Extract DNS queries/responses |
| `wireshark_extract_http` | Extract HTTP hosts, URIs, user agents |
| `wireshark_extract_tls` | TLS handshake info, JA3 fingerprints |
| `tcpdump_capture` | Raw tcpdump capture to evidence |
| `pcap_time_slice` | Extract time window from large PCAP |

## Transport

stdio only — connect via `docker exec -i dfireballz-network-forensics-1 python3 -m server`
