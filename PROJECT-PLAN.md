# Local-AI: Run LLMs Locally on MacBook Pro M4 Pro (24GB)

> **Author:** Simone  
> **Created:** April 12, 2026  
> **Hardware:** MacBook Pro M4 Pro — 24GB unified memory  
> **Goal:** Fully private, local AI stack for coding, chat, RAG, and productivity

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      YOUR MACBOOK PRO M4 PRO                     │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │   Ollama      │   │  LM Studio   │   │   MLX (optional)     │ │
│  │  (primary)    │   │  (GUI/explore)│   │   (speed experiments)│ │
│  │  port 11434   │   │  port 1234   │   │                      │ │
│  └──────┬───────┘   └──────┬───────┘   └──────────────────────┘ │
│         │                  │                                     │
│         └──────┬───────────┘                                     │
│                │  OpenAI-compatible API                           │
│                │  http://localhost:11434/v1                       │
│                │                                                 │
│  ┌─────────────┼──────────────────────────────────────────────┐  │
│  │             ▼          CONSUMERS                           │  │
│  │  ┌──────────────┐ ┌───────────┐ ┌────────────┐            │  │
│  │  │ Continue.dev  │ │ OpenCode  │ │   Aider    │  (coding)  │  │
│  │  └──────────────┘ └───────────┘ └────────────┘            │  │
│  │  ┌──────────────┐ ┌───────────┐ ┌────────────┐            │  │
│  │  │ Open WebUI   │ │AnythingLLM│ │   Khoj     │  (RAG/chat)│  │
│  │  └──────────────┘ └───────────┘ └────────────┘            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  MONITORING: macmon · Ollama /api/ps · Activity Monitor    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Memory Budget

With 24GB total, you need to plan around this:

| Component          | RAM Usage  | Notes                              |
|--------------------|------------|------------------------------------|
| macOS + system     | ~8 GB      | Varies with apps open              |
| LLM model (active) | 5–16 GB   | Depends on model size + quant      |
| RAG / embedding    | ~0.5–1 GB  | Small embedding model              |
| Apps & headroom    | ~2 GB      | Browsers, IDE, etc.                |

**Rule of thumb:** Keep total model VRAM under **14 GB** to avoid swapping. Swapping kills performance on LLMs.

---

## 3. Approved Models Only

> **IMPORTANT:** Only models from the organization's approved list are permitted.
> Models are classified as **Green** (fully approved) or **Yellow** (elevated risk, use with caution).
> Notably, **Qwen** and **DeepSeek** models are NOT on the approved list.

---

### 3a. Complete Gemma Family (All Green)

All Gemma models are Green-approved. Here's every variant and whether it runs on your 24GB M4 Pro:

| Model                    | Ollama name              | VRAM (Q4) | Fits 24GB? | Best for                          |
|--------------------------|--------------------------|-----------|------------|-----------------------------------|
| **Gemma 3 1B**           | `gemma3:1b`              | ~1 GB     | Easily     | Too small for most tasks — skip   |
| **Gemma 3 4B**           | `gemma3:4b`              | ~3 GB     | Easily     | Quick Q&A, multimodal (text+image)|
| **Gemma 2 9B**           | `gemma2:9b`              | ~6 GB     | Yes        | Solid general-purpose, text-only  |
| **Gemma 3 12B**          | `gemma3:12b`             | ~7 GB     | Yes        | **Best Gemma for daily use** — multimodal, strong instruction following (88.9% IFEval) |
| **Gemma 4 E4B**          | `gemma4:e4b-it`          | ~3 GB     | Easily     | Edge model — fast but shallow     |
| **Gemma 4 26B-A4B (MoE)**| `gemma4:26b-a4b-it`     | ~15 GB    | Tight      | MoE: only 4B active params → fast inference, near-31B quality. Close to RAM limit — close other apps. **Confirmed by Reddit user on M3 24GB: 10-20 tok/s via llama.cpp** |
| **Gemma 3 27B**          | `gemma3:27b`             | ~16 GB    | Marginal   | Best Gemma quality overall but leaves <8 GB for system — risky, may swap |
| **Gemma 4 31B**          | `gemma4:31b-it`          | ~20 GB    | No         | Too large — causes swapping, context suffers. Avoid. |
| Gemma 3n E2B/E4B (LiteRT)| —                       | —         | N/A        | On-device edge only (phones). **Not available on Ollama.** Skip. |
| Gemma 2 27B              | `gemma2:27b`             | ~17 GB    | Marginal   | Older generation — prefer Gemma 3 12B instead |
| Gemma 1.1 / 2B / 7B     | `gemma:7b` etc.          | ~5 GB     | Yes        | Older generation — no reason to use over Gemma 3 |

