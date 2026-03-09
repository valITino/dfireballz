"""Custom exceptions for DFIReballz."""

from __future__ import annotations


class DfireballzError(Exception):
    """Base exception for all DFIReballz errors."""


class ReportingError(DfireballzError):
    """Raised on report generation failures."""


class ChainOfCustodyError(DfireballzError):
    """Raised when chain of custody logging fails."""


class BackendError(DfireballzError):
    """Raised when a tool backend encounters an error."""


class ModuleError(DfireballzError):
    """Raised when a custom module encounters an error."""
