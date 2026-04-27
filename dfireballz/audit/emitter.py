"""Audit emitter — writes AIInvocation records to orchestrator + JSONL.

Design goals
------------
* **Defence in depth** — every emit attempts both an HTTP POST to the
  orchestrator and a JSONL append. Either one alone is sufficient
  evidence; together they survive DB outages, network blips, container
  rebuilds.
* **Never blocks the caller fatally** — audit failure is logged but
  must not crash the forensic tool that triggered it. (Forensic
  output > audit metadata; the JSONL path is the safety net.)
* **Async-safe** — uses httpx AsyncClient for the HTTP path. JSONL
  writes are sync (single line append, atomic on POSIX).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from dfireballz.audit.models import AIInvocation

logger = logging.getLogger("dfireballz.audit")

_JSONL_FILENAME = "ai_invocations.jsonl"
_DEFAULT_HTTP_TIMEOUT = 2.0  # seconds; audit must not hang tool execution


def _truncate(text: str | None, limit: int = 4096) -> str | None:
    """Cap a string at ``limit`` bytes (UTF-8) and mark truncation."""
    if text is None:
        return None
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    suffix = b"...[truncated]"
    return (encoded[: limit - len(suffix)] + suffix).decode("utf-8", errors="replace")


def hash_canonical_json(value: Any) -> str:
    """SHA-256 of ``value`` rendered as canonical JSON.

    Sort keys + no whitespace ⇒ identical inputs always hash to the
    same value, regardless of insertion order or pretty-printing.
    """
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_text(text: str) -> str:
    """SHA-256 of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


class AuditEmitter:
    """Emit AIInvocation events to orchestrator + JSONL.

    Thread- and asyncio-safe. The JSONL append uses a process-local
    lock; the HTTP client is constructed lazily and reused.
    """

    def __init__(
        self,
        orchestrator_url: str | None = None,
        jsonl_path: Path | None = None,
        http_timeout: float = _DEFAULT_HTTP_TIMEOUT,
    ) -> None:
        self.orchestrator_url = (
            orchestrator_url
            or os.environ.get("DFIR_ORCHESTRATOR_URL")
            or "http://orchestrator:8800"
        )
        self.jsonl_path = jsonl_path or self._default_jsonl_path()
        self.http_timeout = http_timeout
        self._client: httpx.AsyncClient | None = None
        self._jsonl_lock = threading.Lock()

    @staticmethod
    def _default_jsonl_path() -> Path:
        """Default JSONL location: /workspace/output/logs (in containers)
        or ./output/logs (on host)."""
        candidates = [Path("/workspace/output/logs"), Path("/output/logs")]
        for c in candidates:
            if c.parent.exists():
                return c / _JSONL_FILENAME
        # Final fallback: cwd-relative
        return Path("output/logs") / _JSONL_FILENAME

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.http_timeout)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # JSONL — synchronous append (atomic per line on POSIX)
    # ------------------------------------------------------------------
    def _write_jsonl(self, invocation: AIInvocation) -> bool:
        try:
            self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(invocation.to_jsonl_dict(), default=str) + "\n"
            with self._jsonl_lock, open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(line)
            return True
        except OSError as exc:
            logger.warning("Audit JSONL write failed (%s): %s", self.jsonl_path, exc)
            return False

    # ------------------------------------------------------------------
    # Orchestrator HTTP — async POST
    # ------------------------------------------------------------------
    async def _post_orchestrator(self, invocation: AIInvocation) -> bool:
        url = f"{self.orchestrator_url.rstrip('/')}/audit/ai-invocation"
        try:
            client = await self._get_client()
            resp = await client.post(url, json=invocation.to_jsonl_dict())
            if resp.status_code >= 400:
                logger.warning(
                    "Audit POST returned %d: %s", resp.status_code, resp.text[:200]
                )
                return False
            return True
        except (httpx.HTTPError, OSError) as exc:
            # Network / orchestrator unreachable — JSONL still records it.
            logger.debug("Audit POST failed (%s): %s", url, exc)
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def emit(self, invocation: AIInvocation) -> dict[str, bool]:
        """Persist an AIInvocation to both stores.

        Returns a dict with keys ``jsonl`` and ``orchestrator`` — each
        True iff that sink accepted the record. Callers may inspect
        this for monitoring; failure of one path is non-fatal as long
        as the other succeeded.
        """
        # JSONL first: cheap, local, the safety net.
        jsonl_ok = self._write_jsonl(invocation)
        orchestrator_ok = await self._post_orchestrator(invocation)
        if not jsonl_ok and not orchestrator_ok:
            logger.error(
                "Audit record for %s/%s lost — both JSONL and orchestrator failed",
                invocation.mcp_server,
                invocation.tool_name,
            )
        return {"jsonl": jsonl_ok, "orchestrator": orchestrator_ok}

    def emit_sync(self, invocation: AIInvocation) -> dict[str, bool]:
        """Synchronous variant for sync code paths.

        Runs the HTTP coroutine in a fresh event loop. Use ``emit`` from
        async code instead — this is meant for ``subprocess.run``-driven
        tools where the surrounding code is sync.
        """
        # JSONL is already sync.
        jsonl_ok = self._write_jsonl(invocation)
        orchestrator_ok = False
        try:
            with httpx.Client(timeout=self.http_timeout) as client:
                url = f"{self.orchestrator_url.rstrip('/')}/audit/ai-invocation"
                resp = client.post(url, json=invocation.to_jsonl_dict())
                orchestrator_ok = resp.status_code < 400
                if not orchestrator_ok:
                    logger.warning(
                        "Audit POST returned %d: %s",
                        resp.status_code,
                        resp.text[:200],
                    )
        except (httpx.HTTPError, OSError) as exc:
            logger.debug("Audit POST failed: %s", exc)
        if not jsonl_ok and not orchestrator_ok:
            logger.error(
                "Audit record for %s/%s lost — both sinks failed",
                invocation.mcp_server,
                invocation.tool_name,
            )
        return {"jsonl": jsonl_ok, "orchestrator": orchestrator_ok}


