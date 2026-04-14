# Local-AI Project — Agent Instructions

> This file contains instructions for AI agents working on the Local-AI project.  
> **Hardware:** MacBook Pro M4 Pro — 24GB unified memory  
> **Owner:** Simone

---

## Project Context

This project manages a fully local AI stack on a MacBook Pro M4 Pro (24GB). The stack consists of:

- **Ollama** as the primary LLM runtime (port 11434, OpenAI-compatible API at `/v1`)
- **LM Studio** as a secondary runtime for GUI exploration and MLX models (port 1234)
- **Continue.dev** for VS Code coding assistance
- **OpenCode / Aider** for CLI-based coding
- **Open WebUI** for chat interface and document RAG
- **AnythingLLM** for knowledge base / RAG
- **macmon** for hardware monitoring
- **Tailscale** for secure remote access from iPhone / other devices

The full project plan and architecture are documented in `PROJECT-PLAN.md` in this directory.

### Remote Access
Open WebUI is accessible remotely via Tailscale at `http://<tailscale-ip>:3000`. Ollama API at `http://<tailscale-ip>:11434/v1`. Requires `OLLAMA_HOST=0.0.0.0:11434` to listen on all interfaces. MacBook must be awake (`caffeinate -s`).

---

## Memory Constraints — CRITICAL

The machine has **24GB unified memory**. This is the single most important constraint:

- macOS + system services use ~8 GB at rest
- This leaves **~14–16 GB** for models, apps, and headroom
- **Never recommend models that exceed 16 GB in VRAM** unless explicitly asked
- **Q4_K_M quantization** is the default recommendation for any model
- Only one large model (14B+) should be loaded at a time
- Set `OLLAMA_MAX_LOADED_MODELS=1` to enforce this
- If the user asks about running multiple models simultaneously, warn about memory pressure

---

## Approved Models — MANDATORY

> **Only models from the organization's approved list may be used.**
> Models are classified as **Green** (fully approved) or **Yellow** (elevated risk).
> **Qwen and DeepSeek models are NOT approved** — never suggest them.

When suggesting or selecting models, use the task guide below:

### Task → Best Model (all Green)

| Task                         | Best model                   | Runner-up              | VRAM    |
|------------------------------|------------------------------|------------------------|---------|
| Quick Q&A / brainstorm       | `phi4-mini` (3 GB)           | `gemma3:4b` (3 GB)    | Light   |
| General writing / emails     | `mistral-small3.1:24b`       | `gemma3:12b`           | 14 / 7  |
| Code generation / debugging  | `devstral` (24B)       | `granite3.3:8b`        | 14 / 6  |
| Reasoning / math / logic     | `phi4-reasoning` (14B)       | `magistral:24b-small-2506` | 9 / 14 |
| Summarization                | `gemma3:12b`                 | `granite3.3:8b`        | 7 / 6   |
| RAG / document Q&A           | `granite3.3:8b` (128K ctx)   | `mistral-small3.1:24b` | 6 / 14  |
| Tool/function calling        | `mistral-small3.1:24b`       | `granite3.3:8b`        | 14 / 6  |
| Multilingual                 | `granite3.3:8b` (12 langs)   | `gemma3:12b`           | 6 / 7   |
| Multimodal (text + images)   | `gemma3:12b` (native vision) | `gemma3:4b`            | 7 / 3   |
| Tab autocomplete             | `smollm2:1.7b`               | `phi4-mini-reasoning`  | 1 / 3   |

### Gemma Models That Fit

- `gemma3:4b` (~3 GB) — lightweight, multimodal
- `gemma2:9b` (~6 GB) — solid general, text-only
- `gemma3:12b` (~7 GB) — **best Gemma for daily use**, multimodal, 88.9% IFEval
- `gemma4:26b-a4b-it` (~15 GB) — MoE, near-31B quality but **tight fit**, close other apps
- `gemma4:e4b-it` (~3 GB) — edge model, fast but shallow

### Gemma Models That DON'T Fit — Never Load

- `gemma4:31b-it` (~20 GB) — swapping, context suffers
- `gemma3:27b` / `gemma2:27b` (~16-17 GB) — marginal, risky
- Gemma 3n LiteRT variants — not available on Ollama

### Embeddings (RAG):
1. `nomic-embed-text` — default (~0.3 GB)

### Yellow-risk models (use only if Green alternatives insufficient):
- `llama3.1:8b` — general-purpose (~6 GB)
- `phi4` — good chat model (~5 GB)
- `phi4-reasoning-plus` — enhanced reasoning (~9 GB)

---

## Tool Configuration Reference

