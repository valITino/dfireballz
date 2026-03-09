"""Docker exec backend — execute forensic tools in MCP containers via docker exec."""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import Any

from dfireballz.backends.base import ToolBackend, ToolResult

logger = logging.getLogger("dfireballz.backends.docker")

# Maps tool names to their container and command builder.
_TOOL_COMMANDS: dict[str, dict[str, Any]] = {
    # Kali forensics container
    "volatility3": {
        "container": "dfireballz-kali-forensics-1",
        "build": lambda p: ["vol", "-f", p.get("image", ""), p.get("plugin", "windows.info")],
    },
    "bulk_extractor": {
        "container": "dfireballz-kali-forensics-1",
        "build": lambda p: [
            "bulk_extractor", "-o", p.get("output", "/tmp/be_out"),  # nosec B108
            p.get("image", ""),
        ],
    },
    "yara": {
        "container": "dfireballz-kali-forensics-1",
        "build": lambda p: ["yara", p.get("rules", ""), p.get("target", "")],
    },
    "exiftool": {
        "container": "dfireballz-kali-forensics-1",
        "build": lambda p: ["exiftool", p.get("file", "")],
    },
    "foremost": {
        "container": "dfireballz-kali-forensics-1",
        "build": lambda p: [
            "foremost", "-i", p.get("image", ""),
            "-o", p.get("output", "/tmp/foremost_out"),  # nosec B108
        ],
    },
    "sleuthkit": {
        "container": "dfireballz-kali-forensics-1",
        "build": lambda p: [p.get("command", "fls"), *p.get("args", [])],
    },
    # Network forensics container
    "tshark": {
        "container": "dfireballz-network-forensics-1",
        "build": lambda p: ["tshark", "-r", p.get("pcap", ""), *p.get("args", [])],
    },
    "tcpdump": {
        "container": "dfireballz-network-forensics-1",
        "build": lambda p: ["tcpdump", "-r", p.get("pcap", ""), *p.get("args", [])],
    },
    # OSINT container
    "maigret": {
        "container": "dfireballz-osint-1",
        "build": lambda p: ["maigret", p.get("username", "")],
    },
    "sherlock": {
        "container": "dfireballz-osint-1",
        "build": lambda p: ["sherlock", p.get("username", "")],
    },
    "theharvester": {
        "container": "dfireballz-osint-1",
        "build": lambda p: [
            "theHarvester", "-d", p.get("domain", ""),
            "-b", p.get("source", "all"),
        ],
    },
    # Binary analysis container
    "capa": {
        "container": "dfireballz-binary-analysis-1",
        "build": lambda p: ["capa", p.get("file", "")],
    },
    "radare2": {
        "container": "dfireballz-binary-analysis-1",
        "build": lambda p: ["r2", "-q", "-c", p.get("command", "aaa; afl"), p.get("file", "")],
    },
}

_DEFAULT_TIMEOUT = 300


class DockerBackend(ToolBackend):
    """Execute forensic tools in MCP containers via docker exec."""

    name = "docker"

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def health_check(self) -> bool:
        return shutil.which("docker") is not None

    async def run_tool(
        self,
        category: str,
        tool: str,
        params: dict[str, Any] | None = None,
    ) -> ToolResult:
        params = params or {}
        spec = _TOOL_COMMANDS.get(tool)
        if spec is None:
            return ToolResult(
                success=False,
                tool=f"{category}/{tool}",
                category=category,
                output="",
                errors=[f"Tool '{tool}' is not supported by the docker backend"],
            )

        container = spec["container"]
        args = spec["build"](params)
        cmd = ["docker", "exec", container, *args]
        logger.info("Docker exec: %s", " ".join(cmd))

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=params.get("timeout", _DEFAULT_TIMEOUT),
            )
        except TimeoutError:
            return ToolResult(
                success=False,
                tool=f"{category}/{tool}",
                category=category,
                output="",
                errors=[f"Timeout after {_DEFAULT_TIMEOUT}s"],
            )
        except OSError as exc:
            return ToolResult(
                success=False,
                tool=f"{category}/{tool}",
                category=category,
                output="",
                errors=[str(exc)],
            )

        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")
        errors: list[str] = []
        if stderr_text.strip():
            errors.append(stderr_text.strip())

        return ToolResult(
            success=proc.returncode == 0,
            tool=f"{category}/{tool}",
            category=category,
            output=stdout_text,
            errors=errors,
            raw_data={
                "stdout": stdout_text,
                "stderr": stderr_text,
                "returncode": proc.returncode,
                "command": " ".join(cmd),
            },
        )

    async def list_tools(self) -> list[dict[str, str]]:
        available: list[dict[str, str]] = []
        for tool_name, spec in _TOOL_COMMANDS.items():
            available.append({
                "category": "forensics",
                "tool": tool_name,
                "container": spec["container"],
            })
        return available
