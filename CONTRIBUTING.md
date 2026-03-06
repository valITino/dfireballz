# Contributing to DFIReballz

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run `make setup` to configure your development environment
4. Make your changes
5. Run `make test` and `make test-security`
6. Commit and push
7. Open a Pull Request

## Development Workflow

```bash
make setup          # First-time setup
make dev            # Start development environment (hot-reload)
make test           # Run unit tests
make test-security  # Run security scans
make shell-kali     # Debug Kali container
```

## Code Standards

### Python
- Type annotations on all functions
- Pydantic models for all input validation
- `subprocess.run(args_list, shell=False)` — never `shell=True`
- Every evidence access must create a CoC log entry
- Never log secrets or API keys

```python
# BAD — shell injection risk, violates project rules
subprocess.run(f"volatility3 -f {dump_path} windows.pslist", shell=True)

# GOOD — safe argument list, no shell interpretation
subprocess.run(
    ["volatility3", "-f", dump_path, "windows.pslist"],
    capture_output=True, text=True, timeout=300
)
```

### Docker
- Non-root users in all containers
- Multi-stage builds where applicable
- Health checks on every container
- Evidence volumes read-only in MCP containers

### Adding a New MCP Server

1. Create `mcp-servers/your-server/` with `Dockerfile`, `server.py`, `README.md`
2. Use FastMCP (`from fastmcp import FastMCP`)
3. Add to `docker-compose.yml`
4. Add to all MCP config files in `config/mcp_hosts/`
5. Update `config/mcpo.json`
6. Document in main README.md
7. Add unit tests

## Pull Request Requirements

- All CI checks must pass
- No critical security vulnerabilities
- Chain of custody logging preserved
- Documentation updated for user-facing changes
