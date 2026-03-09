"""Shared pytest fixtures for DFIReballz tests."""

from __future__ import annotations

import pytest

from dfireballz.models.base import Finding, ForensicSession, Severity, Target


@pytest.fixture
def sample_target() -> Target:
    return Target(value="/evidence/memdump.raw", target_type="memory_dump")


@pytest.fixture
def sample_finding() -> Finding:
    return Finding(
        target="/evidence/memdump.raw",
        tool="volatility3",
        category="memory",
        title="Suspicious process detected",
        description="Process csrss.exe running from unusual path",
        severity=Severity.HIGH,
        evidence="PID 4832 - csrss.exe - C:\\Temp\\csrss.exe",
        recommendation="Investigate process origin and check for malware",
    )


@pytest.fixture
def sample_session(sample_target: Target, sample_finding: Finding) -> ForensicSession:
    session = ForensicSession(
        target=sample_target,
        case_id="CASE-2026-001",
    )
    session.add_finding(sample_finding)
    session.mark_tool_done("volatility3")
    return session
