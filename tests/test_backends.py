"""Tests for tool execution backends."""

import pytest

from dfireballz.backends.base import ToolResult
from dfireballz.backends.docker import DockerBackend


def test_tool_result_defaults():
    r = ToolResult()
    assert r.success is True
    assert not r.has_errors


def test_tool_result_with_errors():
    r = ToolResult(success=False, errors=["Connection failed"])
    assert r.has_errors


@pytest.mark.asyncio
async def test_docker_backend_list_tools():
    backend = DockerBackend()
    tools = await backend.list_tools()
    assert len(tools) > 0
    tool_names = [t["tool"] for t in tools]
    assert "volatility3" in tool_names


@pytest.mark.asyncio
async def test_docker_backend_unknown_tool():
    backend = DockerBackend()
    result = await backend.run_tool("test", "nonexistent_tool", {})
    assert not result.success
    assert "not supported" in result.errors[0]
