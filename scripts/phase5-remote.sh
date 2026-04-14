#!/bin/zsh
# ============================================================
#  Local-AI — Phase 5 Setup: Remote Access
#  Configures Tailscale OR Caddy + DuckDNS for iPhone access
# ============================================================

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
CYAN="\033[0;36m"
RED="\033[0;31m"
RESET="\033[0m"

info()    { echo "${BLUE}ℹ ${RESET}$1"; }
success() { echo "${GREEN}✓ ${RESET}$1"; }
warn()    { echo "${YELLOW}⚠ ${RESET}$1"; }
section() { echo "\n${BOLD}═══ $1 ═══${RESET}"; }

# ─────────────────────────────────────────────
# Choose method
# ─────────────────────────────────────────────
echo ""
echo "${BOLD}Remote Access Setup${RESET}"
echo ""
echo "  How do you want to access your AI from iPhone?"
echo ""
echo "  ${BOLD}1)${RESET} Tailscale only    — private mesh VPN, 5 min setup"
echo "  ${BOLD}2)${RESET} Caddy+DDNS only   — public home IP, full HTTPS"
echo "  ${BOLD}3)${RESET} Cloudflare only   — zero-trust tunnel, no port forwarding"
echo "  ${BOLD}4)${RESET} Tailscale + Caddy — both (recommended)"
echo ""
printf "Choose [1/2/3/4]: "; read -r METHOD

# Expand option 4 into running both 1 and 2
RUN_TAILSCALE=false
RUN_CADDY=false
if   [[ "$METHOD" == "1" ]]; then RUN_TAILSCALE=true
elif [[ "$METHOD" == "2" ]]; then RUN_CADDY=true
elif [[ "$METHOD" == "3" ]]; then true  # handled below
elif [[ "$METHOD" == "4" ]]; then RUN_TAILSCALE=true; RUN_CADDY=true
else
  echo "${RED}Invalid choice. Run the script again and enter 1, 2, 3, or 4.${RESET}"
  exit 1
fi

# ─────────────────────────────────────────────
# OPTION 1 / 4: Tailscale
# ─────────────────────────────────────────────
if [[ "$RUN_TAILSCALE" == "true" ]]; then
  section "Tailscale Setup"

  # Ensure Ollama listens on all interfaces
  if ! grep -q "OLLAMA_HOST" ~/.zshrc; then
    echo 'export OLLAMA_HOST=0.0.0.0:11434' >> ~/.zshrc
    success "Added OLLAMA_HOST to ~/.zshrc"
  else
    success "OLLAMA_HOST already set in ~/.zshrc"
  fi

  # Restart Ollama to pick up new binding
  info "Restarting Ollama to apply OLLAMA_HOST..."
  brew services restart ollama
  sleep 2
  success "Ollama restarted"

  # Check if Tailscale CLI is available
  if command -v tailscale &>/dev/null; then
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "")
    if [[ -n "$TAILSCALE_IP" ]]; then
      success "Tailscale is active — your IP is: ${GREEN}${TAILSCALE_IP}${RESET}"
      echo ""
      echo "  ${BOLD}Open WebUI on iPhone:${RESET}"
      echo "  ${BLUE}http://${TAILSCALE_IP}:3000${RESET}"
      echo ""
      echo "  ${BOLD}Ollama API from iPhone:${RESET}"
      echo "  ${BLUE}http://${TAILSCALE_IP}:11434/v1${RESET}"
    else
      warn "Tailscale is installed but not connected. Run: tailscale up"
    fi
  else
    echo ""
    echo "  ${BOLD}Tailscale is not installed yet. Steps:${RESET}"
    echo ""
    echo "  1. Download the standalone .pkg installer (NOT App Store):"
    echo "     ${BLUE}open https://tailscale.com/download/mac${RESET}"
    echo ""
    echo "  2. Install and sign in via the menu bar"
    echo ""
    echo "  3. Install Tailscale on your iPhone (App Store)"
    echo "     Sign in with the same account"
    echo ""
    echo "  4. Run this script again to get your Tailscale IP"
    echo ""
    open "https://tailscale.com/download/mac" 2>/dev/null || true
  fi

  # Keep-awake reminder
  echo ""
  echo "  ${YELLOW}⚠ Keep Mac awake while using remotely:${RESET}"
  echo "  ${BLUE}caffeinate -s &${RESET}  (only works while plugged in)"
  echo ""
  echo "  Or: System Settings → Displays → Advanced"
  echo "      → Prevent automatic sleeping when display is off"

  # PWA tip
  echo ""
  echo "  ${BOLD}Make it a native-looking app on iPhone:${RESET}"
  echo "  Safari → Share → Add to Home Screen"
  echo "  Open WebUI runs fullscreen as a PWA — no browser toolbar."
