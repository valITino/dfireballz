# DFIReballz — Claude Code Instructions

## Project Purpose
DFIReballz is a digital forensics and cybercrime investigation platform. All code decisions
should reflect the context of a professional forensic investigator.

## Development Commands
- `make dev` — Start development environment
- `make test` — Run all tests
- `make test-security` — Security scan
- `make shell-kali` — Debug Kali forensics container

## Architecture
- **MCP Transport: stdio only.** Every MCP server runs `mcp.run(transport="stdio")`.
  The AI host (Claude Code / Claude Desktop / MCPHost) connects via `docker exec -i <container> <cmd>`.
  No HTTP ports, no proxy, no gateway for direct AI host connections.
- **Ollama note:** Ollama has NO native MCP support. Use MCPHost (`mark3labs/mcphost`) or
  Open WebUI + mcpo proxy as the bridge. MCPHost model syntax: `mcphost -m ollama/qwen3:8b --config ~/.mcphost.yml`
- Orchestrator API (port 8800) manages cases, evidence, and playbooks
- UI (port 3000) is the investigator-facing dashboard
- For Open WebUI scenario: mcpo container (port 8812) exposes MCP servers as OpenAPI endpoints.
  The mcpo container needs `/var/run/docker.sock` mounted to run `docker exec` commands.

## Code Standards
- All Python code must be type-annotated
- All MCP tool inputs must be validated with Pydantic
- All tool subprocess calls must use `subprocess.run(args_list, shell=False)`
- Every evidence access must create a chain_of_custody_log entry
- Never use shell=True in subprocess calls
- Never log API keys or secrets

## Adding a New MCP Server
1. Create `mcp-servers/new-server/` directory
2. Write Dockerfile (non-root user, health check required)
3. Write `server.py` using FastMCP
4. Register in `docker-compose.yml` and generate updated `.mcp.json` via `make configure-mcp`
5. Add service to `docker-compose.yml`
6. Document tools in README.md MCP reference table
7. Add unit tests
