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

Two hosts, both 24 GB M4 Pro. The difference is what macOS and the GUI take.

### MacBook Pro M4 Pro (24 GB) — interactive

| Component          | RAM Usage  | Notes                              |
|--------------------|------------|------------------------------------|
| macOS + system     | ~8 GB      | Varies with apps open              |
| LLM model (active) | 5–15 GB    | Depends on model size + quant      |
| RAG / embedding    | ~0.5–1 GB  | Small embedding model              |
| Apps & headroom    | ~2 GB      | Browsers, IDE, etc.                |

**Rule of thumb:** keep model weights under **15 GB**. Swapping kills LLM performance.

### Mac mini M4 Pro (24 GB) — headless inference server

| Component          | RAM Usage  | Notes                                    |
|--------------------|------------|------------------------------------------|
| macOS (headless)   | ~4 GB      | No GUI apps, no browser                  |
| LLM model + KV     | up to 18 GB| Requires raised Metal wired limit         |
| Bot + exporter     | ~1 GB      | Telegram bot process, metrics exporter    |

**Rule of thumb:** keep weights + KV cache under **18 GB combined**.

### The Metal wired limit

macOS caps GPU-addressable memory at ~16–18 GB on a 24 GB machine. A model
above the cap will not load regardless of free RAM:

```bash
sysctl iogpu.wired_limit_mb                # 0 = default cap
sudo sysctl iogpu.wired_limit_mb=20480     # 20 GB — mini only
```

It is a ceiling, not an allocation, and it **resets on every reboot** —
persist it with a LaunchDaemon on the mini. Leave 4 GB for macOS. Do not
raise it on the MacBook; pick a smaller model there instead.

---

## 3. Model Selection

> **Hardware fit is the only constraint.** There is no vendor allow/deny list —
> these are personal machines. A model is acceptable if it fits the host budget
> in §2 with room for KV cache and the OS.
> **Green** = fits with headroom · **Yellow** = fits but tight · **Red** = does not fit.

Use `phi4-reasoning` for local reasoning, math, and logic work on this laptop. Use `granite3.3:8b` for multilingual/RAG document workflows where long context matters.

---

### 3a. Complete Gemma Family (All Green)

Every Gemma variant and whether it runs on a 24 GB M4 Pro:

| Model                    | Ollama name              | VRAM (Q4) | Fits 24GB? | Best for                          |
|--------------------------|--------------------------|-----------|------------|-----------------------------------|
| **Gemma 3 1B**           | `gemma3:1b`              | ~1 GB     | Easily     | Too small for most tasks — skip   |
| **Gemma 3 4B**           | `gemma3:4b`              | ~3 GB     | Easily     | Quick Q&A, multimodal (text+image)|
| **Gemma 2 9B**           | `gemma2:9b`              | ~6 GB     | Yes        | Solid general-purpose, text-only  |
| **Gemma 3 12B**          | `gemma3:12b`             | ~7 GB     | Yes        | Older daily-driver option; replaced by Gemma4 BF16 e4b |
| **Gemma 4 E4B**          | `gemma4:e4b-it`          | ~3 GB     | Easily     | Edge model — fast but shallow     |
| **Gemma4 BF16 e4b**      | `google/gemma-4-e4b`     | 6.33 GB   | Yes        | **Current primary** — BF16 quality with practical RAM headroom |
| **Gemma 3 27B**          | `gemma3:27b`             | ~16 GB    | Marginal   | Best Gemma quality overall but leaves <8 GB for system — risky, may swap |
| **Gemma 4 31B**          | `gemma4:31b-it`          | ~20 GB    | No         | Too large — causes swapping, context suffers. Avoid. |
| Gemma 3n E2B/E4B (LiteRT)| —                       | —         | N/A        | On-device edge only (phones). **Not available on Ollama.** Skip. |
| Gemma 2 27B              | `gemma2:27b`             | ~17 GB    | Marginal   | Older generation — prefer the current primary instead |
| Gemma 1.1 / 2B / 7B     | `gemma:7b` etc.          | ~5 GB     | Yes        | Older generation — no reason to use over Gemma 3 |