# ----------------------------------------------------------------------
# Singleton accessor — most call sites just want a shared emitter
# ----------------------------------------------------------------------
_emitter: AuditEmitter | None = None
_emitter_lock = threading.Lock()


def get_emitter() -> AuditEmitter:
    """Return the process-wide emitter, creating it on first use."""
    global _emitter
    with _emitter_lock:
        if _emitter is None:
            _emitter = AuditEmitter()
        return _emitter


def reset_emitter() -> None:
    """Test helper: drop the cached emitter."""
    global _emitter
    with _emitter_lock:
        _emitter = None


# Convenience: build an invocation with started/finished + previews
def build_invocation(
    *,
    ai_actor: str,
    mcp_server: str,
    tool_name: str,
    tool_args: dict[str, Any],
    started_at: datetime,
    finished_at: datetime | None = None,
    exit_code: int | None = None,
    stdout: str | None = None,
    stderr: str | None = None,
    error: str | None = None,
    case_id: str | None = None,
    evidence_id: str | None = None,
    session_id: str | None = None,
) -> AIInvocation:
    """Construct an AIInvocation, computing hashes/previews/duration."""
    duration_ms: int | None = None
    if finished_at is not None:
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)

    output_full = ""
    if stdout is not None:
        output_full += stdout
    if stderr:
        output_full += stderr

    return AIInvocation(
        ai_actor=ai_actor,
        mcp_server=mcp_server,
        tool_name=tool_name,
        tool_args=tool_args,
        case_id=case_id,
        evidence_id=evidence_id,
        session_id=session_id,
        input_sha256=hash_canonical_json(tool_args),
        output_sha256=hash_text(output_full) if output_full else None,
        exit_code=exit_code,
        duration_ms=duration_ms,
        stdout_preview=_truncate(stdout),
        stderr_preview=_truncate(stderr),
        error=_truncate(error, limit=2048),
        started_at=started_at,
        finished_at=finished_at,
    )


__all__ = [
    "AuditEmitter",
    "build_invocation",
    "get_emitter",
    "hash_canonical_json",
    "hash_text",
    "reset_emitter",
]
