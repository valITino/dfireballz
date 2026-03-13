# DFIReballz — Claude Code Scenario Analysis & Findings

**Date:** 2026-03-13
**Branch:** `claude/setup-dfireballz-docker-eFkF5`

---

## Scenarios Tested

There are **4 distinct ways** Claude Code can run with DFIReballz:

| # | Setup Choice | How Claude Code Runs | Auth Method | Working Dir |
|---|---|---|---|---|
| A | Option 2: Claude Desktop | `make claude-code` (containerized) | Depends on `.env` | `/root` (container) |
| B | Option 1: Claude Code | `make claude-code` (containerized) | Depends on `.env` | `/root` (container) |
| C | Any | Host-installed `claude` CLI in project dir | OAuth or API key | Project dir (e.g. `~/Desktop/dfireballz`) |
| D | Any | Claude Code Web (remote) | OAuth (managed by Anthropic) | `/workspaces/dfireballz` |

---

## Bugs Found

### BUG 1: `ANTHROPIC_API_KEY` Empty String Forces API Billing

**File:** `docker-compose.yml:234`
```yaml
ANTHROPIC_API_KEY: "${ANTHROPIC_API_KEY:-}"
```

**Problem:** When `ANTHROPIC_API_KEY` is NOT in `.env` (or is commented out), Docker Compose resolves `${ANTHROPIC_API_KEY:-}` to an **empty string** and sets `ANTHROPIC_API_KEY=""` inside the container. According to Claude Code docs, setting `ANTHROPIC_API_KEY` (even to empty) can force Claude Code into **"API Usage Billing" mode**, overriding subscription-based (account) authentication.

**Impact:** Users who want account login but don't set an API key still get forced into API billing mode due to the empty string.

**Root cause:** The `:-` operator in `${ANTHROPIC_API_KEY:-}` substitutes empty string when unset — but Docker Compose still **exports the variable** to the container, which Claude Code interprets as "use API key mode."

**Fix:** Use conditional env injection. Only pass the variable if it's actually set and non-empty.

---

### BUG 2: `DFIREBALLZ_CONTAINER` Env Var Never Set

**File:** `.claude/hooks/session-start.sh:9`
```bash
if [ "${DFIREBALLZ_CONTAINER:-}" = "1" ]; then
  exit 0
fi
```

**Problem:** This guard checks `DFIREBALLZ_CONTAINER=1` to skip the session-start hook when running inside the containerized Claude Code. But this variable is **never set** in:
- `docker-compose.yml` (claude-code service environment)
- `docker/claude-code.Dockerfile`
- `docker/claude-code-entrypoint.sh`

**Impact:** If the containerized Claude Code somehow triggers the SessionStart hook (e.g., if `.claude/settings.json` is discovered), the hook would run inside the container where Docker daemon and host paths don't apply, potentially causing errors or confusion.

**Fix:** Add `DFIREBALLZ_CONTAINER: "1"` to the claude-code service environment in `docker-compose.yml`.

---

### BUG 3: No Auth Persistence Volume for Claude Code Container

**File:** `docker-compose.yml:240-245`

**Problem:** The containerized Claude Code mounts `./cases`, `./evidence`, `./reports`, `./results`, and the Docker socket — but does NOT mount a volume for `~/.claude/` (auth credential storage). This means:
- Any OAuth login performed inside the container is **lost on restart** (`--rm` flag in `make claude-code`)
- The `CLAUDE_CODE_OAUTH_TOKEN` env var is not supported
- Users must re-authenticate every single time

**Impact:** OAuth/account login works once (if it works at all), but credentials aren't persisted. This pushes users toward API key auth out of frustration.

**Fix:** Add a named volume `claude-config` mapped to `/root/.claude` to persist authentication across restarts. Also support `CLAUDE_CODE_OAUTH_TOKEN` as an env var.

---

### BUG 4: `MCP_HOST` Choice Has Zero Effect on `make claude-code`

**Files:** `Makefile:169-191`, `scripts/setup.sh:112-118`

**Problem:** Whether the user chooses option 1 (Claude Code) or option 2 (Claude Desktop) during `make setup`, the `make claude-code` target behaves **identically**:
- Same container image
- Same entrypoint
- Same `/root/.mcp.json` (baked into image from `docker/mcp.json`)
- Same volumes

The `MCP_HOST` variable only affects `scripts/configure_mcp.sh` output (which `.mcp.json` to generate for the HOST), not the containerized Claude Code experience.

