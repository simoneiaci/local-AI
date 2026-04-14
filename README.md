# 🧠 Local-AI

**Run powerful LLMs locally on your MacBook Pro M4 Pro (24GB) — for coding, chat, RAG, and productivity. Fully private, no cloud required.**

> Access your AI from anywhere — even your iPhone — using Tailscale or Cloudflare Tunnel.

---

## Why Local AI?

- **Privacy** — Your data never leaves your machine. No cloud, no third-party APIs.
- **Speed** — No network latency. Models respond in real-time.
- **Cost** — Zero ongoing API costs after initial setup.
- **Offline** — Works without internet. On planes, in the field, anywhere.
- **Customizable** — Choose your models, configure system prompts, build knowledge bases.

---

## What's in This Repo

```
Local-AI/
├── README.md                 ← You are here
├── PROJECT-PLAN.md           ← Full setup guide, model recommendations, architecture
├── AGENTS.md                 ← Instructions for AI agents working on this project
├── CLAUDE.md                 ← Entry point for Claude-based agents
├── docs/
│   └── index.html            ← GitHub Pages documentation site
└── scripts/                  ← (future) Automation scripts
```

---

## Quick Start (10 minutes)

### 1. Install Ollama

```bash
brew install ollama
brew services start ollama
```

### 2. Pull your first model

```bash
ollama pull gemma3:12b       # Best daily driver (~7 GB)
```

### 3. Chat with it

```bash
ollama run gemma3:12b
```

### 4. Install Open WebUI (ChatGPT-like interface)

```bash
# Start Podman machine first (macOS requirement)
podman machine start

podman run -d -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://host.containers.internal:11434 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart=always \
  ghcr.io/open-webui/open-webui:main
```

