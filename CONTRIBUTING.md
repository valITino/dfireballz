# Contributing to DFIReballz

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run `make setup` to configure your development environment
4. Install the dfireballz package: `make install-dev`
5. Make your changes
6. Run `make lint && make test-pkg && make test-security`
7. Commit and push
8. Open a Pull Request

## Development Workflow

```bash
# First-time setup
make setup              # Interactive Docker setup
make venv               # Create Python venv with dfireballz[dev]

# Development
make dev                # Start Docker environment (hot-reload)
make install-dev        # Install package with dev dependencies

# Testing & Quality
make test-pkg           # Run dfireballz package tests
make test               # Run all tests (package + orchestrator)
make test-smoke         # Run container smoke tests
make test-security      # Trivy + Bandit scan
make lint               # Run ruff linter
make format             # Auto-format code with ruff
make typecheck          # Run mypy type checking
make audit              # Run pip-audit dependency scan

# Debug containers
make shell-kali         # Debug Kali container
make shell-osint        # Debug OSINT container
make shell-netforensics # Debug network forensics container
make shell-winforensics # Debug Windows forensics container
make shell-binary       # Debug binary analysis container
make shell-threat       # Debug threat-intel container

# Per-service operations
make log-<service>      # Tail logs for a specific service
make restart-<service>  # Restart a specific service

# Cleanup
make clean              # Remove containers and local images
make nuke               # Remove everything (containers, volumes, images)
```

## Code Standards

### Python (`dfireballz/` package + `orchestrator/` + `mcp-servers/`)
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
4. Register in `dfireballz/backends/docker.py` `_TOOL_COMMANDS` mapping
5. Add tools to `dfireballz/data/tools_catalog.json`
6. Add to all MCP config files in `config/mcp_hosts/`
7. Update `config/mcpo.json`
8. Document in main README.md
9. Add unit tests

### Adding a New Investigation Template

1. Create `dfireballz/prompts/templates/your-template.md`
2. Register in `dfireballz/prompts/__init__.py` `TEMPLATES` dict
3. Add test in `tests/test_prompts.py`
4. Document in README.md

## Pull Request Requirements

- All CI checks must pass (lint, type check, tests on Python 3.11-3.13)
- No critical security vulnerabilities
- Chain of custody logging preserved
- Documentation updated for user-facing changes
- Tests added for new functionality