**Recommended Gemma picks:**
- **Daily driver:** `Gemma4 BF16 e4b` (~8 GB) — primary LM Studio model
- **Lightweight:** `gemma3:4b` (~3 GB) — when you need speed or have other models loaded
- **Maximum quality within the daily budget:** `Gemma4 BF16 e4b` (~8 GB) — BF16 quality without pushing the laptop to the ceiling

---

### 3b. Other Models That Fit — Green

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

### 3e. Models That Don't Fit — by host

**Mini only** (over the MacBook's 15 GB ceiling, under the mini's 18 GB):

| Model                       | Size      | Requires                    |
|-----------------------------|-----------|-----------------------------|
| Qwen3.6-35B-A3B UD-IQ4_XS   | 17.7 GB   | raised wired limit          |
| Gemma 4 26B-A4B (MLX 4-bit) | ~16 GB    | raised wired limit          |
| Gemma 3 27B / Gemma 2 27B   | ~16–17 GB | raised wired limit; dense, slow |

**Neither host:**

| Model                      | Why                                            |
|----------------------------|------------------------------------------------|
| Gemma 4 31B                | ~20 GB at Q4 — over budget on both              |
| Qwen3.6-35B-A3B UD-Q4_K_M  | 22.1 GB — use UD-IQ3_S or UD-IQ4_XS instead     |
| CodeLlama 34B/70B          | ~22 GB+ at Q4                                   |
| Any dense 70B+             | Requires 48 GB+ RAM                             |

---

### 3f. What's Best for What — Task Recommendation Guide

```
TASK                               → BEST MODEL                         → RUNNER-UP                    VRAM
────────────────────────────────────────────────────────────────────────────────────────────────────────────────
CODE GENERATION / DEBUGGING        → Gemma4 BF16 e4b (~8 GB)            → granite3.3:8b (lighter)      8 / 6 GB
CREATIVE WRITING / EMAILS          → Gemma4 BF16 e4b (~8 GB)            → granite3.3:8b                 8 / 6 GB
REASONING / MATH / LOGIC           → phi4-reasoning (75.3% AIME)        → magistral:24b-small-2506     9 / 14 GB
SUMMARIZATION                      → Gemma4 BF16 e4b (~8 GB)            → granite3.3:8b (128K ctx)     8 / 6 GB
INSTRUCTION FOLLOWING              → Gemma4 BF16 e4b (~8 GB)            → granite3.3:8b                 8 / 6 GB
RAG / DOCUMENT Q&A                 → granite3.3:8b (RAG LoRAs, 128K)    → mistral-small3.1:24b         6 / 14 GB
FUNCTION / TOOL CALLING            → mistral-small3.1:24b (native)      → granite3.3:8b                14 / 6 GB
MULTILINGUAL                       → granite3.3:8b (12 languages)       → Gemma4 BF16 e4b              6 / 8 GB
MULTIMODAL (text + images)         → gemma3:4b (vision-capable)          → verify loaded LM Studio model 3 / varies
QUICK Q&A / BRAINSTORMING          → phi4-mini (~3 GB, ~30 tok/s)       → gemma3:4b                    3 / 3 GB
TAB AUTOCOMPLETE IN IDE            → smollm2:1.7b (~1 GB, instant)      → phi4-mini-reasoning          1 / 3 GB
```

> **The "Two Model" Strategy:** Use `Gemma4 BF16 e4b` as the LM Studio daily driver (~8 GB).
> When you need specialized power, swap to `phi4-reasoning` for math/reasoning or
> `granite3.3:8b` for long-context RAG/tool workflows.

### Quantization Guide

- **Q4_K_M** — Sweet spot. ~4-bit, great quality-to-size ratio. Use this by default.
- **Q5_K_M** — Slightly better quality, ~20% larger. Use if model fits comfortably.
- **Q8_0** — Near-original quality, 2x size of Q4. Only for small models (≤7B).
- **UD-IQ3_S / UD-IQ4_XS** — Unsloth Dynamic quants. Use these for **MoE**
  models, not plain K-quants. Expert layers tolerate low bits; the shared and
  attention path does not, and UD quants budget bits accordingly.
- **MLX format** — sometimes faster than GGUF, sometimes not. It is model- and
  version-specific: on `gpt-oss-20b`, llama.cpp measured ~1.6x faster prefill
  and ~9% faster generation than MLX (`ml-explore/mlx-lm#858`). Benchmark the
  specific pair you intend to run rather than assuming.

