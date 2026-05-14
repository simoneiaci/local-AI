# Local-AI Project — Agent Instructions

> **Read this entire file before doing any task in this repo.**
> **Hardware:** MacBook Pro M4 Pro — 24 GB unified memory
> **Owner:** Simone (`simoneiaci` on GitHub)
> **Project root:** `/Users/siaci/Documents/AI/Local-AI`

`CLAUDE.md` in this repo is a thin pointer to this file. If they ever
disagree, **AGENTS.md wins** — fix `CLAUDE.md`.

---

## 0. Stop-First Rules — read before any action

These rules override anything below. If you cannot satisfy them, stop and ask.

1. **Never suggest, install, pull, or reference Qwen or DeepSeek models.**
   They are not approved. This includes any variant (`qwen2.5`, `qwen3`,
   `deepseek-r1`, `deepseek-coder`, etc.).
2. **Never load a model larger than ~15 GB.** The hard ceiling is set by
   24 GB unified RAM minus ~8 GB macOS overhead. The current primary model
   `Gemma4 BF16 e4b` is the preferred daily model because it fits with more
   headroom than the previous 26B model. **Do not stack other large models
   alongside it.**
3. **Never commit `.secrets`** or any file containing tokens, API keys, or
   `CONTROL_TOKEN` values. `.secrets` is in `.gitignore` — keep it that way.
4. **Never force-push to `main`.** Never use `git push --force` on a shared
   branch. Use `git pull --rebase` before pushing.
5. **Never run `--no-verify` on commits**, never bypass pre-commit hooks.
6. **Never edit `docs/index.html` model names without also updating
   `AGENTS.md`, `CLAUDE.md`, and `stack-aliases-v2.sh`.**
   See §10 (Docs-sync rule).
7. **Never invent file paths, command names, model tags, or env vars.**
   If you don't know it, grep for it or run `ls` — do not guess.
8. **If a step is unclear or risky, stop and ask the user** rather than
   guessing. Simone prefers a 1-line clarifying question to silent damage.

---

## 1. Project Overview

This repo manages a fully local AI stack on a single MacBook. The user has
zero cloud dependencies; everything runs on `localhost`. The **menu bar app**
is the primary control surface — it shows live system stats, service status,
and provides start/stop controls. No containers are needed.

| Component           | Purpose                                   | Port    |
|---------------------|-------------------------------------------|---------|
| **LM Studio**       | **Default LLM runtime** (MLX/GGUF)        | 1234    |
| Ollama              | Alternate runtime + model manager         | 11434   |
| Metrics exporter    | Host-side metrics + control server        | 9091    |
| Menu bar app        | macOS menu bar controller (rumps)         | —       |

All LLM endpoints are **OpenAI-compatible** at `<host>:<port>/v1`.

The full project plan lives in `PROJECT-PLAN.md`. The public-facing docs
site lives in `docs/index.html`.

---

## 2. Memory Budget — the constraint that drives every decision

```
24 GB total
−  8 GB macOS + Finder + system services
= 16 GB available for models, browsers, IDEs
```

**Practical rules:**
- Only **one** large (≥10 GB) model loaded at a time.
- `OLLAMA_MAX_LOADED_MODELS=1` enforces this for Ollama.
- LM Studio loads one model at a time by default — keep it that way.
- Default quantization for any new model: **Q4_K_M**.
- If user asks "can I run X and Y together?" — check sizes; warn if sum > 14 GB.
- Closing Chrome / Slack frees ~2–4 GB and is the easiest unblock.

---

## 3. Approved Models

> **Green** = fully approved. **Yellow** = elevated risk, use only if no
> Green alternative fits. **Forbidden** = never suggest (Qwen, DeepSeek).

### Configured local inventory (verify with `lms ls`, `ollama list`, and LM Studio `/api/v0/models`)

