
# ── Local-AI stack start / stop (v2 — includes dashboard) ──
_local_ai_secret_file="$HOME/Documents/AI/Local-AI/.secrets"

_local_ai_control_token() {
  mkdir -p "$(dirname "$_local_ai_secret_file")"
  touch "$_local_ai_secret_file"
  chmod 600 "$_local_ai_secret_file"
  if ! grep -q '^CONTROL_TOKEN=' "$_local_ai_secret_file" 2>/dev/null; then
    if command -v openssl >/dev/null 2>&1; then
      printf 'CONTROL_TOKEN=%s\n' "$(openssl rand -hex 32)" >> "$_local_ai_secret_file"
    else
      printf 'CONTROL_TOKEN=%s%s\n' "$(uuidgen | tr -d '-')" "$(uuidgen | tr -d '-')" >> "$_local_ai_secret_file"
    fi
    echo '→ Generated CONTROL_TOKEN in .secrets' >&2
  fi
  grep '^CONTROL_TOKEN=' "$_local_ai_secret_file" | tail -1 | cut -d= -f2-
}

ai-stack-start() {
  local control_token
  control_token="$(_local_ai_control_token)"
  echo '→ Starting LM Studio...'
  ai-use-mlx >/dev/null
  if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo '✓ LM Studio server already running on :1234'
  elif [[ -d "/Applications/LM Studio.app" ]]; then
    open -ga "LM Studio"
    echo '→ LM Studio launched — enable Developer tab → Start Server (port 1234)'
  else
    echo '✗ LM Studio not installed. Run: bash scripts/phase6-improvements.sh'
  fi
  sleep 2
  echo '→ Starting Podman machine...'
  /opt/homebrew/bin/podman machine start 2>/dev/null || true
  echo '→ Starting Open WebUI...'
  /opt/homebrew/bin/podman start open-webui 2>/dev/null || true
  echo '→ Starting Pipelines...'
  /opt/homebrew/bin/podman start open-webui-pipelines 2>/dev/null || true
  echo '→ Starting dashboard...'
  if /opt/homebrew/bin/podman inspect local-ai-dashboard > /dev/null 2>&1; then
    if ! /opt/homebrew/bin/podman inspect --format '{{range .Config.Env}}{{println .}}{{end}}' local-ai-dashboard 2>/dev/null | grep -q '^LMSTUDIO_BASE_URL='; then
      echo '→ Recreating dashboard with LM Studio model support...'
      /opt/homebrew/bin/podman rm -f local-ai-dashboard 2>/dev/null || true
    fi
  fi
  /opt/homebrew/bin/podman inspect local-ai-dashboard > /dev/null 2>&1 || \
    /opt/homebrew/bin/podman run -d --name local-ai-dashboard \
      -p 9090:9090 \
      -e CONTROL_TOKEN="$control_token" \
      -e CONTROL_URL=http://host.containers.internal:9091 \
      -e LMSTUDIO_BASE_URL=http://host.containers.internal:1234/v1 \
      -v /private/tmp:/hosttmp:ro \
      localhost/local-ai-dashboard
  /opt/homebrew/bin/podman start local-ai-dashboard 2>/dev/null || true
  pkill -f "metrics-exporter.py" 2>/dev/null; sleep 1
  CONTROL_TOKEN="$control_token" CONTROL_BIND=0.0.0.0 \
    nohup python3 ~/Documents/AI/Local-AI/scripts/metrics-exporter.py > /tmp/ai-metrics-exporter.log 2>&1 &
  sleep 3
  echo '✓ Stack is up'
  echo '  Runtime     → LM Studio (:1234)'
  echo '  Open WebUI  → http://localhost:3000'
  echo '  Pipelines   → http://localhost:9099'
  echo '  Dashboard   → http://localhost:9090'
  open http://localhost:3000
}

ai-stack-stop() {
  echo '→ Unloading models...'
  for m in $(/opt/homebrew/bin/ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}'); do
    curl -s http://localhost:11434/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null
  done
  echo '→ Stopping Pipelines...'
  /opt/homebrew/bin/podman stop open-webui-pipelines 2>/dev/null || true
  echo '→ Stopping Open WebUI...'
  /opt/homebrew/bin/podman stop open-webui 2>/dev/null || true
  echo '→ Stopping Ollama...'
  pkill -x ollama 2>/dev/null || true
  echo '→ Stopping LM Studio...'
  osascript -e 'tell application "LM Studio" to quit' 2>/dev/null || true
  echo '✓ AI services stopped  (dashboard + metrics still running → http://localhost:9090)'
}