**Impact:** Users choosing "Claude Desktop" who then run `make claude-code` may be confused because:
- The `.mcp.json` on the host is generated for Claude Desktop
- But the container has its own `/root/.mcp.json` baked in at build time
- These are effectively two different, disconnected configurations

**This is NOT technically a bug** — it's by design (the containerized Claude Code always uses the baked-in config). But it's confusing UX.

**Fix:** Document this clearly. Consider making `make claude-code` warn if `MCP_HOST != claude-code`.

---

### BUG 5: `setup.sh` Always Prompts for `ANTHROPIC_API_KEY` Regardless of Mode

**File:** `scripts/setup.sh:154-174`

**Problem:** The setup wizard always asks for an Anthropic API key at step [5/7], even when the user chose option 2 (Claude Desktop) or option 3 (MCPHost + Ollama) — modes that don't use the containerized Claude Code at all.

**Impact:**
- Users who chose Claude Desktop get confused about why they need an Anthropic API key
- If they enter one, it's saved to `.env`, and then if they later run `make claude-code`, it gets picked up and forces API billing
- The prompt text says "required for 'make claude-code'" but doesn't clarify this is only relevant if they plan to use the containerized Claude Code

**Fix:** Only prompt for `ANTHROPIC_API_KEY` when `MCP_HOST=claude-code`. For other modes, skip or make it clearly optional with different wording.

---

### BUG 6: WORKDIR `/root` Is Non-Standard and Runs as Root

**File:** `docker/claude-code.Dockerfile:31`
```dockerfile
WORKDIR /root
```

**Problem:** The container runs as root with WORKDIR `/root`. This is:
1. A security concern — Claude Code runs as root inside the container
2. Non-standard — official Claude Code devcontainers use user `node` with WORKDIR `/workspace`
3. Confusing — the user sees `/root` as CWD, not a project-like directory

**The `/workspaces` mystery:** When users run Claude Code on the Web (remote mode), the working directory is `/workspaces/<repo-name>` (VS Code dev container convention). When they then run `make claude-code` locally, they see `/root`. This directoryinconsistency is jarring.

**Fix:** Create a non-root user, use `/workspace` as WORKDIR, and mount evidence/cases/reports inside it.

---

### BUG 7: `.env.example` Has Contradictory Auth Documentation

**File:** `config/.env.example:17-31`

The `.env.example` says:
```
# Option A (Recommended): Account login — leave this commented out.
```

But the setup wizard says:
```
API key auth is required for Claude Code in Docker.
(OAuth login inside containers is unreliable...)
```

And `mcp-start.sh` says:
```
# Claude Code provides its own authentication via OAuth.
```

**Three different messages about the same topic.** Users get conflicting guidance.

**Fix:** Align documentation. Pick ONE recommended approach and make it consistent.

---

## Root Cause Analysis: Why the Observed Behavior

### "Claude Desktop mode + `make claude-code` = account auth + `/root`"

What likely happened:
1. User chose option 2 (Claude Desktop) during setup
2. User entered `ANTHROPIC_API_KEY=sk-ant-api03-...` when prompted
3. `.env` contains `MCP_HOST=claude-desktop` AND `ANTHROPIC_API_KEY=sk-ant-api03-...`
4. `make claude-code` runs — container gets `ANTHROPIC_API_KEY=sk-ant-api03-...`
5. Claude Code sees a valid API key and uses it — this IS API billing, but the Claude Code UI may label it differently depending on the key type
6. WORKDIR is `/root` — this is the Dockerfile's WORKDIR, correct behavior

