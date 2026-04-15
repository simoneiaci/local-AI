
# ── Local-AI stack start / stop (v2 — includes dashboard) ──
ai-stack-start() {
  echo '→ Starting Ollama...'
  pgrep -x ollama > /dev/null || (nohup /opt/homebrew/bin/ollama serve > /tmp/ollama.log 2>&1 &)
  sleep 2
  echo '→ Starting Podman machine...'
  /opt/homebrew/bin/podman machine start 2>/dev/null || true
  echo '→ Starting Open WebUI...'
  /opt/homebrew/bin/podman start open-webui 2>/dev/null || true
  echo '→ Starting Pipelines...'
  /opt/homebrew/bin/podman start open-webui-pipelines 2>/dev/null || true
  echo '→ Starting dashboard...'
  /opt/homebrew/bin/podman inspect local-ai-dashboard > /dev/null 2>&1 || \
    /opt/homebrew/bin/podman run -d --name local-ai-dashboard \
      -p 9090:9090 \
      -e CONTROL_TOKEN=$(grep CONTROL_TOKEN ~/Documents/AI/Local-AI/.secrets | cut -d= -f2) \
      -e CONTROL_URL=http://host.containers.internal:9091 \
      -v /private/tmp:/hosttmp:ro \
      localhost/local-ai-dashboard
  /opt/homebrew/bin/podman start local-ai-dashboard 2>/dev/null || true
  pkill -f "metrics-exporter.py" 2>/dev/null; sleep 1
  nohup python3 ~/Documents/AI/Local-AI/scripts/metrics-exporter.py > /tmp/ai-metrics-exporter.log 2>&1 &
  sleep 3
  echo '✓ Stack is up'
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
