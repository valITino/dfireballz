"""Tests for ForensicPayload schema validation."""

from dfireballz.models.forensic_payload import (
    ArtifactEntry,
    CoCEntry,
    ForensicFindings,
    ForensicPayload,
    IoCEntry,
    MalwareSample,
    TimelineEvent,
)


def test_payload_minimal():
    payload = ForensicPayload(session_id="test-001", target="/evidence/disk.img")
    assert payload.session_id == "test-001"
    assert payload.target == "/evidence/disk.img"
    assert len(payload.findings.artifacts) == 0


def test_payload_with_findings():
    payload = ForensicPayload(
        session_id="test-002",
        target="/evidence/memdump.raw",
        case_id="CASE-2026-001",
        findings=ForensicFindings(
            artifacts=[
                ArtifactEntry(
                    artifact_type="file",
                    path="C:\\Temp\\malware.exe",
                    description="Suspicious executable",
                    source_tool="volatility3",
                )
            ],
            iocs=[
                IoCEntry(
                    ioc_type="hash_sha256",
                    value="abc123def456",
                    confidence="high",
                    source_tool="yara",
                )
            ],
            malware_samples=[
                MalwareSample(
                    filename="malware.exe",
                    sha256="abc123def456",
                    malware_family="Emotet",
                    yara_matches=["rule_emotet_v4"],
                )
            ],
            timeline_events=[
                TimelineEvent(
                    timestamp="2026-03-09T10:30:00Z",
                    event_type="file_creation",
                    source="mft_parser",
                    description="malware.exe created in C:\\Temp",
                )
            ],
        ),
        chain_of_custody=[
            CoCEntry(
                action="analyze",
                evidence_id="/evidence/memdump.raw",
                description="Memory analysis with Volatility3",
                tool_used="volatility3",
            )
        ],
    )
    assert len(payload.findings.artifacts) == 1
    assert len(payload.findings.iocs) == 1
    assert len(payload.findings.malware_samples) == 1
    assert len(payload.chain_of_custody) == 1


def test_payload_to_dict():
    payload = ForensicPayload(session_id="test-003", target="test.pcap")
    d = payload.to_dict()
    assert d["session_id"] == "test-003"
    assert "findings" in d
    assert "chain_of_custody" in d


def test_payload_json_schema():
    schema = ForensicPayload.model_json_schema()
    assert "properties" in schema
    assert "session_id" in schema["properties"]
    assert "target" in schema["properties"]