**Recommended Gemma picks:**
- **Daily driver:** `gemma3:12b` (~7 GB) — best quality-to-RAM ratio in the family
- **Lightweight:** `gemma3:4b` (~3 GB) — when you need speed or have other models loaded
- **Maximum quality:** `gemma4:26b-a4b-it` (~15 GB) — MoE efficiency, but close other apps first

---

### 3b. Other Approved Models — Green

| Model                   | Ollama name              | VRAM (Q4) | Speed (est.)  | Best for              |
|-------------------------|--------------------------|-----------|---------------|-----------------------|
| Phi 4 Mini              | `phi4-mini`              | ~3 GB     | ~30 tok/s     | Ultra-fast chat       |
| Granite 3.3 8B Instruct | `granite3.3:8b`          | ~6 GB     | ~18 tok/s     | Coding, RAG, 128K context, multilingual (12 langs) |
| Phi 4 Reasoning (14B)   | `phi4-reasoning`         | ~9 GB     | ~14 tok/s     | Math & reasoning (75.3% AIME 2024) |
| Mistral Small 3.1 24B   | `mistral-small3.1:24b`   | ~14 GB    | ~10 tok/s     | Best all-around model on the list |
| Magistral Small 2506    | `magistral:24b-small-2506`| ~14 GB   | ~10 tok/s     | Advanced reasoning (70.7% AIME 2024) |
| Devstral Small 1.1 (24B)| `devstral`         | ~14 GB    | ~10 tok/s     | **Best coder** (53.6% SWE-Bench) |
| Mistral NeMo            | `mistral-nemo`           | ~7 GB     | ~15 tok/s     | Good mid-range general model |

### 3c. Yellow-Risk Models (use with caution)

| Model                   | Ollama name              | VRAM (Q4) | Speed (est.)  | Notes                       |
|-------------------------|--------------------------|-----------|---------------|-----------------------------|
| Phi 4 (14B)             | `phi4`                   | ~5 GB     | ~22 tok/s     | Good chat model             |
| Phi 4 Reasoning Plus    | `phi4-reasoning-plus`    | ~9 GB     | ~14 tok/s     | Enhanced reasoning          |
| Llama 3.1 8B Instruct   | `llama3.1:8b`           | ~6 GB     | ~18 tok/s     | Solid general-purpose       |
| Llama 3.2 3B Instruct   | `llama3.2:3b`           | ~2 GB     | ~35 tok/s     | Ultra-light, fast           |
| CodeLlama 34B Instruct  | `codellama:34b`         | ~22 GB    | —             | **Won't fit** — avoid       |

### 3d. Tiny Models (autocomplete, embeddings) — Green

| Model                   | Ollama name              | Size     | Use case                            |
|-------------------------|--------------------------|----------|-------------------------------------|
| Phi 4 Mini Reasoning    | `phi4-mini-reasoning`    | ~3 GB    | Lightweight reasoning + autocomplete|
| SmolLM2 1.7B            | `smollm2:1.7b`          | ~1 GB    | Tab-completion in IDE               |
| Nomic Embed Text v1.5   | `nomic-embed-text`       | ~0.3 GB  | Embeddings for RAG                  |

### 3e. Models That DON'T Fit 24GB — Avoid

| Model              | Why                                           |
|--------------------|-----------------------------------------------|
| Gemma 4 31B        | ~20 GB at Q4 — context buffer pushes over limit|
| Gemma 3 27B        | ~16 GB at Q4 — marginal, swapping likely      |
| Gemma 2 27B        | ~17 GB at Q4 — older, same problem            |
| CodeLlama 34B/70B  | ~22 GB+ at Q4 — doesn't fit                   |
| Any 70B+ model     | Requires 48GB+ RAM                            |

---

### 3f. What's Best for What — Task Recommendation Guide

