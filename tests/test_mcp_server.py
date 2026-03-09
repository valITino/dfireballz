"""Tests for the MCP server tool dispatch."""

import json

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
