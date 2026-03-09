"""Tests for the MCP server tool dispatch."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from dfireballz.mcp.server import _dispatch


@pytest.mark.asyncio
async def test_list_tools():
    result = await _dispatch("list_tools", {})
    data = json.loads(result)
    assert "tools" in data
    assert len(data["tools"]) > 0


@pytest.mark.asyncio
async def test_get_payload_schema():
    result = await _dispatch("get_payload_schema", {})
    schema = json.loads(result)
    assert "properties" in schema
    assert "session_id" in schema["properties"]


@pytest.mark.asyncio
async def test_list_templates():
    result = await _dispatch("list_templates", {})
    data = json.loads(result)
    assert "templates" in data
    assert len(data["templates"]) >= 9


@pytest.mark.asyncio
async def test_get_template():
    result = await _dispatch("get_template", {"name": "malware-analysis"})
    assert "Malware" in result


@pytest.mark.asyncio
async def test_get_template_unknown():
    result = await _dispatch("get_template", {"name": "nonexistent"})
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_aggregate_results_invalid():
    result = await _dispatch("aggregate_results", {"payload": "not a dict"})
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_aggregate_results_missing_fields():
    result = await _dispatch("aggregate_results", {"payload": {"foo": "bar"}})
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_unknown_tool():
    result = await _dispatch("nonexistent_tool", {})
    assert "Unknown tool" in result


@pytest.mark.asyncio
async def test_aggregate_results_valid():
    """aggregate_results with valid payload should persist session file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from dfireballz.config import Settings

        mock_settings = Settings(results_dir=tmpdir, cases_dir=tmpdir)
        with patch("dfireballz.config.settings", mock_settings):
            result = await _dispatch("aggregate_results", {
                "payload": {
                    "session_id": "agg-test-001",
                    "target": "/evidence/test.img",
                    "case_id": "CASE-AGG",
                }
            })

        data = json.loads(result)
        assert data["status"] == "ok"
        assert data["session_id"] == "agg-test-001"
        # Session file should exist
        session_file = Path(data["session_file"])
        assert session_file.exists()
        stored = json.loads(session_file.read_text())
        assert stored["target"] == "/evidence/test.img"


@pytest.mark.asyncio
async def test_log_chain_of_custody():
    """log_chain_of_custody should append a JSONL entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from dfireballz.config import Settings

        mock_settings = Settings(cases_dir=tmpdir)
        with patch("dfireballz.config.settings", mock_settings):
            result = await _dispatch("log_chain_of_custody", {
                "action": "hash_verify",
                "evidence_id": "/evidence/test.img",
                "description": "Verified SHA256 hash",
                "tool_used": "sha256sum",
            })

        data = json.loads(result)
        assert data["status"] == "logged"
        assert data["entry"]["action"] == "hash_verify"

        # Verify JSONL file was created
        coc_file = Path(tmpdir) / "chain_of_custody.jsonl"
        assert coc_file.exists()
        entry = json.loads(coc_file.read_text().strip())
        assert entry["evidence_id"] == "/evidence/test.img"
        assert entry["actor"] == "mcp_host"


@pytest.mark.asyncio
async def test_get_template_with_target():
    """get_template should replace [TARGET] placeholders."""
    result = await _dispatch("get_template", {
        "name": "malware-analysis",
        "target": "evil.exe",
    })
    assert "evil.exe" in result
    assert "[TARGET]" not in result
