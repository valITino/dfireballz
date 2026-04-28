"""Case lifecycle hooks for the canonical forensic process model.

Pure I/O — no DB, no async. Creates the phase-based directory layout
when a case is opened (Readiness pre-flight) and writes the closure
manifest when a case is closed (Reporting post-flight).

These are *automatic* artifacts. They give every case a minimum
defensible record even if no playbook is run, and they seed the
expected on-disk layout so playbooks can write into the right
phase directories from the first step.
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PHASE_DIRS: tuple[str, ...] = (
    "01-readiness",
    "02-identification",
    "03-acquisition",
    "04-examination",
    "05-analysis",
    "06-reporting",
)

PRECONDITION_FILENAME = "case-precondition.json"
CLOSURE_FILENAME = "closure-manifest.json"


def init_case_directories(case_dir: Path) -> list[Path]:
    """Create the six canonical phase subdirectories under ``case_dir``.

    Returns the list of created (or already-existing) directories.
    Idempotent — safe to call repeatedly.
    """
    created: list[Path] = []
    for name in PHASE_DIRS:
        d = case_dir / name
        d.mkdir(parents=True, exist_ok=True)
        created.append(d)
    return created


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _host_utc_offset_seconds() -> int:
    """Return the host clock's UTC offset in seconds.

    On a UTC-synced host this is 0. Recorded so reviewers can detect
    a host that drifted at the time of case open.
    """
    return -time.timezone if time.daylight == 0 else -time.altzone


def write_precondition(
    case_dir: Path,
    case_record: dict[str, Any],
    *,
    declared_mcp_servers: list[str] | None = None,
    pinned_tool_versions: dict[str, str] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write ``01-readiness/case-precondition.json`` for the case.

    Records what the orchestrator can attest at case-open time. MCP
    health-checks and live tool-version pinning are deferred to the
    runner / pre-flight playbook step — this writes the *declared*
    servers and any tool versions the caller passes in.

    Args:
        case_dir: ``cases/<case-number>/``.
        case_record: The DB row dict returned from ``create_case``.
        declared_mcp_servers: MCP servers the case is expected to use.
        pinned_tool_versions: Optional tool-version pins captured by
            the caller (e.g. read from a config snapshot).
        extra: Free-form additional fields to embed.

    Returns the path written.
    """
    init_case_directories(case_dir)
    payload: dict[str, Any] = {
        "schema": "dfireballz/case-precondition-v1",
        "process_model": "dfireballz/forensic-process-v1",
        "phase": "readiness",
        "case_id": str(case_record.get("id", "")),
        "case_number": case_record.get("case_number"),
        "case_type": case_record.get("case_type"),
        "classification": case_record.get("classification"),
        "investigator": case_record.get("investigator"),
        "title": case_record.get("title"),
        "opened_at_utc": _utc_now_iso(),
        "host_utc_offset_seconds": _host_utc_offset_seconds(),
        "declared_mcp_servers": list(declared_mcp_servers or []),
        "pinned_tool_versions": dict(pinned_tool_versions or {}),
        "orchestrator_version": os.environ.get("DFIR_ORCHESTRATOR_VERSION", "unknown"),
    }
    if extra:
        payload["extra"] = extra
    out = case_dir / PHASE_DIRS[0] / PRECONDITION_FILENAME
    out.write_text(json.dumps(payload, indent=2, default=str))
    return out


def write_closure_manifest(
    case_dir: Path,
    case_record: dict[str, Any],
    *,
    closing_examiner: str | None = None,
    audit_log_path: str | None = None,
    final_status: str = "closed",
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write ``06-reporting/closure-manifest.json`` for the case.

    Records the final state of the case. Hash re-verification and
    audit-log sealing are responsibilities of the reporting playbook
    step — this writes the metadata wrapper around them.

    Returns the path written.
    """
    init_case_directories(case_dir)
    payload: dict[str, Any] = {
        "schema": "dfireballz/closure-manifest-v1",
        "process_model": "dfireballz/forensic-process-v1",
        "phase": "reporting",
        "case_id": str(case_record.get("id", "")),
        "case_number": case_record.get("case_number"),
        "title": case_record.get("title"),
        "final_status": final_status,
        "closed_at_utc": _utc_now_iso(),
        "closing_examiner": closing_examiner or case_record.get("investigator"),
        "audit_log_path": audit_log_path,
        "orchestrator_version": os.environ.get("DFIR_ORCHESTRATOR_VERSION", "unknown"),
    }
    if extra:
        payload["extra"] = extra
    out = case_dir / PHASE_DIRS[5] / CLOSURE_FILENAME
    out.write_text(json.dumps(payload, indent=2, default=str))
    return out


__all__ = [
    "CLOSURE_FILENAME",
    "PHASE_DIRS",
    "PRECONDITION_FILENAME",
    "init_case_directories",
    "write_closure_manifest",
    "write_precondition",
]
