# MCP Servers — Directory Rules

## Mandatory

- All subprocess calls MUST use `subprocess.run(args_list, shell=False)` — never `shell=True`
- All tool inputs MUST be validated with Pydantic models
- All evidence access MUST create a `chain_of_custody_log` entry via the orchestrator API
- All servers MUST use `mcp.run(transport="stdio")` — no HTTP, no SSE
- Never log API keys or secrets — use `***` masking if you must log key presence

## Server Pattern

Every `server.py` follows this structure:
```python
from fastmcp import FastMCP
mcp = FastMCP("server-name")

@mcp.tool()
def tool_name(param: str) -> str:
    """Tool description."""
    result = subprocess.run([...], shell=False, capture_output=True, text=True)
    return result.stdout

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## Testing Changes

Server code is volume-mounted read-only. Restart the container to pick up changes:
```bash
make restart-<service>   # e.g. make restart-kali
```

No image rebuild needed unless you modify a Dockerfile.

## Path Conventions

- Evidence: `/evidence/` (read-only)
- Cases: `/cases/` (read-write)
- Reports: `/reports/` (read-write)
- Output: `/output/` (read-write — host-visible investigation output)
