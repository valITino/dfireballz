"""Case Manager — Creates/loads cases, manages CoC log, evidence hash registry."""

import hashlib
import json
import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg
from case_lifecycle import write_closure_manifest, write_precondition
from fastapi import UploadFile

EVIDENCE_DIR = Path("/evidence")
CASES_DIR = Path("/cases")

_DEFAULT_DECLARED_MCP_SERVERS = (
    "kali-forensics",
    "winforensics",
    "osint",
    "threat-intel",
    "binary-analysis",
    "network-forensics",
    "filesystem",
)

logger = logging.getLogger(__name__)


class CaseManager:
    """Manages cases, evidence, IOCs, findings, and chain of custody."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def init(self):
        """Initialize database connection pool."""
        self.pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)

    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()

    async def health_check(self):
        """Check database connectivity."""
        async with self.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

    # ─── Cases ───────────────────────────────────────────────────────

    async def create_case(self, data: dict) -> dict:
        """Create a new investigation case."""
        async with self.pool.acquire() as conn:
            # Generate case number
            year = datetime.now(UTC).year
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM cases WHERE case_number LIKE $1",
                f"DFIR-{year}-%",
            )
            case_number = f"DFIR-{year}-{count + 1:03d}"

            row = await conn.fetchrow(
                """INSERT INTO cases
                   (case_number, title, case_type,
                    description, classification, investigator)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   RETURNING *""",
                case_number,
                data["title"],
                data.get("case_type", "other"),
                data.get("description"),
                data.get("classification", "confidential"),
                data.get("investigator"),
            )

            # Create case directory + canonical phase layout, write the
            # readiness pre-flight precondition manifest, and append a
            # case_opened CoC entry. Failures here are logged but do
            # not roll back the DB row — a case that exists in the DB
            # without on-disk artifacts is recoverable; the inverse is
            # not.
            case_dir = CASES_DIR / case_number
            case_dir.mkdir(parents=True, exist_ok=True)
            case_record = dict(row)
            try:
                write_precondition(
                    case_dir,
                    case_record,
                    declared_mcp_servers=list(_DEFAULT_DECLARED_MCP_SERVERS),
                )
            except OSError as exc:
                logger.warning(
                    "Failed to write case-precondition.json for %s: %s",
                    case_number,
                    exc,
                )

            try:
                await conn.execute(
                    """INSERT INTO chain_of_custody_log
                       (case_id, action, actor, notes)
                       VALUES ($1, $2, $3, $4)""",
                    row["id"],
                    "case_opened",
                    "orchestrator",
                    (
                        "Case opened. Phase=readiness. "
                        "case-precondition.json written under "
                        "01-readiness/."
                    ),
                )
            except asyncpg.PostgresError as exc:
                logger.warning(
                    "Failed to log case_opened CoC entry for %s: %s",
                    case_number,
                    exc,
                )

            return case_record

    async def list_cases(
        self, status: str | None = None, case_type: str | None = None
    ) -> list[dict]:
        """List cases with optional filters."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM cases WHERE 1=1"
            params: list[Any] = []
            idx = 1
            if status:
                query += f" AND status = ${idx}"
                params.append(status)
                idx += 1
            if case_type:
                query += f" AND case_type = ${idx}"
                params.append(case_type)
                idx += 1
            query += " ORDER BY created_at DESC"
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]

    async def get_case(self, case_id: str) -> dict | None:
        """Get case by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM cases WHERE id = $1", uuid.UUID(case_id))
            return dict(row) if row else None

    _CASE_COLUMNS = frozenset({"title", "description", "status", "classification", "investigator"})

    async def update_case(self, case_id: str, updates: dict) -> dict | None:
        """Update case fields.

        When ``status`` transitions to ``closed`` (and was not closed
        before), emit the post-flight closure manifest under
        ``06-reporting/`` and append a ``case_closed`` CoC entry.
        """
        if not updates:
            return await self.get_case(case_id)

        prior = await self.get_case(case_id)

        async with self.pool.acquire() as conn:
            set_clauses = []
            params: list[Any] = []
            for idx, (key, value) in enumerate(updates.items(), 1):
                if key not in self._CASE_COLUMNS:
                    raise ValueError(f"Invalid column: {key}")
                set_clauses.append(f"{key} = ${idx}")
                params.append(value)
            params.append(uuid.UUID(case_id))
            query = (
                f"UPDATE cases SET {', '.join(set_clauses)} "  # nosec B608
                f"WHERE id = ${len(params)} RETURNING *"
            )
            row = await conn.fetchrow(query, *params)
            if not row:
                return None
            updated = dict(row)

            transitioning_to_closed = (
                updates.get("status") == "closed"
                and (prior is None or prior.get("status") != "closed")
            )
            if transitioning_to_closed:
                case_dir = CASES_DIR / updated["case_number"]
                try:
                    write_closure_manifest(
                        case_dir,
                        updated,
                        closing_examiner=updated.get("investigator"),
                    )
                except OSError as exc:
                    logger.warning(
                        "Failed to write closure-manifest.json for %s: %s",
                        updated.get("case_number"),
                        exc,
                    )
                try:
                    await conn.execute(
                        """INSERT INTO chain_of_custody_log
                           (case_id, action, actor, notes)
                           VALUES ($1, $2, $3, $4)""",
                        row["id"],
                        "case_closed",
                        "orchestrator",
                        (
                            "Case closed. Phase=reporting. "
                            "closure-manifest.json written under "
                            "06-reporting/."
                        ),
                    )
                except asyncpg.PostgresError as exc:
                    logger.warning(
                        "Failed to log case_closed CoC entry for %s: %s",
                        updated.get("case_number"),
                        exc,
                    )

            return updated

    # ─── Evidence ────────────────────────────────────────────────────

    async def add_evidence(self, case_id: str, file: UploadFile) -> dict:
        """Upload evidence, compute hashes, create CoC entry."""
        case = await self.get_case(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        # Read file and compute hashes
        content = await file.read()
        sha256 = hashlib.sha256(content).hexdigest()
        md5 = hashlib.md5(content, usedforsecurity=False).hexdigest()
        sha1 = hashlib.sha1(content, usedforsecurity=False).hexdigest()

        # Save to evidence directory (sanitize filename to prevent path traversal)
        evidence_dir = EVIDENCE_DIR / case["case_number"]
        evidence_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file.filename).name  # Strip any directory components
        if not safe_name or safe_name in (".", ".."):
            raise ValueError(f"Invalid filename: {file.filename}")
        filepath = evidence_dir / safe_name
        if not filepath.resolve().is_relative_to(evidence_dir.resolve()):
            raise ValueError(f"Invalid filename: {file.filename}")
        with open(filepath, "wb") as f:
            f.write(content)

        async with self.pool.acquire() as conn:
            # Create evidence record
            row = await conn.fetchrow(
                """INSERT INTO evidence
                   (case_id, filename, filepath, file_type,
                    sha256, md5, sha1, size_bytes, acquisition_method)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   RETURNING *""",
                uuid.UUID(case_id),
                safe_name,
                str(filepath),
                file.content_type,
                sha256,
                md5,
                sha1,
                len(content),
                "upload",
            )

            # Create CoC entry
            await conn.execute(
                """INSERT INTO chain_of_custody_log
                   (evidence_id, case_id, action, actor,
                    tool_used, input_hash, notes)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                row["id"],
                uuid.UUID(case_id),
                "acquired",
                "system",
                "DFIReballz Upload",
                sha256,
                f"Evidence uploaded: {safe_name} (SHA256: {sha256})",
            )

            return dict(row)

    async def list_evidence(self, case_id: str) -> list[dict]:
        """List evidence for a case."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM evidence WHERE case_id = $1 ORDER BY acquired_at DESC",
                uuid.UUID(case_id),
            )
            return [dict(r) for r in rows]

    # ─── IOCs ────────────────────────────────────────────────────────

    async def add_ioc(self, case_id: str, data: dict) -> dict:
        """Add an IOC to a case."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO iocs
                   (case_id, ioc_type, value, confidence,
                    source, mitre_technique, notes)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   RETURNING *""",
                uuid.UUID(case_id),
                data["ioc_type"],
                data["value"],
                data.get("confidence", 50),
                data.get("source"),
                data.get("mitre_technique"),
                data.get("notes"),
            )
            return dict(row)

    async def list_iocs(self, case_id: str) -> list[dict]:
        """List IOCs for a case."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM iocs WHERE case_id = $1 ORDER BY first_seen DESC",
                uuid.UUID(case_id),
            )
            return [dict(r) for r in rows]

    # ─── Findings ────────────────────────────────────────────────────

    async def add_finding(self, case_id: str, data: dict) -> dict:
        """Add a finding to a case."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO findings
                   (case_id, finding_type, title, description,
                    severity, mitre_techniques,
                    timeline_timestamp, raw_output)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                   RETURNING *""",
                uuid.UUID(case_id),
                data.get("finding_type"),
                data["title"],
                data.get("description"),
                data.get("severity", "info"),
                data.get("mitre_techniques"),
                data.get("timeline_timestamp"),
                data.get("raw_output"),
            )
            return dict(row)

    async def list_findings(self, case_id: str) -> list[dict]:
        """List findings for a case."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM findings WHERE case_id = $1 ORDER BY created_at DESC",
                uuid.UUID(case_id),
            )
            return [dict(r) for r in rows]

    # ─── Playbook Runs ───────────────────────────────────────────────

    async def create_playbook_run(self, case_id: str, playbook_name: str) -> dict:
        """Create a playbook run record."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO playbook_runs (case_id, playbook_name, mcp_host)
                   VALUES ($1, $2, $3) RETURNING *""",
                uuid.UUID(case_id),
                playbook_name,
                os.environ.get("MCP_HOST", "claude-code"),
            )
            return dict(row)

    _RUN_COLUMNS = frozenset({"status", "results", "completed_at", "error", "steps"})

    async def update_playbook_run(self, run_id: str, updates: dict) -> dict:
        """Update a playbook run."""
        async with self.pool.acquire() as conn:
            set_clauses = []
            params: list[Any] = []
            for idx, (key, value) in enumerate(updates.items(), 1):
                if key not in self._RUN_COLUMNS:
                    raise ValueError(f"Invalid column: {key}")
                set_clauses.append(f"{key} = ${idx}")
                params.append(value)
            params.append(uuid.UUID(run_id))
            query = (
                f"UPDATE playbook_runs SET {', '.join(set_clauses)} "  # nosec B608
                f"WHERE id = ${len(params)} RETURNING *"
            )
            row = await conn.fetchrow(query, *params)
            return dict(row) if row else {}

    async def list_playbook_runs(self, case_id: str) -> list[dict]:
        """List playbook runs for a case."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM playbook_runs WHERE case_id = $1 ORDER BY started_at DESC",
                uuid.UUID(case_id),
            )
            return [dict(r) for r in rows]

    # ─── Chain of Custody ────────────────────────────────────────────

    async def log_coc_entry(self, data: dict) -> dict:
        """Create an immutable chain of custody log entry."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO chain_of_custody_log
                   (evidence_id, case_id, action, actor,
                    tool_used, tool_version, input_hash,
                    output_hash, notes, mcp_tool_call)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                   RETURNING *""",
                data.get("evidence_id"),
                uuid.UUID(data["case_id"]) if data.get("case_id") else None,
                data["action"],
                data.get("actor", "system"),
                data.get("tool_used"),
                data.get("tool_version"),
                data.get("input_hash"),
                data.get("output_hash"),
                data.get("notes"),
                data.get("mcp_tool_call"),
            )
            return dict(row)

    # ─── AI Tool Invocations ─────────────────────────────────────────

    async def log_ai_invocation(self, data: dict) -> dict:
        """Persist an AI tool-invocation audit record.

        Inserts into ``ai_tool_invocations`` (immutable). When the call
        targets evidence (``evidence_id`` set), ALSO writes a CoC entry
        so the legal-grade chain stays intact — per the project
        invariant that every evidence access creates a CoC log row.
        """
        case_uuid = uuid.UUID(data["case_id"]) if data.get("case_id") else None
        evidence_uuid = (
            uuid.UUID(data["evidence_id"]) if data.get("evidence_id") else None
        )

        # Tool args may arrive as a dict (preferred) or a JSON string
        # from a serialized payload. Normalise to a JSON string for
        # asyncpg's JSONB binding.
        tool_args = data.get("tool_args")
        if isinstance(tool_args, dict):
            tool_args_json: str | None = json.dumps(tool_args, default=str)
        elif isinstance(tool_args, str):
            tool_args_json = tool_args
        else:
            tool_args_json = None

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO ai_tool_invocations
                   (case_id, evidence_id, session_id, ai_actor,
                    mcp_server, tool_name, tool_args,
                    input_sha256, output_sha256, exit_code,
                    duration_ms, stdout_preview, stderr_preview,
                    error, started_at, finished_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9,
                           $10, $11, $12, $13, $14, $15, $16)
                   RETURNING *""",
                case_uuid,
                evidence_uuid,
                data.get("session_id"),
                data["ai_actor"],
                data["mcp_server"],
                data["tool_name"],
                tool_args_json,
                data.get("input_sha256"),
                data.get("output_sha256"),
                data.get("exit_code"),
                data.get("duration_ms"),
                data.get("stdout_preview"),
                data.get("stderr_preview"),
                data.get("error"),
                data.get("started_at"),
                data.get("finished_at"),
            )

            # If this AI call touched evidence, mirror to CoC so the
            # legal chain reflects it. The CoC entry references the
            # same input/output hashes so the two logs cross-validate.
            if evidence_uuid is not None:
                await conn.execute(
                    """INSERT INTO chain_of_custody_log
                       (evidence_id, case_id, action, actor,
                        tool_used, input_hash, output_hash,
                        notes, mcp_tool_call)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)""",
                    evidence_uuid,
                    case_uuid,
                    "analyzed",
                    data["ai_actor"],
                    f"{data['mcp_server']}.{data['tool_name']}",
                    data.get("input_sha256"),
                    data.get("output_sha256"),
                    f"AI invocation {row['id']}",
                    tool_args_json,
                )

            return dict(row)

    async def list_ai_invocations(
        self,
        case_id: str | None = None,
        session_id: str | None = None,
        limit: int = 200,
    ) -> list[dict]:
        """List AI tool-invocation records, newest first.

        Caller must supply at least one filter (enforced by the API
        layer); both filters can be combined.
        """
        async with self.pool.acquire() as conn:
            clauses: list[str] = []
            params: list[Any] = []
            if case_id:
                clauses.append(f"case_id = ${len(params) + 1}")
                params.append(uuid.UUID(case_id))
            if session_id:
                clauses.append(f"session_id = ${len(params) + 1}")
                params.append(session_id)
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            params.append(limit)
            query = (
                f"SELECT * FROM ai_tool_invocations{where} "  # nosec B608
                f"ORDER BY started_at DESC LIMIT ${len(params)}"
            )
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]
