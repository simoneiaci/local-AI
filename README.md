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
| **Ollama** | Runs LLMs locally — fast GPU inference via Metal |
| **Open WebUI** | ChatGPT-like interface, runs in Podman |
| **Continue.dev** | AI assistant inside VS Code (Cmd+L / Cmd+I) |
| **OpenCode + Aider** | Terminal AI coding agents |
| **Dashboard** | Live system monitor at `localhost:9090` |
| **Tailscale / Caddy** | Access your AI from iPhone, anywhere |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/simoneiaci/local-AI.git
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
```

After Phase 1, use these aliases from any terminal:

```bash
ai-stack-start    # start everything (Ollama + WebUI + Dashboard)
ai-stack-stop     # cleanly shut everything down
ai-health         # check all services at a glance
ai-monitor        # live GPU/CPU/RAM via macmon
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
| Italian · Tax · Reasoning | `qwen3:14b` | 9.3 GB | Italian docs, 730/F24, reasoning + `/think` mode |
| Tab autocomplete | `smollm2:1.7b` | 1 GB | Instant, always loaded |
| Embeddings | `nomic-embed-text` | 0.3 GB | For RAG pipelines |

> ⚠️ Only one large model fits in RAM at a time. `smollm2:1.7b` and `nomic-embed-text` can always stay loaded alongside any model.

---

## Architecture

```
┌────────────────────────────────────────────────┐
│           MacBook Pro M4 Pro (24 GB)           │
│                                                │
│  Ollama (:11434) ──► Open WebUI (:3000)        │
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
- **Services** — Ollama, Open WebUI, Podman VM, Tailscale with start/stop buttons
- **Models** — All available models, which is loaded, VRAM used, expiry countdown

![Dashboard](docs/dashboard-preview.png)

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

```bash
# VS Code — install Continue extension, then:
Cmd+L    # open AI chat sidebar
Cmd+I    # inline edit / refactor

# Terminal agents
opencode          # full TUI coding agent (uses devstral)
aider-code        # Aider with devstral
aider-think       # Aider with phi4-reasoning (for complex refactors)

# Quick model switching
ai-use-coding     # → devstral
ai-use-general    # → mistral-small3.1:24b
```

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
│   ├── metrics-exporter.py      # Host metrics + control server (port 9091)
│   └── status.sh                # Quick stack health check
├── dashboard/
│   ├── app.py                   # Dashboard web server (no dependencies)
│   └── Dockerfile               # python:3.11-alpine, port 9090
├── docs/
│   └── index.html               # GitHub Pages documentation
├── PROJECT-PLAN.md              # Full architecture + decisions log
└── AGENTS.md                    # Rules for AI agents working on this project
```

---

## Documentation

📖 **[Full docs on GitHub Pages →](https://simoneiaci.github.io/local-AI/)**

---

## Key Tools

[Ollama](https://ollama.com) · [Open WebUI](https://openwebui.com) · [Continue.dev](https://continue.dev) · [OpenCode](https://github.com/opencode-ai/opencode) · [Aider](https://aider.chat) · [Tailscale](https://tailscale.com) · [macmon](https://github.com/vladkens/macmon) · [Podman](https://podman.io)
