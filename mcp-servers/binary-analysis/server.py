"""Binary Analysis MCP Server — Ghidra, Radare2, Capa, YARA, pefile, entropy analysis."""

import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP(
    "binary-analysis",
    instructions="Binary/malware: Ghidra headless, Radare2, Capa, YARA, pefile, entropy analysis",
)

EVIDENCE_DIR = Path("/evidence")
CASES_DIR = Path("/cases")
REPORTS_DIR = Path("/reports")
OUTPUT_DIR = Path("/output")


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
    except OSError as e:
        return {"error": f"OS error running {args[0]}: {e}", "returncode": -1}


def _validate_path(path: str) -> Path:
    """Validate file path."""
    resolved = Path(path).resolve()
    for d in [EVIDENCE_DIR, CASES_DIR, REPORTS_DIR, OUTPUT_DIR]:
        d_resolved = d.resolve()
        if resolved == d_resolved or str(resolved).startswith(str(d_resolved) + "/"):
            return resolved
    raise ValueError(f"Path {path} is outside allowed directories")


@mcp.tool()
def static_analyze(file_path: str) -> dict:
    """Perform static analysis: file type, hashes, PE/ELF headers, packed detection.

    Args:
        file_path: Path to binary file
    """
    path = _validate_path(file_path)
    results: dict = {}

    # File type
    file_result = _run(["file", "-b", str(path)])
    results["file_type"] = file_result.get("stdout", "").strip()

    # Hashes
    with open(path, "rb") as f:
        data = f.read()
    results["size_bytes"] = len(data)
    results["md5"] = hashlib.md5(data, usedforsecurity=False).hexdigest()
    results["sha1"] = hashlib.sha1(data, usedforsecurity=False).hexdigest()
    results["sha256"] = hashlib.sha256(data).hexdigest()

    # PE analysis
    try:
        import pefile
        pe = pefile.PE(str(path))
        results["pe"] = {
            "machine": hex(pe.FILE_HEADER.Machine),
            "timestamp": pe.FILE_HEADER.TimeDateStamp,
            "sections": [
                {
                    "name": s.Name.decode("utf-8", errors="replace").strip("\x00"),
                    "virtual_size": s.Misc_VirtualSize,
                    "raw_size": s.SizeOfRawData,
                    "entropy": s.get_entropy(),
                }
                for s in pe.sections
            ],
            "imports": [
                e.dll.decode("utf-8", errors="replace")
                for e in (
                    pe.DIRECTORY_ENTRY_IMPORT
                    if hasattr(pe, "DIRECTORY_ENTRY_IMPORT")
                    else []
                )
            ],
            "is_dll": pe.is_dll(),
            "is_exe": pe.is_exe(),
        }
        # Packer detection heuristic
        high_entropy_sections = [s for s in pe.sections if s.get_entropy() > 7.0]
        results["packed_likely"] = len(high_entropy_sections) > 0
        pe.close()
    except Exception:
        results["pe"] = None

    # ELF analysis
    try:
        import lief
        binary = lief.parse(str(path))
        if binary and binary.format == lief.EXE_FORMATS.ELF:
            results["elf"] = {
                "type": str(binary.header.file_type),
                "machine": str(binary.header.machine_type),
                "sections": [
                    {"name": s.name, "size": s.size, "entropy": s.entropy}
                    for s in binary.sections
                ],
            }
    except Exception:
        pass

    return results


@mcp.tool()
def strings_extract(file_path: str, min_length: int = 4, encoding: str = "both") -> dict:
    """Extract strings from a binary file.

    Args:
        file_path: Path to binary file
        min_length: Minimum string length (1-100)
        encoding: Encoding to search (ascii, unicode, both)
    """
    allowed_encodings = ("ascii", "unicode", "both")
    if encoding not in allowed_encodings:
        return {"error": f"encoding must be one of: {allowed_encodings}"}
    min_length = max(1, min(min_length, 100))
    path = _validate_path(file_path)
    results = {}

    if encoding in ("ascii", "both"):
        result = _run(["strings", f"-n{min_length}", str(path)])
        results["ascii"] = result.get("stdout", "").split("\n")[:1000]

    if encoding in ("unicode", "both"):
        result = _run(["strings", f"-n{min_length}", "-el", str(path)])
        results["unicode"] = result.get("stdout", "").split("\n")[:1000]

    # Count total
    total = len(results.get("ascii", [])) + len(results.get("unicode", []))
    results["total_strings"] = total

    return results


@mcp.tool()
def ghidra_decompile(binary_path: str, function_name_or_offset: str | None = None) -> dict:
    """Decompile a binary using Ghidra headless analyzer.

    Args:
        binary_path: Path to binary file
        function_name_or_offset: Specific function name or address offset to decompile
    """
    path = _validate_path(binary_path)
    project_dir = tempfile.mkdtemp(prefix="ghidra-projects-")
    project_name = f"analysis_{path.stem}"

    try:
        cmd = [
            "/opt/ghidra/support/analyzeHeadless",
            project_dir,
            project_name,
            "-import", str(path),
            "-overwrite",
            "-scriptPath", "/opt/ghidra/Ghidra/Features/Decompiler/ghidra_scripts",
        ]

        result = _run(cmd, timeout=600)
        return {
            "analysis_output": result.get("stdout", ""),
            "errors": result.get("stderr", ""),
            "function": function_name_or_offset,
        }
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