The "account login" observation may actually be API key auth that LOOKED like account auth in the Claude Code status bar (API keys from Console don't always show "API Usage" — the billing label depends on account type).

### "Claude Code mode = API usage + `/workspaces`"

What likely happened:
1. User chose option 1 (Claude Code) during setup
2. User entered same `ANTHROPIC_API_KEY`
3. This scenario may have been tested via **Claude Code Web** (remote), not `make claude-code`
4. Claude Code Web uses `/workspaces/<repo-name>` as the working directory
5. The API key in `.env` was sourced by `mcp-start.sh`, potentially affecting billing mode
6. Or: if this was also containerized, the `/workspaces` is unexplained — the Dockerfile hardcodes `/root`

**Key question for the user:** Was the `/workspaces` scenario observed when running:
- (a) `make claude-code` on the host?
- (b) Claude Code Web (remote, browser-based)?
- (c) Something else?

---

## Proposed Solutions

### Solution 1: Fix ANTHROPIC_API_KEY Empty String (Critical)

**`docker-compose.yml`** — Change from:
```yaml
ANTHROPIC_API_KEY: "${ANTHROPIC_API_KEY:-}"
```
To using a conditional in the entrypoint instead. Remove the env var from docker-compose.yml entirely and pass it through the entrypoint only if non-empty:

```yaml
environment:
  # Only set if the var exists and is non-empty
  ANTHROPIC_API_KEY: "${ANTHROPIC_API_KEY-__UNSET__}"
```

Then in `claude-code-entrypoint.sh`:
```bash
if [ "${ANTHROPIC_API_KEY:-}" = "__UNSET__" ] || [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  unset ANTHROPIC_API_KEY
fi
```

**Alternative (simpler):** Use `${ANTHROPIC_API_KEY-}` (without colon) — this only substitutes if the variable is truly unset, not if it's empty. But Docker Compose doesn't differentiate well between "unset" and "empty."

**Best approach:** Handle it in the entrypoint script by unsetting empty values before launching Claude.

### Solution 2: Add DFIREBALLZ_CONTAINER Env Var

**`docker-compose.yml`** claude-code service:
```yaml
environment:
  DFIREBALLZ_CONTAINER: "1"
```

### Solution 3: Add Auth Persistence Volume + OAuth Token Support

**`docker-compose.yml`** claude-code service:
```yaml
volumes:
  - claude-config:/root/.claude   # Persist OAuth tokens
```

And add to top-level volumes:
```yaml
volumes:
  claude-config:
```

Also add `CLAUDE_CODE_OAUTH_TOKEN` support:
```yaml
environment:
  CLAUDE_CODE_OAUTH_TOKEN: "${CLAUDE_CODE_OAUTH_TOKEN:-}"
```

With the same empty-string guard in the entrypoint.

### Solution 4: Conditional API Key Prompt in Setup

**`scripts/setup.sh`** — wrap the Anthropic API key prompt:
```bash
if [ "$MCP_HOST" = "claude-code" ]; then
  # prompt for ANTHROPIC_API_KEY
else
  echo "  Skipping Anthropic API key (only needed for 'make claude-code')."
  echo "  Set it later with: make setup-api-key"
fi
```

### Solution 5: Add MCP_HOST Warning to `make claude-code`

**`Makefile`** claude-code target:
```makefile
@MCP_HOST_VAL=$$(grep '^MCP_HOST=' .env 2>/dev/null | cut -d= -f2); \
if [ "$$MCP_HOST_VAL" != "claude-code" ] && [ -n "$$MCP_HOST_VAL" ]; then \
  echo "  Note: MCP_HOST is set to '$$MCP_HOST_VAL', but 'make claude-code'"; \
  echo "  runs its own containerized Claude Code with a built-in MCP config."; \
fi
```

### Solution 6: Non-Root Container + `/workspace` WORKDIR

**`docker/claude-code.Dockerfile`**:
```dockerfile
# Create non-root user
RUN useradd -m -s /bin/bash claude
USER claude
WORKDIR /workspace

COPY docker/mcp.json /workspace/.mcp.json
```

Update volume mounts accordingly.

### Solution 7: Align Auth Documentation

Pick ONE message: "API key is recommended for Docker. OAuth can work with a persistent volume."

Update consistently in:
- `config/.env.example`
- `scripts/setup.sh`
- `.claude/mcp-start.sh` comments
- `Makefile` claude-code target messaging

---

## Recommended Priority

| Priority | Bug | Impact | Effort |
|----------|-----|--------|--------|
| P0 | BUG 1: Empty ANTHROPIC_API_KEY | Users get unexpected billing | Low |
| P0 | BUG 7: Contradictory auth docs | User confusion | Low |
| P1 | BUG 2: DFIREBALLZ_CONTAINER missing | Hook errors in container | Trivial |
| P1 | BUG 3: No auth persistence | Repeated login friction | Low |
| P1 | BUG 5: Always prompts for API key | Setup confusion | Low |
| P2 | BUG 4: MCP_HOST doesn't affect container | UX confusion | Low |
| P2 | BUG 6: Root user + /root WORKDIR | Security + convention | Medium |

---

## Questions for User Before Proceeding

1. When you saw `/workspaces` — was that from `make claude-code`, from Claude Code Web (browser), or from a host-installed `claude` CLI?
2. Do you want to support **both** API key AND OAuth token auth methods in the container? Or pick one as the default?
3. For the non-root container change (BUG 6) — is this a priority, or are you OK with root for now given it's a forensics tool container?
