# DFIReballz Makefile

.PHONY: help setup start stop restart logs status build pull clean \
        dev test test-unit test-security shell-kali shell-osint shell-netforensics \
        case-new playbook-list check-gpu configure-mcp start-openwebui

help:
	@echo "╔══════════════════════════════════════════╗"
	@echo "║           DFIReballz Commands             ║"
	@echo "╚══════════════════════════════════════════╝"
	@echo ""
	@echo "  Setup & Installation:"
	@echo "    make setup          — Interactive first-run setup wizard"
	@echo "    make pull           — Pull all Docker images"
	@echo "    make build          — Build all custom Docker images"
	@echo ""
	@echo "  Running:"
	@echo "    make start          — Start all services (detached)"
	@echo "    make start-openwebui — Start with Open WebUI + Ollama (--profile openwebui)"
	@echo "    make stop           — Stop all services"
	@echo "    make restart        — Restart all services"
	@echo "    make status         — Show container health status"
	@echo "    make logs           — Tail all logs"
	@echo "    make logs s=<svc>   — Tail specific service logs"
	@echo ""
	@echo "  Development:"
	@echo "    make dev            — Start in dev mode (hot reload)"
	@echo "    make test           — Run all tests"
	@echo "    make test-security  — Run security scan (Trivy + Bandit)"
	@echo "    make shell-kali     — Shell into Kali forensics container"
	@echo "    make shell-osint    — Shell into OSINT container"
	@echo "    make shell-netforensics — Shell into Wireshark/tcpdump container"
	@echo ""
	@echo "  Utilities:"
	@echo "    make check-gpu      — Check NVIDIA GPU availability"
	@echo "    make clean          — Remove containers and images"
	@echo "    make case-new       — Create a new case (interactive)"
	@echo "    make playbook-list  — List available playbooks"
	@echo "    make configure-mcp  — Generate MCP config for chosen host"

setup:
	@bash scripts/setup.sh

build:
	docker compose build --parallel

pull:
	docker compose pull
	@if [ "$(ENABLE_GPU)" = "true" ]; then docker compose --profile openwebui pull; fi

start:
	docker compose up -d
	@echo ""
	@echo "  DFIReballz running at http://localhost:3000"
	@echo "  Orchestrator API: http://localhost:8800"
	@echo "  Run 'make configure-mcp' to generate .mcp.json for Claude Code / Claude Desktop"

start-openwebui:
	docker compose --profile openwebui up -d
	@echo ""
	@echo "  DFIReballz + Open WebUI + Ollama running"
	@echo "  Open WebUI: http://localhost:8080"
	@echo "  mcpo API bridge: http://localhost:8812"

stop:
	docker compose --profile openwebui down

restart:
	docker compose restart

status:
	@docker compose ps
	@echo ""
	@echo "MCP Server Health:"
	@curl -s http://localhost:8800/settings/mcp-status 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  Orchestrator not reachable"

logs:
	@if [ -n "$(s)" ]; then docker compose logs -f $(s); else docker compose logs -f; fi

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

test:
	docker compose run --rm orchestrator pytest tests/ -v

test-security:
	@echo "Running Trivy image scan..."
	@trivy image crhacky/dfireballz:latest 2>/dev/null || echo "  Trivy not installed or image not found"
	@echo ""
	@echo "Running Bandit Python security scan..."
	@docker compose run --rm orchestrator bandit -r . -x tests/ 2>/dev/null || echo "  Run 'make start' first"

shell-kali:
	docker compose exec kali-forensics bash

shell-osint:
	docker compose exec osint bash

shell-netforensics:
	docker compose exec network-forensics bash

check-gpu:
	@nvidia-smi 2>/dev/null && echo "NVIDIA GPU detected" || echo "No NVIDIA GPU found (GPU acceleration disabled)"

clean:
	docker compose --profile openwebui down -v --rmi local

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
