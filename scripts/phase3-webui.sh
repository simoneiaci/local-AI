#!/bin/zsh
# ============================================================
#  Local-AI — Phase 3 Setup: Open WebUI
#  Run after phase1-setup.sh
# ============================================================

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
RESET="\033[0m"

info()    { echo "${BLUE}ℹ ${RESET}$1"; }
success() { echo "${GREEN}✓ ${RESET}$1"; }
warn()    { echo "${YELLOW}⚠ ${RESET}$1"; }
section() { echo "\n${BOLD}═══ $1 ═══${RESET}"; }

# ─────────────────────────────────────────────
# 1. Check Docker
# ─────────────────────────────────────────────
section "Checking Docker"

if ! command -v docker &>/dev/null; then
  echo "${RED}✗ Docker not found.${RESET}"
  echo "  Install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
  exit 1
fi

if ! docker info &>/dev/null; then
  echo "${RED}✗ Docker is not running.${RESET} Please start Docker Desktop first."
  exit 1
fi

success "Docker is running"

# ─────────────────────────────────────────────
# 2. Check Ollama is running
# ─────────────────────────────────────────────
section "Checking Ollama"

if ! curl -s http://localhost:11434 &>/dev/null; then
  warn "Ollama doesn't seem to be running. Starting it..."
  brew services start ollama
  sleep 3
fi

success "Ollama is running"

# ─────────────────────────────────────────────
# 3. Install or update Open WebUI
# ─────────────────────────────────────────────
section "Setting up Open WebUI"

if docker ps -a --format '{{.Names}}' | grep -q '^open-webui$'; then
  warn "Open WebUI container already exists."
  info "Options:"
  echo "  - Start existing: docker start open-webui"
  echo "  - Update to latest: docker rm -f open-webui && run this script again"
  echo ""
  read "REPLY?Start the existing container? [Y/n] "
  if [[ "$REPLY" =~ ^[Nn]$ ]]; then
    echo "Aborted."
    exit 0
  fi
  docker start open-webui
else
  info "Pulling and starting Open WebUI (this may take a few minutes)..."
  docker run -d \
    -p 3000:8080 \
    --add-host=host.docker.internal:host-gateway \
    -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    -v open-webui:/app/backend/data \
    --name open-webui \
    --restart always \
    ghcr.io/open-webui/open-webui:main
fi

# ─────────────────────────────────────────────
# 4. Wait for it to be ready
# ─────────────────────────────────────────────
section "Waiting for Open WebUI to start"

info "Waiting for http://localhost:3000 ..."
for i in {1..30}; do
  if curl -s http://localhost:3000 &>/dev/null; then
    success "Open WebUI is up!"
    break
  fi
  sleep 2
  echo -n "."
done
echo ""

# ─────────────────────────────────────────────
# 5. Open in browser
# ─────────────────────────────────────────────
section "Opening in Browser"

open http://localhost:3000
success "Opened http://localhost:3000 in your browser"

# ─────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────
echo ""
echo "${GREEN}${BOLD}════════════════════════════════════════${RESET}"
echo "${GREEN}${BOLD}  Open WebUI is running!${RESET}"
echo "${GREEN}${BOLD}════════════════════════════════════════${RESET}"
echo ""
echo "  ${BOLD}URL:${RESET}     ${BLUE}http://localhost:3000${RESET}"
echo "  ${BOLD}Model:${RESET}   gemma3:12b (via Ollama)"
echo ""
echo "  ${BOLD}First time?${RESET}"
echo "  Create an admin account on the sign-up screen."
echo "  Your data is stored locally in a Docker volume."
echo ""
echo "  ${BOLD}iPhone access:${RESET}"
echo "  Install Tailscale on your Mac + iPhone, then access"
echo "  Open WebUI at http://<tailscale-ip>:3000"
echo "  See: ./scripts/phase5-remote.sh"
echo ""