@mcp.tool()
def radare2_analyze(binary_path: str, command: str = "aaa;afl") -> dict:
    """Analyze a binary with Radare2.

    Args:
        binary_path: Path to binary file
        command: r2 command sequence (e.g., 'aaa;afl' for full analysis + function list)
    """
    # Block shell escape commands — r2pipe '!' prefix executes shell commands
    for cmd_part in command.split(";"):
        cmd_part = cmd_part.strip()
        if cmd_part.startswith("!") or cmd_part.startswith("#!"):
            return {"error": "Shell commands (! prefix) are not allowed in r2 commands"}
    path = _validate_path(binary_path)
    try:
        import r2pipe
        r2 = r2pipe.open(str(path), flags=["-2"])
        output = r2.cmd(command)
        r2.quit()
        return {"output": output, "command": command}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def capa_detect(binary_path: str) -> dict:
    """Detect malware capabilities mapped to MITRE ATT&CK using Capa.

    Args:
        binary_path: Path to binary file
    """
    path = _validate_path(binary_path)
    result = _run(["capa", "--json", str(path)], timeout=300)
    if result.get("stdout"):
        try:
            result["parsed"] = json.loads(result["stdout"])
        except json.JSONDecodeError:
            pass
    return result


@mcp.tool()
def yara_match(binary_path: str, rule_set: str = "community") -> dict:
    """Match a binary against YARA rules.

    Args:
        binary_path: Path to binary file
        rule_set: Rule set to use (community, custom, or path to .yar file)
    """
    path = _validate_path(binary_path)
    rules_dir = Path("/app/yara-rules")

    if rule_set == "community":
        rules_path = str(rules_dir / "index.yar")
    elif rule_set == "custom":
        rules_path = str(rules_dir / "custom.yar")
    else:
        # Validate custom rule paths against allowed directories
        rules_path = str(_validate_path(rule_set))

    try:
        import yara
        rules = yara.compile(filepath=rules_path)
        matches = rules.match(str(path))
        return {
            "matches": [
                {
                    "rule": m.rule,
                    "namespace": m.namespace,
                    "tags": m.tags,
                    "meta": m.meta,
                }
                for m in matches
            ],
            "total_matches": len(matches),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def entropy_analysis(file_path: str) -> dict:
    """Analyze file entropy to detect packed/encrypted sections.

    Args:
        file_path: Path to binary file
    """
    path = _validate_path(file_path)

    with open(path, "rb") as f:
        data = f.read()

    # Overall entropy
    def calc_entropy(data_bytes: bytes) -> float:
        if not data_bytes:
            return 0.0
        counter = Counter(data_bytes)
        length = len(data_bytes)
        entropy = 0.0
        for count in counter.values():
            p = count / length
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy

    overall = calc_entropy(data)

    # Block entropy (1KB blocks)
    block_size = 1024
    blocks = []
    for i in range(0, len(data), block_size):
        block = data[i:i + block_size]
        blocks.append({"offset": i, "entropy": round(calc_entropy(block), 4)})

    return {
        "overall_entropy": round(overall, 4),
        "max_entropy": 8.0,
        "packed_likely": overall > 7.0,
        "encrypted_likely": overall > 7.5,
        "block_count": len(blocks),
        "high_entropy_blocks": sum(1 for b in blocks if b["entropy"] > 7.0),
        "blocks_sample": blocks[:50],
    }


@mcp.tool()
def import_export_table(binary_path: str) -> dict:
    """Parse import and export tables of a PE/ELF binary.

    Args:
        binary_path: Path to binary file
    """
    path = _validate_path(binary_path)
    results: dict = {"imports": [], "exports": []}

    try:
        import pefile
        pe = pefile.PE(str(path))
        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                dll_name = entry.dll.decode("utf-8", errors="replace")
                for imp in entry.imports:
                    func_name = (
                        imp.name.decode("utf-8", errors="replace")
                        if imp.name
                        else f"ordinal_{imp.ordinal}"
                    )
                    results["imports"].append({
                        "dll": dll_name,
                        "function": func_name,
                        "address": hex(imp.address),
                    })

        if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
            for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                func_name = (
                    exp.name.decode("utf-8", errors="replace")
                    if exp.name
                    else f"ordinal_{exp.ordinal}"
                )
                results["exports"].append({
                    "function": func_name,
                    "ordinal": exp.ordinal,
                    "address": hex(exp.address),
                })

        pe.close()
    except Exception as e:
        results["error"] = str(e)

    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
