"""Core domain models for forensic investigations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Target(BaseModel):
    """Represents an investigation target (evidence source)."""

    value: str = Field(description="Evidence file path, disk image, IP, domain, or case reference")
    target_type: str = Field(
        default="auto",
        description="Type: disk_image, memory_dump, pcap, file, ip, domain, case",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        return self.value


class Evidence(BaseModel):
    """A piece of evidence under investigation."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    filename: str = ""
    file_path: str = ""
    file_size: int = 0
    sha256: str = ""
    md5: str = ""
    sha1: str = ""
    evidence_type: str = Field(
        default="unknown",
        description="Type: disk_image, memory_dump, pcap, document, binary, email, other",
    )
    case_id: str = ""
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    """A single forensic finding from any tool or analysis."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    target: str
    tool: str = Field(description="Tool that produced this finding")
    category: str = Field(default="general")
    title: str
    description: str = ""
    severity: Severity = Severity.INFO
    evidence: str = ""
    recommendation: str = ""
    raw_data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(use_enum_values=True)


class ForensicSession(BaseModel):
    """Tracks a complete forensic investigation session."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    target: Target
    case_id: str = ""
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    tools_executed: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    status: str = Field(default="running")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_finding(self, finding: Finding) -> None:
        self.findings.append(finding)

    def mark_tool_done(self, tool_name: str) -> None:
        if tool_name not in self.tools_executed:
            self.tools_executed.append(tool_name)

    def finish(self) -> None:
        self.finished_at = datetime.now(UTC)
        self.status = "completed"

    @property
    def severity_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in self.findings:
            sev = f.severity if isinstance(f.severity, str) else f.severity.value
            counts[sev] = counts.get(sev, 0) + 1
        return counts

    @property
    def duration_seconds(self) -> float | None:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
