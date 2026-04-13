#!/usr/bin/env bash
# =============================================================================
# Local-AI Phase 2 — Coding Tools Setup
# Configures Continue.dev, OpenCode, Aider, and tab autocomplete
# All tools use approved models via local Ollama
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

log()    { echo -e "${GREEN}✓${NC} $*"; }
info()   { echo -e "${BLUE}→${NC} $*"; }
warn()   { echo -e "${YELLOW}⚠${NC} $*"; }
error()  { echo -e "${RED}✗${NC} $*"; }
header() { echo -e "\n${BOLD}$*${NC}"; }

echo -e "${BOLD}"
echo "╔══════════════════════════════════════╗"
echo "║  Local-AI  •  Phase 2: Coding Tools  ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Verify Ollama is running ───────────────────────────────────────────────
header "1. Checking Ollama"

if ! /opt/homebrew/bin/ollama list &>/dev/null 2>&1; then
  error "Ollama is not running. Start it with: ollama serve"
  exit 1
fi
log "Ollama is up"

MODELS=$(/opt/homebrew/bin/ollama list 2>/dev/null | awk 'NR>1 {print $1}')

# ── 2. Pull coding models (if not present) ────────────────────────────────────
header "2. Pulling coding models (if needed)"

pull_if_missing() {
  local model="$1"
  local label="$2"
  if echo "$MODELS" | grep -q "^${model%%:*}"; then
    log "$label already present"
  else
    info "Pulling $label (~may take a few minutes)…"
    /opt/homebrew/bin/ollama pull "$model"
    log "$label pulled"
  fi
}

pull_if_missing "devstral"   "Devstral Small 1.1 (best coding model)"
pull_if_missing "smollm2:1.7b"     "SmolLM2 1.7B (fast tab autocomplete)"

echo ""
info "Optional: pull Phi 4 Mini for quick Q&A chat"
read -r -p "  Pull phi4-mini? (y/N) " answer
if [[ "${answer,,}" == "y" ]]; then
  pull_if_missing "phi4-mini" "Phi 4 Mini"
fi

# ── 3. Continue.dev config ────────────────────────────────────────────────────
header "3. Continue.dev — VS Code AI assistant"

CONTINUE_DIR="$HOME/.continue"
CONTINUE_CFG="$CONTINUE_DIR/config.json"

mkdir -p "$CONTINUE_DIR"

if [[ -f "$CONTINUE_CFG" ]]; then
  warn "Existing config found — backing up to config.json.bak"
  cp "$CONTINUE_CFG" "$CONTINUE_CFG.bak"
fi

cat > "$CONTINUE_CFG" << 'EOF'
{
  "models": [
    {
      "title": "Devstral Small 1.1 (coding)",
      "provider": "ollama",
      "model": "devstral",
      "apiBase": "http://localhost:11434",
      "contextLength": 32768
    },
    {
      "title": "Gemma 3 12B (balanced)",
      "provider": "ollama",
      "model": "gemma3:12b",
      "apiBase": "http://localhost:11434",
      "contextLength": 32768
    },
    {
      "title": "Mistral Small 3.1 (general / long context)",
      "provider": "ollama",
      "model": "mistral-small3.1:24b",
      "apiBase": "http://localhost:11434",
      "contextLength": 32768
    }
  ],
  "tabAutocompleteModel": {
    "title": "SmolLM2 1.7B (fast autocomplete)",
    "provider": "ollama",
    "model": "smollm2:1.7b",
    "apiBase": "http://localhost:11434"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  },
  "contextProviders": [
    { "name": "code" },
    { "name": "docs" },
    { "name": "diff" },
    { "name": "terminal" },
    { "name": "problems" },
    { "name": "folder" },
    { "name": "codebase" }
  ],
  "slashCommands": [
    { "name": "share", "description": "Export conversation as markdown" },
    { "name": "cmd", "description": "Generate a shell command" }
  ]
}
EOF

log "Continue.dev config written → $CONTINUE_CFG"
info "In VS Code: install 'Continue' extension, then Cmd+L to chat, Cmd+I to edit"

# ── 4. OpenCode env vars ──────────────────────────────────────────────────────
header "4. OpenCode — terminal AI coding agent"

OPENCODE_BIN=$(command -v opencode 2>/dev/null || true)
if [[ -z "$OPENCODE_BIN" ]]; then
  info "OpenCode not found. Trying brew install…"
  if command -v brew &>/dev/null; then
    brew install opencode 2>/dev/null || warn "brew install failed — try: go install github.com/opencode-ai/opencode@latest"
  else
    warn "Install manually: go install github.com/opencode-ai/opencode@latest"
  fi
else
  log "OpenCode already installed at $OPENCODE_BIN"
fi

# ── 5. Aider ─────────────────────────────────────────────────────────────────
header "5. Aider — CLI pair programmer"

if command -v aider &>/dev/null; then
  log "Aider already installed ($(aider --version 2>/dev/null | head -1))"
else
  info "Installing aider…"
  pip install aider-chat --break-system-packages --quiet && log "Aider installed" || warn "pip install failed — try: pip3 install aider-chat --break-system-packages"
fi

# ── 6. Append env vars to .zshrc ─────────────────────────────────────────────
header "6. Shell environment — coding tool vars"

ZSHRC="$HOME/.zshrc"
MARKER="# ── Local-AI coding tools ──"

if grep -q "$MARKER" "$ZSHRC" 2>/dev/null; then
  warn "Coding tool vars already in ~/.zshrc — skipping"
else
  cat >> "$ZSHRC" << 'SHELLBLOCK'

# ── Local-AI coding tools ──
# OpenCode: use local Ollama (approved models only)
export OPENCODE_PROVIDER=openai-compatible
export OPENCODE_API_BASE=http://localhost:11434/v1
export OPENCODE_MODEL=devstral

# Aider: use local Ollama
alias aider-code='aider --model ollama/devstral'
alias aider-think='aider --model ollama/phi4-reasoning'

# Quick model switcher for coding tools
ai-use-coding()  { export OPENCODE_MODEL=devstral; echo "→ devstral"; }
ai-use-general() { export OPENCODE_MODEL=mistral-small3.1:24b; echo "→ mistral-small3.1"; }
SHELLBLOCK

  log "Env vars appended to ~/.zshrc"
  info "Run: source ~/.zshrc   (or open a new terminal)"
fi

# ── 7. Smoke test ─────────────────────────────────────────────────────────────
header "7. Smoke test — devstral"

info "Sending a test prompt to devstral…"
RESULT=$(curl -s http://localhost:11434/api/generate \
  -d '{"model":"devstral","prompt":"Reply with exactly: CODING TOOLS OK","stream":false}' \
  2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','').strip())" 2>/dev/null || true)

if [[ "$RESULT" == *"OK"* ]]; then
  log "Devstral responded: $RESULT"
else
  warn "Unexpected response: '${RESULT}' — model may still be loading, retry manually"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════╗"
echo   "║  Phase 2 complete! Coding tools ready.  ║"
echo -e "╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}What's set up:${NC}"
echo "  • Continue.dev config  → ~/.continue/config.json"
echo "  • VS Code shortcut:    Cmd+L (chat), Cmd+I (inline edit)"
echo "  • Tab autocomplete:    SmolLM2 1.7B (fast)"
echo "  • OpenCode:            opencode  (uses devstral)"
echo "  • Aider aliases:       aider-code / aider-think"
echo ""
echo -e "${BOLD}Next step:${NC} source ~/.zshrc  →  then run: ${BLUE}opencode${NC}"