fi

# ─────────────────────────────────────────────
# OPTION 2 / 4: Caddy + DuckDNS
# ─────────────────────────────────────────────
if [[ "$RUN_CADDY" == "true" ]]; then
  section "Caddy + DuckDNS Setup"

  # Install Caddy
  if ! command -v caddy &>/dev/null; then
    info "Installing Caddy..."
    brew install caddy
    success "Caddy installed"
  else
    success "Caddy already installed: $(caddy version)"
  fi

  # Get DuckDNS subdomain
  echo ""
  printf "Enter your DuckDNS subdomain (e.g. 'myai' for myai.duckdns.org): "; read -r SUBDOMAIN
  printf "Enter your DuckDNS token: "; read -r DUCKDNS_TOKEN
  HOSTNAME="${SUBDOMAIN}.duckdns.org"

  # Create Caddyfile
  CADDYFILE="$HOME/.config/local-ai/Caddyfile"
  mkdir -p "$HOME/.config/local-ai"

  cat > "$CADDYFILE" << EOF
${HOSTNAME} {
    reverse_proxy localhost:3000
}
EOF

  success "Caddyfile written to ${CADDYFILE}"

  # Create DuckDNS updater script
  DDNS_SCRIPT="$HOME/.config/local-ai/update-ddns.sh"
  cat > "$DDNS_SCRIPT" << DDNS
#!/bin/zsh
# Updates DuckDNS with your current public IP
TOKEN="${DUCKDNS_TOKEN}"
SUBDOMAIN="${SUBDOMAIN}"
RESULT=\$(curl -s "https://www.duckdns.org/update?domains=\${SUBDOMAIN}&token=\${TOKEN}&ip=")
echo "\$(date): \${RESULT}" >> \$HOME/.config/local-ai/ddns.log
DDNS
  chmod +x "$DDNS_SCRIPT"
  success "DuckDNS updater script written to ${DDNS_SCRIPT}"

  # Add cron job to update DDNS every 5 minutes
  (crontab -l 2>/dev/null; echo "*/5 * * * * $DDNS_SCRIPT") | crontab -
  success "Cron job added: DuckDNS updates every 5 minutes"

  # Run initial update
  "$DDNS_SCRIPT"
  success "Initial DuckDNS update sent"

  echo ""
  echo "  ${BOLD}Now:${RESET}"
  echo "  1. Forward ports ${BOLD}80${RESET} and ${BOLD}443${RESET} on your router → your Mac's local IP"
  echo "  2. Start Caddy:"
  echo "     ${BLUE}caddy run --config ${CADDYFILE}${RESET}"
  echo ""
  echo "  3. Your AI will be at:"
  echo "     ${GREEN}https://${HOSTNAME}${RESET}"
  echo ""
  warn "Test from a non-home network (mobile data). WiFi gives false results due to NAT loopback."
fi

# ─────────────────────────────────────────────
# OPTION 3: Cloudflare Tunnel
# ─────────────────────────────────────────────
if [[ "$METHOD" == "3" ]]; then
  section "Cloudflare Tunnel Setup"

  if ! command -v cloudflared &>/dev/null; then
    info "Installing cloudflared..."
    brew install cloudflare/warp/cloudflared
    success "cloudflared installed"
  else
    success "cloudflared already installed: $(cloudflared --version)"
  fi

  echo ""
  echo "  ${BOLD}Steps to complete setup:${RESET}"
  echo ""
  echo "  1. Login to Cloudflare (opens browser):"
  echo "     ${BLUE}cloudflared tunnel login${RESET}"
  echo ""
  echo "  2. Create a tunnel:"
  echo "     ${BLUE}cloudflared tunnel create my-ai-tunnel${RESET}"
  echo ""
  echo "  3. Create ${BOLD}~/.cloudflared/config.yml${RESET}:"
  echo ""
  echo "     ${CYAN}tunnel: my-ai-tunnel"
  echo "     credentials-file: ~/.cloudflared/<UUID>.json"
  echo ""
  echo "     ingress:"
  echo "       - hostname: myai.yourdomain.com"
  echo "         service: http://localhost:3000"
  echo "       - service: http_status:404${RESET}"
  echo ""
  echo "  4. Start the tunnel:"
  echo "     ${BLUE}cloudflared tunnel run my-ai-tunnel${RESET}"
  echo ""
  info "Opening Cloudflare login now..."
  cloudflared tunnel login || true

fi

echo ""
echo "${GREEN}${BOLD}════════════════════════════════════════${RESET}"
echo "${GREEN}${BOLD}  Remote access setup complete!${RESET}"
echo "${GREEN}${BOLD}════════════════════════════════════════${RESET}"
echo ""
