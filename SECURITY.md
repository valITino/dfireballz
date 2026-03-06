# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | Yes                |
| < 1.0   | No                 |

## Reporting a Vulnerability

If you discover a security vulnerability in DFIReballz, please report it responsibly:

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email security findings to the maintainers with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Design Principles

### Container Isolation
- Every service runs in its own Docker container
- All containers run as non-root users (MCP: `investigator`, Claude Code: `claude`)
- Evidence volumes are mounted read-only in MCP containers
- No shared process namespaces
- `security_opt: no-new-privileges:true` on all containers (prevents setuid escalation)
- `pids_limit: 256` on claude-code container (fork bomb defense)
- `tmpfs /tmp:noexec,nosuid` on claude-code (prevents temp directory code execution)
- Docker socket mounted read-only where needed, with `group_add` for permission scoping
- `ENTRYPOINT []` on all MCP containers (prevents inherited entrypoints from interfering)
- `tini` as PID 1 on claude-code for proper SIGTERM/SIGINT signal forwarding

### Data Protection
- API keys stored encrypted in PostgreSQL (pgcrypto)
- Secrets never committed to git (enforced via .gitignore)
- Database passwords auto-generated with 32+ character entropy
- HTTPS enforced for production deployments

### Input Validation
- All MCP tool call parameters are validated with Pydantic
- No `shell=True` in any subprocess calls
- Path traversal protection on all file operations
- SQL injection prevention via parameterized queries (asyncpg)

### Chain of Custody
- Immutable audit log (database triggers prevent UPDATE/DELETE)
- Every evidence access, tool invocation, and report generation is logged
- Forensic hashes (SHA256/MD5/SHA1) computed on all evidence

### CI/CD Security
- Trivy vulnerability scanning on all Docker images
- Bandit static analysis on all Python code
- pip-audit dependency vulnerability scanning on every CI run
- CodeQL analysis on every PR to main
- Dependabot for automated dependency updates
- Docker Compose configuration validation (all profiles)
- Container smoke tests (`make test-smoke`) for runtime verification
