# ⚡ Local-AI

> **Run powerful LLMs privately on a MacBook Pro M4 Pro — for coding, chat, RAG, and productivity. No cloud. No API costs. Works on your iPhone too.**

[![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-black?logo=apple)](https://www.apple.com/mac/)
[![Ollama](https://img.shields.io/badge/Ollama-v0.20+-white?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0id2hpdGUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iOCIgY3k9IjgiIHI9IjgiLz48L3N2Zz4=)](https://ollama.com)
[![Podman](https://img.shields.io/badge/Podman-5.x-892CA0?logo=podman)](https://podman.io)
[![License](https://img.shields.io/badge/license-Personal-gray)](#)

---

## What This Is

A complete, production-ready local AI stack on Apple Silicon:

| Component | What it does |
|-----------|-------------|
| **LM Studio** | Default runtime for MLX models and OpenAI-compatible local API |
| **Ollama** | Alternate local runtime and model manager |
| **Open WebUI** | ChatGPT-like interface, runs in Podman |
| **Continue.dev** | AI assistant inside VS Code (Cmd+L / Cmd+I) |
| **OpenCode + Aider** | Terminal AI coding agents |
| **Dashboard** | Live system monitor at `localhost:9090` |
| **Tailscale / Caddy** | Access your AI from iPhone, anywhere |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/<your-org-or-user>/local-ai.git
cd local-AI

# 2. Run Phase 1 — Ollama + core models
bash scripts/phase1-setup.sh

# 3. Run Phase 2 — Coding tools (Continue.dev, OpenCode, Aider)
bash scripts/phase2-coding-tools.sh

# 4. Run Phase 3 — Open WebUI in Podman
bash scripts/phase3-webui.sh

# 5. Run Phase 4 — Live dashboard
bash scripts/phase4-dashboard.sh

# 6. Run Phase 5 — Remote access (Tailscale / Caddy / Cloudflare)
bash scripts/phase5-remote.sh

# 7. Run Phase 6 — Community improvements (LM Studio MLX, web search MCP, Pi, TurboQuant)
bash scripts/phase6-improvements.sh
```

After Phase 1, use these aliases from any terminal:

```bash
ai-stack-start      # start everything (LM Studio + WebUI + Dashboard)
ai-stack-stop       # stop AI services (dashboard stays up)
ai-stack-off        # full shutdown — everything off
ai-mlx-up           # launch LM Studio (MLX backend, faster than Ollama)
ai-mlx-down         # quit LM Studio
ai-mlx-status       # show MLX models loaded
ai-mlx              # one-shot mlx-lm generation (--prompt "...")
ai-use-mlx          # switch OpenCode to LM Studio backend (default)
ai-use-ollama       # switch OpenCode back to Ollama
ai-menubar-start    # launch menu bar app
ai-menubar-stop     # quit menu bar app
ai-health           # check all services at a glance
ai-health-phase6    # check Phase 6 services (MLX, Pi, mlx-lm, search MCP)
ai-monitor          # live GPU/CPU/RAM via macmon
```

---

## Hardware

| | |
|---|---|
| **Machine** | MacBook Pro M4 Pro |
| **RAM** | 24 GB unified memory |
| **Available for models** | ~14–16 GB (after macOS overhead) |
| **GPU** | Apple Silicon Neural Engine + Metal |

---

## Model Stack

| Role | Model | Size | Notes |
|------|-------|------|-------|
| Daily driver | `gemma3:12b` | 7 GB | Best all-round, multimodal |
| Coding | `gemma3:12b` | 7 GB | Coding + daily use, multimodal |
| Coding (alt) | `granite3.3:8b` | 6 GB | Tool-calling, 128K context, multilingual |
| Reasoning · Math · Logic | `phi4-reasoning` | 9 GB | Approved reasoning model that fits comfortably |
| Tab autocomplete | `smollm2:1.7b` | 1 GB | Instant, always loaded |
| Embeddings | `nomic-embed-text` | 0.3 GB | For RAG pipelines |

> ⚠️ Only one large model fits in RAM at a time. `smollm2:1.7b` and `nomic-embed-text` can always stay loaded alongside any model.

---

## Architecture

```
┌────────────────────────────────────────────────┐
│           MacBook Pro M4 Pro (24 GB)           │
│                                                │
│  LM Studio (:1234) ─► Open WebUI (:3000)       │
│       │                                        │
│       ├──► Continue.dev  (VS Code)             │
│       ├──► OpenCode / Aider  (terminal)        │
│       └──► Dashboard (:9090)                   │
│                                                │
│  Tailscale / Caddy ──► iPhone (anywhere)       │
└────────────────────────────────────────────────┘
```

---

## Dashboard

A lightweight Podman container at `http://localhost:9090` shows:

- **System** — CPU%, RAM used/total, disk free, swap
- **Services** — LM Studio app/API, Ollama, Open WebUI, Podman VM, Tailscale with start/stop buttons
- **Models** — Active runtime models; LM Studio by default, Ollama when selected

![Dashboard](docs/dashboard-preview.png)

---

## Menu Bar App

A native macOS menu bar widget that lives in your top menu bar.

**Install** (one-time):

```bash
pip3 install --break-system-packages rumps
```

**Run:**

```bash
ai-menubar-start    # launch in background
ai-menubar-stop     # quit
```

The menu bar icon shows a live status dot:

| Icon | Meaning |
|-------|---------|
| Green | RAM under 60% |
| Yellow | RAM 60–79% |
| Red | RAM 80%+ |
| Grey | Metrics exporter not running |

Click the icon to expand the menu: CPU / RAM / Disk stats, per-service status, and **Start Stack / Stop Stack / Full Off** buttons — plus one-click links to Open WebUI and the Dashboard.

LM Studio API status is green only when `:1234/v1/models` exposes a non-embedding chat model. Yellow means the API server is reachable but no chat model is exposed.

If the app is running under the `local-ai-menubar` launchd job, quitting from the menu or running `ai-menubar-stop` unloads that job first so macOS does not relaunch it immediately.

**Add to Login Items** so it starts automatically:

1. System Settings → General → Login Items → click `+`
2. Navigate to `menubar/app.py` — or add a wrapper script that runs `ai-menubar-start`

Log output goes to `/tmp/ai-menubar.log`.

---

## Remote Access

Run `bash scripts/phase5-remote.sh` and choose:

| Option | How | Setup time |
|--------|-----|-----------|
| **Tailscale** | Private mesh VPN | 5 min |
| **Cloudflare Tunnel** | Zero-trust, no port forwarding | 15 min |
| **Caddy + DuckDNS** | Public HTTPS, full control | 20 min |
| **Both (recommended)** | Tailscale + Caddy | 25 min |

Then on iPhone: Safari → Open WebUI → Share → **Add to Home Screen** for a native-looking PWA.

---

## Coding Tools

Continue.dev is configured in `~/.continue/config.json` with three groups:

- **Lab vLLM** entries stay at the top and are left untouched.
- **Local LM Studio** entries are the primary local choices, using `http://localhost:1234/v1`.
- **Local Ollama** entries remain available as fallback, with `smollm2:1.7b` for tab autocomplete and `nomic-embed-text` for embeddings.

```bash
# VS Code — install Continue extension, then:
Cmd+L    # open AI chat sidebar
Cmd+I    # inline edit / refactor

# Terminal agents
opencode          # full TUI coding agent (uses gemma3:12b)
aider-code        # Aider with gemma3:12b
aider-think       # Aider with phi4-reasoning (for complex refactors)

# Quick model switching
ai-use-coding     # → gemma3:12b
ai-use-general    # → mistral-small3.1:24b
```

Recommended Continue selection for daily local coding: **Local LM Studio - Gemma 3 12B (coding / daily)**.

---

## Repo Structure

```
Local-AI/
├── scripts/
│   ├── phase1-setup.sh          # Ollama + core models + shell aliases
│   ├── phase2-coding-tools.sh   # Continue.dev, OpenCode, Aider
│   ├── phase3-webui.sh          # Open WebUI via Podman
│   ├── phase4-dashboard.sh      # Dashboard container + metrics exporter
│   ├── phase5-remote.sh         # Tailscale / Caddy / Cloudflare
│   ├── phase6-improvements.sh   # LM Studio MLX, web search MCP, Pi, TurboQuant
│   ├── metrics-exporter.py      # Host metrics + control server (port 9091)
│   └── status.sh                # Quick stack health check
├── dashboard/
│   ├── app.py                   # Dashboard web server (no dependencies)
│   └── Dockerfile               # python:3.11-alpine, port 9090
├── menubar/
│   ├── app.py                   # macOS menu bar app (rumps)
│   └── requirements.txt         # pip: rumps
├── docs/
│   └── index.html               # GitHub Pages documentation
├── stack-aliases-v2.sh          # Shell functions: ai-stack-* and ai-menubar-*
├── PROJECT-PLAN.md              # Full architecture + decisions log
└── AGENTS.md                    # Rules for AI agents working on this project
```

---

## Documentation

📖 **Full docs can be published with GitHub Pages from `docs/index.html`.**

---

## Phase 6 — Community-Recommended Improvements

Based on community-reported local AI practices. On a 24 GB MacBook Pro M4 Pro, these close the biggest gaps vs what experienced practitioners run.

> All figures below are **community-reported** (room participants), not benchmarks reproduced on this machine. Treat as directional until you measure on your own workload.

| Improvement | Why | Reported gain |
|---|---|---|
| **LM Studio (MLX)** | Faster Apple Silicon inference path than Ollama on some workloads | +20–30% tok/s (reported) |
| **mlx-lm CLI** | Direct Apple MLX framework — best Apple Silicon perf | Comparable to LM Studio, scriptable |
| **Web search MCP** | Live search helps compensate for model training cutoffs | Quality bump on doc lookups (qualitative) |
| **Pi coding agent** | Lower base prompt can reduce prompt-processing overhead | Faster prompt-processing than OpenCode (reported) |
| **Speculative decoding** | Pair `smollm2:1.7b` (draft) with `gemma3:12b` | 1.5–2× tok/s (reported) |
| **TurboQuant variants** | Recent llama.cpp addition — lower VRAM for tight-fit models | Bigger approved models on same hardware |

### Switch backends on the fly

```bash
ai-use-mlx       # OpenCode → LM Studio (MLX) at :1234, persists for new shells (default)
ai-use-ollama    # OpenCode → Ollama at :11434, persists for new shells
ai-mlx-up        # launch LM Studio
ai-mlx-down      # quit LM Studio
ai-mlx-status    # see what's loaded in MLX
ai-mlx "prompt"  # one-shot generation via mlx-lm
ai-health-phase6 # verify all phase 6 services
```

### Web search for your local models

Phase 6 writes a shared Tavily + Brave + fetch MCP config and wires it into Continue.dev when `config.json` is present. Add API keys to `.secrets`:

```bash
TAVILY_API_KEY=tvly-xxxxx   # 1000 free searches/month — https://tavily.com
BRAVE_API_KEY=BSAxxxxx      # 2000 free searches/month — https://brave.com/search/api/
```

The MCP launch wrapper loads `.secrets` automatically when Continue starts the servers. Use `ai-secrets` only when you also want those keys in the current shell.

`ai-stack-start` uses LM Studio as the default runtime. Use `ai-use-ollama` when you explicitly want the Ollama API instead.

> ⚠️ **Compliance note:** Qwen and DeepSeek models are not used in this project. Use `phi4-reasoning` for reasoning workflows and `granite3.3:8b` for multilingual/RAG work.

---

## Key Tools

[Ollama](https://ollama.com) · [Open WebUI](https://openwebui.com) · [Continue.dev](https://continue.dev) · [OpenCode](https://github.com/opencode-ai/opencode) · [Aider](https://aider.chat) · [Tailscale](https://tailscale.com) · [macmon](https://github.com/vladkens/macmon) · [Podman](https://podman.io)
