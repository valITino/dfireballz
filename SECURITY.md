# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 2.x     | Yes                |
| 1.x     | Security fixes only|
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
- `security_opt: no-new-privileges:true` on all MCP containers (prevents setuid escalation)
- Docker socket mounted where needed, with `group_add` for permission scoping on orchestrator/mcpo
- `ENTRYPOINT []` on all MCP containers (prevents inherited entrypoints from interfering)

### Data Protection
- API keys stored encrypted in PostgreSQL (pgcrypto)
- Secrets never committed to git (enforced via .gitignore)
- Database passwords auto-generated with 32+ character entropy
- HTTPS enforced for production deployments
- Reports and results exported via bind mounts (no network transfer needed)

### Input Validation
- All MCP tool call parameters are validated with Pydantic
- No `shell=True` in any subprocess calls (enforced project-wide)
- Path traversal protection on all file operations
- SQL injection prevention via parameterized queries (asyncpg)
- ForensicPayload schema validation for all aggregated results

### Chain of Custody
- Immutable audit log (database triggers prevent UPDATE/DELETE)
- Every evidence access, tool invocation, and report generation is logged
- Forensic hashes (SHA256/MD5/SHA1) computed on all evidence
- Chain of custody tracked in both database and ForensicPayload data contract

### CI/CD Security
- Trivy vulnerability scanning on all Docker images
- Bandit static analysis on all Python code (dfireballz/, orchestrator/, mcp-servers/)
- pip-audit dependency vulnerability scanning on every CI run
- CodeQL analysis on every PR to main
- Dependabot for automated dependency updates
- Docker Compose configuration validation (all profiles)
- Container smoke tests (`make test-smoke`) for runtime verification
- Multi-Python version testing (3.11, 3.12, 3.13) for compatibility assurance
