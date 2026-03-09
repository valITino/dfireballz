"""Rich-powered structured logging for DFIReballz."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "banner": "bold magenta",
        "forensic": "bold blue",
    }
)

console = Console(theme=_THEME, stderr=True)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure the root dfireballz logger with Rich output."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    handler.setLevel(numeric_level)

    logger = logging.getLogger("dfireballz")
    logger.setLevel(numeric_level)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the dfireballz namespace."""
    return logging.getLogger(f"dfireballz.{name}")


def print_banner() -> None:
    """Print the DFIReballz startup banner."""
    from dfireballz import __version__

    banner = rf"""
[banner]
 ____  _____ ___ ____       _           _ _
|  _ \|  ___|_ _|  _ \ ___ | |__   __ _| | |____
| | | | |_   | || |_) / _ \| '_ \ / _` | | |_  /
| |_| |  _|  | ||  _ <  __/| |_) | (_| | | |/ /
|____/|_|   |___|_| \_\___||_.__/ \__,_|_|_/___|

 AI-Native Digital Forensics Platform v{__version__}
[/banner]
"""
    console.print(banner)


def print_forensic_banner() -> None:
    """Print a notice banner before forensic operations."""
    divider = "=" * 70
    console.print(
        f"\n[forensic]"
        f"{divider}\n"
        f"  DIGITAL FORENSICS MODE\n"
        f"  All evidence access is logged to the chain of custody.\n"
        f"  Ensure proper authorization before analyzing evidence.\n"
        f"{divider}"
        f"[/forensic]\n"
    )
