"""Network Forensics MCP Server — 18-tool Wireshark/tshark suite + tcpdump capture."""

import os
import subprocess
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP(
    "network-forensics",
    instructions=(
        "Network: 18-tool Wireshark/tshark suite, tcpdump capture, "
        "PCAP split/merge/carve, threat detection"
    ),
)

EVIDENCE_DIR = Path("/evidence")
CASES_DIR = Path("/cases")
REPORTS_DIR = Path("/reports")


def _run(args: list[str], timeout: int = 300) -> dict:
    """Run a subprocess safely."""
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, shell=False
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s", "returncode": -1}
    except FileNotFoundError:
        return {"error": f"Command not found: {args[0]}", "returncode": -1}


def _validate_path(path: str, allowed_dirs: list[Path] | None = None) -> Path:
    """Validate file path."""
    resolved = Path(path).resolve()
    if allowed_dirs is None:
        allowed_dirs = [EVIDENCE_DIR, CASES_DIR, REPORTS_DIR]
    for d in allowed_dirs:
        if str(resolved).startswith(str(d.resolve())):
            return resolved
    raise ValueError(f"Path {path} is outside allowed directories")


@mcp.tool()
def wireshark_system_info(info_type: str = "interfaces") -> dict:
    """Get Wireshark/tshark system information.

    Args:
        info_type: Type of info — interfaces | capabilities | version
    """
    if info_type == "interfaces":
        return _run(["tshark", "-D"])
    elif info_type == "capabilities":
        return _run(["tshark", "-v"])
    elif info_type == "version":
        return _run(["tshark", "--version"])
    return {"error": f"Unknown info_type: {info_type}"}


@mcp.tool()
def wireshark_live_capture(
    interface: str = "any",
    duration: int = 30,
    filter: str | None = None,
    max_packets: int = 1000,
) -> dict:
    """Perform live packet capture with tshark.

    Args:
        interface: Network interface to capture on
        duration: Capture duration in seconds (max 300)
        filter: BPF capture filter
        max_packets: Maximum packets to capture
    """
    duration = min(duration, 300)
    cmd = ["tshark", "-i", interface, "-a", f"duration:{duration}", "-c", str(max_packets)]
    if filter:
        cmd.extend(["-f", filter])
    return _run(cmd, timeout=duration + 30)


@mcp.tool()
def wireshark_analyze_pcap(filepath: str, analysis_type: str = "summary") -> dict:
    """Comprehensive PCAP analysis.

    Args:
        filepath: Path to PCAP file
        analysis_type: Analysis type — summary | protocols | conversations | security
    """
    path = _validate_path(filepath)

    if analysis_type == "summary":
        return _run(["capinfos", str(path)])
    elif analysis_type == "protocols":
        return _run(["tshark", "-r", str(path), "-q", "-z", "io,phs"])
    elif analysis_type == "conversations":
        return _run(["tshark", "-r", str(path), "-q", "-z", "conv,tcp"])
    elif analysis_type == "security":
        # Run multiple security-relevant analyses
        results = {}
        results["cleartext"] = _run([
            "tshark", "-r", str(path), "-Y",
            "http.request or ftp or telnet or smtp",
            "-T", "fields", "-e", "ip.src",
            "-e", "ip.dst", "-e", "frame.protocols",
        ])
        results["dns"] = _run([
            "tshark", "-r", str(path), "-Y", "dns.qry.name",
            "-T", "fields", "-e", "dns.qry.name",
        ])
        results["suspicious_ports"] = _run([
            "tshark", "-r", str(path), "-Y",
            "tcp.port==4444 or tcp.port==1337 "
            "or tcp.port==31337 or tcp.port==8888",
            "-c", "100",
        ])
        return results
    return {"error": f"Unknown analysis_type: {analysis_type}"}


@mcp.tool()
def wireshark_get_protocol_stats(filepath: str) -> dict:
    """Get protocol hierarchy statistics from a PCAP.

    Args:
        filepath: Path to PCAP file
    """
    path = _validate_path(filepath)
    return _run(["tshark", "-r", str(path), "-q", "-z", "io,phs"])


@mcp.tool()
def wireshark_get_conversations(filepath: str, transport: str = "tcp") -> dict:
    """Get conversation flows from a PCAP.

    Args:
        filepath: Path to PCAP file
        transport: Transport type — tcp | udp | ip | ethernet
    """
    path = _validate_path(filepath)
    return _run(["tshark", "-r", str(path), "-q", "-z", f"conv,{transport}"])


@mcp.tool()
def wireshark_follow_stream(
    filepath: str,
    stream_type: str = "tcp",
    stream_index: int = 0,
) -> dict:
    """Reconstruct and follow a stream from a PCAP.

    Args:
        filepath: Path to PCAP file
        stream_type: Stream type — tcp | udp | http
        stream_index: Stream index to follow
    """
    path = _validate_path(filepath)
    follow_arg = f"follow,{stream_type},ascii,{stream_index}"
    return _run(["tshark", "-r", str(path), "-q", "-z", follow_arg])


