"""Tests for prompt template management."""

import pytest

from dfireballz.prompts import list_templates, load_template


def test_list_templates():
    templates = list_templates()
    assert len(templates) >= 10
    names = [t["name"] for t in templates]
    assert "complete-investigation" in names
    assert "malware-analysis" in names
    assert "full-investigation" in names
    assert "incident-response" in names


def test_load_template():
    content = load_template("malware-analysis")
    assert "Malware" in content
    assert "[TARGET]" in content


def test_load_template_with_target():
    content = load_template("malware-analysis", target="/evidence/sample.exe")
    assert "/evidence/sample.exe" in content
    assert "[TARGET]" not in content


def test_load_unknown_template():
    with pytest.raises(ValueError, match="Unknown template"):
        load_template("nonexistent")


def test_all_templates_loadable():
    templates = list_templates()
    for tpl in templates:
        content = load_template(tpl["name"])
        assert len(content) > 50
