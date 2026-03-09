"""Tests for report generation."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from dfireballz.models.base import Finding, ForensicSession, Severity, Target
from dfireballz.reporting.html_generator import generate_html_report
from dfireballz.reporting.md_generator import (
    generate_md_report,
    generate_md_report_from_payload,
)


def _make_session() -> ForensicSession:
    session = ForensicSession(
        target=Target(value="test-evidence.raw"),
        case_id="CASE-TEST-001",
    )
    session.add_finding(
        Finding(
            target="test-evidence.raw",
            tool="volatility3",
            title="Suspicious process",
            severity=Severity.HIGH,
            description="Process running from temp directory",
        )
    )
    session.add_finding(
        Finding(
            target="test-evidence.raw",
            tool="yara",
            title="YARA match: Emotet",
            severity=Severity.CRITICAL,
            evidence="Matched rule emotet_v4",
        )
    )
    session.mark_tool_done("volatility3")
    session.mark_tool_done("yara")
    return session


def test_generate_html_report():
    session = _make_session()
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        out = generate_html_report(session, output_path=f.name)
    content = Path(out).read_text()
    assert "DFIReballz" in content
    assert "Suspicious process" in content
    assert "CRITICAL" in content.upper()
    Path(out).unlink()


def test_generate_md_report():
    session = _make_session()
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        out = generate_md_report(session, output_path=f.name)
    content = Path(out).read_text()
    assert "DFIReballz" in content
    assert "Suspicious process" in content
    assert "volatility3" in content
    Path(out).unlink()


def _make_payload():
    from dfireballz.models.forensic_payload import (
        CoCEntry,
        ExecutiveSummary,
        FindingCounts,
        ForensicFindings,
        ForensicMetadata,
        ForensicPayload,
        IoCEntry,
        MalwareSample,
        RecommendationEntry,
        TimelineEvent,
    )

    return ForensicPayload(
        session_id="test-payload-001",
        target="/evidence/sample.exe",
        case_id="CASE-RPT-001",
        findings=ForensicFindings(
            iocs=[
                IoCEntry(
                    ioc_type="hash_sha256",
                    value="deadbeef" * 8,
                    confidence="high",
                    context="Main payload hash",
                ),
            ],
            malware_samples=[
                MalwareSample(
                    filename="sample.exe",
                    sha256="deadbeef" * 8,
                    malware_family="Emotet",
                    yara_matches=["emotet_v4"],
                    mitre_techniques=["T1059.001"],
                ),
            ],
            timeline_events=[
                TimelineEvent(
                    timestamp="2026-03-09T10:00:00Z",
                    event_type="execution",
                    source="prefetch",
                    description="sample.exe first run",
                ),
            ],
        ),
        chain_of_custody=[
            CoCEntry(
                action="analyze",
                evidence_id="/evidence/sample.exe",
                description="Static analysis",
                tool_used="capa",
            ),
        ],
        executive_summary=ExecutiveSummary(
            risk_level="critical",
            headline="Active malware found",
            summary="Emotet variant detected with C2 beaconing.",
            total_findings=FindingCounts(critical=1, high=1),
        ),
        recommendations=[
            RecommendationEntry(
                priority=1,
                title="Isolate infected host",
                description="Disconnect from network immediately",
                category="containment",
                effort="low",
            ),
        ],
        metadata=ForensicMetadata(
            tools_run=["capa", "yara", "virustotal"],
            total_artifacts=5,
            total_iocs=3,
            model="claude-opus-4-6",
            duration_seconds=120.5,
        ),
    )


def test_generate_md_report_from_payload():
    payload = _make_payload()
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        out = generate_md_report_from_payload(payload, output_path=f.name)
    content = Path(out).read_text()
    # Header
    assert "DFIReballz" in content
    assert "sample.exe" in content
    assert "CASE-RPT-001" in content
    # Executive summary
    assert "critical" in content.lower()
    assert "Active malware found" in content
    # IoCs
    assert "deadbeef" in content
    # Malware samples
    assert "Emotet" in content
    assert "T1059.001" in content
    # Timeline
    assert "execution" in content
    # Chain of custody
    assert "analyze" in content
    # Recommendations
    assert "Isolate infected host" in content
    assert "containment" in content
    # Metadata
    assert "claude-opus-4-6" in content
    Path(out).unlink()


def test_generate_md_report_empty_session():
    """MD report should handle a session with no findings gracefully."""
    session = ForensicSession(
        target=Target(value="empty.img"),
        case_id="CASE-EMPTY",
    )
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        out = generate_md_report(session, output_path=f.name)
    content = Path(out).read_text()
    assert "Findings (0)" in content
    assert "No tools recorded" in content
    Path(out).unlink()


def test_generate_pdf_report_weasyprint_missing():
    """PDF generation should raise ReportingError when weasyprint is missing."""
    import builtins

    from dfireballz.exceptions import ReportingError

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "weasyprint":
            raise ImportError("no weasyprint")
        return original_import(name, *args, **kwargs)

    session = _make_session()
    from dfireballz.reporting.pdf_generator import generate_pdf_report
    with patch.object(builtins, "__import__", side_effect=mock_import):
        try:
            generate_pdf_report(session)
            raise AssertionError("Should have raised ReportingError")
        except ReportingError as e:
            assert "weasyprint" in str(e).lower()


def test_html_report_severity_badges():
    """HTML report should contain severity CSS classes/badges."""
    session = _make_session()
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        out = generate_html_report(session, output_path=f.name)
    content = Path(out).read_text()
    assert "CRITICAL" in content
    assert "HIGH" in content
    assert "YARA match" in content
    Path(out).unlink()