| Model                              | Size      | Runtime    | Role                                 |
|------------------------------------|-----------|------------|--------------------------------------|
| `mlx-community/gemma-4-e4b-it-8bit` (gemma4 arch, MLX 8-bit) | ~9.00 GB | LM Studio  | **Primary alt** — chat, code, MTP enabled |
| `google/gemma-4-e4b` (GGUF Q8_0)  | 9.02 GB   | LM Studio  | **Primary** (loaded by default, multimodal) |
| `phi-4-reasoning` (15B)            | 11.12 GB  | LM Studio  | Chain-of-thought reasoning           |
| `granite-3.3-8b-instruct`          | 4.94 GB   | LM Studio  | Tool calling, RAG, 128K context      |
| `smollm2-1.7b-instruct`            | 1.82 GB   | LM Studio  | Tab autocomplete (Continue.dev)      |
| `text-embedding-nomic-embed-text-v1.5` | 84 MB | LM Studio  | Embeddings (RAG)                     |
| `phi4-mini`                        | ~3 GB     | Ollama     | Fast chat fallback (when Ollama up)  |

### Task → Best Model

| Task                         | Best                          | Runner-up              |
|------------------------------|-------------------------------|------------------------|
| Quick Q&A / brainstorm       | `phi4-mini`                   | `gemma3:4b`            |
| General writing / emails     | `Gemma4 BF16 e4b`             | `granite3.3:8b`        |
| Code generation / debugging  | `Gemma4 BF16 e4b`             | `granite3.3:8b`        |
| Tool / function calling      | `granite3.3:8b`               | `Gemma4 BF16 e4b`      |
| Reasoning / math / logic     | `phi-4-reasoning`             | `Gemma4 BF16 e4b`      |
| Summarization                | `Gemma4 BF16 e4b`             | `granite3.3:8b`        |
| RAG / document Q&A           | `granite3.3:8b` (128K ctx)    | `Gemma4 BF16 e4b`      |
| Multilingual                 | `granite3.3:8b` (12 langs)    | `Gemma4 BF16 e4b`      |
| Multimodal (text + images)   | `gemma3:4b`                   | `Gemma4 BF16 e4b`      |
| Tab autocomplete             | `smollm2:1.7b`                | `phi4-mini-reasoning`  |
| Embeddings                   | `nomic-embed-text`            | —                      |

### Models that fit in 24 GB

- `google/gemma-4-e4b` (9.02 GB, GGUF Q8_0) — **default loaded model**, multimodal (mmproj bundled)
- `mlx-community/gemma-4-e4b-it-8bit` (~9.00 GB, MLX 8-bit) — alt, MTP enabled via mlx-engine
- `granite-3.3-8b-instruct` (4.94 GB) — tool calling, 128K context
- `phi-4-reasoning` (11.12 GB) — chain-of-thought, fits with headroom
- `smollm2-1.7b-instruct` (1.82 GB) — autocomplete only
- `phi4-mini` (~3 GB via Ollama) — fast chat fallback

### Models that do NOT fit — never load

- `mlx-community/gemma-4-26b-a4b-it-4bit` (~16 GB) — too tight on 24 GB, removed (not installed)
- `gemma4:31b-it` (~20 GB) — swaps, context degrades
- `gemma3:27b` / `gemma2:27b` (~16–17 GB) — marginal, risky
- Anything ≥18 GB on Q4_K_M

### Yellow-risk (only if Green alternatives are insufficient)

- `llama3.1:8b` (~6 GB) — general purpose
- `phi4` (~5 GB) — chat
- `phi4-reasoning-plus` (~9 GB) — enhanced reasoning

---

## 4. Runtime Selection — when to use LM Studio vs Ollama

**Decision rule (apply in order):**

1. Is the request about the **primary model** (`Gemma4 BF16 e4b`)? →
   **LM Studio** (port 1234). Use LM Studio chat tab, opencode, Pi, or Continue.dev.
2. Is the request a **quick terminal chat with a small model**
   (`phi4-mini`, `granite-3.3-8b-instruct`)? → **Ollama**
   (`ollama run <name>`).
3. Is the user explicitly wiring up an OpenAI-compatible client? →
   Default to **LM Studio** (`http://localhost:1234/v1`) unless they
   specifically named Ollama.
4. Embeddings (`nomic-embed-text`) → **Ollama** (the embedder lives there).

