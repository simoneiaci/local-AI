#!/usr/bin/env bash
# =============================================================================
# Local-AI Phase 6 — Community-Recommended Improvements
# Based on community-reported local AI practices.
#
#   1. LM Studio (MLX backend)   → 20-30% faster inference on Apple Silicon
#   2. mlx-lm CLI                → Direct MLX inference + OpenAI-compat server
#   3. Web search MCP            → Adds live lookup for stale model knowledge
#   4. Pi (pi.dev) coding agent  → Lighter base prompt than OpenCode
#   5. Speculative decoding      → smollm2:1.7b as draft for gemma3:12b
#   6. TurboQuant model variants → Lower VRAM, fits bigger models on 24 GB
#
# Idempotent — safe to re-run.
# =============================================================================

set -euo pipefail

if [[ -t 1 ]]; then
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  RED='\033[0;31m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  GREEN='' YELLOW='' BLUE='' RED='' BOLD='' NC=''
fi

log()    { echo -e "${GREEN}✓${NC} $*"; }
info()   { echo -e "${BLUE}→${NC} $*"; }
warn()   { echo -e "${YELLOW}⚠${NC} $*"; }
error()  { echo -e "${RED}✗${NC} $*"; }
header() { echo -e "\n${BOLD}$*${NC}"; }
ask()    { local p="$1"; local a; read -r -p "  $p (y/N) " a; [[ "$(echo "$a" | tr '[:upper:]' '[:lower:]')" == "y" ]]; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BOLD}"
echo "╔════════════════════════════════════════════════╗"
echo "║  Local-AI  •  Phase 6: Community Improvements  ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 0. Sanity checks ──────────────────────────────────────────────────────────
header "0. Pre-flight checks"

if [[ "$(uname -s)" != "Darwin" ]]; then
  error "Phase 6 is macOS-only (depends on MLX / Apple Silicon)"
  exit 1
fi

if [[ "$(uname -m)" != "arm64" ]]; then
  warn "Apple Silicon recommended — MLX requires arm64 for GPU acceleration"
fi

command -v brew >/dev/null || { error "Homebrew required. Install from https://brew.sh"; exit 1; }
log "Environment looks good"

# ── 1. LM Studio (MLX backend, faster than Ollama on Apple Silicon) ──────────
header "1. LM Studio — faster MLX backend"

if [[ -d "/Applications/LM Studio.app" ]]; then
  log "LM Studio already installed"
else
  if ask "Install LM Studio (~500 MB)?"; then
    info "Installing via Homebrew Cask..."
    brew install --cask lm-studio && log "LM Studio installed → /Applications/LM Studio.app"
    info "Open it once, enable 'Developer' tab, then enable the local server (port 1234)"
  else
    warn "Skipped LM Studio install"
  fi
fi

# ── 2. mlx-lm CLI (programmatic MLX) ──────────────────────────────────────────
header "2. mlx-lm — Apple's MLX CLI runtime"

if python3 -c "import mlx_lm" 2>/dev/null; then
  log "mlx-lm Python package already installed"
else
  if ask "Install mlx-lm (Python package)?"; then
    info "Installing via pipx (preferred) or pip..."
    if command -v pipx >/dev/null; then
      pipx install mlx-lm && log "mlx-lm installed via pipx"
    else
      pip3 install --break-system-packages --quiet mlx-lm && log "mlx-lm installed via pip"
    fi
    info "Quick test: mlx_lm.generate --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit --prompt 'hi'"
  else
    warn "Skipped mlx-lm install"
  fi
fi

# ── 3. Web search MCP (adds live lookup for stale model knowledge) ────────────
header "3. Web search MCP — shared config for local tools"

MCP_CFG_DIR="$HOME/.config/local-ai"
MCP_CFG="$MCP_CFG_DIR/mcp-servers.json"
MCP_WRAPPER="$REPO_ROOT/scripts/mcp-with-secrets.sh"
mkdir -p "$MCP_CFG_DIR"

if [[ -f "$MCP_CFG" ]]; then
  warn "Existing MCP config — backing up to $(basename "$MCP_CFG").bak"
  cp "$MCP_CFG" "$MCP_CFG.bak"
fi

