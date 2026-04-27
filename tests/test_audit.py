"""Tests for the AI audit logging subsystem.

Covers:
* Pydantic validation of ``AIInvocation``
* Hash determinism (canonical JSON, text)
* JSONL append + format (one JSON object per line)
* HTTP POST contract — mocked with respx
* ``build_invocation`` previews/truncation
* The MCP shared audit decorator (``mcp-servers/_common/audit.py``)
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from dfireballz.audit import AIInvocation, AuditEmitter
from dfireballz.audit.emitter import (
    build_invocation,
    hash_canonical_json,
    hash_text,
    reset_emitter,
)

# Make the volume-mounted MCP audit module importable for in-process tests.
_MCP_COMMON = Path(__file__).resolve().parents[1] / "mcp-servers"
sys.path.insert(0, str(_MCP_COMMON))


# ─────────────────────────── Pydantic model ──────────────────────────


def test_aiinvocation_minimum_fields_validate():
    inv = AIInvocation(
        ai_actor="claude-code",
        mcp_server="kali-forensics",
        tool_name="volatility_run",
    )
    assert inv.ai_actor == "claude-code"
    assert inv.tool_args == {}
    assert inv.started_at.tzinfo is not None  # UTC default


def test_aiinvocation_rejects_empty_required():
    with pytest.raises(ValueError):
        AIInvocation(ai_actor="", mcp_server="x", tool_name="y")


def test_aiinvocation_to_jsonl_dict_is_json_serialisable():
    inv = AIInvocation(
        ai_actor="claude-code",
        mcp_server="osint",
        tool_name="username_search",
        tool_args={"username": "alice"},
    )
    # Should round-trip through json.dumps without errors
    raw = inv.to_jsonl_dict()
    assert json.dumps(raw)
    assert raw["tool_args"] == {"username": "alice"}


# ───────────────────────── Hash determinism ──────────────────────────


def test_hash_canonical_json_is_order_independent():
    a = hash_canonical_json({"b": 1, "a": 2})
    b = hash_canonical_json({"a": 2, "b": 1})
    assert a == b


def test_hash_canonical_json_differs_for_different_values():
    assert hash_canonical_json({"a": 1}) != hash_canonical_json({"a": 2})


def test_hash_text_is_deterministic():
    assert hash_text("forensic output") == hash_text("forensic output")
    assert len(hash_text("x")) == 64


# ─────────────────────────── build_invocation ────────────────────────


def test_build_invocation_computes_duration():
    started = datetime(2026, 4, 27, 10, 0, 0, tzinfo=UTC)
    finished = started + timedelta(milliseconds=1234)
    inv = build_invocation(
        ai_actor="claude-code",
        mcp_server="kali-forensics",
        tool_name="dc3dd_hash",
        tool_args={"file_path": "/evidence/disk.img"},
        started_at=started,
        finished_at=finished,
        stdout="abc",
        exit_code=0,
    )
    assert inv.duration_ms == 1234
    assert inv.exit_code == 0
    assert inv.input_sha256 == hash_canonical_json({"file_path": "/evidence/disk.img"})
    assert inv.output_sha256 == hash_text("abc")


def test_build_invocation_truncates_long_output():
    big = "A" * 10_000
    inv = build_invocation(
        ai_actor="claude-code",
        mcp_server="kali-forensics",
        tool_name="strings_extract",
        tool_args={},
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        stdout=big,
    )
    # Preview is capped, but the full hash matches the untruncated text.
    assert inv.stdout_preview is not None
    assert len(inv.stdout_preview.encode("utf-8")) <= 4096
    assert "[truncated]" in inv.stdout_preview
    assert inv.output_sha256 == hash_text(big)


# ─────────────────────────── JSONL emit ──────────────────────────────


def test_emitter_writes_jsonl(tmp_path: Path):
    reset_emitter()
    jsonl = tmp_path / "logs" / "ai_invocations.jsonl"
    emitter = AuditEmitter(orchestrator_url="http://nonexistent:1", jsonl_path=jsonl)
    inv = AIInvocation(
        ai_actor="claude-code",
        mcp_server="osint",
        tool_name="whois_lookup",
        tool_args={"target": "example.com"},
    )
    result = emitter.emit_sync(inv)
    assert result["jsonl"] is True
    assert jsonl.exists()
    line = jsonl.read_text(encoding="utf-8").strip()
    parsed = json.loads(line)
    assert parsed["ai_actor"] == "claude-code"
    assert parsed["tool_name"] == "whois_lookup"


def test_emitter_jsonl_append_preserves_existing_lines(tmp_path: Path):
    reset_emitter()
    jsonl = tmp_path / "ai_invocations.jsonl"
    jsonl.write_text('{"existing": true}\n', encoding="utf-8")

    emitter = AuditEmitter(orchestrator_url="http://nonexistent:1", jsonl_path=jsonl)
    inv = AIInvocation(
        ai_actor="claude-code",
        mcp_server="kali-forensics",
        tool_name="exiftool_read",
    )
    emitter.emit_sync(inv)
    lines = [json.loads(line) for line in jsonl.read_text().splitlines() if line.strip()]
    assert len(lines) == 2
    assert lines[0] == {"existing": True}
    assert lines[1]["tool_name"] == "exiftool_read"


# ──────────────────────── HTTP POST contract ─────────────────────────


@respx.mock
def test_emitter_posts_to_orchestrator(tmp_path: Path):
    reset_emitter()
    jsonl = tmp_path / "ai_invocations.jsonl"
    route = respx.post("http://orch.test/audit/ai-invocation").mock(
        return_value=httpx.Response(201, json={"id": "abc", "status": "logged"})
    )
    emitter = AuditEmitter(orchestrator_url="http://orch.test", jsonl_path=jsonl)
    inv = AIInvocation(
        ai_actor="claude-code",
        mcp_server="kali-forensics",
        tool_name="yara_scan",
    )
    result = emitter.emit_sync(inv)
    assert route.called
    assert result["orchestrator"] is True
    body = json.loads(route.calls.last.request.content)
    assert body["tool_name"] == "yara_scan"


@respx.mock
def test_emitter_orchestrator_failure_does_not_break_jsonl(tmp_path: Path):
    """If orchestrator is down, JSONL must still capture the record."""
    reset_emitter()
    jsonl = tmp_path / "ai_invocations.jsonl"
    respx.post("http://orch.test/audit/ai-invocation").mock(
        return_value=httpx.Response(503, text="db down")
    )
    emitter = AuditEmitter(orchestrator_url="http://orch.test", jsonl_path=jsonl)
    inv = AIInvocation(
        ai_actor="claude-code",
        mcp_server="kali-forensics",
        tool_name="binwalk_scan",
    )
    result = emitter.emit_sync(inv)
    assert result["orchestrator"] is False
    assert result["jsonl"] is True
    assert jsonl.exists()


# ─────────────────── MCP shared decorator (stdlib) ───────────────────


@pytest.fixture
def mcp_audit_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Import the MCP _common.audit module fresh, with audit JSONL
    pointed at a temp file and the orchestrator URL pointed nowhere."""
    monkeypatch.setenv("DFIR_AI_ACTOR", "test-host")
    monkeypatch.setenv("DFIR_ORCHESTRATOR_URL", "http://nonexistent.invalid:1")
    monkeypatch.setenv("DFIR_AUDIT_JSONL", str(tmp_path / "mcp_inv.jsonl"))
    monkeypatch.delenv("DFIR_AUDIT_DISABLED", raising=False)

    # Force a clean import each test so env vars are picked up.
    sys.modules.pop("_common.audit", None)
    sys.modules.pop("_common", None)
    from _common import audit as mod  # type: ignore[import-not-found]

    return mod, tmp_path / "mcp_inv.jsonl"