ai-stack-off() {
  ai-stack-stop
  echo '→ Stopping dashboard...'
  pkill -f "metrics-exporter.py" 2>/dev/null || true
  /opt/homebrew/bin/podman stop local-ai-dashboard 2>/dev/null || true
  echo '→ Stopping Podman machine...'
  /opt/homebrew/bin/podman machine stop 2>/dev/null || true
  echo '✓ Stack fully off'
}

ai-menubar-start() {
  if pgrep -f "menubar/app.py" > /dev/null 2>&1; then
    echo 'Menu bar app is already running'
    return
  fi
  nohup python3 ~/Documents/AI/Local-AI/menubar/app.py > /tmp/ai-menubar.log 2>&1 &
  echo "✓ Menu bar app started (log → /tmp/ai-menubar.log)"
}

ai-menubar-stop() {
  launchctl bootout "gui/$(id -u)/local-ai-menubar" 2>/dev/null || true
  launchctl remove local-ai-menubar 2>/dev/null || true
  pkill -f "menubar/app.py" 2>/dev/null && echo '✓ Menu bar app stopped' || echo 'Not running'
}

# ── Phase 6: LM Studio (MLX backend) integration ──
ai-mlx-up() {
  if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo '✓ LM Studio server already running on :1234'
    return
  fi
  if [[ -d "/Applications/LM Studio.app" ]]; then
    open -ga "LM Studio"
    echo '→ LM Studio launched — enable Developer tab → Start Server (port 1234)'
  else
    echo '✗ LM Studio not installed. Run: bash scripts/phase6-improvements.sh'
  fi
}

ai-mlx-down() {
  osascript -e 'tell application "LM Studio" to quit' 2>/dev/null \
    && echo '✓ LM Studio stopped' || echo 'Not running'
}

ai-mlx-status() {
  curl -s http://localhost:1234/v1/models 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('Loaded models:'); [print(' •', m['id']) for m in d.get('data',[])]" \
    2>/dev/null || echo '✗ LM Studio server not reachable on :1234'
}

_local_ai_backend_file="$HOME/.config/local-ai/active-backend"

_local_ai_apply_backend() {
  local backend="${1:-}"
  [[ -z "$backend" && -f "$_local_ai_backend_file" ]] && backend="$(<"$_local_ai_backend_file")"
  case "$backend" in
    lmstudio|mlx)
      export OPENCODE_PROVIDER=openai-compatible
      export OPENCODE_API_BASE=http://localhost:1234/v1
      ;;
    ollama)
      export OPENCODE_PROVIDER=openai-compatible
      export OPENCODE_API_BASE=http://localhost:11434/v1
      ;;
    "")
      export OPENCODE_PROVIDER=openai-compatible
      export OPENCODE_API_BASE=http://localhost:1234/v1
      ;;
  esac
}

# Switch OpenCode between LM Studio (MLX) and Ollama backends.
ai-use-mlx() {
  mkdir -p "$(dirname "$_local_ai_backend_file")"
  printf 'lmstudio\n' > "$_local_ai_backend_file"
  _local_ai_apply_backend lmstudio
  echo "→ OpenCode now using LM Studio (MLX) at :1234"
}

ai-use-ollama() {
  mkdir -p "$(dirname "$_local_ai_backend_file")"
  printf 'ollama\n' > "$_local_ai_backend_file"
  _local_ai_apply_backend ollama
  echo "→ OpenCode now using Ollama at :11434"
}

_local_ai_apply_backend

# mlx-lm direct generation (Apple MLX framework) with an approved Gemma model.
alias ai-mlx='mlx_lm.generate --model mlx-community/gemma-3-12b-it-4bit --prompt'

# Pi coding agent (lighter base prompt than OpenCode).
alias ai-pi='pi'

# Load secrets (TAVILY_API_KEY etc.) into the current shell.
alias ai-secrets='set -a; source ~/Documents/AI/Local-AI/.secrets; set +a; echo "→ secrets loaded"'

# Health check for Phase 6 services.
ai-health-phase6() {
  echo "── Phase 6 services ──"
  curl -s http://localhost:1234/v1/models > /dev/null 2>&1 \
    && echo "✓ LM Studio (MLX) on :1234" \
    || echo "✗ LM Studio not running"
  command -v pi >/dev/null && echo "✓ Pi installed" || echo "✗ Pi not installed"
  python3 -c "import mlx_lm" 2>/dev/null && echo "✓ mlx-lm installed" || echo "✗ mlx-lm not installed"
  [[ -n "${TAVILY_API_KEY:-}${BRAVE_API_KEY:-}" ]] \
    && echo "✓ Web search API key present" \
    || echo "✗ No web search API key (run: ai-secrets)"
}
