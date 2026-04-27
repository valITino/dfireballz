"""Audit decorator for MCP tool functions — stdlib only.

This file is mounted (read-only) into every in-house MCP server
container so each ``@mcp.tool()`` function can be wrapped with
``@audited(server="…")``.  Every wrapped call emits an audit record
describing exactly what the AI host asked for, how long it took, and
what came back.

Why stdlib only
---------------
The MCP server containers have heterogeneous Python deps (kali-forensics
ships ``fastmcp`` only, threat-intel adds ``requests``, etc.).  Adding a
shared dependency would force coordinated image rebuilds.  ``urllib`` +
``json`` + ``hashlib`` are guaranteed in every Python 3.11+ runtime.

Records go to two places (defence in depth):

1. ``POST {DFIR_ORCHESTRATOR_URL}/audit/ai-invocation`` — DB-backed,
   immutable (PostgreSQL trigger).
2. ``/output/logs/ai_invocations.jsonl`` — append-only JSONL,
   host-visible via the ``./output`` bind mount.

Either alone is sufficient evidence; together they survive DB or
network outage.

Environment
-----------
``DFIR_AI_ACTOR``       — AI host identifier (default ``unknown-ai``)
``DFIR_ORCHESTRATOR_URL`` — orchestrator base URL
                          (default ``http://orchestrator:8800``)
``DFIR_AUDIT_DISABLED`` — if ``1``/``true``, skip audit emission entirely
                          (useful for unit tests that import the server
                          module without a running orchestrator)
``DFIR_AUDIT_JSONL``    — override JSONL path (default
                          ``/output/logs/ai_invocations.jsonl``)
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
import threading
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("dfireballz.mcp.audit")

_HTTP_TIMEOUT = 2.0  # audit must never hang a forensic tool
_PREVIEW_BYTES = 4096
_ERROR_PREVIEW_BYTES = 2048

_jsonl_lock = threading.Lock()


def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in ("1", "true", "yes", "on")


def _audit_disabled() -> bool:
    return _truthy(os.environ.get("DFIR_AUDIT_DISABLED"))


def _ai_actor() -> str:
    return os.environ.get("DFIR_AI_ACTOR", "unknown-ai") or "unknown-ai"


def _orchestrator_url() -> str:
    return os.environ.get("DFIR_ORCHESTRATOR_URL", "http://orchestrator:8800").rstrip("/")


def _jsonl_path() -> Path:
    override = os.environ.get("DFIR_AUDIT_JSONL")
    if override:
        return Path(override)
    return Path("/output/logs/ai_invocations.jsonl")


def _truncate(text: str | None, limit: int = _PREVIEW_BYTES) -> str | None:
    if text is None:
        return None
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    suffix = b"...[truncated]"
    return (encoded[: limit - len(suffix)] + suffix).decode("utf-8", errors="replace")


def _hash_canonical_json(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _serialize_result(result: Any) -> str:
    """Render the tool's return value to a string for hashing/preview."""
    if isinstance(result, (str, bytes)):
        return result.decode("utf-8", errors="replace") if isinstance(result, bytes) else result
    try:
        return json.dumps(result, default=str, sort_keys=True)
    except (TypeError, ValueError):
        return repr(result)


def _write_jsonl(record: dict[str, Any]) -> bool:
    path = _jsonl_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, default=str) + "\n"
        with _jsonl_lock, open(path, "a", encoding="utf-8") as f:
            f.write(line)
        return True
    except OSError as exc:
        logger.warning("Audit JSONL write failed (%s): %s", path, exc)
        return False


def _post_orchestrator(record: dict[str, Any]) -> bool:
    url = f"{_orchestrator_url()}/audit/ai-invocation"
    body = json.dumps(record, default=str).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 — internal http://orchestrator URL
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:  # noqa: S310
            return 200 <= resp.status < 400
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        logger.debug("Audit POST failed (%s): %s", url, exc)
        return False


def _emit(record: dict[str, Any]) -> None:
    """Send a record to JSONL + orchestrator. Never raises."""
    if _audit_disabled():
        return
    try:
        _write_jsonl(record)
        _post_orchestrator(record)
    except Exception:  # pragma: no cover — final safety net
        logger.exception("Audit emit raised unexpectedly — swallowing")


def _build_record(
    *,
    server: str,
    tool_name: str,
    tool_args: dict[str, Any],
    started_at: datetime,
    finished_at: datetime,
    result: Any = None,
    error: str | None = None,
) -> dict[str, Any]:
    output_str = _serialize_result(result) if result is not None else ""
    duration_ms = int((finished_at - started_at).total_seconds() * 1000)

    # If the result is a dict with stdout/stderr/returncode (the common
    # _run() shape across our MCP servers), surface those fields
    # explicitly so reviewers don't have to dig into stdout_preview.
    exit_code: int | None = None
    stdout_preview: str | None = None
    stderr_preview: str | None = None
    if isinstance(result, dict):
        if isinstance(result.get("returncode"), int):
            exit_code = result["returncode"]
        if isinstance(result.get("stdout"), str):
            stdout_preview = _truncate(result["stdout"])
        if isinstance(result.get("stderr"), str):
            stderr_preview = _truncate(result["stderr"])
    if stdout_preview is None and not stderr_preview and result is not None:
        stdout_preview = _truncate(output_str)

    return {
        "ai_actor": _ai_actor(),
        "mcp_server": server,
        "tool_name": tool_name,
        "tool_args": tool_args,
        "input_sha256": _hash_canonical_json(tool_args),
        "output_sha256": _hash_text(output_str) if output_str else None,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "stdout_preview": stdout_preview,
        "stderr_preview": stderr_preview,
        "error": _truncate(error, limit=_ERROR_PREVIEW_BYTES),
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        # Correlation IDs come from env (set by the AI host when known)
        "case_id": os.environ.get("DFIR_CASE_ID") or None,
        "session_id": os.environ.get("DFIR_SESSION_ID") or None,
    }


def audited(server: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Wrap an MCP tool function so each call is captured in the audit log.

    Use *before* ``@mcp.tool()`` so FastMCP introspects the wrapped
    signature::

        @mcp.tool()
        @audited(server="kali-forensics")
        def volatility_run(image_path: str, plugin: str) -> dict:
            ...

    ``functools.wraps`` preserves the function's name, docstring, and
    type annotations — the metadata FastMCP reads to advertise the tool.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tool_args = _kwargs_only(func, args, kwargs)
            started = datetime.now(UTC)
            error: str | None = None
            result: Any = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as exc:  # noqa: BLE001 — re-raised below
                error = f"{type(exc).__name__}: {exc}"
                raise
            finally:
                finished = datetime.now(UTC)
                record = _build_record(
                    server=server,
                    tool_name=func.__name__,
                    tool_args=tool_args,
                    started_at=started,
                    finished_at=finished,
                    result=result,
                    error=error,
                )
                _emit(record)

        return wrapper

    return decorator


def _kwargs_only(func: Callable[..., Any], args: tuple, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Render a call's positional + keyword args as a single dict.

    Falls back gracefully if introspection fails (e.g. C-extension
    callables); we'd rather log ``{"_args": [...], "_kwargs": {...}}``
    than lose the audit record.
    """
    import inspect

    try:
        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        return dict(bound.arguments)
    except (TypeError, ValueError):
        return {"_args": list(args), "_kwargs": dict(kwargs)}


__all__ = ["audited"]
