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
make setup              # First-time setup
make dev                # Start development environment (hot-reload)
make test               # Run unit tests
make test-smoke         # Run container smoke tests (docker exec probes)
make test-security      # Run security scans (Trivy + Bandit)
make mcp-health-check   # Check MCP server container health
make shell-kali         # Debug Kali container
make shell-osint        # Debug OSINT container
make shell-netforensics # Debug Wireshark/tcpdump container
make claude-code        # Run Claude Code in Docker (interactive)
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
- Non-root users in all containers (MCP: `investigator`, Claude Code: `claude`)
- `security_opt: no-new-privileges:true` on every container
- `ENTRYPOINT []` on all MCP containers (prevents inherited entrypoint interference)
- `.dockerignore` in every MCP server directory
- Multi-stage builds where applicable
- Health checks on every container
- Evidence volumes read-only in MCP containers

### Adding a New MCP Server

1. Create `mcp-servers/your-server/` with `Dockerfile`, `server.py`, `README.md`, `.dockerignore`
2. Use FastMCP (`from fastmcp import FastMCP`)
3. Dockerfile must include: non-root user, health check, `ENTRYPOINT []`
4. Add `security_opt: no-new-privileges:true` in `docker-compose.yml`
5. Add to all MCP config files in `config/mcp_hosts/`
6. Update `config/mcpo.json`
7. Document in main README.md MCP reference table
8. Add unit tests
9. Run `make configure-mcp` to regenerate `.mcp.json`

## Pull Request Requirements

- All CI checks must pass (lint, type check, pytest, pip-audit, Bandit, Docker build, Trivy)
- No critical security vulnerabilities
- Chain of custody logging preserved
- Documentation updated for user-facing changes
- Container smoke tests pass (`make test-smoke`)
