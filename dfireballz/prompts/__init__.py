"""Prompt management for DFIReballz investigation templates."""

from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent
_TEMPLATES_DIR = _PROMPTS_DIR / "templates"

# Template registry: slug -> filename
TEMPLATES = {
    "full-investigation": "full-investigation.md",
    "malware-analysis": "malware-analysis.md",
    "ransomware-investigation": "ransomware-investigation.md",
    "phishing-investigation": "phishing-investigation.md",
    "network-forensics": "network-forensics.md",
    "osint-person": "osint-person.md",
    "osint-domain": "osint-domain.md",
    "memory-forensics": "memory-forensics.md",
    "incident-response": "incident-response.md",
}


def load_template(name: str, target: str | None = None) -> str:
    """Load an investigation template by name.

    Args:
        name: Template slug (e.g. ``"malware-analysis"``).
        target: If provided, replaces ``[TARGET]`` placeholders in the template.

    Returns:
        The template content as a string.

    Raises:
        FileNotFoundError: If the template does not exist.
        ValueError: If the template name is unknown.
    """
    filename = TEMPLATES.get(name)
    if filename is None:
        available = ", ".join(sorted(TEMPLATES.keys()))
        raise ValueError(f"Unknown template: {name!r}. Available: {available}")

    path = _TEMPLATES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")

    content = path.read_text(encoding="utf-8")
    if target is not None:
        content = content.replace("[TARGET]", target)
        content = content.replace("[EVIDENCE_PATH]", target)
    return content


def list_templates() -> list[dict[str, str]]:
    """Return metadata for all available investigation templates.

    Returns:
        List of dicts with ``name``, ``file``, and ``title`` keys.
    """
    templates = []
    for slug, filename in sorted(TEMPLATES.items()):
        path = _TEMPLATES_DIR / filename
        title = slug.replace("-", " ").title()
        if path.exists():
            first_line = path.read_text(encoding="utf-8").split("\n")[0]
            if first_line.startswith("# "):
                title = first_line[2:].strip()
        templates.append({"name": slug, "file": filename, "title": title})
    return templates


def load_playbook() -> str:
    """Load the Claude forensic investigation playbook."""
    path = _PROMPTS_DIR / "claude_playbook.md"
    return path.read_text(encoding="utf-8")
