"""Pydantic model for an AI tool-invocation audit event.

Field semantics intentionally mirror the ``ai_tool_invocations`` table
in ``database/init.sql`` so a model instance maps 1:1 to a DB row.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AIInvocation(BaseModel):
    """One AI-driven MCP tool execution.

    Required fields are the minimum needed to attribute the call:
    actor, server, tool, started_at. Everything else is optional so
    partial records (e.g. emitted before completion) still validate.
    """

    # Attribution
    ai_actor: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="AI host identifier, e.g. 'claude-code', 'mcphost/qwen3:8b'",
    )
    mcp_server: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="MCP server name, e.g. 'kali-forensics'",
    )
    tool_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="MCP tool name, e.g. 'volatility_run'",
    )

    # Correlation (optional — populated when the AI host knows the case)
    case_id: str | None = None
    evidence_id: str | None = None
    session_id: str | None = Field(default=None, max_length=100)

    # Call detail
    tool_args: dict[str, Any] = Field(default_factory=dict)
    input_sha256: str | None = Field(default=None, max_length=64)
    output_sha256: str | None = Field(default=None, max_length=64)

    # Result
    exit_code: int | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    stdout_preview: str | None = None
    stderr_preview: str | None = None
    error: str | None = None

    # Timestamps (UTC ISO 8601)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None

    def to_jsonl_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict suitable for one JSONL line."""
        return self.model_dump(mode="json")
