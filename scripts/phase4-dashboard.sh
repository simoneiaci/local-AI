#!/usr/bin/env bash
# =============================================================================
# Local-AI Phase 4 — Dashboard
# Builds the dashboard container image and starts:
#   1. metrics-exporter.py  (host process — writes /tmp/ai-metrics.json)
#   2. local-ai-dashboard   (Podman container — serves http://localhost:9090)
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
log()  { echo -e "${GREEN}✓${NC} $*"; }
info() { echo -e "${BLUE}→${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DASHBOARD_DIR="$SCRIPT_DIR/../dashboard"
EXPORTER="$SCRIPT_DIR/metrics-exporter.py"
CONTAINER_NAME="local-ai-dashboard"
IMAGE_NAME="local-ai-dashboard:latest"
METRICS_DIR="/private/tmp"
PORT=9090

echo -e "\n${BOLD}╔══════════════════════════════════════╗"
echo   "║  Local-AI  •  Phase 4: Dashboard     ║"
echo -e "╚══════════════════════════════════════╝${NC}\n"

# ── 1. Start metrics exporter on host ────────────────────────────────────────
info "Starting metrics exporter (background)..."

# Kill any existing exporter
pkill -f "metrics-exporter.py" 2>/dev/null || true
sleep 1

# Start fresh
nohup python3 "$EXPORTER" > /tmp/ai-metrics-exporter.log 2>&1 &
EXPORTER_PID=$!

METRICS_FILE="/tmp/ai-metrics.json"

# Wait for first write
for i in $(seq 1 10); do
  sleep 1
  [[ -f "$METRICS_FILE" ]] && break
done

if [[ -f "$METRICS_FILE" ]]; then
  log "Metrics exporter running (PID $EXPORTER_PID) → $METRICS_FILE"
else
  warn "Metrics file not yet written — creating placeholder"
  echo '{}' > "$METRICS_FILE"
fi

# ── 2. Ensure Podman machine is running ──────────────────────────────────────
info "Checking Podman machine..."
MACHINE_STATE=$(podman machine list --format '{{.Running}}' 2>/dev/null | head -1 || echo "false")
if [[ "$MACHINE_STATE" != "true" ]]; then
  info "Starting Podman machine..."
  podman machine start
fi
log "Podman machine running"

# ── 3. Build dashboard image ─────────────────────────────────────────────────
info "Building dashboard image (python:3.11-alpine, ~50 MB)..."
podman build -t "$IMAGE_NAME" "$DASHBOARD_DIR" --quiet
log "Image built: $IMAGE_NAME"

# ── 4. Remove old container if exists ────────────────────────────────────────
podman rm -f "$CONTAINER_NAME" 2>/dev/null || true

# ── 5. Run dashboard container ───────────────────────────────────────────────
# NOTE: Mount the parent /private/tmp as /hosttmp — Podman virtiofs cannot bind
# a single file on macOS (see AGENTS.md gotcha #1). The container reads
# /hosttmp/ai-metrics.json from that directory view.
info "Starting dashboard container on port $PORT..."
CONTROL_TOKEN_VALUE=""
SECRETS_FILE="$SCRIPT_DIR/../.secrets"
if [[ -f "$SECRETS_FILE" ]]; then
  CONTROL_TOKEN_VALUE=$(grep '^CONTROL_TOKEN=' "$SECRETS_FILE" | cut -d= -f2 || true)
fi

podman run -d \
  --name "$CONTAINER_NAME" \
  -p "${PORT}:9090" \
  -e OLLAMA_BASE_URL=http://host.containers.internal:11434 \
  -e CONTROL_URL=http://host.containers.internal:9091 \
  -e CONTROL_TOKEN="$CONTROL_TOKEN_VALUE" \
  -v "${METRICS_DIR}:/hosttmp:ro" \
  --restart=always \
  "$IMAGE_NAME"

# Wait for it to come up
for i in $(seq 1 10); do
  sleep 1
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$PORT 2>/dev/null || true)
  [[ "$STATUS" == "200" ]] && break
done

log "Dashboard container running"

# ── 6. Open browser ──────────────────────────────────────────────────────────
open "http://localhost:$PORT" 2>/dev/null || true

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════╗"
echo   "║  Dashboard is live!                          ║"
echo -e "╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}URL:${NC}      http://localhost:${PORT}"
echo -e "  ${BOLD}Refresh:${NC}  every 5 seconds (auto)"
echo -e "  ${BOLD}Shows:${NC}    CPU · RAM · Disk · Models · Services"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo   "  podman logs $CONTAINER_NAME       # container logs"
echo   "  podman stop $CONTAINER_NAME       # stop dashboard"
echo   "  pkill -f metrics-exporter.py     # stop host exporter"
echo   "  cat /tmp/ai-metrics-exporter.log  # exporter logs"