Open [http://localhost:3000](http://localhost:3000) — done.

---

## Hardware

| Spec              | Value                        |
|-------------------|------------------------------|
| Machine           | MacBook Pro M4 Pro           |
| RAM               | 24 GB unified memory         |
| Usable for models | ~14-16 GB (after macOS)      |
| GPU               | Apple Silicon Metal (built-in)|

---

## Approved Models

Only organization-approved models are used. Sorted by use case:

### Recommended Stack

| Role                 | Model                      | Ollama name              | VRAM   |
|----------------------|----------------------------|--------------------------|--------|
| **Quick chat**       | Phi 4 Mini                 | `phi4-mini`              | ~3 GB  |
| **Daily driver**     | Gemma 3 12B                | `gemma3:12b`             | ~7 GB  |
| **Coding**           | Devstral Small 1.1         | `devstral`         | ~14 GB |
| **Reasoning**        | Phi 4 Reasoning            | `phi4-reasoning`         | ~9 GB  |
| **Power model**      | Mistral Small 3.1 24B      | `mistral-small3.1:24b`   | ~14 GB |
| **RAG / docs**       | Granite 3.3 8B             | `granite3.3:8b`          | ~6 GB  |
| **Autocomplete**     | SmolLM2 1.7B               | `smollm2:1.7b`           | ~1 GB  |
| **Embeddings**       | Nomic Embed Text           | `nomic-embed-text`       | ~0.3 GB|

> ⚠️ Only load ONE 14 GB model at a time. See [PROJECT-PLAN.md](PROJECT-PLAN.md) for full model details.

### Gemma Family

| Model               | VRAM   | Fits? | Notes                                         |
|----------------------|--------|-------|-----------------------------------------------|
| Gemma 3 4B          | ~3 GB  | ✅    | Lightweight, multimodal                       |
| Gemma 2 9B          | ~6 GB  | ✅    | Solid general-purpose, text-only              |
| Gemma 3 12B         | ~7 GB  | ✅    | **Best Gemma overall** — multimodal, 88.9% IFEval |
| Gemma 4 26B-A4B     | ~15 GB | ⚠️    | MoE — tight fit but works (10-20 tok/s confirmed) |
| Gemma 4 31B         | ~20 GB | ❌    | Too large — swapping kills performance        |
| Gemma 3 27B         | ~16 GB | ❌    | Marginal — not recommended                    |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    MACBOOK PRO M4 PRO (24 GB)                    │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │   Ollama      │   │  LM Studio   │   │   MLX (optional)     │ │
│  │  (primary)    │   │  (GUI)       │   │   (speed tests)      │ │
│  │  port 11434   │   │  port 1234   │   │                      │ │
│  └──────┬───────┘   └──────────────┘   └──────────────────────┘ │
│         │                                                        │
│         │  OpenAI-compatible API: http://localhost:11434/v1       │
│         │                                                        │
│  ┌──────┴─────────────────────────────────────────────────────┐  │
│  │  Continue.dev · OpenCode · Aider · Cline      (coding)    │  │
│  │  Open WebUI · AnythingLLM · Khoj              (chat/RAG)  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  macmon · ollama ps · Prometheus + Grafana   (monitoring)  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Tailscale / Caddy + DDNS / Cloudflare Tunnel (remote)    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
         │
         │  Encrypted tunnel
         ▼
   ┌──────────┐
   │  iPhone   │  Open WebUI PWA
   │ (anywhere)│  = ChatGPT in your pocket
   └──────────┘
```

---

## Remote Access (AI in Your Pocket)

Three options for accessing your AI from your iPhone:

| Method             | Security        | Setup      | Best for                           |
|--------------------|-----------------|------------|------------------------------------|
| **Tailscale**      | End-to-end E2EE | 5 min      | Personal use, simplest & safest    |
| **Cloudflare Tunnel** | Zero-trust   | 15 min     | No port forwarding, free           |
| **Caddy + DDNS**   | HTTPS/TLS       | 20 min     | Public IP, full control            |

See [PROJECT-PLAN.md](PROJECT-PLAN.md) § Phase 5 for full setup instructions.

---

## What's Best for What

| Task                        | Best Model                    | VRAM   |
|-----------------------------|-------------------------------|--------|
| Code generation / debugging | `devstral`              | 14 GB  |
| Creative writing / emails   | `mistral-small3.1:24b`        | 14 GB  |
| Reasoning / math / logic    | `phi4-reasoning`              | 9 GB   |
| Summarization               | `gemma3:12b`                  | 7 GB   |
| RAG / document Q&A          | `granite3.3:8b`               | 6 GB   |
| Tool / function calling     | `mistral-small3.1:24b`        | 14 GB  |
| Multilingual                | `granite3.3:8b`               | 6 GB   |
| Multimodal (text + images)  | `gemma3:12b`                  | 7 GB   |
| Quick Q&A                   | `phi4-mini`                   | 3 GB   |

---

## Shell Aliases

Add to `~/.zshrc`:

```bash
# Ollama config
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_GPU=99
export OLLAMA_HOST=0.0.0.0:11434

# Quick model switching
alias ai-chat="ollama run phi4-mini"
alias ai-general="ollama run gemma3:12b"
alias ai-code="ollama run devstral"
alias ai-reason="ollama run phi4-reasoning"
alias ai-power="ollama run mistral-small3.1:24b"
alias ai-status="ollama ps"
```

---

## Documentation

Full documentation is available as a GitHub Pages site:

📖 **[View the docs →](https://simoneiaci.github.io/local-AI/)**

---

## Key Links

| Tool            | URL                                      |
|-----------------|------------------------------------------|
| Ollama          | https://ollama.com                       |
| LM Studio       | https://lmstudio.ai                     |
| Open WebUI       | https://openwebui.com                   |
| Continue.dev     | https://continue.dev                    |
| AnythingLLM      | https://useanything.com                 |
| OpenCode         | https://github.com/opencode-ai/opencode|
| Aider            | https://aider.chat                      |
| Tailscale        | https://tailscale.com                   |
| macmon           | https://github.com/vladkens/macmon      |

---

## License

Personal project. Not for redistribution.
