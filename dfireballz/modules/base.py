"""Base module class for DFIReballz extensions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseModule(ABC):
    """Interface for DFIReballz extension modules."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    async def run(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the module with given parameters."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if this module is operational."""
