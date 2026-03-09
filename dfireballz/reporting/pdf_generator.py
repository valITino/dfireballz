"""Generate PDF reports from forensic sessions or payloads using WeasyPrint."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from dfireballz.exceptions import ReportingError
from dfireballz.models.base import ForensicSession
from dfireballz.reporting.html_generator import generate_html_report

if TYPE_CHECKING:
    from dfireballz.models.forensic_payload import ForensicPayload

logger = logging.getLogger("dfireballz.reporting.pdf_generator")


def generate_pdf_report(
    session: ForensicSession,
    output_path: str | None = None,
) -> Path:
    """Generate a PDF report from a forensic session.

    First generates an HTML report, then converts it to PDF via WeasyPrint.

    Args:
        session: Completed forensic session with findings.
        output_path: Override output file path.

    Returns:
        Path to the generated PDF file.
    """
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise ReportingError(
            "weasyprint is required for PDF generation. "
            "Install it with: pip install weasyprint"
        ) from exc

    html_path = generate_html_report(session)

    if output_path:
        pdf_path = Path(output_path)
    else:
        pdf_path = html_path.with_suffix(".pdf")

    try:
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
    except Exception as exc:
        raise ReportingError(f"PDF generation failed: {exc}") from exc

    logger.info("PDF report generated: %s", pdf_path)
    return pdf_path
