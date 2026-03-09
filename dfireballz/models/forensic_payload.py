"""ForensicPayload — structured forensic findings for report generation.

This model represents the structured payload that the MCP host (Claude Code,
Claude Desktop, or MCPHost) produces after collecting raw tool outputs,
parsing, deduplicating, and synthesizing them.  The MCP host calls
``aggregate_results`` to validate and persist this payload, then
``generate_report`` to produce the final forensic report.

Adapted from blhackbox's AggregatedPayload for digital forensics context.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Sub-models for forensic findings
# ---------------------------------------------------------------------------


class ArtifactEntry(BaseModel):
    """A forensic artifact (file, registry key, MFT entry, etc.)."""

    id: str = ""
    artifact_type: str = Field(
        default="file",
        description="Type: file, registry_key, mft_entry, event_log, prefetch, shellbag, usn_journal",
    )
    path: str = ""
    description: str = ""
    source_tool: str = ""
    timestamps: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TimelineEvent(BaseModel):
    """A timestamped event in the forensic timeline."""

    timestamp: str = ""
    event_type: str = ""
    source: str = ""
    description: str = ""
    artifact_ref: str = ""
    severity: str = "info"


class IoCEntry(BaseModel):
    """An Indicator of Compromise."""

    ioc_type: str = Field(
        default="unknown",
        description="Type: ip, domain, url, hash_md5, hash_sha256, email, file_path, registry_key",
    )
    value: str = ""
    context: str = ""
    source_tool: str = ""
    confidence: str = Field(default="medium", description="Confidence: low, medium, high")
    threat_intel_match: str = ""
    references: list[str] = Field(default_factory=list)


class NetworkConnection(BaseModel):
    """A network connection found during forensic analysis."""

    source_ip: str = ""
    source_port: int = 0
    dest_ip: str = ""
    dest_port: int = 0
    protocol: str = "tcp"
    direction: str = "outbound"
    process_name: str = ""
    timestamp: str = ""
    suspicious: bool = False
    notes: str = ""


class ProcessEntry(BaseModel):
    """A process from memory or volatile analysis."""

    pid: int = 0
    ppid: int = 0
    name: str = ""
    path: str = ""
    cmdline: str = ""
    user: str = ""
    start_time: str = ""
    suspicious: bool = False
    injected: bool = False
    hidden: bool = False
    notes: str = ""


class UserAccountEntry(BaseModel):
    """A user account found during investigation."""

    username: str = ""
    domain: str = ""
    sid: str = ""
    last_login: str = ""
    account_type: str = ""
    suspicious_activity: str = ""
    source_tool: str = ""


class MalwareSample(BaseModel):
    """An identified malware sample."""

    filename: str = ""
    file_path: str = ""
    sha256: str = ""
    md5: str = ""
    file_size: int = 0
    malware_family: str = ""
    detection_name: str = ""
    yara_matches: list[str] = Field(default_factory=list)
    capa_matches: list[str] = Field(default_factory=list)
    virustotal_detections: int = 0
    mitre_techniques: list[str] = Field(default_factory=list)
    source_tool: str = ""


class VulnerabilityEntry(BaseModel):
    """An exploited or relevant vulnerability."""

    id: str = ""
    cve: str = ""
    title: str = ""
    severity: str = "info"
    cvss: float = 0.0
    description: str = ""
    affected_component: str = ""
    evidence_of_exploitation: str = ""
    references: list[str] = Field(default_factory=list)
    source_tool: str = ""


class DNSRecordEntry(BaseModel):
    """A DNS record found during investigation."""

    type: str = ""
    name: str = ""
    value: str = ""
    priority: int = 0


class WhoisRecord(BaseModel):
    """WHOIS domain information."""

    domain: str = ""
    registrar: str = ""
    creation_date: str = ""
    expiration_date: str = ""
    nameservers: list[str] = Field(default_factory=list)
    registrant_org: str = ""


class EmailArtifact(BaseModel):
    """An email artifact (phishing analysis, headers, etc.)."""

    subject: str = ""
    sender: str = ""
    recipient: str = ""
    date: str = ""
    headers: dict[str, str] = Field(default_factory=dict)
    attachments: list[str] = Field(default_factory=list)
    urls_found: list[str] = Field(default_factory=list)
    spf_result: str = ""
    dkim_result: str = ""
    dmarc_result: str = ""
    suspicious: bool = False
    notes: str = ""


# ---------------------------------------------------------------------------
# Findings container
# ---------------------------------------------------------------------------


class ForensicFindings(BaseModel):
    """All structured findings from the forensic investigation."""

    artifacts: list[ArtifactEntry] = Field(default_factory=list)
    timeline_events: list[TimelineEvent] = Field(default_factory=list)
    iocs: list[IoCEntry] = Field(default_factory=list)
    network_connections: list[NetworkConnection] = Field(default_factory=list)
    processes: list[ProcessEntry] = Field(default_factory=list)
    user_accounts: list[UserAccountEntry] = Field(default_factory=list)
    malware_samples: list[MalwareSample] = Field(default_factory=list)
    vulnerabilities: list[VulnerabilityEntry] = Field(default_factory=list)
    dns_records: list[DNSRecordEntry] = Field(default_factory=list)
    whois: WhoisRecord = Field(default_factory=WhoisRecord)
    email_artifacts: list[EmailArtifact] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Chain of custody
# ---------------------------------------------------------------------------


class CoCEntry(BaseModel):
    """A chain of custody log entry."""

    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    action: str = ""
    actor: str = ""
    evidence_id: str = ""
    description: str = ""
    tool_used: str = ""
    hash_before: str = ""
    hash_after: str = ""


# ---------------------------------------------------------------------------
# Error log
# ---------------------------------------------------------------------------


class ErrorLogEntry(BaseModel):
    """A single error/noise entry with forensic relevance annotation."""

    type: str = "other"
    count: int = 0
    locations: list[str] = Field(default_factory=list)
    likely_cause: str = ""
    forensic_relevance: str = "none"
    notes: str = ""


# ---------------------------------------------------------------------------
# Executive summary
# ---------------------------------------------------------------------------


class TopFinding(BaseModel):
    """A top finding for the executive summary."""

    title: str = ""
    severity: str = "info"
    impact: str = ""
    recommendation: str = ""


class AttackChain(BaseModel):
    """A reconstructed attack chain from forensic evidence."""

    name: str = ""
    steps: list[str] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)
    overall_severity: str = "info"


class FindingCounts(BaseModel):
    """Counts of findings by severity."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ExecutiveSummary(BaseModel):
    """Executive summary of the forensic investigation."""

    risk_level: str = "info"
    headline: str = ""
    summary: str = ""
    total_findings: FindingCounts = Field(default_factory=FindingCounts)
    top_findings: list[TopFinding] = Field(default_factory=list)
    attack_chains: list[AttackChain] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


