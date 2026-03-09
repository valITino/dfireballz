"""Tests for report path resolution."""

from datetime import UTC, datetime

from dfireballz.reporting.paths import _slugify, get_report_path


def test_slugify():
    assert _slugify("example.com") == "example-com"
    assert _slugify("CASE 2026-001") == "case-2026-001"
    assert _slugify("a" * 100, max_len=10) == "a" * 10


def test_get_report_path():
    dt = datetime(2026, 3, 9, tzinfo=UTC)
    path = get_report_path("case-2026-001", "md", date=dt)
    assert "report-case-2026-001-09032026.md" in str(path)
    assert "reports-09032026" in str(path)


def test_get_report_path_pdf():
    dt = datetime(2026, 3, 9, tzinfo=UTC)
    path = get_report_path("disk-image", "pdf", date=dt)
    assert str(path).endswith(".pdf")