---

### 3g. MoE Models & the Chat / Telegram Shortlist

A Mixture-of-Experts model holds N total parameters but activates only a
subset per token. On a memory-bound Mac that is the highest-leverage property
available — 35B of knowledge at roughly 3B of compute cost. **Prefer MoE over
dense at equal footprint.**

Quality retention for `Qwen3.6-35B-A3B` (35B total / 3B active, 262K context,
natively multimodal), measured on code-gen benchmarks — directional for chat:

| Quant       | Size    | vs BF16 | Host      |
|-------------|---------|---------|-----------|
| UD-IQ2_M    | 11.5 GB | ~87%    | both      |
| UD-IQ3_XXS  | 13.2 GB | ~95%    | both      |
| UD-IQ3_S    | 13.7 GB | ~95%    | both      |
| UD-IQ4_XS   | 17.7 GB | ~99%    | mini only |
| UD-Q4_K_M   | 22.1 GB | ~99%    | neither   |

`UD-IQ3_S` is the sweet spot: ~95% of full quality, and it loads under the
**default** Metal wired limit, so it needs no sysctl change on either host.

**Shortlist for general chat / the Telegram bot** (not a coding shortlist):

| Model | Quant | Size | Host | Why |
|-------|-------|------|------|-----|
| `Qwen3.6-35B-A3B` | UD-IQ3_S | 13.7 GB | both | 3B active, fast. Multimodal, 262K ctx. No wired-limit change needed. Primary candidate. |
| `gemma-4-26b-a4b-it-4bit` | MLX 4-bit | ~16 GB | mini | Multimodal MoE, 140+ languages. A/B against Qwen for tone and Italian. |
| `mistral-small3.2:24b` | Q4_K_M | 14.3 GB | both | Dense, native tool calling. Zero-tuning fallback. |
| `maple-preview-2bit-mlx` | 2-bit MLX | — | both | 20B-A1B ternary MoE. Vendor claims 200+ tok/s on a base M4 mini. Preview quality — test for latency only. |
| `Qwen3.8-27B` | IQ4_XS | ~15.6 GB | both | Dense 27B, ~11 tok/s on M4 Pro. Only if it beats every MoE above. |

**Validate on real traffic.** Run the same five Italian prompts, one
follow-up turn and one image through each candidate. Benchmark scores do not
predict whether a model is pleasant to talk to.

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

# Primary daily workhorse (Green, ~8 GB)
# Download Gemma4 BF16 e4b in LM Studio. API model ID: google/gemma-4-e4b

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
alias ai-general="ollama run granite3.3:8b"        # ~6 GB, Ollama fallback
alias ai-code="ollama run granite3.3:8b"           # ~6 GB, tool-calling + long context
alias ai-reason="ollama run phi4-reasoning"        # ~9 GB, chain-of-thought
alias ai-power="ollama run mistral-small3.1:24b"   # ~14 GB, best overall

