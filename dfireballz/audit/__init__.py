"""AI tool-invocation audit logging.

Every MCP tool call made on behalf of an AI host (Claude Code, ChatGPT
via mcpo, MCPHost+Ollama, …) is captured here so reviewers can verify
after the fact exactly what the AI did:

    - which AI actor initiated the call
    - which MCP server / tool ran, with what arguments
    - SHA-256 of the canonicalised input and the full output
    - exit code, duration, stdout/stderr previews
    - timestamps (started_at, finished_at) in UTC

Records are persisted in two places (defence in depth):

    1. PostgreSQL ``ai_tool_invocations`` table via the orchestrator
       (immutable: UPDATE/DELETE blocked by trigger).
    2. Append-only JSONL at ``output/logs/ai_invocations.jsonl`` — host
       visible, survives DB / network outage.

Both writes happen on every emit; either alone is sufficient to
reconstruct the audit trail.
"""

from __future__ import annotations

from dfireballz.audit.emitter import AuditEmitter, get_emitter
from dfireballz.audit.models import AIInvocation

__all__ = ["AIInvocation", "AuditEmitter", "get_emitter"]