**Switch between backends:**
```bash
ai-use-mlx     # → LM Studio (default)
ai-use-ollama  # → Ollama
```

---

## 5. Tool Configuration Reference

### Ollama
- HTTP base: `http://localhost:11434`
- OpenAI-compatible: `http://localhost:11434/v1`
- API key: any non-empty string (Ollama doesn't validate)
- Loaded models: `ollama ps` or `GET /api/ps`
- Unload: `POST /api/generate` with `{"model":"<name>","keep_alive":0}`
- Pull: `ollama pull <name>` (only Green-approved models — see §3)

### LM Studio
- HTTP base: `http://localhost:1234`
- OpenAI-compatible: `http://localhost:1234/v1`
- Native model list: `GET /api/v0/models` (preferred — `/v1/models` works but LM Studio logs it as unexpected)
- **API key: requires a real LM Studio token** (not a dummy string). Generate in LM Studio → Developer → API Keys. Store as `LM_STUDIO_API_KEY` in `.secrets`.
- Models live on disk under `~/.lmstudio/models/<vendor>/<model>/`
- The app must be **running with Developer → Start Server** for the API
- Verify the API is up: `curl -s http://localhost:1234/api/v0/models`
- List models without API: `lms ls`
- Set per-model default load settings in **My Models → gear icon**.
  For `granite-3.3-8b-instruct`, use **32K context** by default; use **64K** only
  for long-document sessions. Do not use **128K** as the default on this
  24 GB laptop because KV cache memory can push the system into swap.
- CLI equivalent: `lms load granite-3.3-8b-instruct --context-length 32768`

---

## 6. IDE Integration Reference

These tools are installed and configured on this machine. Config paths are canonical.

### Pi (`pi` CLI)

Pi is a lightweight coding agent with a smaller base prompt than opencode.

| Setting          | Value                                          |
|------------------|------------------------------------------------|
| Binary           | `/opt/homebrew/bin/pi`                         |
| Settings         | `~/.pi/agent/settings.json`                    |
| Auth             | `~/.pi/agent/auth.json` — **chmod 600, never commit** |
| Default provider | `lmstudio`                                     |
| Default model    | `google/gemma-4-e4b`                           |

**Providers configured:**
- `lmstudio` — local LM Studio at `http://localhost:1234/v1`
- `ocp1` — lab vLLM at `https://api-models.apps.ocp1.telcocloud.poc.lab/v1`
- `github-copilot` — Claude Opus/Sonnet 4.6, Gemini 3 Pro (via GitHub Copilot OAuth)
- `anthropic` — via Anthropic OAuth

**Local models exposed:** `google/gemma-4-e4b`, `google/gemma-4-26b-a4b`, `granite3.3:8b`, `phi4-reasoning`, `smollm2-1.7b-instruct`

**Daily usage:**
```bash
pi                                                  # interactive session, default model
pi -c                                               # continue previous session
pi --model lmstudio/google/gemma-4-e4b "..."        # force local
pi --model github-copilot/claude-opus-4.6 "..."     # use cloud model
```

**Switch model mid-session:** Ctrl+P to cycle through configured models.

### Continue.dev (VS Code extension)

| Setting       | Value                             |
|---------------|-----------------------------------|
| Config        | `~/.continue/config.json`         |
| Shortcuts     | Cmd+L (chat), Cmd+I (inline edit) |
| Tab complete  | automatic (SmolLM2 1.7B via LM Studio) |

**Local LM Studio entries (primary):**
- `google/gemma-4-e4b` — 131072 ctx, default for coding/chat
- `google/gemma-4-26b-a4b` — 65536 ctx, heavy multimodal
- `granite-3.3-8b-instruct` — 65536 ctx, tools/RAG
- `phi4-mini` — 32768 ctx, quick chat
- `phi-4-reasoning` — 32768 ctx, logic/math

**Lab vLLM entries** (at `https://api-models.apps.ocp1.telcocloud.poc.lab/v1`, `apiKey: "EMPTY"`):
- `phi-4`, `granite-3.3-8b`, `phi-4-reasoning`, `mistral-7b-v0.2`, `gemma-3-12b`, `gemma-4-E4B-it`, `gemma-4-26B-A4B-it`

**Tab autocomplete model:** `smollm2-1.7b-instruct` via LM Studio (fast, 1.82 GB).

**Embeddings:** `nomic-embed-text` via Ollama.

**When editing `~/.continue/config.json`:** do not touch the lab vLLM entries or existing API keys. Preserve the `tabAutocompleteModel` stanza.

### opencode (CLI)

| Setting         | Value                                   |
|-----------------|-----------------------------------------|
| Binary          | `/opt/homebrew/bin/opencode`            |
| Config          | `~/.config/opencode/opencode.json`      |
| Project rules   | `~/.config/opencode/AGENTS.md`          |
| MCP servers     | `~/.config/opencode/mcp.json`           |

**Providers configured:**
- `lmstudio` — `@ai-sdk/openai-compatible` at `http://127.0.0.1:1234/v1`
- `google` — Antigravity OAuth (Gemini 3 Pro/Flash, Claude Sonnet/Opus 4.5)
- `ocp1` — lab vLLM

**Local LM Studio models (provider `lmstudio`):**

| Model ID                  | Display name                   | Context |
|---------------------------|--------------------------------|---------|
| `google/gemma-4-e4b`      | Gemma 4 E4B Q8 (local · 7.5 GB) | 131072 |
| `google/gemma-4-26b-a4b`  | Gemma 4 26B-A4B Q4 (local · 16 GB) | 65536 |
| `granite-3.3-8b-instruct` | Granite 3.3 8B Instruct        | 32768  |
| `phi-4-reasoning`         | Phi-4 Reasoning                | 16384  |
| `smollm2-1.7b-instruct`   | SmolLM2 1.7B                   | 8192   |

**Backend switching:**
- `ai-use-mlx` writes `~/.config/local-ai/active-backend = lmstudio` and exports `OPENCODE_API_BASE=http://localhost:1234/v1`
- `ai-use-ollama` writes `ollama` and exports `OPENCODE_API_BASE=http://localhost:11434/v1`
- The opencode `lmstudio` **provider name** is separate from the backend file — it always points to LM Studio. The backend file only governs which API base the shell exports.

**MCP servers wired in opencode:**
- `topic-search`, `github-enterprise`, Cisco MCP bridges (see `mcp.json`)

**Compaction:** enabled with `reserveTokens: 8192`, `keepRecentTokens: 20000`.

---

## 7. Stack Lifecycle

The menu bar app (`menubar/app.py`) is the primary control surface. Shell commands are available for terminal workflows.

| Command            | What it does                                                           |
|--------------------|------------------------------------------------------------------------|
| `ai-stack-start`   | Starts LM Studio app + metrics exporter. Prints LM Studio URL.         |
| `ai-stack-stop`    | Unloads Ollama models, quits LM Studio, stops Ollama. **Leaves metrics exporter running** so menu bar stays functional. |
| `ai-stack-off`     | Full shutdown: everything `ai-stack-stop` does PLUS kills metrics exporter. |

Smaller helpers (also in `stack-aliases-v2.sh`):
- `ai-mlx-up` / `ai-mlx-down` / `ai-mlx-status` — LM Studio only
- `ai-menubar-start` / `ai-menubar-stop` — rumps menu bar app
- `ai-use-mlx` / `ai-use-ollama` — switch backend (LM Studio ↔ Ollama)
- `ai-secrets` — load `.secrets` into the current shell
- `ai-health-phase6` — verify LM Studio + Pi + mlx-lm + web search key

**Difference between `ai-mlx-*` and `ai-stack-*`:**
- `ai-stack-*` manages the full lifecycle: LM Studio + Ollama + metrics exporter.
- `ai-mlx-*` manages only LM Studio itself (lighter, no exporter management).

---

## 8. The `.secrets` File

Path: `~/Documents/AI/Local-AI/.secrets` (in `.gitignore`).
Format: `KEY=value` per line.

Currently holds:
```
CONTROL_TOKEN=<random-hex>
TAVILY_API_KEY=<key>     # optional — web search
BRAVE_API_KEY=<key>      # optional — web search
```

`CONTROL_TOKEN` is bearer auth between the menu bar app and the metrics-exporter control server (:9091). It is generated automatically by `ai-stack-start` and `menubar/app.py` if missing. The control server rejects all POST actions without it.

---

## 9. Metrics Exporter Architecture

```
Menu bar app (rumps, host)
    │
    ├─ reads /tmp/ai-metrics.json  ← metrics-exporter.py writes every 3s
    │
    └─ POST http://localhost:9091/control  ← metrics-exporter.py control server
                (Bearer CONTROL_TOKEN)
```

**Invariants:**
- `metrics-exporter.py` runs on the **host** (no container). Started by `ai-stack-start` or the menu bar app's `_ensure_exporter()`.
- Control server binds to `127.0.0.1:9091` by default. Token auth always required.
- Metrics written atomically (`.tmp` + `os.replace`) to `/tmp/ai-metrics.json`.
- **Services monitored:** LM Studio app (pgrep), LM Studio API (`/api/v0/models`), Ollama (`/api/tags`).
- **Actions supported:** `stack_start`, `stack_stop`, `ollama_stop`, `ollama_start`, `lmstudio_start`, `lmstudio_stop`.

### Metrics exporter cheat sheet
- Lives at `scripts/metrics-exporter.py`, started by `ai-stack-start` or menu bar.
- Runs on the **host** (needs `top`, `vm_stat`, `du`).
- Writes `/tmp/ai-metrics.json` every 3 s (`cpu_pct`, `ram`, `disk`, `services`).
- Control server: `POST /control` with `{"action":"<name>"}` and bearer auth.
- Logs: `/tmp/ai-stack.log` (subprocess actions) and `/tmp/ai-metrics-exporter.log` (stdout).
- **Uses `/api/v0/models`** (not `/v1/models`) to check LM Studio status — avoids LM Studio's "unexpected endpoint" error log.

---

## 10. Docs-sync Rule — MANDATORY

**Every code change must consider whether `docs/index.html` needs an update.**
The docs site is the public-facing description; if it drifts, users hit
broken setup steps.

Run this checklist before finishing any task:

| If you changed…                                | Then update…                                                       |
|------------------------------------------------|--------------------------------------------------------------------|
| Model name / size / role                       | Models table, Task→Model guide, code examples in `docs/index.html` |
| Port, URL, container name                      | Architecture section in `docs/index.html`                          |
| Shell alias added/removed/renamed              | Commands & Aliases table in `docs/index.html`                      |
| Service added/removed                          | Overview cards + Architecture diagram in `docs/index.html`         |
| Env var added/changed                          | Environment Variables table in `docs/index.html`                   |
| Phase script behavior                          | Matching Setup step + example commands in `docs/index.html`        |

Always grep before committing:
```bash
grep -n "<old-name>" docs/index.html AGENTS.md CLAUDE.md stack-aliases-v2.sh
```
If grep finds a hit, fix it in the **same commit** as the code change.

If the change is purely internal (refactor, no user-visible surface),
say so explicitly in the commit/PR: `docs-sync: N/A — internal refactor only.`

---

## 11. Coding Guidelines

1. **Shell scripts:** target `zsh` (macOS default), shebang `#!/bin/zsh`.
2. **Python:** 3.11+ (system Python). Use `pip install --break-system-packages`
   when needed. Stdlib-first; avoid heavy deps for small tools.
3. **No containers.** Podman was removed. Do not add Docker or Podman to this stack.
4. **Package manager:** Homebrew. Prefer `brew install` over manual installs.
5. **Config files:** `~/.config/local-ai/` or in this project directory.
6. **API format:** OpenAI-compatible everywhere — easier tool integration.
7. **Plan-then-build:** for non-trivial coding tasks, plan with
   `phi-4-reasoning`, implement with `google/gemma-4-e4b`.
8. **Context budget:** model max context is not the same as loaded context.
   LM Studio can expose `granite3.3:8b` as a 128K-capable model while it is
   loaded at only 4K, which will fail on long prompts. Default Granite to
   32K context in LM Studio; use 64K for long documents; avoid 128K as an
   everyday default on 24 GB RAM.
9. **No new files unless required.** Prefer editing existing files.
10. **No emojis in files** unless explicitly requested.

---

## 12. Common Tasks (with exact commands)

### Install a new (approved) model
```bash
ollama pull <model-name>            # for Ollama
# Or in LM Studio: GUI → Search → Download (saves to ~/.lmstudio/models/)
ollama run <model-name> "Hi"        # smoke test
```

### Switch the coding model
For opencode / Pi via LM Studio:
```bash
ai-use-mlx                          # LM Studio backend
# Then in LM Studio: load the desired model
```
For Ollama-based clients:
```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"<old-model>","keep_alive":0}' >/dev/null
ollama run <new-model> --keepalive 5m
```

### Check system resources
```bash
macmon          # real-time Apple Silicon metrics (CPU/GPU/RAM/power)
ollama ps       # currently loaded Ollama models
curl -s http://localhost:1234/api/v0/models | python3 -m json.tool   # LM Studio
```

### Free up memory
```bash
# Unload all Ollama models
for m in $(ollama ps | tail -n +2 | awk '{print $1}'); do
  curl -s http://localhost:11434/api/generate \
    -d "{\"model\":\"$m\",\"keep_alive\":0}" >/dev/null
done
# In LM Studio: click "Eject" on the loaded model in the GUI.
```

---

## 13. Troubleshooting

| Symptom                              | Cause                          | Fix                                                  |
|--------------------------------------|--------------------------------|------------------------------------------------------|
| Generation very slow                 | Memory swap — model too large  | Use smaller model or Q4_K_M; close apps              |
| `out of memory` error                | Total exceeds 24 GB            | Unload models; close Chrome/Slack; smaller quant     |
| Tool can't reach Ollama              | Ollama not running             | `ollama serve` or `brew services start ollama`       |
| Tool can't reach LM Studio API       | App running but server isn't   | LM Studio → Developer tab → Start Server (:1234)     |
| Poor code quality                    | Wrong model for task           | Switch to `Gemma4 BF16 e4b` or `granite3.3:8b`      |
| Continue.dev autocomplete laggy      | Autocomplete model too large   | Use `smollm2:1.7b` for autocomplete only             |
| `git add` hangs                      | Stale `.git/index.lock`        | `rm -f .git/index.lock` and retry                    |
| LM Studio logs "unexpected endpoint" | `/v1/models` called instead of `/api/v0/models` | Check that no tool is polling `/v1/models` — metrics-exporter and menubar both use `/api/v0/models` |
| Menu bar shows all red               | metrics-exporter not running   | Run `ai-stack-start` or `ai-menubar-start`           |

---

## 14. Known Gotchas (each cost real debugging time)

1. **`BaseHTTPRequestHandler` header order matters.** `send_response()`
   must come before any `send_header()`, and `end_headers()` must come
   last. Wrong order produces cryptic 502s.

2. **`osascript do shell script` runs `/bin/sh`, not zsh.** If a one-liner
   uses zsh features (process substitution, `**` globs), wrap with
   `zsh -c '<command>'`. Same applies to `subprocess.Popen(['zsh','-c',…])`
   in `metrics-exporter.py`.

3. **`ai-stack-start` kills and restarts the metrics-exporter.** Therefore
   the exporter's control server **cannot invoke `ai-stack-start`** (it
   would kill itself mid-request). The `_stack_start` function in
   `metrics-exporter.py` inlines the equivalent commands via
   `subprocess.Popen(['zsh','-c', …])` to avoid this.