```
TASK                               → BEST MODEL                         → RUNNER-UP                    VRAM
────────────────────────────────────────────────────────────────────────────────────────────────────────────────
CODE GENERATION / DEBUGGING        → devstral (53.6% SWE-Bench)   → granite3.3:8b (lighter)      14 / 6 GB
CREATIVE WRITING / EMAILS          → mistral-small3.1:24b (87.6% Arena) → gemma3:12b (faster)          14 / 7 GB
REASONING / MATH / LOGIC           → phi4-reasoning (75.3% AIME)        → magistral:24b-small-2506     9 / 14 GB
SUMMARIZATION                      → gemma3:12b (88.9% IFEval)          → granite3.3:8b (128K ctx)     7 / 6 GB
INSTRUCTION FOLLOWING              → gemma3:12b (88.9% IFEval)          → mistral-small3.1:24b         7 / 14 GB
RAG / DOCUMENT Q&A                 → granite3.3:8b (RAG LoRAs, 128K)    → mistral-small3.1:24b         6 / 14 GB
FUNCTION / TOOL CALLING            → mistral-small3.1:24b (native)      → granite3.3:8b                14 / 6 GB
MULTILINGUAL                       → granite3.3:8b (12 languages)       → gemma3:12b                   6 / 7 GB
MULTIMODAL (text + images)         → gemma3:12b (native vision)         → gemma3:4b (lighter)          7 / 3 GB
QUICK Q&A / BRAINSTORMING          → phi4-mini (~3 GB, ~30 tok/s)       → gemma3:4b                    3 / 3 GB
TAB AUTOCOMPLETE IN IDE            → smollm2:1.7b (~1 GB, instant)      → phi4-mini-reasoning          1 / 3 GB
```

> **The "Two Model" Strategy:** Keep `gemma3:12b` as your always-loaded daily driver (~7 GB).
> When you need specialized power, swap to: `devstral` (coding), `phi4-reasoning` (math),
> or `mistral-small3.1:24b` (everything else). Only one 14 GB model at a time.

### Quantization Guide

- **Q4_K_M** — Sweet spot. ~4-bit, great quality-to-size ratio. Use this by default.
- **Q5_K_M** — Slightly better quality, ~20% larger. Use if model fits comfortably.
- **Q8_0** — Near-original quality, 2x size of Q4. Only for small models (≤7B).
- **MLX format** — ~25% faster than GGUF on models under 7B. Check `mlx-community` on HuggingFace.

---

## 4. Phase 1 — Foundation Setup

### 4.1 Install Ollama (Primary Runtime)

```bash
# Install Ollama
brew install ollama

# Start the server (runs in background)
ollama serve

# Or set it to auto-start
brew services start ollama
```

Ollama exposes an **OpenAI-compatible API** at:
```
http://localhost:11434/v1
```

### 4.2 Pull Your First Models

```bash
# Daily driver — fast general chat (Green, ~3 GB)
ollama pull phi4-mini

# General-purpose workhorse (Green, ~8 GB)
ollama pull gemma3:12b

# Coding specialist (Green, ~14 GB)
ollama pull devstral

# Power model — general + reasoning (Green, ~14 GB)
ollama pull mistral-small3.1:24b

# Reasoning specialist (Green, ~9 GB)
ollama pull phi4-reasoning

# Small model for tab-autocomplete (Green, ~1 GB)
ollama pull smollm2:1.7b

# Embedding model for RAG (Green, ~0.3 GB)
ollama pull nomic-embed-text
```

### 4.3 Install LM Studio (GUI + Exploration)

