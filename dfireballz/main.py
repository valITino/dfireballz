"""DFIReballz CLI — Click-based command-line interface."""

from __future__ import annotations

import asyncio
import json

import click
from rich.table import Table

import dfireballz
from dfireballz.config import settings
from dfireballz.utils.catalog import load_tools_catalog
from dfireballz.utils.logger import (
    console as rich_console,
)
from dfireballz.utils.logger import (
    get_logger,
    print_banner,
    print_forensic_banner,
    setup_logging,
)

logger = get_logger("cli")


def _run_async(coro):  # type: ignore[no-untyped-def]
    """Run an async coroutine from synchronous Click handlers."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging.")
def cli(debug: bool) -> None:
    """DFIReballz — AI-Native Digital Forensics Platform."""
    level = "DEBUG" if debug else settings.log_level
    setup_logging(level)


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------


@cli.command()
def version() -> None:
    """Show the DFIReballz version."""
    print_banner()
    rich_console.print(f"[info]Version:[/info] {dfireballz.__version__}")
    rich_console.print(f"[info]Database:[/info] {settings.database_url}")
    rich_console.print(f"[info]Reports:[/info] {settings.reports_dir}")
    rich_console.print(f"[info]Results:[/info] {settings.results_dir}")


# ---------------------------------------------------------------------------
# catalog
# ---------------------------------------------------------------------------


@cli.command()
def catalog() -> None:
    """Display the available forensic tools catalogue."""
    tools = load_tools_catalog()

    table = Table(title="Forensic Tool Catalogue")
    table.add_column("Category", style="cyan")
    table.add_column("Tool", style="green")
    table.add_column("Description", style="white")
    table.add_column("Container", style="yellow")

    for entry in tools:
        table.add_row(
            entry.get("category", ""),
            entry.get("tool_name", ""),
            entry.get("description", ""),
            entry.get("container", ""),
        )

    rich_console.print(table)


# ---------------------------------------------------------------------------
# run-tool
# ---------------------------------------------------------------------------


@cli.command("run-tool")
@click.option("--category", "-c", required=True, help="Tool category (memory, disk, network, ...).")
@click.option("--tool", "-t", required=True, help="Tool name (volatility3, tshark, yara, ...).")
@click.option(
    "--params",
    "-p",
    required=True,
    help="JSON string of tool parameters.",
)
def run_tool(category: str, tool: str, params: str) -> None:
    """Run a single forensic tool via the docker exec backend."""
    print_forensic_banner()

    try:
        params_dict = json.loads(params)
    except json.JSONDecodeError as exc:
        rich_console.print(f"[error]Invalid JSON in --params: {exc}[/error]")
        raise SystemExit(1) from exc

    _run_async(_do_run_tool(category, tool, params_dict))


async def _do_run_tool(category: str, tool: str, params: dict) -> None:
    from dfireballz.backends import get_backend

    backend = await get_backend()
    try:
        result = await backend.run_tool(category, tool, params)
        rich_console.print(f"[success]Tool {category}/{tool} completed.[/success]")
        rich_console.print(json.dumps(result.model_dump(), indent=2, default=str))
    finally:
        await backend.close()


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--session", "-s", required=True, help="Session ID or results JSON file path.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["pdf", "html", "md"]),
    default="pdf",
    help="Report format.",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path.")
@click.option(
    "--both",
    is_flag=True,
    default=False,
    help="Generate both .md and .pdf reports in the organized reports folder.",
)
def report(session: str, fmt: str, output: str | None, both: bool) -> None:
    """Generate a forensic report from session results."""
    _run_async(_do_report(session, fmt, output, both))


async def _do_report(session_id: str, fmt: str, output: str | None, both: bool = False) -> None:
    import re
    from pathlib import Path

    from dfireballz.models.base import ForensicSession

    safe_session_id = re.sub(r"[^a-zA-Z0-9_\-]", "", session_id)
    if not safe_session_id:
        rich_console.print("[error]Invalid session ID.[/error]")
        raise SystemExit(1)

    session_path = Path(session_id)
    if session_path.exists():
        resolved = session_path.resolve()
        results_resolved = settings.results_dir.resolve()
        cwd_resolved = Path.cwd().resolve()
        if not (
            str(resolved).startswith(str(results_resolved))
            or str(resolved).startswith(str(cwd_resolved))
        ):
            rich_console.print("[error]Session file path is outside allowed directories.[/error]")
            raise SystemExit(1)
    else:
        results_dir = settings.results_dir
        matches = list(results_dir.glob(f"*{safe_session_id}*"))
        if not matches:
            rich_console.print(f"[error]Session '{safe_session_id}' not found.[/error]")
            raise SystemExit(1)
        session_path = matches[0]

    session_data = ForensicSession.model_validate_json(session_path.read_text())

    if both:
        from dfireballz.reporting.md_generator import generate_md_report
        from dfireballz.reporting.pdf_generator import generate_pdf_report

        md_out = generate_md_report(session_data)
        rich_console.print(f"[success]Markdown report generated: {md_out}[/success]")
        pdf_out = generate_pdf_report(session_data)
        rich_console.print(f"[success]PDF report generated: {pdf_out}[/success]")
    elif fmt == "md":
        from dfireballz.reporting.md_generator import generate_md_report

        out = generate_md_report(session_data, output)
        rich_console.print(f"[success]Report generated: {out}[/success]")
    elif fmt == "pdf":
        from dfireballz.reporting.pdf_generator import generate_pdf_report

        out = generate_pdf_report(session_data, output)
        rich_console.print(f"[success]Report generated: {out}[/success]")
    else:
        from dfireballz.reporting.html_generator import generate_html_report

        out = generate_html_report(session_data, output)
        rich_console.print(f"[success]Report generated: {out}[/success]")


# ---------------------------------------------------------------------------
# templates
# ---------------------------------------------------------------------------


@cli.group()
def templates() -> None:
    """Manage investigation templates for autonomous forensics."""


@templates.command("list")
def templates_list() -> None:
    """List available investigation templates."""
    from dfireballz.prompts import list_templates

    tpl_list = list_templates()

    table = Table(title="Investigation Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("File", style="dim")

    for tpl in tpl_list:
        table.add_row(tpl["name"], tpl["title"], tpl["file"])

    rich_console.print(table)
    rich_console.print(
        "\n[info]Use 'dfireballz templates show <name>' to view a template.[/info]"
    )


@templates.command("show")
@click.argument("name")
@click.option("--target", "-t", default=None, help="Replace [TARGET] placeholders.")
def templates_show(name: str, target: str | None) -> None:
    """Display an investigation template by name."""
    from dfireballz.prompts import load_template

    try:
        content = load_template(name, target=target)
    except (ValueError, FileNotFoundError) as exc:
        rich_console.print(f"[error]{exc}[/error]")
        raise SystemExit(1) from exc

    from rich.markdown import Markdown

    rich_console.print(Markdown(content))


# ---------------------------------------------------------------------------
# mcp serve
# ---------------------------------------------------------------------------


@cli.command("mcp")
def mcp_serve() -> None:
    """Start the DFIReballz MCP server (stdio transport).

    Connect any MCP-compatible LLM to DFIReballz for autonomous forensics.
    """
    _run_async(_do_mcp_serve())


async def _do_mcp_serve() -> None:
    from dfireballz.mcp.server import run_server

    await run_server()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
