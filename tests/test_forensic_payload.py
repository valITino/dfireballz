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


def test_payload_all_sub_models():
    """Validate that all sub-models can be instantiated and nested."""
    from dfireballz.models.forensic_payload import (
        DNSRecordEntry,
        EmailArtifact,
        ErrorLogEntry,
        ExecutiveSummary,
        FindingCounts,
        NetworkConnection,
        ProcessEntry,
        RecommendationEntry,
        TopFinding,
        UserAccountEntry,
        VulnerabilityEntry,
        WhoisRecord,
    )

    payload = ForensicPayload(
        session_id="sub-model-test",
        target="target.img",
        findings=ForensicFindings(
            artifacts=[ArtifactEntry(artifact_type="registry_key", path="HKLM\\...")],
            timeline_events=[TimelineEvent(timestamp="2026-01-01T00:00:00Z")],
            iocs=[IoCEntry(ioc_type="ip", value="10.0.0.1", confidence="high")],
            network_connections=[
                NetworkConnection(
                    source_ip="10.0.0.1", dest_ip="1.2.3.4",
                    dest_port=443, suspicious=True,
                )
            ],
            processes=[
                ProcessEntry(pid=1234, name="evil.exe", suspicious=True, injected=True)
            ],
            user_accounts=[UserAccountEntry(username="admin", suspicious_activity="lateral")],
            malware_samples=[MalwareSample(sha256="aabbcc", yara_matches=["rule1"])],
            vulnerabilities=[
                VulnerabilityEntry(cve="CVE-2024-1234", severity="critical", cvss=9.8)
            ],
            dns_records=[DNSRecordEntry(type="A", name="evil.com", value="1.2.3.4")],
            whois=WhoisRecord(domain="evil.com", registrar="shady-registrar"),
            email_artifacts=[
                EmailArtifact(
                    subject="Invoice", sender="attacker@evil.com",
                    suspicious=True, urls_found=["http://evil.com/payload"],
                )
            ],
        ),
        chain_of_custody=[
            CoCEntry(action="analyze", evidence_id="target.img", description="Full scan")
        ],
        error_log=[ErrorLogEntry(type="timeout", count=2, likely_cause="slow disk")],
        executive_summary=ExecutiveSummary(
            risk_level="critical",
            headline="Active compromise detected",
            total_findings=FindingCounts(critical=1, high=2),
            top_findings=[TopFinding(title="Injected process", severity="critical")],
        ),
        recommendations=[
            RecommendationEntry(
                priority=1, title="Isolate host", category="containment"
            )
        ],
    )
    d = payload.to_dict()
    assert d["findings"]["network_connections"][0]["suspicious"] is True
    assert d["findings"]["processes"][0]["injected"] is True
    assert d["findings"]["dns_records"][0]["type"] == "A"
    assert d["executive_summary"]["risk_level"] == "critical"
    assert d["recommendations"][0]["title"] == "Isolate host"
    assert len(d["error_log"]) == 1
    assert d["findings"]["whois"]["domain"] == "evil.com"
    assert d["findings"]["email_artifacts"][0]["suspicious"] is True


def test_coc_entry_auto_timestamp():
    """CoCEntry should auto-generate a timestamp."""
    entry = CoCEntry(action="hash_verify", evidence_id="test.img", description="verified")
    assert entry.timestamp
    assert "T" in entry.timestamp  # ISO format


def test_payload_roundtrip_json():
    """Payload should survive JSON serialization and deserialization."""
    import json
    payload = ForensicPayload(
        session_id="roundtrip",
        target="test.raw",
        case_id="CASE-RT-001",
    )
    json_str = json.dumps(payload.to_dict(), default=str)
    restored = ForensicPayload.model_validate_json(json_str)
    assert restored.session_id == "roundtrip"
    assert restored.case_id == "CASE-RT-001"
