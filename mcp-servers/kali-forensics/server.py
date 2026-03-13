"""Kali Forensics MCP Server — Core forensic tooling."""

import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP(
    "kali-forensics",
    instructions=(
        "Kali Linux forensics: Volatility3, bulk_extractor, tshark, "
        "YARA, dc3dd, Sleuthkit, foremost, binwalk, exiftool"
    ),
)

EVIDENCE_DIR = Path("/evidence")
CASES_DIR = Path("/cases")
REPORTS_DIR = Path("/reports")


def _run(args: list[str], timeout: int = 300) -> dict:
    """Run a subprocess safely (never shell=True)."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
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
    except OSError as e:
        return {"error": f"OS error running {args[0]}: {e}", "returncode": -1}


def _validate_path(path: str, allowed_dirs: list[Path] | None = None) -> Path:
    """Validate and resolve file path to prevent path traversal."""
    resolved = Path(path).resolve()
    if allowed_dirs is None:
        allowed_dirs = [EVIDENCE_DIR, CASES_DIR]
    for d in allowed_dirs:
        d_resolved = d.resolve()
        if resolved == d_resolved or str(resolved).startswith(str(d_resolved) + "/"):
            return resolved
    raise ValueError(f"Path {path} is outside allowed directories")


@mcp.tool()
def volatility_run(image_path: str, plugin: str, args: str | None = None) -> dict:
    """Run a Volatility3 plugin against a memory image.

    Args:
        image_path: Path to memory dump (e.g., /evidence/memory.raw)
        plugin: Volatility3 plugin name (e.g., windows.pslist.PsList, linux.bash.Bash)
        args: Additional plugin arguments
    """
    path = _validate_path(image_path)
    cmd = ["vol", "-f", str(path), plugin]
    if args:
        cmd.extend(args.split())
    return _run(cmd, timeout=600)


@mcp.tool()
def tshark_analyze(pcap_path: str, filter: str | None = None, output_format: str = "json") -> dict:
    """Analyze PCAP file with tshark display filters.

    Args:
        pcap_path: Path to PCAP file
        filter: Wireshark display filter (e.g., 'http.request', 'dns', 'tcp.port==443')
        output_format: Output format (json, text, fields)
    """
    path = _validate_path(pcap_path)
    cmd = ["tshark", "-r", str(path)]
    if filter:
        cmd.extend(["-Y", filter])
    if output_format == "json":
        cmd.extend(["-T", "json"])
    result = _run(cmd)
    if output_format == "json" and result.get("stdout"):
        try:
            result["parsed"] = json.loads(result["stdout"])
        except json.JSONDecodeError:
            pass
    return result


@mcp.tool()
def bulk_extract(image_path: str, output_dir: str) -> dict:
    """Extract artifacts from a disk/memory image using bulk_extractor.

    Args:
        image_path: Path to disk or memory image
        output_dir: Output directory for extracted artifacts
    """
    path = _validate_path(image_path)
    out = _validate_path(output_dir, [CASES_DIR, REPORTS_DIR])
    return _run(["bulk_extractor", "-o", str(out), str(path)], timeout=1800)


@mcp.tool()
def foremost_recover(image_path: str, types: str | None = None) -> dict:
    """Recover/carve files from a disk image using foremost.

    Args:
        image_path: Path to disk image
        types: Comma-separated file types to carve (e.g., 'jpg,png,pdf,doc')
    """
    path = _validate_path(image_path)
    cmd = ["foremost", "-i", str(path)]
    if types:
        cmd.extend(["-t", types])
    return _run(cmd, timeout=1800)


@mcp.tool()
def binwalk_scan(file_path: str, extract: bool = False) -> dict:
    """Scan a file for embedded files/firmware signatures using binwalk.

    Args:
        file_path: Path to file to scan
        extract: If True, extract discovered files
    """
    path = _validate_path(file_path)
    cmd = ["binwalk", str(path)]
    if extract:
        cmd.insert(1, "-e")
    return _run(cmd)


@mcp.tool()
def exiftool_read(file_path: str) -> dict:
    """Extract metadata from a file using exiftool.

    Args:
        file_path: Path to file
    """
    path = _validate_path(file_path)
    result = _run(["exiftool", "-json", str(path)])
    if result.get("stdout"):
        try:
            result["parsed"] = json.loads(result["stdout"])
        except json.JSONDecodeError:
            pass
    return result


@mcp.tool()
def yara_scan(target_path: str, rules_path: str) -> dict:
    """Scan a file or directory with YARA rules.

    Args:
        target_path: Path to file or directory to scan
        rules_path: Path to YARA rules file
    """
    target = _validate_path(target_path)
    rules = _validate_path(rules_path)
    return _run(["yara", "-r", str(rules), str(target)])


@mcp.tool()
def dc3dd_hash(file_path: str, algorithm: str = "sha256") -> dict:
    """Compute forensic hash of a file for chain of custody verification.

    Args:
        file_path: Path to file to hash
        algorithm: Hash algorithm (sha256, md5, sha1)
    """
    path = _validate_path(file_path)
    algo_map = {"sha256": hashlib.sha256, "md5": hashlib.md5, "sha1": hashlib.sha1}
    if algorithm not in algo_map:
        return {"error": f"Unsupported algorithm: {algorithm}"}

    h = algo_map[algorithm]()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)

    file_size = os.path.getsize(path)
    return {
        "file": str(path),
        "algorithm": algorithm,
        "hash": h.hexdigest(),
        "size_bytes": file_size,
    }


@mcp.tool()
def sleuthkit_analyze(image_path: str, command: str, args: str | None = None) -> dict:
    """Run Sleuthkit (TSK) commands for disk forensics.

    Args:
        image_path: Path to disk image
        command: TSK command (fls, icat, mmls, fsstat, blkstat, tsk_recover)
        args: Additional command arguments
    """
    path = _validate_path(image_path)
    allowed_commands = ["fls", "icat", "mmls", "fsstat", "blkstat", "tsk_recover", "img_stat"]
    if command not in allowed_commands:
        return {"error": f"Command must be one of: {allowed_commands}"}
    cmd = [command, str(path)]
    if args:
        cmd.extend(args.split())
    return _run(cmd)


@mcp.tool()
def extract_archive(archive_path: str, output_dir: str) -> dict:
    """Extract a ZIP archive to a writable directory.

    Args:
        archive_path: Path to the ZIP file (e.g., /evidence/artifacts.zip)
        output_dir: Destination directory under /cases (e.g., /cases/case-1/artifacts)
    """
    src = _validate_path(archive_path, [EVIDENCE_DIR, CASES_DIR])
    dst = _validate_path(output_dir, [CASES_DIR])

    if not src.exists():
        return {"error": f"Archive not found: {src}"}
    if not zipfile.is_zipfile(src):
        return {"error": f"Not a valid ZIP file: {src}"}

    dst.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(src, "r") as zf:
        bad = [n for n in zf.namelist() if n.startswith("/") or ".." in n]
        if bad:
            return {"error": f"Archive contains unsafe paths: {bad}"}
        zf.extractall(dst)
        extracted = zf.namelist()

    return {
        "archive": str(src),
        "output_dir": str(dst),
        "files_extracted": len(extracted),
        "listing": extracted[:200],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