# Tavily is recommended (1000 free searches/month, designed for LLMs)
cat > "$MCP_CFG" << EOF
{
  "_comment": "Web search MCP servers for local AI tools. Commands go through mcp-with-secrets.sh so .secrets is loaded before each server starts.",
  "mcpServers": {
    "tavily": {
      "_doc": "Get free key at https://tavily.com — 1000 searches/mo. Set TAVILY_API_KEY in .secrets",
      "command": "$MCP_WRAPPER",
      "args": ["npx", "-y", "tavily-mcp@latest"]
    },
    "brave-search": {
      "_doc": "Alternative — get free key at https://brave.com/search/api/ — 2000 searches/mo",
      "command": "$MCP_WRAPPER",
      "args": ["npx", "-y", "@modelcontextprotocol/server-brave-search"]
    },
    "fetch": {
      "_doc": "Free, no API key — fetches any URL as markdown. Pair with the search MCP above.",
      "command": "$MCP_WRAPPER",
      "args": ["uvx", "mcp-server-fetch"]
    }
  }
}
EOF
log "MCP config written → $MCP_CFG"

# Wire into Continue.dev (idempotent merge). Recent versions use config.yaml;
# older ones use config.json. Detect and act accordingly.
CONTINUE_JSON="$HOME/.continue/config.json"
CONTINUE_YAML="$HOME/.continue/config.yaml"

if [[ -f "$CONTINUE_JSON" ]]; then
  if grep -q '"mcpServers"' "$CONTINUE_JSON"; then
    log "Continue.dev (config.json) already has mcpServers — leaving alone"
  else
    info "Adding MCP reference to Continue.dev config.json..."
    cp "$CONTINUE_JSON" "$CONTINUE_JSON.bak.phase6"
    python3 - "$CONTINUE_JSON" "$MCP_CFG" << 'PYEOF'
import json, sys
cfg_path, mcp_path = sys.argv[1], sys.argv[2]
with open(cfg_path) as f: cfg = json.load(f)
with open(mcp_path) as f: mcp = json.load(f)
cfg["mcpServers"] = mcp.get("mcpServers", {})
with open(cfg_path, "w") as f: json.dump(cfg, f, indent=2)
PYEOF
    log "Continue.dev (config.json) now references web search MCPs (backup → .bak.phase6)"
  fi
elif [[ -f "$CONTINUE_YAML" ]]; then
  warn "Continue.dev uses config.yaml — automatic merge not implemented."
  warn "Add manually under the 'mcpServers' key. Reference: $MCP_CFG"
else
  warn "No Continue.dev config found — run phase2 first to wire MCP into it"
fi

info "Add API keys to ~/Documents/AI/Local-AI/.secrets:"
echo "    TAVILY_API_KEY=tvly-xxxxx"
echo "    BRAVE_API_KEY=BSAxxxxx"

# ── 4. Pi — lighter coding agent (lower base-prompt overhead) ────────────────
header "4. Pi (pi.dev) — lightweight coding agent"

if command -v pi >/dev/null 2>&1; then
  log "Pi already installed: $(pi --version 2>/dev/null || echo 'present')"
else
  warn "The Pi installer pipes a remote shell script to sh:"
  warn "    curl -fsSL https://pi.dev/install.sh | sh"
  warn "Inspect it first if you don't trust the source."
  if ask "Install Pi via the above piped install?"; then
    info "Installing Pi..."
    if curl -fsSL https://pi.dev/install.sh | sh; then
      log "Pi installed"
      info "Configure with: pi config set api_base http://localhost:11434/v1"
    else
      warn "Pi install script failed — see https://pi.dev for manual install"
    fi
  fi
fi

# ── 5. Speculative decoding (smollm2 as draft for gemma3) ────────────────────
header "5. Speculative decoding — 1.5–2× tok/s boost"

info "Speculative decoding pairs a small 'draft' model with the main model."
info "Your smollm2:1.7b can act as draft for gemma3:12b → faster inference."
echo ""
warn "Ollama doesn't yet expose speculative decoding flags."
warn "MLX-LM and llama.cpp do. Recommendation:"
echo ""
echo "  Once LM Studio is running, in its server config:"
echo "    Main model:  mlx-community/gemma-3-12b-it-4bit"
echo "    Draft model: mlx-community/SmolLM2-1.7B-Instruct-4bit"
echo "    Enable: 'Speculative Decoding' in advanced settings"
echo ""
log "Documented — manual GUI step in LM Studio"

