"""Tests for the forensic tools catalogue."""

from dfireballz.utils.catalog import (
    catalog_to_tool_list_string,
    load_tools_catalog,
    resolve_tool_names,
)


def test_load_catalog():
    catalog = load_tools_catalog()
    assert len(catalog) > 0
    assert all("tool_name" in entry for entry in catalog)
    assert all("category" in entry for entry in catalog)


def test_catalog_has_expected_tools():
    catalog = load_tools_catalog()
    tool_names = [e["tool_name"] for e in catalog]
    assert "volatility3" in tool_names
    assert "tshark" in tool_names
    assert "yara" in tool_names
    assert "capa" in tool_names


def test_catalog_to_string():
    catalog = load_tools_catalog()
    text = catalog_to_tool_list_string(catalog)
    assert "volatility3" in text
    assert len(text) > 100


def test_resolve_tool_names():
    catalog = load_tools_catalog()
    resolved = resolve_tool_names(catalog, ["volatility3", "tshark"])
    assert len(resolved) == 2


def test_resolve_category():
    catalog = load_tools_catalog()
    resolved = resolve_tool_names(catalog, ["memory"])
    assert len(resolved) >= 2  # volatility3, bulk_extractor


def test_resolve_unknown_raises():
    catalog = load_tools_catalog()
    try:
        resolve_tool_names(catalog, ["nonexistent_tool"])
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