class RecommendationEntry(BaseModel):
    """A prioritized remediation/containment recommendation."""

    priority: int = 0
    finding_id: str = ""
    title: str = ""
    description: str = ""
    effort: str = "medium"
    category: str = Field(
        default="containment",
        description="Category: containment, eradication, recovery, prevention",
    )


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class ForensicMetadata(BaseModel):
    """Metadata about the forensic investigation run."""

    tools_run: list[str] = Field(default_factory=list)
    evidence_hashes: dict[str, str] = Field(
        default_factory=dict,
        description="Map of evidence file paths to their SHA256 hashes",
    )
    total_artifacts: int = 0
    total_iocs: int = 0
    model: str = Field(
        default="",
        description="Which AI model performed the analysis (e.g. 'claude-opus-4-6')",
    )
    duration_seconds: float = 0.0
    warning: str = ""


# ---------------------------------------------------------------------------
# Top-level payload
# ---------------------------------------------------------------------------


class ForensicPayload(BaseModel):
    """The complete forensic investigation payload.

    Produced by the MCP host (Claude) after collecting and structuring raw
    tool outputs from forensic analysis.  Validated and persisted via the
    ``aggregate_results`` MCP tool, then used by ``generate_report`` to
    produce the final forensic report.
    """

    case_id: str = ""
    session_id: str
    target: str
    investigation_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    findings: ForensicFindings = Field(default_factory=ForensicFindings)
    chain_of_custody: list[CoCEntry] = Field(default_factory=list)
    error_log: list[ErrorLogEntry] = Field(default_factory=list)
    executive_summary: ExecutiveSummary = Field(default_factory=ExecutiveSummary)
    recommendations: list[RecommendationEntry] = Field(default_factory=list)
    metadata: ForensicMetadata = Field(default_factory=ForensicMetadata)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return self.model_dump(mode="json")
