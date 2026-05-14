# Local-AI

> Run powerful LLMs privately on a MacBook Pro M4 Pro — for coding, chat, RAG, and productivity. No cloud. No API costs.

[![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-black?logo=apple)](https://www.apple.com/mac/)
[![Ollama](https://img.shields.io/badge/Ollama-v0.20+-white)](https://ollama.com)
[![LM Studio](https://img.shields.io/badge/LM%20Studio-latest-blue)](https://lmstudio.ai)
[![License](https://img.shields.io/badge/license-Personal-gray)](#)

---

## What This Is

A complete, production-ready local AI stack on Apple Silicon. The **menu bar app** is the single control surface — no containers required.

| Component           | What it does                                                    |
|---------------------|-----------------------------------------------------------------|
| **LM Studio**       | Default runtime for MLX models, OpenAI-compatible API on :1234  |
| **Ollama**          | Alternate local runtime and model manager on :11434             |
| **Menu bar app**    | macOS status bar controller — live stats + start/stop controls  |
| **Continue.dev**    | AI assistant inside VS Code (Cmd+L / Cmd+I, tab autocomplete)   |
| **opencode**        | Terminal AI coding agent (TUI)                                  |
| **Pi**              | Lightweight CLI coding agent                                    |
| **Aider**           | CLI pair programmer                                             |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/simoneiaci/local-ai.git
cd local-ai

# 2. Phase 1 — Ollama + core models
bash scripts/phase1-setup.sh

# 3. Phase 2 — Coding tools (Continue.dev, opencode, Aider)
bash scripts/phase2-coding-tools.sh

# 4. Phase 6 — LM Studio MLX, web search MCP, Pi
bash scripts/phase6-improvements.sh
```

Source the aliases file (done automatically if `~/.zshrc` sources it):

```bash
source stack-aliases-v2.sh
```

---

## Key Aliases

```bash
ai-stack-start      # start LM Studio + metrics exporter
ai-stack-stop       # stop AI services (metrics exporter stays up)
ai-stack-off        # full shutdown — everything off
ai-mlx-up           # launch LM Studio only
ai-mlx-down         # quit LM Studio
ai-mlx-status       # show models loaded in LM Studio
ai-use-mlx          # switch opencode/Aider to LM Studio backend (default)
ai-use-ollama       # switch opencode/Aider to Ollama
ai-menubar-start    # launch the menu bar app in background
ai-menubar-stop     # quit the menu bar app
ai-health-phase6    # verify LM Studio + Pi + mlx-lm + search keys
ai-secrets          # load .secrets into current shell
```

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                  MacBook Pro M4 Pro · 24 GB                    │
│                                                                │
│   ┌──────────────────┐         ┌──────────────────┐           │
│   │   LM Studio       │         │     Ollama        │           │
│   │   (primary)       │         │   (alternate)     │           │
│   │   :1234 /v1       │         │   :11434 /v1      │           │
│   └────────┬──────────┘         └────────┬──────────┘           │
│            │   OpenAI-compatible API      │                     │
│            └──────────────┬──────────────┘                      │
│                           │                                     │
│   ┌───────────────────────┼───────────────────────────────────┐ │
│   │       CLIENTS (all OpenAI-compatible, local-only)          │ │
│   │   Continue.dev (VS Code)   Pi (CLI)   opencode (CLI)       │ │
│   │   LM Studio Chat tab        Aider (CLI)                    │ │
│   └────────────────────────────────────────────────────────────┘ │
│                                                                │
│   ┌────────────────────────────────────────────────────────────┐│
│   │  CONTROL PLANE                                              ││
│   │  Menu bar app (rumps)  ──▶  metrics-exporter :9091          ││
│   │  /tmp/ai-metrics.json  ◀──  (host process, no container)    ││
│   └─────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
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

| Role | Model | Size | Runtime |
|------|-------|------|---------|
| Daily driver · Coding | `google/gemma-4-e4b` | 9.02 GB | LM Studio (primary, GGUF Q8_0) |
| MLX alt · MTP enabled | `mlx-community/gemma-4-e4b-it-8bit` | 9.00 GB | LM Studio (MLX 8-bit) |
| Tool-calling · RAG · Multilingual | `granite-3.3-8b-instruct` | 4.94 GB | LM Studio |
| Reasoning · Math · Logic | `phi-4-reasoning` | 11.12 GB | LM Studio |
| Tab autocomplete | `smollm2-1.7b-instruct` | 1.82 GB | LM Studio |
| Embeddings | `text-embedding-nomic-embed-text-v1.5` | 84 MB | LM Studio |
| Fast chat fallback | `phi4-mini` | ~3 GB | Ollama |

Only one large model fits in RAM at a time. `smollm2-1.7b-instruct` and the embedding model can stay loaded alongside any other model.

For `granite-3.3-8b-instruct` in LM Studio, set the per-model default context length to **32K** in **My Models → gear icon**. Use **64K** for long-document sessions only.

---

## Menu Bar App

The native macOS menu bar widget is the primary control surface.

**Install** (one-time):

```bash
pip3 install --break-system-packages rumps pyobjc-framework-Cocoa
```

**Run:**

```bash
ai-menubar-start    # launch in background
ai-menubar-stop     # quit
```

The `LAI` text in the menu bar is colored based on RAM pressure:

| Color  | Meaning          |
|--------|------------------|
| Green  | RAM under 60%    |
| Yellow | RAM 60–79%       |
| Red    | RAM 80%+         |
| Grey   | Exporter offline |

Click to expand: CPU / RAM / Disk stats, LM Studio and Ollama status, model switcher, and **Start Stack / Stop Stack / Full Off** controls.

LM Studio API is shown as "API ready" only when `/api/v0/models` exposes a non-embedding chat model. "API idle" means the server is reachable but no chat model is loaded.

**Autostart:** System Settings → General → Login Items → add a wrapper script that runs `ai-menubar-start`.

Log output → `/tmp/ai-menubar.log`.

---

## IDE Integrations

### Continue.dev (VS Code)

Config: `~/.continue/config.json`

```bash
Cmd+L    # open AI chat sidebar
Cmd+I    # inline edit / refactor
Tab      # autocomplete (SmolLM2 1.7B via LM Studio — instant)
```

Primary local models (via LM Studio `:1234`):
- `google/gemma-4-e4b` — daily coding/chat (default)
- `granite-3.3-8b-instruct` — tools/RAG, 65K context
- `phi-4-reasoning` — logic and math

### opencode (CLI)

Config: `~/.config/opencode/opencode.json`

```bash
opencode          # full TUI coding agent
ai-use-mlx        # switch to LM Studio backend (default)
ai-use-ollama     # switch to Ollama backend
```

Uses `google/gemma-4-e4b` via LM Studio by default. Cloud models (Gemini 3 Pro, Claude) available via Antigravity OAuth when needed.

### Pi (CLI)

```bash
pi                                                  # interactive session
pi -c                                               # continue last session
pi --model lmstudio/google/gemma-4-e4b "..."        # force local model
```

Config: `~/.pi/agent/settings.json`. Default provider: `lmstudio`.

---

## Coding Tools

```bash
opencode          # full TUI agent (uses google/gemma-4-e4b via LM Studio)
pi                # lighter CLI agent (uses google/gemma-4-e4b via LM Studio)
aider-code        # Aider with Ollama/devstral
aider-think       # Aider with Ollama/phi4-reasoning
```

---

## Repo Structure

```
Local-AI/
├── scripts/
│   ├── phase1-setup.sh          # Ollama + core models + shell aliases
│   ├── phase2-coding-tools.sh   # Continue.dev, opencode, Aider
│   ├── phase6-improvements.sh   # LM Studio MLX, web search MCP, Pi
│   ├── metrics-exporter.py      # Host metrics + control server (:9091)
│   ├── mcp-with-secrets.sh      # MCP launcher with .secrets sourced
│   └── status.sh                # Quick stack health check
├── menubar/
│   ├── app.py                   # macOS menu bar app (rumps)
│   └── requirements.txt
├── docs/
│   └── index.html               # GitHub Pages documentation
├── stack-aliases-v2.sh          # Shell functions: ai-stack-* / ai-use-* / ai-mlx-*
├── PROJECT-PLAN.md              # Full architecture + decisions log
└── AGENTS.md                    # Rules for AI agents working on this project
```

---

## Phase 6 — Community-Recommended Improvements

| Improvement | Why |
|---|---|
| **LM Studio (MLX)** | Faster Apple Silicon inference path |
| **mlx-lm CLI** | Direct Apple MLX framework, scriptable |
| **Web search MCP** | Live search compensates for model training cutoffs |
| **Pi coding agent** | Smaller base prompt, lower overhead |
| **Speculative decoding** | Pair `smollm2-1.7b-instruct` as draft model |

### Web search API keys

Add to `.secrets`:

```bash
TAVILY_API_KEY=tvly-xxxxx   # 1000 free searches/month
BRAVE_API_KEY=BSAxxxxx      # 2000 free searches/month
```

Load into the current shell: `ai-secrets`

---

## Key Links

[Ollama](https://ollama.com) · [LM Studio](https://lmstudio.ai) · [Continue.dev](https://continue.dev) · [opencode](https://github.com/opencode-ai/opencode) · [Pi](https://pi.dev) · [Aider](https://aider.chat) · [macmon](https://github.com/vladkens/macmon)