@mcp.tool()
def wireshark_apply_filter(
    filepath: str,
    display_filter: str,
    output_file: str | None = None,
) -> dict:
    """Filter PCAP with a Wireshark display filter.

    Args:
        filepath: Path to PCAP file
        display_filter: Wireshark display filter expression
        output_file: Optional output file for filtered PCAP
    """
    path = _validate_path(filepath)
    cmd = ["tshark", "-r", str(path), "-Y", display_filter]
    if output_file:
        out = _validate_path(output_file, [CASES_DIR, REPORTS_DIR])
        cmd.extend(["-w", str(out)])
    return _run(cmd)


@mcp.tool()
def wireshark_export_objects(
    filepath: str,
    protocol: str = "http",
    output_dir: str | None = None,
) -> dict:
    """Carve transferred files from PCAP (HTTP/SMB/FTP/DICOM objects).

    Args:
        filepath: Path to PCAP file
        protocol: Protocol to extract objects from — http | smb | ftp | dicom
        output_dir: Output directory for extracted objects
    """
    path = _validate_path(filepath)
    out_dir = output_dir or f"/cases/exported_{path.stem}_{protocol}"
    os.makedirs(out_dir, exist_ok=True)
    return _run(["tshark", "-r", str(path), "--export-objects", f"{protocol},{out_dir}"])


@mcp.tool()
def wireshark_split_pcap(
    filepath: str,
    split_by: str = "packets",
    value: int = 10000,
    output_dir: str | None = None,
) -> dict:
    """Split a PCAP into smaller files.

    Args:
        filepath: Path to PCAP file
        split_by: Split method — packets | filesize | duration
        value: Split value (packets count, KB, or seconds)
        output_dir: Output directory
    """
    path = _validate_path(filepath)
    out = output_dir or f"/cases/split_{path.stem}"
    os.makedirs(out, exist_ok=True)

    split_flags = {
        "packets": ["-c", str(value)],
        "filesize": ["-b", f"filesize:{value}"],
        "duration": ["-b", f"duration:{value}"],
    }
    flags = split_flags.get(split_by, ["-c", str(value)])
    cmd = ["editcap"] + flags + [str(path), f"{out}/split.pcap"]
    return _run(cmd)


@mcp.tool()
def wireshark_merge_pcaps(input_files: list[str], output_file: str) -> dict:
    """Merge multiple PCAP files chronologically.

    Args:
        input_files: List of PCAP file paths to merge
        output_file: Output merged PCAP path
    """
    validated = [str(_validate_path(f)) for f in input_files]
    out = str(_validate_path(output_file, [CASES_DIR, REPORTS_DIR]))
    cmd = ["mergecap", "-w", out] + validated
    return _run(cmd)


@mcp.tool()
def wireshark_security_audit(filepath: str) -> dict:
    """Automated security threat detection in PCAP.

    Args:
        filepath: Path to PCAP file
    """
    path = _validate_path(filepath)
    results = {}

    # Cleartext credentials
    results["cleartext_auth"] = _run([
        "tshark", "-r", str(path), "-Y",
        "http.authorization or ftp.request.command==PASS or smtp.req.parameter",
        "-T", "fields", "-e", "ip.src", "-e", "ip.dst", "-e", "frame.protocols",
    ])

    # Port scans (many SYN, no SYN-ACK)
    results["syn_scan"] = _run([
        "tshark", "-r", str(path), "-Y",
        "tcp.flags.syn==1 && tcp.flags.ack==0",
        "-q", "-z", "conv,tcp",
    ])

    # DNS tunneling heuristics (long query names)
    results["dns_queries"] = _run([
        "tshark", "-r", str(path), "-Y", "dns.qry.name",
        "-T", "fields", "-e", "dns.qry.name", "-e", "dns.qry.type",
    ])

    # Beaconing detection (regular interval connections)
    results["connections_timeline"] = _run([
        "tshark", "-r", str(path), "-Y", "tcp.flags.syn==1",
        "-T", "fields", "-e", "frame.time_relative", "-e", "ip.dst", "-e", "tcp.dstport",
    ])

    # Suspicious user agents
    results["user_agents"] = _run([
        "tshark", "-r", str(path), "-Y", "http.user_agent",
        "-T", "fields", "-e", "http.user_agent",
    ])

    return results