Download from [lmstudio.ai](https://lmstudio.ai). Use it for:
- Browsing & downloading models visually
- Quick A/B testing between models
- Trying MLX-format models (faster on small models)
- It also serves an OpenAI API on port `1234`

### 4.4 Model Switching Strategy

Ollama handles model switching automatically — when you request a model, it loads it and unloads the previous one. To control this explicitly:

```bash
# See what's currently loaded
ollama ps

# Preload a model
ollama run devstral --keepalive 0  # load then immediately make available

# Force unload everything (free RAM)
curl http://localhost:11434/api/generate -d '{"model":"phi4-mini","keep_alive":0}'
```

**Create aliases for quick switching** (add to `~/.zshrc`):

```bash
# Model shortcuts (all approved Green models)
alias ai-chat="ollama run phi4-mini"              # ~3 GB, ultra-fast
alias ai-general="ollama run gemma3:12b"           # ~8 GB, balanced
alias ai-code="ollama run devstral"          # ~14 GB, coding
alias ai-reason="ollama run phi4-reasoning"        # ~9 GB, chain-of-thought
alias ai-power="ollama run mistral-small3.1:24b"   # ~14 GB, best overall

# Management
alias ai-status="ollama ps"
alias ai-stop="pkill ollama"
```

---

## 5. Phase 2 — Coding Tools

### 5.1 Continue.dev (VS Code — Recommended)

Install from VS Code marketplace. Create `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "Devstral Small 1.1 (coding)",
      "provider": "ollama",
      "model": "devstral",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Mistral Small 3.1 (general)",
      "provider": "ollama",
      "model": "mistral-small3.1:24b",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Gemma 3 12B (balanced)",
      "provider": "ollama",
      "model": "gemma3:12b",
      "apiBase": "http://localhost:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "SmolLM2 1.7B (fast autocomplete)",
    "provider": "ollama",
    "model": "smollm2:1.7b",
    "apiBase": "http://localhost:11434"
  }
}
```

This gives you: a local coding chat (Cmd+L), inline editing (Cmd+I), and tab-autocomplete — all running locally with approved models only.

### 5.2 OpenCode (CLI)

```bash
# Install
go install github.com/opencode-ai/opencode@latest
# OR
brew install opencode

# Configure for local Ollama
export OPENCODE_PROVIDER=openai-compatible
export OPENCODE_API_BASE=http://localhost:11434/v1
export OPENCODE_MODEL=devstral
```

OpenCode needs models with **tool calling** support and **64K+ context**. Devstral Small 1.1 and Mistral Small 3.1 both support this.

### 5.3 Aider (CLI — Pair Programming)

```bash
pip install aider-chat --break-system-packages

# Run with local approved coding model
aider --model ollama/devstral
```

### 5.4 Cline / Roo Code (VS Code)

Both support Ollama. In VS Code settings, configure:
- API Provider: `OpenAI Compatible`
- Base URL: `http://localhost:11434/v1`
- Model: `devstral`

Note: These are context-heavy tools. Use Devstral Small or Mistral Small 3.1 for best results.

### 5.5 Tabby (Self-Hosted Code Completion)

```bash
# Install via Homebrew
brew install tabbyml/tabby/tabby

# Run with Metal GPU acceleration (using approved small model)
tabby serve --model SmolLM2-1.7B --device metal
```

Tabby provides IDE-integrated code completion similar to GitHub Copilot, entirely local.

### 5.6 Workflow Patterns — Plan + Build

Real-world users of coding agents (see r/opencodeCLI discussions) consistently land on a two-phase workflow: one model reasons about the plan, a second model executes it. This splits cognitive vs. mechanical work and keeps each model in its comfort zone.

Adapted to the approved-model roster on a 24 GB M4 Pro:

| Phase           | Model                                | Why                                                  |
|-----------------|--------------------------------------|------------------------------------------------------|
| **Plan / think**| `phi4-reasoning` (14B)               | 75.3% AIME 2024 — strong step-by-step reasoning      |
| **Build / code**| `devstral` (24B)                     | 53.6% SWE-Bench — best approved coder                |
| **Debug / review** | `mistral-small3.1:24b`            | 128K context, broad knowledge, good at tracing bugs  |

Practical OpenCode example:

```bash
# Plan mode — draft the approach, no code yet
OPENCODE_MODEL=phi4-reasoning opencode "Design a retry layer for the API client"

# Switch to devstral to implement
ai-use-coding   # alias from Phase 2 → sets OPENCODE_MODEL=devstral
opencode "Now implement the plan we just designed"
```

### 5.7 Context Budget — Keep Prompts Under ~100K Tokens

Reddit practitioners consistently report that even models advertising 128K context degrade noticeably after ~100K (hallucinations, language drift, lost references). Approved models and their realistic effective context:

| Model                        | Advertised | Recommended working budget |
|------------------------------|------------|----------------------------|
| `gemma3:12b`                 | 128K       | ≤ 32K (sweet spot)         |
| `mistral-small3.1:24b`       | 128K       | ≤ 100K                     |
| `granite3.3:8b`              | 128K       | ≤ 100K                     |
| `phi4-reasoning`             | 16K        | ≤ 16K (hard limit)         |
| `devstral`                   | 32K        | ≤ 32K                      |

Practical rules:
- **Summarize, don't stuff** — ask the model to produce a running summary every ~20K tokens and restart the session with that summary as the new seed.
- **Split large repos** — feed directory listings + file headers first, then pull in specific files on demand.
- **Reserve 20% of context for the output** — a 32K-context model writing a 4K patch has only 28K for inputs.

---

## 6. Phase 3 — Chat & RAG

### 6.1 Open WebUI (Primary Chat Interface)

```bash
# Start Podman machine first (macOS requirement)
podman machine start

# Run Open WebUI via Podman
# host.containers.internal resolves to the Mac host automatically — no --add-host needed
podman run -d -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://host.containers.internal:11434 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart=always \
  ghcr.io/open-webui/open-webui:main
```

Open `http://localhost:3000`. Features:
- Beautiful ChatGPT-like UI for all your local models
- Built-in RAG: upload documents and chat with them
- Supports hybrid search (BM25 + semantic) with re-ranking
- Model switching via dropdown
- Conversation history, sharing, user management

### 6.2 AnythingLLM (All-in-One RAG)

Download from [useanything.com](https://useanything.com). Configure:
- LLM Provider → Ollama → `http://127.0.0.1:11434`
- Embedding → Ollama → `nomic-embed-text`
- Vector DB → built-in LanceDB (no setup needed)

Drag & drop PDFs, markdown, code files → instant private knowledge base.

### 6.3 Khoj (AI Assistant + RAG)

```bash
pip install khoj --break-system-packages

# Configure to use Ollama with approved model
# Edit ~/.khoj/khoj.yml:
#   chat-model: http://localhost:11434/v1
#   model: gemma3:12b
```

Khoj can index your notes, files, and even web content. Works with Obsidian via plugin.

> **Note:** Configure all RAG tools to use approved models only. Use `gemma3:12b` or `mistral-small3.1:24b` as the chat model, and `nomic-embed-text` for embeddings.

---

## 7. Phase 4 — Monitoring & Management

### 7.1 System Monitoring

```bash
# Install macmon (no sudo required, real-time Apple Silicon metrics)
brew install vladkens/tap/macmon

# Run it
macmon
# Shows: CPU%, GPU%, ANE%, Memory pressure, Power draw — live
```

### 7.2 Ollama Monitoring

```bash
# Check loaded models and their memory usage
ollama ps

# API endpoint for programmatic monitoring
curl http://localhost:11434/api/ps | python3 -m json.tool
```

### 7.3 Memory Management Best Practices

```bash
# Set environment variables (add to ~/.zshrc)

# Auto-unload models after 5 minutes of inactivity (saves RAM)
export OLLAMA_KEEP_ALIVE=5m

# Limit concurrent models (important for 24GB!)
export OLLAMA_MAX_LOADED_MODELS=1

# Set number of GPU layers (99 = all layers on GPU)
export OLLAMA_NUM_GPU=99
```

### 7.4 Performance Benchmarking

Quick benchmark script to test your models:

```bash
#!/bin/bash
# save as ~/Local-AI/benchmark.sh

models=("phi4-mini" "gemma3:12b" "devstral" "phi4-reasoning")
prompt="Write a Python function that implements binary search on a sorted list."

for model in "${models[@]}"; do
  echo "=== Benchmarking: $model ==="
  time ollama run "$model" "$prompt" --verbose 2>&1 | tail -5
  echo ""
  # Unload after test
  curl -s http://localhost:11434/api/generate -d "{\"model\":\"$model\",\"keep_alive\":0}" > /dev/null
done
```

### 7.5 Optional: Prometheus + Grafana Dashboard

For serious monitoring, set up the Ollama Metrics sidecar:

```bash
# Clone and run the metrics exporter
git clone https://github.com/NorskHelsenett/ollama-metrics
cd ollama-metrics
podman compose up -d
```

This exposes metrics like `ollama_loaded_models`, `ollama_model_ram_mb`, and inference speed to Grafana.

---

## 8. Phase 5 — Remote Access (AI in Your Pocket)

Access your local AI from your **iPhone or any device**, anywhere — using Tailscale.
This is inspired by the r/ollama community: users running Gemma4 on their Macs and chatting from their phones via Tailscale.

### 8.1 Install Tailscale

```bash
# Download the standalone version (NOT the App Store version)
# https://tailscale.com/download/mac — use the .pkg installer

# After install, launch Tailscale from the menu bar and sign in
# Grant system extension permission: Settings → General → Network Extensions
```

Install Tailscale on your iPhone too (App Store → Tailscale). Sign in with the same account. Both devices are now on a private encrypted mesh network.

### 8.2 Configure Ollama for Remote Access

By default Ollama only listens on `localhost`. You need to allow connections from Tailscale:

```bash
# Add to ~/.zshrc (if not already there)
export OLLAMA_HOST=0.0.0.0:11434

# Restart Ollama
brew services restart ollama
```

### 8.3 Access Open WebUI from Your Phone

1. Find your Mac's Tailscale IP: click the Tailscale menu bar icon → it shows something like `100.x.y.z`
2. On your iPhone, open Safari and go to: `http://100.x.y.z:3000`
3. Open WebUI loads with all your models available

**Make it feel like a native app (PWA):**
1. In Safari on your iPhone, tap the Share button → "Add to Home Screen"
2. Open WebUI installs as a Progressive Web App — launches fullscreen, no Safari toolbar
3. You now have a "ChatGPT-like" icon on your home screen that talks to YOUR local models

### 8.4 Keep Your Mac Awake for Remote Access

Your MacBook needs to be awake and Ollama needs to be running. When plugged in:

```bash
# Keep Mac awake while plugged in (run in background)
caffeinate -s &

# Or set via System Settings:
# System Settings → Displays → Advanced → Prevent automatic sleeping when the display is off
```

### 8.5 Security Notes

- Tailscale uses **end-to-end WireGuard encryption** — traffic is secure even on public WiFi
- Your services are **only visible to your Tailscale network** — not exposed to the internet
- **Do NOT use Tailscale Funnel** (that exposes to the public internet — unnecessary here)
- No API keys needed since only your devices can reach the services

### 8.6 What This Gives You

```
┌──────────────┐     Tailscale      ┌──────────────────────┐
│  Your iPhone │ ◄──(encrypted)───► │  Your MacBook Pro    │
│  (anywhere)  │     WireGuard      │  running Ollama +    │
│              │                    │  Open WebUI          │
│  Safari PWA  │                    │  on 100.x.y.z:3000  │
│  = native    │                    │                      │
│    chat app  │                    │  Models loaded:      │
│              │                    │  gemma3:12b / etc.   │
└──────────────┘                    └──────────────────────┘
```

Private, encrypted, no cloud involved. Your own ChatGPT in your pocket.

### 8.7 Alternative: Cloudflare Tunnel (Zero-Trust, No Port Forwarding)

If you prefer not to install Tailscale on every device, Cloudflare Tunnel creates an outbound connection from your Mac to Cloudflare — no port forwarding needed.

```bash
# Install cloudflared
brew install cloudflare/warp/cloudflared

# Login (opens browser)
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create my-ai-tunnel
```

Create `~/.cloudflared/config.yml`:
```yaml
tunnel: my-ai-tunnel
credentials-file: ~/.cloudflared/<UUID>.json

ingress:
  - hostname: myai.yourdomain.com
    service: http://localhost:3000
  - service: http_status:404
```

```bash
# Run the tunnel
cloudflared tunnel run my-ai-tunnel
```

Now `https://myai.yourdomain.com` is live — automatic HTTPS, no port forwarding, free tier.

### 8.8 Alternative: Caddy Reverse Proxy + DDNS (Public IP)

Since you have a **public IP at home**, this gives you the most control:

```bash
# Install Caddy
brew install caddy
```

Create a `Caddyfile`:
```
myai.duckdns.org {
    reverse_proxy localhost:3000
}
```

```bash
# Run Caddy (handles HTTPS automatically via Let's Encrypt)
caddy run --config Caddyfile
```

**Required setup:**
1. **Dynamic DNS:** Register at [duckdns.org](https://www.duckdns.org) (free) — maps a hostname to your public IP
2. **Port forwarding:** Forward ports **80** and **443** on your router to your Mac's local IP
3. **Open WebUI auth:** Open WebUI has built-in user accounts — set a strong password

**Security checklist:**
- Caddy handles HTTPS automatically (Let's Encrypt) — all traffic encrypted
- Open WebUI's built-in authentication protects against unauthorized access
- Consider adding `basic_auth` in Caddy as a second layer
- Test from a non-home network (don't test on WiFi — NAT loopback gives false results)

### 8.9 Which Remote Method to Use?

| Method             | Security        | Setup  | Port Forwarding | Best for                        |
|--------------------|-----------------|--------|-----------------|----------------------------------|
| **Tailscale**      | E2E encrypted   | 5 min  | Not needed      | Personal use, simplest           |
| **Cloudflare Tunnel** | Zero-trust   | 15 min | Not needed      | No port forwarding, free         |
| **Caddy + DDNS**   | HTTPS/TLS       | 20 min | Ports 80 + 443  | Full control with your public IP |

**Recommendation:** Start with Tailscale (simplest). If you want to use your public IP later, add Caddy + DuckDNS.

---

## 9. Quick Reference: Connecting Any Tool to Local Models

Any tool that supports the **OpenAI API** can use your local models. Just set:

| Setting        | Value                                |
|----------------|--------------------------------------|
| API Base URL   | `http://localhost:11434/v1`          |
| API Key        | `ollama` (or any non-empty string)   |
| Model          | e.g. `devstral`                |

For tools that need a proxy to multiple backends, use **LiteLLM**:

```bash
pip install litellm --break-system-packages

# Proxy that routes to Ollama
litellm --model ollama/devstral --port 4000
```

Now any tool can hit `http://localhost:4000/v1` with standard OpenAI SDK calls.

---

## 10. Recommended Setup Order

| Step | Action                                         | Time   |
|------|------------------------------------------------|--------|
| 1    | Install Ollama + pull `phi4-mini`              | 10 min |
| 2    | Pull coding model (`devstral`)           | 15 min |
| 3    | Pull general model (`gemma3:12b`)              | 10 min |
| 4    | Set up shell aliases + env vars                | 5 min  |
| 5    | Install Continue.dev in VS Code                | 10 min |
| 6    | Install Open WebUI (Podman)                    | 10 min |
| 7    | Pull embedding model + test RAG                | 10 min |
| 8    | Install macmon for monitoring                  | 5 min  |
| 9    | (Optional) Pull power models (`mistral-small3.1:24b`, `phi4-reasoning`) | 15 min |
| 10   | (Optional) Install OpenCode / Aider            | 10 min |
| 11   | (Optional) Set up AnythingLLM for RAG          | 15 min |
| 12   | (Optional) Install Tailscale for remote access | 10 min |
| 13   | (Optional) Prometheus + Grafana                | 30 min |

**Total for core setup: ~1 hour**

---

## 11. Model Switching Cheat Sheet

```
SITUATION                          → MODEL TO USE                           RISK    VRAM
──────────────────────────────────────────────────────────────────────────────────────────
Quick question / brainstorm        → phi4-mini (~3 GB, ultra-fast)          Green   ~3 GB
Write an email / document          → gemma3:12b (good prose)                Green   ~8 GB
General-purpose workhorse          → mistral-small3.1:24b (best overall)    Green   ~14 GB
Code generation / refactoring      → devstral (best approved coder)   Green   ~14 GB
Lighter coding tasks               → granite3.3:8b (code-aware, smaller)    Green   ~6 GB
Tab autocomplete in IDE            → smollm2:1.7b (instant)                 Green   ~1 GB
Deep reasoning / math              → phi4-reasoning (chain-of-thought)      Green   ~9 GB
Advanced reasoning                 → magistral:24b-small-2506 (Mistral)     Green   ~14 GB
```

> **Remember:** Only load ONE large model (14 GB+) at a time. Switch between them using the aliases.

---

## 12. Key Links & Resources

- **Ollama:** https://ollama.com
- **LM Studio:** https://lmstudio.ai
- **Continue.dev:** https://continue.dev
- **Open WebUI:** https://openwebui.com
- **AnythingLLM:** https://useanything.com
- **OpenCode:** https://github.com/opencode-ai/opencode
- **Aider:** https://aider.chat
- **Tabby:** https://tabby.tabbyml.com
- **macmon:** https://github.com/vladkens/macmon
- **Tailscale:** https://tailscale.com
- **MLX Community Models:** https://huggingface.co/mlx-community
