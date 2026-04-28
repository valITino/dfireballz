"""Tests for orchestrator.case_lifecycle — pure I/O case lifecycle hooks."""

import json
from pathlib import Path

import pytest
from case_lifecycle import (
    CLOSURE_FILENAME,
    PHASE_DIRS,
    PRECONDITION_FILENAME,
    init_case_directories,
    write_closure_manifest,
    write_precondition,
)


@pytest.fixture
def case_dir(tmp_path: Path) -> Path:
    d = tmp_path / "DFIR-2026-001"
    d.mkdir()
    return d


def test_phase_dirs_canonical():
    assert PHASE_DIRS == (
        "01-readiness",
        "02-identification",
        "03-acquisition",
        "04-examination",
        "05-analysis",
        "06-reporting",
    )


def test_init_creates_six_phase_dirs(case_dir: Path):
    created = init_case_directories(case_dir)
    assert len(created) == 6
    for name in PHASE_DIRS:
        assert (case_dir / name).is_dir()


def test_init_is_idempotent(case_dir: Path):
    init_case_directories(case_dir)
    # Second call must not raise.
    init_case_directories(case_dir)
    for name in PHASE_DIRS:
        assert (case_dir / name).is_dir()


def test_precondition_payload_shape(case_dir: Path):
    record = {
        "id": "abc-123",
        "case_number": "DFIR-2026-001",
        "case_type": "phishing",
        "classification": "confidential",
        "investigator": "alice",
        "title": "Test",
    }
    out = write_precondition(
        case_dir,
        record,
        declared_mcp_servers=["osint", "threat-intel"],
        pinned_tool_versions={"dc3dd": "7.2.646"},
    )
    assert out == case_dir / "01-readiness" / PRECONDITION_FILENAME
    data = json.loads(out.read_text())
    assert data["schema"] == "dfireballz/case-precondition-v1"
    assert data["process_model"] == "dfireballz/forensic-process-v1"
    assert data["phase"] == "readiness"
    assert data["case_id"] == "abc-123"
    assert data["case_number"] == "DFIR-2026-001"
    assert data["investigator"] == "alice"
    assert data["declared_mcp_servers"] == ["osint", "threat-intel"]
    assert data["pinned_tool_versions"] == {"dc3dd": "7.2.646"}
    assert "opened_at_utc" in data
    assert "host_utc_offset_seconds" in data


def test_precondition_creates_phase_dirs_if_missing(tmp_path: Path):
    """write_precondition should create the layout itself, not require
    a separate init call."""
    case_dir = tmp_path / "DFIR-2026-002"
    case_dir.mkdir()
    write_precondition(case_dir, {"id": "x", "case_number": "DFIR-2026-002"})
    for name in PHASE_DIRS:
        assert (case_dir / name).is_dir()


def test_closure_manifest_payload_shape(case_dir: Path):
    record = {
        "id": "abc-123",
        "case_number": "DFIR-2026-001",
        "title": "Test",
        "investigator": "alice",
    }
    out = write_closure_manifest(
        case_dir,
        record,
        closing_examiner="bob",
        audit_log_path="/workspace/output/logs/ai_invocations.jsonl",
    )
    assert out == case_dir / "06-reporting" / CLOSURE_FILENAME
    data = json.loads(out.read_text())
    assert data["schema"] == "dfireballz/closure-manifest-v1"
    assert data["phase"] == "reporting"
    assert data["case_id"] == "abc-123"
    assert data["final_status"] == "closed"
    assert data["closing_examiner"] == "bob"
    assert data["audit_log_path"] == "/workspace/output/logs/ai_invocations.jsonl"
    assert "closed_at_utc" in data


def test_closure_examiner_falls_back_to_investigator(case_dir: Path):
    record = {"id": "x", "case_number": "DFIR-2026-001", "investigator": "alice"}
    out = write_closure_manifest(case_dir, record)
    data = json.loads(out.read_text())
    assert data["closing_examiner"] == "alice"


def test_extra_fields_pass_through(case_dir: Path):
    out = write_precondition(
        case_dir, {"id": "x", "case_number": "y"}, extra={"sandbox": "iso-vm-3"}
    )
    data = json.loads(out.read_text())
    assert data["extra"] == {"sandbox": "iso-vm-3"}