@mcp.tool()
def wireshark_generate_filter(description: str, complexity: str = "basic") -> dict:
    """Generate a Wireshark display filter from a natural language description.

    Args:
        description: Natural language description of what to filter
        complexity: Filter complexity — basic | intermediate | advanced
    """
    filter_map = {
        "http traffic": "http",
        "dns queries": "dns",
        "tls handshakes": "tls.handshake",
        "ssh": "ssh",
        "smtp": "smtp",
        "ftp": "ftp",
        "syn scans": "tcp.flags.syn==1 && tcp.flags.ack==0",
        "cleartext passwords": "http.authorization or ftp.request.command==PASS",
        "dns tunneling": 'dns.qry.name matches "^.{50,}"',
        "c2 beaconing": "tcp.flags.syn==1 && tcp.flags.ack==0",
        "malware callbacks": (
            "http.request && !(http.host matches "
            "\"(google|microsoft|apple|amazon)\")"
        ),
    }

    desc_lower = description.lower()
    for key, filter_str in filter_map.items():
        if key in desc_lower:
            return {
                "filter": filter_str,
                "description": description,
                "note": "Generated from pattern matching",
            }

    return {
        "filter": description,
        "description": description,
        "note": "Could not auto-generate — use raw display filter syntax",
    }


@mcp.tool()
def wireshark_geo_resolve(filepath: str) -> dict:
    """Resolve GeoIP information for external IPs in a PCAP.

    Args:
        filepath: Path to PCAP file
    """
    path = _validate_path(filepath)
    result = _run([
        "tshark", "-r", str(path), "-q", "-z", "endpoints,ip",
    ])
    return result


@mcp.tool()
def wireshark_extract_dns(filepath: str) -> dict:
    """Extract all DNS queries and responses from a PCAP.

    Args:
        filepath: Path to PCAP file
    """
    path = _validate_path(filepath)
    return _run([
        "tshark", "-r", str(path), "-Y", "dns",
        "-T", "fields",
        "-e", "frame.time",
        "-e", "ip.src",
        "-e", "dns.qry.name",
        "-e", "dns.qry.type",
        "-e", "dns.a",
        "-e", "dns.resp.name",
    ])


@mcp.tool()
def wireshark_extract_http(filepath: str) -> dict:
    """Extract HTTP requests, hosts, URIs, and user agents from a PCAP.

    Args:
        filepath: Path to PCAP file
    """
    path = _validate_path(filepath)
    return _run([
        "tshark", "-r", str(path), "-Y", "http.request",
        "-T", "fields",
        "-e", "frame.time",
        "-e", "ip.src",
        "-e", "ip.dst",
        "-e", "http.host",
        "-e", "http.request.uri",
        "-e", "http.request.method",
        "-e", "http.user_agent",
    ])


@mcp.tool()
def wireshark_extract_tls(filepath: str) -> dict:
    """Extract TLS handshake info, JA3 fingerprints, and certificate metadata.

    Args:
        filepath: Path to PCAP file
    """
    path = _validate_path(filepath)
    results = {}

    # TLS handshakes
    results["handshakes"] = _run([
        "tshark", "-r", str(path), "-Y", "tls.handshake",
        "-T", "fields",
        "-e", "ip.src",
        "-e", "ip.dst",
        "-e", "tls.handshake.type",
        "-e", "tls.handshake.version",
        "-e", "tls.handshake.extensions_server_name",
    ])

    # JA3 fingerprints
    results["ja3"] = _run([
        "tshark", "-r", str(path), "-Y", "tls.handshake.type==1",
        "-T", "fields",
        "-e", "ip.src",
        "-e", "tls.handshake.extensions_server_name",
        "-e", "tls.handshake.ja3",
    ])

    return results


@mcp.tool()
def tcpdump_capture(
    interface: str = "any",
    filter: str | None = None,
    duration: int = 30,
    output_file: str = "/evidence/capture.pcap",
) -> dict:
    """Capture packets with tcpdump and save to evidence directory.

    Args:
        interface: Network interface
        filter: BPF filter expression
        duration: Capture duration in seconds (max 300)
        output_file: Output PCAP file path (must be in /evidence)
    """
    duration = min(duration, 300)
    out = _validate_path(output_file, [EVIDENCE_DIR])

    cmd = ["tcpdump", "-i", interface, "-w", str(out), "-G", str(duration), "-W", "1"]
    if filter:
        cmd.extend(filter.split())
    return _run(cmd, timeout=duration + 30)


@mcp.tool()
def pcap_time_slice(filepath: str, start_time: str, end_time: str, output_file: str) -> dict:
    """Extract a time window from a large PCAP file.

    Args:
        filepath: Path to source PCAP file
        start_time: Start time (format: 'YYYY-MM-DD HH:MM:SS')
        end_time: End time (format: 'YYYY-MM-DD HH:MM:SS')
        output_file: Output PCAP path
    """
    path = _validate_path(filepath)
    out = _validate_path(output_file, [CASES_DIR, REPORTS_DIR])
    return _run([
        "editcap", "-A", start_time, "-B", end_time, str(path), str(out),
    ])


if __name__ == "__main__":
    mcp.run(transport="stdio")
