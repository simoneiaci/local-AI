#!/bin/zsh
# ============================================================
#  Local-AI — Status Check
#  Quick overview of what's running and how much RAM is used
# ============================================================

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
RESET="\033[0m"

ok()   { echo "  ${GREEN}✓${RESET} $1"; }
warn() { echo "  ${YELLOW}⚠${RESET} $1"; }
fail() { echo "  ${RED}✗${RESET} $1"; }

echo ""
echo "${BOLD}Local-AI Status${RESET}"
echo "───────────────────────────────────"

# Ollama
echo ""
echo "${BOLD}Ollama${RESET}"
if command -v ollama &>/dev/null; then
  ok "Installed: $(ollama --version)"
  if curl -s http://localhost:11434 &>/dev/null; then
    ok "Running at http://localhost:11434"
    LOADED=$(ollama ps 2>/dev/null | tail -n +2)
    if [[ -n "$LOADED" ]]; then
      ok "Loaded models:"
      echo "$LOADED" | while read line; do
        echo "     $line"
      done
    else
      warn "No models currently loaded"
    fi
    echo ""
    echo "${BOLD}Available models:${RESET}"
    ollama list 2>/dev/null | while read line; do
      echo "  $line"
    done
  else
    fail "Not running — start with: brew services start ollama"
  fi
else
  fail "Not installed — run: brew install ollama"
fi

# Podman machine
echo ""
echo "${BOLD}Podman${RESET}"
if command -v podman &>/dev/null; then
  ok "Installed: $(podman --version)"
  MACHINE_STATE=$(podman machine list --format '{{.LastUp}}' 2>/dev/null | head -1)
  if [[ "$MACHINE_STATE" == *"Currently running"* ]]; then
    ok "Machine is running"
    # Open WebUI container
    STATUS=$(podman inspect --format='{{.State.Status}}' open-webui 2>/dev/null || echo "not found")
    if [[ "$STATUS" == "running" ]]; then
      ok "Open WebUI running at ${BLUE}http://localhost:3000${RESET}"
    elif [[ "$STATUS" == "exited" ]]; then
      warn "Open WebUI container stopped — start with: podman start open-webui"
    else
      warn "Open WebUI not installed — run: ./scripts/phase3-webui.sh"
    fi
  else
    warn "Podman machine not running — start with: podman machine start"
  fi
else
  warn "Podman not installed — run: brew install podman"
fi

# Tailscale
echo ""
echo "${BOLD}Tailscale${RESET}"
if command -v tailscale &>/dev/null; then
  TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
  if [[ -n "$TS_IP" ]]; then
    ok "Connected — Tailscale IP: ${BLUE}${TS_IP}${RESET}"
    ok "Open WebUI from iPhone: ${BLUE}http://${TS_IP}:3000${RESET}"
  else
    warn "Installed but not connected — run: tailscale up"
  fi
else
  warn "Not installed — run: ./scripts/phase5-remote.sh"
fi

# Disk usage
echo ""
echo "${BOLD}Disk Usage${RESET}"
if [[ -d ~/.ollama/models ]]; then
  MODELS_SIZE=$(du -sh ~/.ollama/models 2>/dev/null | cut -f1)
  ok "Ollama models: ${MODELS_SIZE}"
fi
DISK_FREE=$(df -h / | tail -1 | awk '{print $4}')
DISK_TOTAL=$(df -h / | tail -1 | awk '{print $2}')
echo "  Free: ${DISK_FREE} / ${DISK_TOTAL}"

echo ""
echo "───────────────────────────────────"
echo ""
