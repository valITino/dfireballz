## Summary

<!-- Brief description of changes -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] MCP server addition/modification
- [ ] Playbook addition/modification
- [ ] Documentation
- [ ] CI/CD
- [ ] Security fix

## Testing

- [ ] Unit tests pass (`make test`)
- [ ] Security scan clean (`make test-security`)
- [ ] Docker builds succeed (`make build`)
- [ ] Manual testing with MCP host (which host?)

## Chain of Custody Impact

- [ ] Changes do not affect CoC logging
- [ ] CoC logging updated to reflect changes
- [ ] New evidence handling paths are logged

## Checklist

- [ ] Code follows project style (type annotations, Pydantic validation)
- [ ] No `shell=True` in subprocess calls
- [ ] No secrets or API keys in code
- [ ] Evidence access creates CoC log entries
- [ ] README updated if applicable
