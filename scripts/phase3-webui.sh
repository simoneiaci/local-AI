#!/bin/zsh
# ============================================================
#  Local-AI — Phase 3 Setup: Open WebUI
#  Run after phase1-setup.sh
#  Uses Podman (not Docker)
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
# 1. Check Podman
# ─────────────────────────────────────────────
section "Checking Podman"

if ! command -v podman &>/dev/null; then
  echo "${RED}✗ Podman not found.${RESET}"
  echo "  Install it with: brew install podman"
  exit 1
fi

success "Podman installed: $(podman --version)"

# Ensure the Podman machine is running (required on macOS)
MACHINE_STATE=$(podman machine list --format '{{.LastUp}}' 2>/dev/null | head -1)
if [[ "$MACHINE_STATE" != *"Currently running"* ]]; then
  info "Podman machine is not running. Starting it..."
  podman machine start
  sleep 5
fi

if ! podman info &>/dev/null; then
  echo "${RED}✗ Podman machine failed to start.${RESET}"
  echo "  Try manually: podman machine start"
  exit 1
fi

success "Podman machine is running"

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

# On macOS, Podman containers reach the host via host.containers.internal
# No --add-host flag needed — it resolves automatically with libkrun

if podman ps -a --format '{{.Names}}' | grep -q '^open-webui$'; then
  warn "Open WebUI container already exists."
  info "Options:"
  echo "  - Start existing:  podman start open-webui"
  echo "  - Update to latest: podman rm -f open-webui && run this script again"
  echo ""
  read "REPLY?Start the existing container? [Y/n] "
  if [[ "$REPLY" =~ ^[Nn]$ ]]; then
    echo "Aborted."
    exit 0
  fi
  podman start open-webui
else
  info "Pulling and starting Open WebUI (this may take a few minutes)..."
  podman run -d \
    -p 3000:8080 \
    -e OLLAMA_BASE_URL=http://host.containers.internal:11434 \
    -v open-webui:/app/backend/data \
    --name open-webui \
    --restart=always \
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
echo "  Your data is stored locally in a Podman volume."
echo ""
echo "  ${BOLD}Useful Podman commands:${RESET}"
echo "  podman ps                  # list running containers"
echo "  podman stop open-webui     # stop the UI"
echo "  podman start open-webui    # restart it"
echo "  podman logs open-webui     # view logs"
echo "  podman rm -f open-webui    # remove (data volume kept)"
echo ""
echo "  ${BOLD}iPhone access:${RESET}"
echo "  Install Tailscale on your Mac + iPhone, then access"
echo "  Open WebUI at http://<tailscale-ip>:3000"
echo "  See: ./scripts/phase5-remote.sh"
echo ""
