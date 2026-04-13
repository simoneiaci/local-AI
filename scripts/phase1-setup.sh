#!/bin/zsh
# ============================================================
#  Local-AI — Phase 1 Setup Script
#  MacBook Pro M4 Pro (24 GB)
#  Run this once after cloning the repo.
# ============================================================

set -e  # stop on any error

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
# 1. Check Ollama is running
# ─────────────────────────────────────────────
section "Checking Ollama"

if ! command -v ollama &>/dev/null; then
  echo "${RED}✗ Ollama not found.${RESET} Install it first:"
  echo "  brew install ollama"
  exit 1
fi

success "Ollama is installed: $(ollama --version)"

# Start Ollama service if not running
if ! curl -s http://localhost:11434 &>/dev/null; then
  info "Starting Ollama service..."
  brew services start ollama
  sleep 3
  if curl -s http://localhost:11434 &>/dev/null; then
    success "Ollama service started"
  else
    warn "Ollama may not have started — try running 'ollama serve' manually in another terminal"
  fi
else
  success "Ollama is running at http://localhost:11434"
fi

# ─────────────────────────────────────────────
# 2. Pull the model
# ─────────────────────────────────────────────
section "Pulling gemma3:12b (~7 GB)"

info "This will take a few minutes depending on your connection..."
echo ""

ollama pull gemma3:12b

echo ""
success "gemma3:12b downloaded"

# ─────────────────────────────────────────────
# 3. Pull the embedding model (tiny, needed for RAG later)
# ─────────────────────────────────────────────
section "Pulling nomic-embed-text (~274 MB)"

ollama pull nomic-embed-text
success "nomic-embed-text downloaded"

# ─────────────────────────────────────────────
# 4. Quick smoke test
# ─────────────────────────────────────────────
section "Smoke Test"

info "Running a quick test prompt on gemma3:12b..."
echo ""

RESPONSE=$(ollama run gemma3:12b "Reply with exactly: OK" 2>/dev/null)
echo "  Model response: ${GREEN}${RESPONSE}${RESET}"
echo ""
success "Model is working"

# ─────────────────────────────────────────────
# 5. Configure shell environment
# ─────────────────────────────────────────────
section "Configuring ~/.zshrc"

ZSHRC="$HOME/.zshrc"
MARKER="# === Local-AI config ==="

if grep -q "$MARKER" "$ZSHRC" 2>/dev/null; then
  warn "Local-AI config already present in ~/.zshrc — skipping (no duplicates)"
else
  info "Appending Local-AI config to ~/.zshrc..."
  cat >> "$ZSHRC" << 'ZSHBLOCK'

# === Local-AI config ===
# Ollama settings
export OLLAMA_KEEP_ALIVE=5m           # auto-unload model after 5 min idle
export OLLAMA_MAX_LOADED_MODELS=1     # only 1 model at a time (24 GB constraint)
export OLLAMA_NUM_GPU=99              # use all GPU layers via Metal
export OLLAMA_HOST=0.0.0.0:11434     # allow Podman/Tailscale to reach Ollama

# Quick model switching aliases
alias ai="ollama run gemma3:12b"          # default model
alias ai-chat="ollama run phi4-mini"       # fast lightweight chat (when pulled)
alias ai-code="ollama run devstral-small"  # coding model (when pulled)
alias ai-reason="ollama run phi4-reasoning" # reasoning model (when pulled)
alias ai-status="ollama ps"                # show loaded models + VRAM
alias ai-stop='for m in $(ollama ps | tail -n +2 | awk "{print \$1}"); do curl -s http://localhost:11434/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null; done && echo "All models unloaded"'
# === End Local-AI config ===
ZSHBLOCK

  success "~/.zshrc updated"
fi

# ─────────────────────────────────────────────
# 6. Check disk usage
# ─────────────────────────────────────────────
section "Disk Usage"

info "Ollama models are stored in ~/.ollama/models/"
du -sh ~/.ollama/models/ 2>/dev/null || echo "  (no models directory found)"
df -h / | tail -1 | awk '{print "  Disk free: " $4 " / " $2}'

# ─────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────
echo ""
echo "${GREEN}${BOLD}════════════════════════════════════════${RESET}"
echo "${GREEN}${BOLD}  Phase 1 complete!${RESET}"
echo "${GREEN}${BOLD}════════════════════════════════════════${RESET}"
echo ""
echo "  ${BOLD}Next steps:${RESET}"
echo ""
echo "  1. Reload your shell:"
echo "     ${BLUE}source ~/.zshrc${RESET}"
echo ""
echo "  2. Chat with your model:"
echo "     ${BLUE}ai${RESET}  (or: ollama run gemma3:12b)"
echo ""
echo "  3. Check what's loaded:"
echo "     ${BLUE}ai-status${RESET}"
echo ""
echo "  4. When ready, run Phase 3 to get the web UI:"
echo "     ${BLUE}./scripts/phase3-webui.sh${RESET}"
echo ""
