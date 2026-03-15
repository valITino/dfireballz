# Backends — Directory Rules

## Tool Execution

The `docker.py` backend executes MCP tools via `docker exec -i`. The `_TOOL_COMMANDS` dict maps tool names to their container + command.

- When adding a new MCP server, register its tools in `_TOOL_COMMANDS`
- All tool execution MUST use `subprocess.run(args_list, shell=False)`
- Never hardcode container names — use the mapping
- Handle Docker exec failures gracefully (container not running, timeout, etc.)

## Adding a New Backend

If implementing a non-Docker backend (e.g., local, SSH):
1. Subclass `ToolBackend` from `base.py`
2. Implement `execute_tool()` and `list_available_tools()`
3. Register in `dfireballz/config.py`
