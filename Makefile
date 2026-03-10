# DFIReballz Makefile — Digital Forensics & Cybercrime Investigation Platform

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Containers
SERVICES := kali-forensics winforensics osint threat-intel binary-analysis network-forensics filesystem
INFRA := db redis orchestrator

.PHONY: help setup start stop restart logs status build pull clean \
        dev test test-unit test-pkg test-smoke test-security lint format typecheck audit \
        shell-kali shell-osint shell-netforensics shell-winforensics shell-binary shell-threat \
        shell-filesystem shell-orchestrator \
        case-new playbook-list check-gpu configure-mcp start-openwebui claude-code \
        mcp-health-check up down ps health nuke push-all report version \
        log-kali log-osint log-netforensics log-winforensics log-binary log-threat \
        log-filesystem log-orchestrator log-db log-redis \
        restart-kali restart-osint restart-netforensics restart-winforensics restart-binary \
        restart-threat restart-filesystem restart-orchestrator \
        venv install install-dev

# ─── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║                    DFIReballz Commands                          ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  Setup & Installation:"
	@echo "    make setup              — Interactive first-run setup wizard"
	@echo "    make pull               — Pull pre-built images from Docker Hub"
	@echo "    make build              — Build images locally from source (dev only)"
	@echo "    make venv               — Create Python venv and install package"
	@echo "    make install            — Install dfireballz package in current env"
	@echo "    make install-dev        — Install dfireballz with dev dependencies"
	@echo ""
	@echo "  Running:"
	@echo "    make start / make up    — Start all services (detached)"
	@echo "    make start-openwebui    — Start with Open WebUI + Ollama"
	@echo "    make claude-code        — Run Claude Code in Docker (interactive)"
	@echo "    make stop / make down   — Stop all services"
	@echo "    make restart            — Restart all services"
	@echo "    make status / make ps   — Show container health status"
	@echo "    make logs               — Tail all logs"
	@echo "    make logs s=<svc>       — Tail specific service logs"
	@echo ""
	@echo "  Development & Testing:"
	@echo "    make dev                — Start in dev mode (hot reload)"
	@echo "    make test               — Run all tests (package + orchestrator)"
	@echo "    make test-pkg           — Run dfireballz package tests only"
	@echo "    make test-smoke         — Run container smoke tests"
	@echo "    make test-security      — Run security scan (Trivy + Bandit)"
	@echo "    make lint               — Run ruff linter on dfireballz/"
	@echo "    make format             — Auto-format code with ruff"
	@echo "    make typecheck          — Run mypy type checking"
	@echo "    make audit              — Run pip-audit on dependencies"
	@echo ""
	@echo "  Shells (debug containers):"
	@echo "    make shell-kali         — Shell into Kali forensics container"
	@echo "    make shell-osint        — Shell into OSINT container"
	@echo "    make shell-netforensics — Shell into network forensics container"
	@echo "    make shell-winforensics — Shell into Windows forensics container"
	@echo "    make shell-binary       — Shell into binary analysis container"
	@echo "    make shell-threat       — Shell into threat-intel container"
	@echo "    make shell-filesystem   — Shell into filesystem container"
	@echo "    make shell-orchestrator — Shell into orchestrator container"
	@echo ""
	@echo "  Per-Service Logs:"
	@echo "    make log-<service>      — Tail logs for a specific service"
	@echo "    Services: kali, osint, netforensics, winforensics, binary,"
	@echo "              threat, filesystem, orchestrator, db, redis"
	@echo ""
	@echo "  Per-Service Restart:"
	@echo "    make restart-<service>  — Restart a specific service"
	@echo ""
	@echo "  Reporting:"
	@echo "    make report             — Generate report from last session"
	@echo "    make version            — Show dfireballz version"
	@echo ""
	@echo "  Utilities:"
	@echo "    make health             — Check MCP server container health"
	@echo "    make check-gpu          — Check NVIDIA GPU availability"
	@echo "    make clean              — Remove containers and local images"
	@echo "    make nuke               — Remove EVERYTHING (containers, volumes, images)"
	@echo "    make case-new           — Create a new case (interactive)"
	@echo "    make playbook-list      — List available playbooks"
	@echo "    make configure-mcp      — Generate MCP config for chosen host"
	@echo "    make push-all           — Push all images to registry"

# ─── Setup & Build ────────────────────────────────────────────────────────────

setup:
	@bash scripts/setup.sh

build:
	docker compose build --parallel

pull:
	docker compose pull
	@if [ "$(ENABLE_GPU)" = "true" ]; then docker compose --profile openwebui pull; fi

venv:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"
	@echo "Virtualenv ready. Activate with: source .venv/bin/activate"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# ─── Start / Stop ─────────────────────────────────────────────────────────────

start up:
	docker compose pull --ignore-pull-failures
	docker compose up -d --no-build
	@echo ""
	@echo "  Waiting for containers to become healthy..."
	@bash scripts/configure_mcp.sh --host "$$(grep '^MCP_HOST=' .env 2>/dev/null | cut -d= -f2 || echo claude-code)" 2>/dev/null || true
	@echo ""
	@echo "  DFIReballz running — Orchestrator API: http://localhost:8800"
	@echo "  MCP config auto-generated — no need to run 'make configure-mcp' separately"

start-openwebui:
	docker compose --profile openwebui pull --ignore-pull-failures
	docker compose --profile openwebui up -d --no-build
	@echo ""
	@echo "  DFIReballz + Open WebUI + Ollama running"
	@echo "  Open WebUI: http://localhost:8080"
	@echo "  mcpo API bridge: http://localhost:8812"