def test_mcp_decorator_records_successful_call(mcp_audit_module):
    mod, jsonl = mcp_audit_module

    @mod.audited(server="kali-forensics")
    def fake_tool(image_path: str, plugin: str) -> dict:
        return {"stdout": "PsList output\n", "stderr": "", "returncode": 0}

    out = fake_tool("/evidence/mem.raw", plugin="windows.pslist.PsList")
    assert out["returncode"] == 0
    assert jsonl.exists()
    record = json.loads(jsonl.read_text().strip())
    assert record["tool_name"] == "fake_tool"
    assert record["mcp_server"] == "kali-forensics"
    assert record["ai_actor"] == "test-host"
    assert record["exit_code"] == 0
    assert record["tool_args"] == {
        "image_path": "/evidence/mem.raw",
        "plugin": "windows.pslist.PsList",
    }
    # input hash must match canonical JSON of args
    canonical = json.dumps(record["tool_args"], sort_keys=True, separators=(",", ":"))
    expected = hash_text(canonical)
    assert record["input_sha256"] == expected


def test_mcp_decorator_records_exception(mcp_audit_module):
    mod, jsonl = mcp_audit_module

    @mod.audited(server="osint")
    def broken_tool(target: str) -> dict:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        broken_tool("example.com")

    record = json.loads(jsonl.read_text().strip())
    assert record["error"].startswith("RuntimeError: boom")
    assert record["tool_name"] == "broken_tool"