4. **`docs/index.html` — do NOT use `display:none` + JS tab switching.**
   Sections must always be visible; nav uses `href="#s-..."` with
   `html { scroll-behavior: smooth }`, `.section { scroll-margin-top: 54px }`,
   and an `IntersectionObserver` highlights the active link.

5. **Fonts: system stack only.** Current stack:
   `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`.
   **Do not add Google Fonts `<link>` tags.**

6. **LM Studio model IDs include the full path on disk.** Do not assume
   `Gemma4 BF16 e4b` is the literal API model ID — query
   `GET /api/v0/models` to see what LM Studio actually exposes, then use
   that exact ID in OpenAI-compatible clients.

7. **Pi `~/.pi/agent/auth.json` contains live OAuth tokens.** Never commit
   this file. It is not in `.gitignore` by default — verify before any
   `git add ~/.pi` or similar.

---

## 15. Environment Variables

Add to `~/.zshrc`:

```bash
# Ollama
export OLLAMA_KEEP_ALIVE=5m           # auto-unload after 5 min idle
export OLLAMA_MAX_LOADED_MODELS=1     # 1 model at a time (24 GB constraint)
export OLLAMA_NUM_GPU=99              # use all GPU layers (Metal)
export OLLAMA_HOST=0.0.0.0:11434     # allow local tools to reach Ollama

# OpenCode (LM Studio default — managed by ai-use-mlx / ai-use-ollama)
export OPENCODE_PROVIDER=openai-compatible
export OPENCODE_API_BASE=http://localhost:1234/v1
export OPENCODE_MODEL="google/gemma-4-e4b"
```