# Management
alias ai-status="ollama ps"
alias ai-stop="pkill ollama"
```

---

## 5. Phase 2 — Coding Tools

### 5.1 Continue.dev (VS Code — Recommended)

Install from VS Code marketplace. Configure `~/.continue/config.json` with local LM Studio entries first, then Ollama fallbacks. This project does not use remote model endpoints.

```json
{
  "models": [
    {
      "title": "Local LM Studio - Gemma4 BF16 e4b",
      "provider": "lmstudio",
      "model": "google/gemma-4-e4b",
      "apiBase": "http://localhost:1234/v1",
      "contextLength": 32768
    },
    {
      "title": "Local Ollama - Granite 3.3 8B (tools / RAG)",
      "provider": "ollama",
      "model": "granite3.3:8b",
      "apiBase": "http://localhost:11434",
      "contextLength": 65536
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

This gives you: LM Studio as the primary local coding chat/edit runtime (Cmd+L/Cmd+I), Ollama as fallback, and tab-autocomplete running locally with `smollm2:1.7b`.

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

Adapted to the local model roster on a 24 GB M4 Pro:

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

Reddit practitioners consistently report that even models advertising 128K context degrade noticeably after ~100K (hallucinations, language drift, lost references). Models and their realistic effective context:

| Model                        | Advertised | Recommended working budget |
|------------------------------|------------|----------------------------|
| `Gemma4 BF16 e4b`            | check LM Studio | ≤ 32K unless verified higher |
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

# Configure to use Ollama
# Edit ~/.khoj/khoj.yml:
#   chat-model: http://localhost:11434/v1
#   model: Gemma4 BF16 e4b
```

Khoj can index your notes, files, and even web content. Works with Obsidian via plugin.

> **Note:** Use `Gemma4 BF16 e4b` or `granite3.3:8b` as the RAG chat model, and `nomic-embed-text` for embeddings.

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

models=("phi4-mini" "granite3.3:8b" "phi4-reasoning")
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

## 8. Cloud Escape Hatch — GLM 5.1 & MiniMax 2.7

When a task exceeds what fits in 24 GB (huge codebases, long reasoning chains, multi-agent pipelines), you can drop into a cloud model. Both GLM 5.1 and MiniMax 2.7 expose **OpenAI-compatible APIs**, so every tool you already have plugs in with a base URL + model name swap.

### 9a. Why these two (community consensus, r/opencodeCLI)

| Model             | Good for                                           | Caveat                                      |
|-------------------|----------------------------------------------------|---------------------------------------------|
| **GLM 5.1**       | Planning, complex reasoning, long-range analysis   | Degrades after ~100K context; needs focus   |
| **MiniMax 2.7**   | Build mode: fast, cheap, reliable code generation  | Less capable on deep reasoning              |
| **Combo pattern** | GLM 5.1 → plan, MiniMax 2.7 → implement           | Best cost/quality ratio for heavy workloads |

### 9b. Getting API access (cheapest routes)

**Option 1 — OpenRouter (simplest, one API key)**

Both models available. 5% surcharge but zero setup friction.

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Generate an API key
3. Add to `.secrets`:
```
OPENROUTER_API_KEY=sk-or-...
```
Models: `zhipuai/glm-5.1` and `minimax/minimax-m2.7`

**Option 2 — Direct providers (cheaper, no surcharge)**

Recommended by power users (Novita, Atlas Cloud, Deep Infra all carry these models):
- [novita.ai](https://novita.ai) — competitive pricing, good uptime
- [deepinfra.com](https://deepinfra.com) — inference-focused, GLM/MiniMax available
- [atlascloud.ai](https://atlascloud.ai) — low latency

### 9c. Connecting to your existing tools

All tools use the same pattern — swap `OPENAI_BASE_URL` and model name.

**OpenCode (terminal agent):**
```bash
# Plan with GLM 5.1 (cloud)
OPENCODE_PROVIDER=openai-compatible \
OPENCODE_API_BASE=https://openrouter.ai/api/v1 \
OPENCODE_API_KEY=$(grep OPENROUTER_API_KEY ~/.secrets-local | cut -d= -f2) \
OPENCODE_MODEL=zhipuai/glm-5.1 \
opencode "Design the architecture for this service"

# Build with MiniMax 2.7 (cloud)
OPENCODE_MODEL=minimax/minimax-m2.7 opencode "Now implement it"
```

**Continue.dev** — add cloud providers to `~/.continue/config.json`:
```json
{
  "title": "GLM 5.1 (cloud - plan mode)",
  "provider": "openai",
  "model": "zhipuai/glm-5.1",
  "apiBase": "https://openrouter.ai/api/v1",
  "apiKey": "sk-or-..."
},
{
  "title": "MiniMax 2.7 (cloud - build mode)",
  "provider": "openai",
  "model": "minimax/minimax-m2.7",
  "apiBase": "https://openrouter.ai/api/v1",
  "apiKey": "sk-or-..."
}
```

**Aider:**
```bash
aider --model openrouter/zhipuai/glm-5.1 --input-history-file .aider.history
```

**Open WebUI** — add a new connection:
Settings → Connections → Add OpenAI-compatible connection:
- URL: `https://openrouter.ai/api/v1`
- Key: your OpenRouter key
- Available models will include GLM 5.1 and MiniMax 2.7

### 9d. Shell aliases (add to ~/.zshrc after getting your key)

```bash
# Cloud model switchers
ai-use-glm()      { export OPENCODE_PROVIDER=openai-compatible
                    export OPENCODE_API_BASE=https://openrouter.ai/api/v1
                    export OPENCODE_MODEL=zhipuai/glm-5.1
                    echo "→ GLM 5.1 (cloud)"; }

ai-use-minimax()  { export OPENCODE_PROVIDER=openai-compatible
                    export OPENCODE_API_BASE=https://openrouter.ai/api/v1
                    export OPENCODE_MODEL=minimax/minimax-m2.7
                    echo "→ MiniMax 2.7 (cloud)"; }

ai-use-local()    { export OPENCODE_PROVIDER=openai-compatible
                    export OPENCODE_API_BASE=http://localhost:11434/v1
                    export OPENCODE_MODEL=devstral
                    echo "→ devstral (local)"; }
```

### 9e. When to use cloud vs local

| Situation                                     | Use                        |
|-----------------------------------------------|----------------------------|
| Daily coding, focused tasks, private data      | Local (devstral / gemma3)  |
| Large refactor across 50+ files               | MiniMax 2.7 (build)        |
| Architectural planning, complex debugging     | GLM 5.1 (plan)             |
| Long-running agent with many tool calls       | GLM 5.1 plan → MiniMax build |
| Sensitive/confidential data you keep private  | Local always               |

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
| 3    | Download primary model (`Gemma4 BF16 e4b`) in LM Studio | 10 min |
| 4    | Set up shell aliases + env vars                | 5 min  |
| 5    | Install Continue.dev in VS Code                | 10 min |
| 6    | Install Open WebUI (Podman)                    | 10 min |
| 7    | Pull embedding model + test RAG                | 10 min |
| 8    | Install macmon for monitoring                  | 5 min  |
| 9    | (Optional) Pull power models (`mistral-small3.1:24b`, `phi4-reasoning`) | 15 min |
| 10   | (Optional) Install OpenCode / Aider            | 10 min |
| 11   | (Optional) Set up AnythingLLM for RAG          | 15 min |
| 13   | (Optional) Prometheus + Grafana                | 30 min |

**Total for core setup: ~1 hour**

---

## 11. Model Switching Cheat Sheet

```
SITUATION                          → MODEL TO USE                           RISK    VRAM
──────────────────────────────────────────────────────────────────────────────────────────
Quick question / brainstorm        → phi4-mini (~3 GB, ultra-fast)          Green   ~3 GB
Write an email / document          → Gemma4 BF16 e4b                        Green   ~8 GB
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
- **MLX Community Models:** https://huggingface.co/mlx-community

---

## 13. Remote Access & the Telegram Bot

Remote access was removed in `29adcf1` when the stack went local-only. The
Mac mini as an always-on host brings it back.

### Tailscale only — never port-forward

LM Studio (:1234) and Ollama (:11434) have **no authentication**. Exposing
either publicly hands out a free GPU and every prompt. The metrics-exporter
control server (:9091) has bearer auth but must stay on `127.0.0.1`.

```bash
brew install --cask tailscale
tailscale up
tailscale ip -4          # 100.x.y.z
```

From any device on the tailnet:

- LM Studio — `http://<tailscale-ip>:1234/v1`
- Ollama — `http://<tailscale-ip>:11434/v1`

`scripts/status.sh` already reports Tailscale state; its check was never
removed and starts working again after `tailscale up`.

**Watch out:** `OLLAMA_HOST=0.0.0.0:11434` binds Ollama to *all* interfaces,
not just the tailnet. Bind to the Tailscale IP or enable the macOS firewall,
especially on the MacBook.

### Telegram bot

The bot runs on the mini against `http://127.0.0.1:1234/v1`, so it does not
need the tailnet. Telegram is reached by outbound long-polling
(`getUpdates`) — **no inbound port, no webhook, no public endpoint**. Switch
to webhooks only if polling latency becomes a problem; that changes the
threat model and needs public HTTPS.

`TELEGRAM_BOT_TOKEN` goes in `.secrets`, never in git.

Keep the model warm so each message does not pay a cold load:

```bash
export OLLAMA_KEEP_ALIVE=-1        # mini only — overrides the 5m laptop default
export OLLAMA_MAX_LOADED_MODELS=1
```

### Recovering the old script

```bash
git show 29adcf1^:scripts/phase5-remote.sh   # Tailscale + Caddy + Cloudflare
```

Not reviewed against the current stack — its Open WebUI and Podman references
are stale.
