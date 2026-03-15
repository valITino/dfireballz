# Reporting — Directory Rules

## Report Generators

Three output formats — HTML, Markdown, PDF. All consume `ForensicPayload`.

- HTML: `html_generator.py` — uses Jinja2 templates
- Markdown: `md_generator.py` — plain text generation
- PDF: `pdf_generator.py` — uses WeasyPrint (HTML-to-PDF)

## Rules

- Never break the `ForensicPayload` → report pipeline
- Reports MUST include: executive summary, evidence list, IoC table, timeline, chain of custody log
- Output to `/reports/<case-id>/` (containers) or `./reports/` (host)
- All timestamps in UTC ISO 8601
- Do not embed API keys or secrets in reports