def test_mcp_decorator_disabled_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("DFIR_AUDIT_DISABLED", "1")
    monkeypatch.setenv("DFIR_AUDIT_JSONL", str(tmp_path / "off.jsonl"))
    sys.modules.pop("_common.audit", None)
    sys.modules.pop("_common", None)
    from _common import audit as mod  # type: ignore[import-not-found]

    @mod.audited(server="osint")
    def t(x: int) -> int:
        return x + 1

    assert t(5) == 6
    assert not (tmp_path / "off.jsonl").exists()


def test_mcp_decorator_preserves_signature_for_fastmcp(mcp_audit_module):
    """FastMCP introspects __name__/__doc__/annotations — wrapper must
    forward them via functools.wraps."""
    import inspect

    mod, _ = mcp_audit_module

    @mod.audited(server="osint")
    def whois_lookup(target: str) -> dict:
        """Look up WHOIS for target."""
        return {"target": target}

    assert whois_lookup.__name__ == "whois_lookup"
    assert "WHOIS" in (whois_lookup.__doc__ or "")
    sig = inspect.signature(whois_lookup)
    assert list(sig.parameters) == ["target"]


# ───────────────── Backward compat: ForensicPayload field ────────────


def test_forensic_payload_default_ai_invocations_is_empty():
    from dfireballz.models.forensic_payload import AIInvocationEntry, ForensicPayload

    payload = ForensicPayload(session_id="s1", target="/evidence/x")
    assert payload.ai_invocations == []
    payload.ai_invocations.append(
        AIInvocationEntry(
            ai_actor="claude-code",
            mcp_server="kali-forensics",
            tool_name="volatility_run",
        )
    )
    assert payload.ai_invocations[0].tool_name == "volatility_run"


def test_forensic_payload_round_trip_with_invocations():
    from dfireballz.models.forensic_payload import AIInvocationEntry, ForensicPayload

    payload = ForensicPayload(
        session_id="s1",
        target="/evidence/x",
        ai_invocations=[
            AIInvocationEntry(
                ai_actor="claude-code",
                mcp_server="osint",
                tool_name="whois_lookup",
                tool_args={"target": "example.com"},
                input_sha256="a" * 64,
            )
        ],
    )
    raw = payload.to_dict()
    restored = ForensicPayload(**raw)
    assert restored.ai_invocations[0].tool_name == "whois_lookup"
    assert restored.ai_invocations[0].input_sha256 == "a" * 64


# ───────────────── teardown — drop singleton between tests ───────────


@pytest.fixture(autouse=True)
def _reset_emitter_singleton():
    reset_emitter()
    yield
    reset_emitter()


# ───────────────── log_chain_of_custody still appends JSONL ──────────


@pytest.mark.asyncio
async def test_log_chain_of_custody_still_appends_jsonl(tmp_path: Path):
    """Regression: extending the handler to call the orchestrator must
    not break the existing JSONL contract."""
    from dfireballz.config import Settings
    from dfireballz.mcp.server import _dispatch

    mock_settings = Settings(cases_dir=tmp_path)
    with patch("dfireballz.config.settings", mock_settings):
        result = await _dispatch(
            "log_chain_of_custody",
            {
                "action": "hash_verify",
                "evidence_id": "/evidence/x",
                "description": "test",
                "tool_used": "sha256sum",
            },
        )
    data = json.loads(result)
    assert data["status"] == "logged"
    coc_file = tmp_path / "chain_of_custody.jsonl"
    assert coc_file.exists()
    entry = json.loads(coc_file.read_text().strip())
    assert entry["evidence_id"] == "/evidence/x"
