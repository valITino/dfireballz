"""Docker exec backend — execute forensic tools in MCP containers via docker exec."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from datetime import UTC, datetime
from typing import Any

from dfireballz.audit import get_emitter
from dfireballz.audit.emitter import build_invocation
from dfireballz.backends.base import ToolBackend, ToolResult

logger = logging.getLogger("dfireballz.backends.docker")

DOCKER_SOCKET = "/var/run/docker.sock"

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
        # Prefer Docker socket (works inside containers without docker CLI)
        if os.path.exists(DOCKER_SOCKET):
            return True
        # Fall back to checking for docker CLI on PATH
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

        started_at = datetime.now(UTC)
        stdout_text = ""
        stderr_text = ""
        returncode: int | None = None
        run_error: str | None = None

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
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")
            returncode = proc.returncode
        except TimeoutError:
            run_error = f"Timeout after {_DEFAULT_TIMEOUT}s"
        except OSError as exc:
            run_error = str(exc)
        finally:
            await self._emit_audit(
                tool=tool,
                container=container,
                params=params,
                started_at=started_at,
                stdout=stdout_text,
                stderr=stderr_text,
                returncode=returncode,
                error=run_error,
            )

        if run_error is not None:
            return ToolResult(
                success=False,
                tool=f"{category}/{tool}",
                category=category,
                output="",
                errors=[run_error],
            )

        errors: list[str] = []
        if stderr_text.strip():
            errors.append(stderr_text.strip())

        return ToolResult(
            success=returncode == 0,
            tool=f"{category}/{tool}",
            category=category,
            output=stdout_text,
            errors=errors,
            raw_data={
                "stdout": stdout_text,
                "stderr": stderr_text,
                "returncode": returncode,
                "command": " ".join(cmd),
            },
        )

    @staticmethod
    async def _emit_audit(
        *,
        tool: str,
        container: str,
        params: dict[str, Any],
        started_at: datetime,
        stdout: str,
        stderr: str,
        returncode: int | None,
        error: str | None,
    ) -> None:
        """Persist one AI-driven tool execution to the audit log.

        Failure here must not block the caller — the surrounding
        ``finally`` already swallowed the original exception path.
        """
        try:
            invocation = build_invocation(
                ai_actor=os.environ.get("DFIR_AI_ACTOR", "unknown-ai") or "unknown-ai",
                mcp_server=container,
                tool_name=tool,
                tool_args=params,
                started_at=started_at,
                finished_at=datetime.now(UTC),
                exit_code=returncode,
                stdout=stdout or None,
                stderr=stderr or None,
                error=error,
                case_id=os.environ.get("DFIR_CASE_ID") or None,
                session_id=os.environ.get("DFIR_SESSION_ID") or None,
            )
            await get_emitter().emit(invocation)
        except Exception:  # pragma: no cover — final safety net
            logger.exception("Audit emit failed for %s/%s", container, tool)

    async def list_tools(self) -> list[dict[str, str]]:
        available: list[dict[str, str]] = []
        for tool_name, spec in _TOOL_COMMANDS.items():
            available.append({
                "category": "forensics",
                "tool": tool_name,
                "container": spec["container"],
            })
        return available
