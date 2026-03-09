"""Tests for report generation."""

import tempfile
from pathlib import Path

from dfireballz.models.base import Finding, ForensicSession, Severity, Target
from dfireballz.reporting.html_generator import generate_html_report
from dfireballz.reporting.md_generator import generate_md_report


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
