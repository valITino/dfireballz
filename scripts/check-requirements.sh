#!/usr/bin/env bash
set -euo pipefail

echo "DFIReballz Requirements Check"
echo "=============================="
echo ""

ERRORS=0

# Docker
if command -v docker &>/dev/null; then
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
    echo "[OK] Docker: ${DOCKER_VERSION}"
else
    echo "[FAIL] Docker is not installed"
    ERRORS=$((ERRORS + 1))
fi

# Docker Compose
if docker compose version &>/dev/null; then
    COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || echo "unknown")
    echo "[OK] Docker Compose: ${COMPOSE_VERSION}"
else
    echo "[FAIL] Docker Compose v2 is not installed"
    ERRORS=$((ERRORS + 1))
fi

# RAM check
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")
TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
if [ "$TOTAL_RAM_GB" -ge 16 ]; then
    echo "[OK] RAM: ${TOTAL_RAM_GB}GB (16GB minimum)"
elif [ "$TOTAL_RAM_GB" -ge 8 ]; then
    echo "[WARN] RAM: ${TOTAL_RAM_GB}GB (16GB recommended, 8GB minimum)"
else
    echo "[FAIL] RAM: ${TOTAL_RAM_GB}GB (need at least 8GB)"
    ERRORS=$((ERRORS + 1))
fi

# Disk space
AVAIL_GB=$(df -BG . 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G' || echo "0")
if [ "$AVAIL_GB" -ge 50 ]; then
    echo "[OK] Disk: ${AVAIL_GB}GB available"
elif [ "$AVAIL_GB" -ge 20 ]; then
    echo "[WARN] Disk: ${AVAIL_GB}GB available (50GB recommended)"
else
    echo "[FAIL] Disk: ${AVAIL_GB}GB available (need at least 20GB)"
    ERRORS=$((ERRORS + 1))
fi

# NVIDIA GPU (optional)
if command -v nvidia-smi &>/dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo "unknown")
    echo "[OK] NVIDIA GPU: ${GPU_NAME}"
    if command -v nvidia-container-runtime &>/dev/null || docker info 2>/dev/null | grep -q nvidia; then
        echo "[OK] NVIDIA Container Toolkit: Installed"
    else
        echo "[WARN] NVIDIA Container Toolkit: Not detected (needed for GPU in Docker)"
    fi
else
    echo "[INFO] NVIDIA GPU: Not detected (optional — CPU mode works fine)"
fi

echo ""
if [ "$ERRORS" -gt 0 ]; then
    echo "Found ${ERRORS} issue(s). Please resolve before running 'make setup'."
    exit 1
else
    echo "All requirements met. Run 'make setup' to get started."
fi