Convenience aliases (already in `stack-aliases-v2.sh`):

```bash
alias ai-chat="ollama run phi4-mini"                    # ~3 GB, ultra-fast
alias ai-general="ollama run granite-3.3-8b-instruct"   # ~5 GB, Ollama fallback
alias ai-code="ollama run granite-3.3-8b-instruct"      # ~5 GB, tool-calling + 128K ctx
alias ai-reason="ollama run phi-4-reasoning"            # ~11 GB, chain-of-thought
alias ai-status="ollama ps"
# Primary (google/gemma-4-e4b, 6.33 GB) is in LM Studio — use LM Studio chat, opencode, or Pi.
```

---

## 16. Git Workflow

- Default branch: `main`. Remote: `origin` (GitHub).
- GitHub account: **`simoneiaci`**. If active credentials are different,
  switch or re-auth before pushing.
- Always `git pull --rebase` before pushing — no merge commits.
- Commit message format: `<type>: <short summary>`. Types: `feat`, `fix`,
  `docs`, `refactor`, `chore`.
- **Never** force-push to `main`. **Never** commit `.secrets`.
- Before any commit that touches a model name, port, alias, or service,
  run the docs-sync grep (§10).

---

## 17. End-to-End Smoke Test

After any infrastructure change:

1. `ai-stack-off` (clean slate)
2. `ai-stack-start` — watch for errors; LM Studio opens
3. Menu bar app shows green dots for LM Studio app + API, Ollama optional
4. `ai-use-mlx` → `opencode` or `pi` → ask a question → should respond via `google/gemma-4-e4b`
5. Continue.dev in VS Code: Cmd+L → select "Local LM Studio - Gemma 4 E4B" → ask a question
6. `ai-stack-stop` — LM Studio quits; menu bar stays functional (metrics exporter running)
7. `ai-stack-off` — everything down cleanly

---

## 18. How to Think About the User

- Simone wants things that **just work** and **look good**. Polish > features.
- Prefers **direct answers and working code** over long explanations.
- Prefers **minimal fonts, system stack, no Google Fonts**.
- When he says "commit and push", do it — no extra prompts.
- When he reports a bug, **reproduce the cause before patching** — don't guess.
- Short replies are better than long ones. End-of-turn summary: 1–2 sentences max.
- He uses Italian for tax/legal documents — `granite3.3:8b` for those (multilingual).

---

## 19. If You Get Stuck

1. **Re-read §0 (Stop-First Rules).**
2. Grep the repo (`grep -rn "<thing>" .`) before assuming a path or name.
3. Check the actual filesystem (`ls`, `cat`) before editing.
4. Read `/tmp/ai-metrics-exporter.log` and `/tmp/ai-stack.log` for errors.
5. **If still unclear, ask the user a single specific question.** Do not
   guess and do not make destructive changes.
