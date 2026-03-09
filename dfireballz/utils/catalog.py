"""Forensic tool catalogue loader and helpers."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any


def load_tools_catalog() -> list[dict[str, Any]]:
    """Load the forensic tools catalogue from the bundled JSON file.

    Returns a list of dicts with keys: category, tool_name, description, container.
    """
    ref = resources.files("dfireballz.data").joinpath("tools_catalog.json")
    text = ref.read_text(encoding="utf-8")
    catalog: list[dict[str, Any]] = json.loads(text)
    return catalog


def catalog_to_tool_list_string(catalog: list[dict[str, Any]]) -> str:
    """Format the catalogue as a readable string for the LLM.

    Groups tools by category, matching the format the AI host expects.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    for entry in catalog:
        cat = entry.get("category", "other")
        groups.setdefault(cat, []).append(entry)

    lines: list[str] = []
    for category, tools in groups.items():
        label = category.replace("_", " ").title()
        lines.append(f"{label}:")
        for tool in tools:
            lines.append(f"  - {tool['tool_name']}: {tool['description']}")
        lines.append("")

    return "\n".join(lines)


def resolve_tool_names(
    catalog: list[dict[str, Any]],
    names: list[str],
) -> list[dict[str, str]]:
    """Resolve a list of tool names (or category names) to (category, tool_name) pairs.

    Accepts both exact tool names (e.g. 'volatility3') and category names (e.g. 'memory'),
    which expand to all tools in that category.

    Raises ValueError if a name cannot be resolved.
    """
    by_tool: dict[str, dict[str, str]] = {}
    by_category: dict[str, list[dict[str, str]]] = {}
    for entry in catalog:
        key = {"category": entry["category"], "tool_name": entry["tool_name"]}
        by_tool[entry["tool_name"]] = key
        by_category.setdefault(entry["category"], []).append(key)

    resolved: list[dict[str, str]] = []
    seen: set[str] = set()

    for name in names:
        name_lower = name.strip().lower()
        if name_lower in by_tool:
            tool_key = f"{by_tool[name_lower]['category']}/{by_tool[name_lower]['tool_name']}"
            if tool_key not in seen:
                resolved.append(by_tool[name_lower])
                seen.add(tool_key)
        elif name_lower in by_category:
            for entry in by_category[name_lower]:
                tool_key = f"{entry['category']}/{entry['tool_name']}"
                if tool_key not in seen:
                    resolved.append(entry)
                    seen.add(tool_key)
        else:
            raise ValueError(
                f"Unknown tool or category: {name!r}. "
                f"Run 'dfireballz catalog' to see available tools."
            )

    return resolved