### Ollama API
- Base URL: `http://localhost:11434`
- OpenAI-compatible endpoint: `http://localhost:11434/v1`
- API Key: `ollama` (or any non-empty string — Ollama doesn't validate keys)
- List loaded models: `GET /api/ps`
- Unload a model: `POST /api/generate` with `{"model":"<name>","keep_alive":0}`

### Continue.dev
- Config location: `~/.continue/config.json`
- Provider: `ollama`
- Supports separate models for chat vs. tab-autocomplete

### OpenCode
- Set `OPENCODE_API_BASE=http://localhost:11434/v1`
- Requires models with tool-calling support and 64K+ context
- Recommended model: `devstral` or `mistral-small3.1:24b`

### Open WebUI
- Runs in Podman on port 3000
- Connects to Ollama via `http://host.containers.internal:11434` (Podman's hostname for the Mac host)
- Has built-in RAG with document upload
- Manage with: `podman start/stop/logs open-webui`

### LiteLLM (API Proxy)
- Use when a tool needs a unified proxy to multiple backends
- `litellm --model ollama/<model> --port 4000`
- Exposes standard OpenAI API at `http://localhost:4000/v1`

---

## Coding Guidelines for This Project

When writing scripts, configs, or automation for this project:

1. **Shell scripts** should target `zsh` (macOS default). Use `#!/bin/zsh` shebang.
2. **Python scripts** should use Python 3.11+ (system Python on macOS). Use `pip install --break-system-packages` if needed.
3. **Podman** is used for containerized services like Open WebUI. Use `podman` commands, not `docker`.
4. **Homebrew** is the primary package manager. Prefer `brew install` where possible.
5. **Config files** belong in `~/.config/local-ai/` or within this project directory.
6. All API interactions should default to the **OpenAI-compatible format** for maximum tool compatibility.
7. **Plan-then-build**: for non-trivial coding tasks, first use `phi4-reasoning` to outline the approach, then switch to `devstral` to implement it. Do not attempt to reason deeply and emit code in the same call with a 24B model on 24 GB RAM.
8. **Context budget**: keep prompt + context under ~100K tokens even for 128K-context models (`gemma3:12b`, `mistral-small3.1:24b`, `granite3.3:8b`). Quality degrades measurably above that threshold. If approaching the limit, summarize and restart the session with the summary as the new seed.

---

## Common Tasks an Agent Might Be Asked

### "Install a new model"
```bash
ollama pull <model-name>
# Then test it
ollama run <model-name> "Hello, how are you?"
```

### "Switch the coding model"
Update the relevant tool config (Continue.dev, OpenCode env var, etc.) and optionally unload the old model:
```bash
curl -s http://localhost:11434/api/generate -d '{"model":"old-model","keep_alive":0}' > /dev/null
ollama run new-model --keepalive 5m
```

### "Check system resources"
```bash
macmon          # Real-time Apple Silicon metrics
ollama ps       # Currently loaded models + VRAM usage
```

### "Add documents to RAG"
Use AnythingLLM GUI or Open WebUI's document upload. For programmatic ingestion, use the AnythingLLM API or Open WebUI's API endpoints.

### "Benchmark a model"
```bash
ollama run <model> "Write a Python function for binary search" --verbose
# The --verbose flag shows token generation speed
```

### "Free up memory"
```bash
# Unload all models
for model in $(ollama ps | tail -n +2 | awk '{print $1}'); do
  curl -s http://localhost:11434/api/generate -d "{\"model\":\"$model\",\"keep_alive\":0}" > /dev/null
done
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Model loads but generation is very slow | Memory swapping — model too large | Use a smaller model or Q4_K_M quantization |
| "out of memory" error | Model + system exceed 24 GB | Unload other models, close apps, use smaller quant |
| Tool can't connect to Ollama | Ollama not running | `ollama serve` or `brew services start ollama` |
| Podman can't reach Ollama | Network isolation | Use `host.containers.internal:11434` — Podman's hostname for the Mac host |
| Poor code quality from model | Model too small or wrong type | Switch to `devstral` for coding tasks |
| Continue.dev autocomplete laggy | Autocomplete model too large | Use `smollm2:1.7b` for autocomplete only |

---

## Environment Variables Reference

Add these to `~/.zshrc`:

```bash
# Ollama configuration
export OLLAMA_KEEP_ALIVE=5m           # Auto-unload after 5 min idle
export OLLAMA_MAX_LOADED_MODELS=1     # Only 1 model at a time (24GB constraint)
export OLLAMA_NUM_GPU=99              # Use all GPU layers (Metal)
export OLLAMA_HOST=0.0.0.0:11434     # Allow Podman containers to connect

# OpenCode
export OPENCODE_API_BASE=http://localhost:11434/v1
export OPENCODE_MODEL=devstral

# Convenience aliases (all Green-approved models)
alias ai-chat="ollama run phi4-mini"              # ~3 GB, ultra-fast
alias ai-general="ollama run gemma3:12b"           # ~8 GB, balanced
alias ai-code="ollama run devstral"          # ~14 GB, coding
alias ai-reason="ollama run phi4-reasoning"        # ~9 GB, chain-of-thought
alias ai-power="ollama run mistral-small3.1:24b"   # ~14 GB, best overall
alias ai-status="ollama ps"
```
