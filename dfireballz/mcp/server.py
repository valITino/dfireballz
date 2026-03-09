"""MCP server for DFIReballz.

Exposes high-level forensic investigation capabilities so that any
MCP-compatible LLM can drive autonomous forensic analysis, aggregate
findings, and generate reports.

DFIReballz MCP provides *forensic workflows*:
  - run_tool           -> execute a forensic tool via docker exec backend
  - list_tools         -> discover available forensic tools across containers
  - aggregate_results  -> validate & store structured ForensicPayload
  - get_payload_schema -> return the ForensicPayload JSON schema
  - generate_report    -> produce HTML/PDF/MD forensic reports
  - list_templates     -> discover available investigation templates
  - get_template       -> retrieve an investigation template
  - log_chain_of_custody -> record a chain of custody entry
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from dfireballz.backends import ToolBackend, get_backend

logger = logging.getLogger("dfireballz.mcp.server")

_server = Server("dfireballz")

# Lazily initialised backend
_backend: ToolBackend | None = None


async def _get_backend() -> ToolBackend:
    global _backend
    if _backend is None:
        _backend = await get_backend()
    return _backend


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

_TOOLS: list[Tool] = [
    Tool(
        name="run_tool",
        description=(
            "Execute a single forensic tool (e.g. volatility3, tshark, yara, capa) "
            "via docker exec in the appropriate MCP container."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Tool category: memory, disk, network, "
                    "malware, windows, osint, threat_intel",
                },
                "tool": {
                    "type": "string",
                    "description": "Tool name: volatility3, tshark, yara, capa, exiftool, etc.",
                },
                "params": {
                    "type": "object",
                    "description": "Tool parameters (varies by tool)",
                },
            },
            "required": ["category", "tool", "params"],
        },
    ),
    Tool(
        name="list_tools",
        description=(
            "List all available forensic tools across all MCP containers. "
            "Shows which tools can be executed and in which container."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="generate_report",
        description=(
            "Generate a professional forensic report from a session. "
            "Reports are saved to an organized folder structure: "
            "reports/reports-DDMMYYYY/report-<case>-DDMMYYYY.<ext>. "
            "Use format 'both' to generate .md and .pdf together. "
            "Reports written to /reports/ are automatically available on the host."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID or path to session JSON file",
                },
                "format": {
                    "type": "string",
                    "enum": ["html", "pdf", "md", "both"],
                    "description": "Report format. Use 'both' for .md + .pdf (default: both)",
                    "default": "both",
                },
            },
            "required": ["session_id"],
        },
    ),
    Tool(
        name="list_templates",
        description=(
            "List all available investigation templates for autonomous forensics. "
            "Templates provide structured workflows for different investigation "
            "types (malware analysis, ransomware, phishing, OSINT, network forensics, etc.)."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="get_template",
        description=(
            "Retrieve an investigation template by name. Returns the full template "
            "content with [TARGET] placeholders replaced if a target is provided. "
            "Each template instructs the AI to use all available MCP servers "
            "and aggregate results into a ForensicPayload."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Template name: full-investigation, malware-analysis, "
                        "ransomware-investigation, phishing-investigation, "
                        "network-forensics, osint-person, osint-domain, "
                        "memory-forensics, incident-response"
                    ),
                },
                "target": {
                    "type": "string",
                    "description": "Target to replace [TARGET] placeholders with",
                },
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="aggregate_results",
        description=(
            "Validate and store structured forensic findings produced by the "
            "MCP host (Claude). The MCP host parses raw tool outputs, "
            "deduplicates, correlates, and structures them into a "
            "ForensicPayload — then calls this tool to validate and persist "
            "the payload for report generation. "
            "Use get_payload_schema first to see the expected JSON schema."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "payload": {
                    "type": "object",
                    "description": (
                        "Complete ForensicPayload JSON object. Must include "
                        "session_id, target, and at least one of: findings, "
                        "chain_of_custody, executive_summary, recommendations."
                    ),
                },
            },
            "required": ["payload"],
        },
    ),
    Tool(
        name="get_payload_schema",
        description=(
            "Return the ForensicPayload JSON schema so the MCP host knows "
            "exactly what structure to produce when aggregating raw tool "
            "outputs. Call this before aggregate_results to understand the "
            "expected format."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="log_chain_of_custody",
        description=(
            "Record a chain of custody entry for evidence access. "
            "Every evidence interaction must be logged for legal defensibility."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action performed: access, analyze, copy, export, hash_verify",
                },
                "evidence_id": {
                    "type": "string",
                    "description": "Evidence file path or identifier",
                },
                "description": {
                    "type": "string",
                    "description": "Description of what was done",
                },
                "tool_used": {
                    "type": "string",
                    "description": "Tool used for the action",
                },
            },
            "required": ["action", "evidence_id", "description"],
        },
    ),
]


@_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return _TOOLS


@_server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        result = await _dispatch(name, arguments)
        return [TextContent(type="text", text=result)]
    except Exception as exc:
        logger.exception("MCP tool %s failed", name)
        return [TextContent(type="text", text=f"Error: {exc}")]


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


async def _dispatch(name: str, args: dict[str, Any]) -> str:
    if name == "run_tool":
        return await _do_run_tool(args)
    elif name == "list_tools":
        return await _do_list_tools()
    elif name == "generate_report":
        return await _do_generate_report(args)
    elif name == "list_templates":
        return await _do_list_templates()
    elif name == "get_template":
        return await _do_get_template(args)
    elif name == "aggregate_results":
        return await _do_aggregate_results(args)
    elif name == "get_payload_schema":
        return await _do_get_payload_schema()
    elif name == "log_chain_of_custody":
        return await _do_log_chain_of_custody(args)
    else:
        return f"Unknown tool: {name}"


async def _do_run_tool(args: dict[str, Any]) -> str:
    backend = await _get_backend()
    result = await backend.run_tool(
        category=args["category"],
        tool=args["tool"],
        params=args.get("params"),
    )
    return json.dumps(result.model_dump(), indent=2, default=str)


async def _do_list_tools() -> str:
    backend = await _get_backend()
    tools = await backend.list_tools()
    return json.dumps(
        {"backend": backend.name, "tools": tools},
        indent=2,
    )


async def _do_generate_report(args: dict[str, Any]) -> str:
    import re
    from pathlib import Path

    from dfireballz.config import settings
    from dfireballz.models.base import ForensicSession

    session_id = args["session_id"]
    fmt = args.get("format", "both")

    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", session_id)
    if not safe_id:
        return json.dumps({"error": "Invalid session ID"})

    session_path = Path(session_id)
    if not session_path.exists():
        results_dir = settings.results_dir
        matches = list(results_dir.glob(f"*{safe_id}*"))
        if not matches:
            return json.dumps({"error": f"Session '{safe_id}' not found"})
        session_path = matches[0]

    session_data = ForensicSession.model_validate_json(
        session_path.read_text(encoding="utf-8")
    )

    if fmt == "both":
        from dfireballz.reporting.md_generator import generate_md_report
        from dfireballz.reporting.pdf_generator import generate_pdf_report

        md_out = generate_md_report(session_data)
        pdf_out = generate_pdf_report(session_data)
        return json.dumps({
            "reports": [
                {"path": str(md_out), "format": "md"},
                {"path": str(pdf_out), "format": "pdf"},
            ],
            "host_path_hint": "Reports are available on the host at ./reports/",
        })
    elif fmt == "md":
        from dfireballz.reporting.md_generator import generate_md_report

        out = generate_md_report(session_data)
    elif fmt == "pdf":
        from dfireballz.reporting.pdf_generator import generate_pdf_report

        out = generate_pdf_report(session_data)
    else:
        from dfireballz.reporting.html_generator import generate_html_report

        out = generate_html_report(session_data)

    return json.dumps({
        "report_path": str(out),
        "format": fmt,
        "host_path_hint": "Reports are available on the host at ./reports/",
    })


async def _do_list_templates() -> str:
    from dfireballz.prompts import list_templates

    templates = list_templates()
    return json.dumps({"templates": templates}, indent=2)


async def _do_get_template(args: dict[str, Any]) -> str:
    from dfireballz.prompts import load_template

    name = args["name"]
    target = args.get("target")
    try:
        content = load_template(name, target=target)
        return content
    except (ValueError, FileNotFoundError) as exc:
        return json.dumps({"error": str(exc)})


async def _do_aggregate_results(args: dict[str, Any]) -> str:
    from dfireballz.models.forensic_payload import ForensicPayload

    raw_payload = args["payload"]
    if not isinstance(raw_payload, dict):
        return json.dumps({"error": "payload must be a JSON object"})

    if "session_id" not in raw_payload or "target" not in raw_payload:
        return json.dumps({
            "error": "payload must include 'session_id' and 'target'"
        })

    try:
        payload = ForensicPayload(**raw_payload)
    except Exception as exc:
        return json.dumps({
            "error": f"Payload validation failed: {exc}",
            "hint": "Use get_payload_schema to see the expected format.",
        })

    # Persist as JSON for report generation
    from dfireballz.config import settings

    results_dir = settings.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    session_file = results_dir / f"session-{payload.session_id}.json"
    session_file.write_text(
        json.dumps(payload.to_dict(), indent=2, default=str),
        encoding="utf-8",
    )

    ioc_count = len(payload.findings.iocs)
    artifact_count = len(payload.findings.artifacts)
    malware_count = len(payload.findings.malware_samples)
    return json.dumps({
        "status": "ok",
        "session_id": payload.session_id,
        "session_file": str(session_file),
        "summary": {
            "artifacts": artifact_count,
            "iocs": ioc_count,
            "malware_samples": malware_count,
            "timeline_events": len(payload.findings.timeline_events),
            "network_connections": len(payload.findings.network_connections),
            "risk_level": payload.executive_summary.risk_level,
        },
        "hint": f"Use generate_report with session_id='{session_file}' to create the report.",
        "host_path_hint": "Session file is available on the host at ./results/",
    })


async def _do_get_payload_schema() -> str:
    from dfireballz.models.forensic_payload import ForensicPayload

    schema = ForensicPayload.model_json_schema()
    return json.dumps(schema, indent=2)


async def _do_log_chain_of_custody(args: dict[str, Any]) -> str:
    from datetime import UTC, datetime

    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "action": args["action"],
        "evidence_id": args["evidence_id"],
        "description": args["description"],
        "tool_used": args.get("tool_used", ""),
        "actor": "mcp_host",
    }

    # Append to CoC log file
    from dfireballz.config import settings

    coc_dir = settings.cases_dir
    coc_dir.mkdir(parents=True, exist_ok=True)
    coc_file = coc_dir / "chain_of_custody.jsonl"

    with open(coc_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")

    logger.info("Chain of custody logged: %s on %s", args["action"], args["evidence_id"])
    return json.dumps({"status": "logged", "entry": entry})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def run_server() -> None:
    """Start the DFIReballz MCP server on stdio."""
    logger.info("Starting DFIReballz MCP server")
    async with stdio_server() as (read_stream, write_stream):
        await _server.run(
            read_stream,
            write_stream,
            _server.create_initialization_options(),
        )