claude-code:
	@if [ -z "$${ANTHROPIC_API_KEY:-}" ] && ! grep -q '^ANTHROPIC_API_KEY=.' .env 2>/dev/null; then \
		echo ""; \
		echo "  ℹ️  No ANTHROPIC_API_KEY found — Claude Code will prompt you to log in"; \
		echo "     via your Anthropic account (recommended)."; \
		echo ""; \
		echo "     To use an API key instead, set ANTHROPIC_API_KEY in .env"; \
		echo "     or export it before running this command."; \
		echo ""; \
	fi
	docker compose --profile claude-code pull --ignore-pull-failures
	docker compose --profile claude-code run --rm claude-code

stop down:
	docker compose --profile claude-code --profile openwebui down

restart:
	docker compose restart

# ─── Status & Logs ─────────────────────────────────────────────────────────────

status ps:
	@docker compose ps
	@echo ""
	@echo "MCP Server Health:"
	@curl -s http://localhost:8800/settings/mcp-status 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  Orchestrator not reachable"

logs:
	@if [ -n "$(s)" ]; then docker compose logs -f $(s); else docker compose logs -f; fi

health mcp-health-check:
	@bash .claude/mcp-health-check.sh

# ─── Per-Service Logs ──────────────────────────────────────────────────────────

log-kali:
	docker compose logs -f kali-forensics

log-osint:
	docker compose logs -f osint

log-netforensics:
	docker compose logs -f network-forensics

log-winforensics:
	docker compose logs -f winforensics

log-binary:
	docker compose logs -f binary-analysis

log-threat:
	docker compose logs -f threat-intel

log-filesystem:
	docker compose logs -f filesystem

log-orchestrator:
	docker compose logs -f orchestrator

log-db:
	docker compose logs -f db

log-redis:
	docker compose logs -f redis

# ─── Per-Service Restart ───────────────────────────────────────────────────────

restart-kali:
	docker compose restart kali-forensics

restart-osint:
	docker compose restart osint

restart-netforensics:
	docker compose restart network-forensics

restart-winforensics:
	docker compose restart winforensics

restart-binary:
	docker compose restart binary-analysis

restart-threat:
	docker compose restart threat-intel

restart-filesystem:
	docker compose restart filesystem

restart-orchestrator:
	docker compose restart orchestrator

# ─── Shells ────────────────────────────────────────────────────────────────────

shell-kali:
	docker compose exec kali-forensics bash

shell-osint:
	docker compose exec osint bash

shell-netforensics:
	docker compose exec network-forensics bash

shell-winforensics:
	docker compose exec winforensics bash

shell-binary:
	docker compose exec binary-analysis bash

shell-threat:
	docker compose exec threat-intel bash

shell-filesystem:
	docker compose exec filesystem bash

shell-orchestrator:
	docker compose exec orchestrator bash

# ─── Development & Testing ─────────────────────────────────────────────────────

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

test: test-pkg
	docker compose run --rm orchestrator pytest tests/ -v 2>/dev/null || true

test-pkg:
	python3 -m pytest tests/ -v --tb=short

test-smoke:
	@bash scripts/smoke-test.sh

test-security:
	@echo "Running Trivy image scan..."
	@trivy image crhacky/dfireballz:latest 2>/dev/null || echo "  Trivy not installed — install from https://trivy.dev"
	@echo ""
	@echo "Running Bandit Python security scan..."
	bandit -r orchestrator/ mcp-servers/ dfireballz/ -x orchestrator/tests/,tests/ -ll

lint:
	ruff check dfireballz/ tests/

format:
	ruff check --fix dfireballz/ tests/
	ruff format dfireballz/ tests/

typecheck:
	mypy dfireballz/ --ignore-missing-imports

audit:
	pip-audit -r requirements.txt

# ─── Reporting & CLI ───────────────────────────────────────────────────────────

report:
	@dfireballz report --format html 2>/dev/null || echo "Run 'make install' first to use the dfireballz CLI"

version:
	@python3 -c "from dfireballz import __version__; print(f'DFIReballz v{__version__}')" 2>/dev/null || echo "Package not installed"

# ─── Utilities ─────────────────────────────────────────────────────────────────

check-gpu:
	@nvidia-smi 2>/dev/null && echo "NVIDIA GPU detected" || echo "No NVIDIA GPU found (GPU acceleration disabled)"

clean:
	docker compose --profile claude-code --profile openwebui down -v --rmi local

nuke:
	docker compose --profile claude-code --profile openwebui down -v --rmi all --remove-orphans
	@echo "All DFIReballz containers, volumes, and images removed."

push-all:
	@echo "Pushing all DFIReballz images..."
	@for svc in $(SERVICES) $(INFRA); do \
		echo "  Pushing $$svc..."; \
		docker compose push $$svc 2>/dev/null || echo "  $$svc: no image to push"; \
	done
	@echo "Done."

case-new:
	@echo "Creating new case..."
	@curl -s -X POST http://localhost:8800/cases \
	  -H "Content-Type: application/json" \
	  -d '{"title":"New Investigation","case_type":"other"}' | python3 -m json.tool

playbook-list:
	@curl -s http://localhost:8800/playbooks | python3 -m json.tool

configure-mcp:
	@bash scripts/configure_mcp.sh $(if $(MCP_HOST),--host $(MCP_HOST),)
	@echo "MCP config generated for host: $(or $(MCP_HOST),claude-code)"
