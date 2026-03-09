"""Tests for core domain models."""

from dfireballz.models.base import Evidence, Finding, ForensicSession, Severity, Target


def test_target_str():
    t = Target(value="192.168.1.1", target_type="ip")
    assert str(t) == "192.168.1.1"


def test_finding_defaults():
    f = Finding(target="test", tool="yara", title="YARA match")
    assert f.severity == Severity.INFO
    assert f.id  # Auto-generated
    assert f.timestamp


def test_session_add_finding():
    session = ForensicSession(target=Target(value="test.raw"))
    assert len(session.findings) == 0
    session.add_finding(
        Finding(target="test", tool="vol3", title="Test finding")
    )
    assert len(session.findings) == 1


def test_session_mark_tool_done():
    session = ForensicSession(target=Target(value="test.raw"))
    session.mark_tool_done("volatility3")
    session.mark_tool_done("volatility3")  # Duplicate
    assert session.tools_executed == ["volatility3"]


def test_session_finish():
    session = ForensicSession(target=Target(value="test.raw"))
    assert session.status == "running"
    session.finish()
    assert session.status == "completed"
    assert session.finished_at is not None
    assert session.duration_seconds is not None


def test_session_severity_counts():
    session = ForensicSession(target=Target(value="test.raw"))
    session.add_finding(Finding(target="t", tool="a", title="f1", severity=Severity.HIGH))
    session.add_finding(Finding(target="t", tool="b", title="f2", severity=Severity.HIGH))
    session.add_finding(Finding(target="t", tool="c", title="f3", severity=Severity.LOW))
    counts = session.severity_counts
    assert counts["high"] == 2
    assert counts["low"] == 1


def test_evidence_defaults():
    e = Evidence(filename="disk.img", sha256="abc123")
    assert e.evidence_type == "unknown"
    assert e.id
