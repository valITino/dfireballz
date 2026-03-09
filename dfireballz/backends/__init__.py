"""Tool execution backends — Docker exec or auto-detect."""

from dfireballz.backends.base import ToolBackend, ToolResult
from dfireballz.backends.docker import DockerBackend

__all__ = [
    "ToolBackend",
    "ToolResult",
    "DockerBackend",
    "get_backend",
]


async def get_backend() -> ToolBackend:
    """Return the best available backend (Docker exec).

    The caller is responsible for calling ``await backend.close()`` when done.
    """
    docker = DockerBackend()
    await docker.connect()
    return docker