# ── 6. TurboQuant variants (denser models that fit 24 GB) ────────────────────
header "6. TurboQuant model variants — fit bigger models on 24 GB"

info "TurboQuant (recent llama.cpp addition) reduces VRAM significantly."
info "On your 24 GB Mac (~14-16 GB usable), this opens up:"
echo ""
echo "    • Qwen2.5-Coder-14B-Instruct-MLX-4bit  ~8 GB   (Apache 2.0)"
echo "    • Gemma-4-26B-a4b-it                   ~15 GB  (approved, tight fit)"
echo "    • Mistral-Small-24B-MLX-4bit           ~13 GB"
echo ""
warn "Compliance note:"
warn "Qwen models are personal-use only under this project policy."
warn "For corporate hardware, follow your organization's approved-model policy."
echo ""

# Show free RAM before any 'tight on 24 GB' prompts.
FREE_GB=$(vm_stat 2>/dev/null | awk '
  /page size of/   { ps=$8 }
  /Pages free/     { free=$3 }
  /Pages inactive/ { inactive=$3 }
  END { if (ps && free) printf "%.1f", (free+inactive)*ps/1024/1024/1024 }')
[[ -n "$FREE_GB" ]] && info "Approx free RAM right now: ${FREE_GB} GB"
echo ""

if ask "Pull mlx-community/Qwen2.5-Coder-14B-Instruct-4bit via Ollama (Apache, ~8 GB) — personal use only per AGENTS.md?"; then
  /opt/homebrew/bin/ollama pull qwen2.5-coder:14b && log "qwen2.5-coder:14b pulled"
else
  warn "Skipped — pull manually with: ollama pull qwen2.5-coder:14b"
fi

warn "Skipping Gemma 27B pulls: project policy says Gemma 27B variants are marginal/risky on 24 GB and must not be loaded."

# ── 7. Shell aliases ──────────────────────────────────────────────────────────
header "7. Shell environment — Phase 6 aliases"

# Phase 6 aliases live in stack-aliases-v2.sh (sourced from ~/.zshrc).
# Verify the source line is present so a fresh clone works out of the box.
ZSHRC="$HOME/.zshrc"
ALIASES_FILE="$REPO_ROOT/stack-aliases-v2.sh"

if [[ ! -f "$ALIASES_FILE" ]]; then
  warn "stack-aliases-v2.sh missing from repo — Phase 6 aliases won't be available"
elif grep -qF "stack-aliases-v2.sh" "$ZSHRC" 2>/dev/null; then
  log "stack-aliases-v2.sh already sourced from ~/.zshrc"
else
  if ask "Add 'source $ALIASES_FILE' to ~/.zshrc?"; then
    printf '\n# ── Local-AI stack aliases ──\nsource %s\n' "$ALIASES_FILE" >> "$ZSHRC"
    log "Sourced stack-aliases-v2.sh from ~/.zshrc"
  else
    warn "Skipped — add 'source $ALIASES_FILE' to your shell rc manually"
  fi
fi

# Clean up the previous-phase6 inline block if it's still in ~/.zshrc.
if grep -q "# ── Local-AI phase 6 improvements ──" "$ZSHRC" 2>/dev/null; then
  warn "Found legacy Phase 6 alias block in ~/.zshrc — those now live in stack-aliases-v2.sh."
  warn "Remove the block manually to avoid duplicate definitions."
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔═════════════════════════════════════════════╗"
echo   "║  Phase 6 complete!                          ║"
echo -e "╚═════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}New tools installed (per your selections):${NC}"
echo "  • LM Studio          → /Applications/LM Studio.app   (port 1234)"
echo "  • mlx-lm             → mlx_lm.generate / mlx_lm.server"
echo "  • Web search MCP     → $MCP_CFG"
echo "  • Pi agent           → pi  (alias: ai-pi)"
echo "  • TurboQuant models  → ollama list"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo "  1. ${BLUE}source ~/.zshrc${NC}"
echo "  2. Add API keys to ${BLUE}~/Documents/AI/Local-AI/.secrets${NC}"
echo "  3. Open LM Studio once → enable Developer tab → start server on :1234"
echo "  4. ${BLUE}ai-use-mlx${NC} to switch OpenCode to LM Studio backend"
echo "  5. ${BLUE}ai-health-phase6${NC} to verify everything"
echo ""
