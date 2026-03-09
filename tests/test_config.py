"""Tests for configuration loading."""

from pathlib import Path

from dfireballz.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.postgres_user == "dfireballz"
    assert s.log_level == "INFO"
    assert isinstance(s.results_dir, Path)
    assert isinstance(s.reports_dir, Path)


def test_settings_extra_ignored():
    s = Settings(UNKNOWN_FIELD="test")
    assert not hasattr(s, "UNKNOWN_FIELD")
