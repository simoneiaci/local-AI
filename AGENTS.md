# Local-AI Project — Agent Instructions

> This file contains instructions for AI agents working on the Local-AI project.  
> **Hardware:** MacBook Pro M4 Pro — 24GB unified memory  
> **Owner:** Simone

---

## Project Context

This project manages a fully local AI stack on a MacBook Pro M4 Pro (24GB). The stack consists of:

- **LM Studio** as the default LLM runtime for MLX models (port 1234, OpenAI-compatible API at `/v1`)
- **Ollama** as an alternate LLM runtime and model manager (port 11434, OpenAI-compatible API at `/v1`)
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
> **Qwen models are NOT approved for this project — never suggest or install them.**
> **DeepSeek models are NOT approved** — never suggest them.

When suggesting or selecting models, use the task guide below:

### Task → Best Model (all Green)

| Task                         | Best model                   | Runner-up              | VRAM    |
|------------------------------|------------------------------|------------------------|---------|
| Quick Q&A / brainstorm       | `phi4-mini` (3 GB)           | `gemma3:4b` (3 GB)    | Light   |
| General writing / emails     | `mistral-small3.1:24b`       | `gemma3:12b`           | 14 / 7  |
| Code generation / debugging  | `gemma3:12b`           | `granite3.3:8b`        | 7 / 6   |
| Tool / function calling      | `granite3.3:8b`        | `gemma3:12b`           | 6 / 7   |
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
- Provider: Ollama or OpenAI-compatible local API, depending on runtime
- Supports separate models for chat vs. tab-autocomplete

### OpenCode
- Default: `OPENCODE_API_BASE=http://localhost:1234/v1` for LM Studio
- Alternate: `OPENCODE_API_BASE=http://localhost:11434/v1` for Ollama
- Requires models with tool-calling support and 64K+ context
- Recommended model: `gemma3:12b` or `mistral-small3.1:24b`

### Open WebUI
- Runs in Podman on port 3000
- Connects to LM Studio by default via `OPENAI_API_BASE_URL=http://host.containers.internal:1234/v1`
- Keeps Ollama available as the alternate runtime via `OLLAMA_BASE_URL=http://host.containers.internal:11434`
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
7. **Plan-then-build**: for non-trivial coding tasks, first use `phi4-reasoning` to outline the approach, then switch to `gemma3:12b` to implement it.
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
| Poor code quality from model | Model too small or wrong type | Switch to `gemma3:12b` for coding tasks |
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
export OPENCODE_API_BASE=http://localhost:1234/v1
export OPENCODE_MODEL=gemma3:12b

# Convenience aliases (all Green-approved models)
alias ai-chat="ollama run phi4-mini"              # ~3 GB, ultra-fast
alias ai-general="ollama run gemma3:12b"           # ~8 GB, balanced
alias ai-code="ollama run gemma3:12b"          # ~7 GB, coding + daily use
alias ai-reason="ollama run phi4-reasoning"        # ~9 GB, chain-of-thought
alias ai-power="ollama run mistral-small3.1:24b"   # ~14 GB, best overall
alias ai-status="ollama ps"
```

---

## Dashboard, Docs & Stack Infrastructure — Agent Guide

> This section is written for any AI agent (including less capable ones) that will continue
> evolving the infrastructure in this repo. Read it fully before making changes.

### Repo Layout

```
Local-AI/
├── AGENTS.md                 ← this file
├── README.md                 ← human-facing overview
├── PROJECT-PLAN.md           ← architectural plan, hardware constraints
├── CLAUDE.md                 ← symlink/twin of AGENTS.md for Claude Code
├── stack-aliases-v2.sh       ← shell functions: ai-stack-start / -stop / -off
├── scripts/
│   └── metrics-exporter.py   ← runs on HOST Mac (not in container), writes
│                               /tmp/ai-metrics.json every 3s + control server :9091
├── dashboard/
│   ├── app.py                ← Flask-ish stdlib HTTP server, runs in Podman on :9090
│   ├── Dockerfile            ← python:3.11-alpine image
│   └── config.json           ← dashboard config
└── docs/
    └── index.html            ← GitHub Pages site (single-file HTML + inline CSS/JS)
```

### Stack Lifecycle Commands

Three shell functions defined in `stack-aliases-v2.sh` (sourced from `~/.zshrc`):

- **`ai-stack-start`** — starts LM Studio, Podman machine, Open WebUI, Pipelines,
  dashboard container (creating it on first run with the correct bind mount),
  and the metrics-exporter (killing any old instance first). Opens
  http://localhost:3000.
- **`ai-stack-stop`** — unloads models, stops Pipelines + WebUI + local runtimes.
  **Intentionally leaves the dashboard container and metrics-exporter running**
  so the user can still see system stats and restart services from the dashboard.
- **`ai-stack-off`** — full shutdown: everything `ai-stack-stop` does PLUS
  kills metrics-exporter, stops dashboard container, stops Podman machine.

### The `.secrets` File

Located at `~/Documents/AI/Local-AI/.secrets` (never commit — in `.gitignore`).
Format: `KEY=value` lines. Currently holds:

```
CONTROL_TOKEN=<random-hex>
```

Used by the dashboard proxy → metrics-exporter control server for bearer auth.
The token is injected into the dashboard container via `-e CONTROL_TOKEN=...`
at `ai-stack-start` time and read by `metrics-exporter.py` from the same file.
`ai-stack-start`, `phase4-dashboard.sh`, and the menu bar app generate this
token if it is missing. The control server rejects all POST actions without it.

### Dashboard Architecture (CRITICAL)

```
Browser  ──HTTP──▶  dashboard container :9090  ──HTTP+Bearer──▶  metrics-exporter :9091 (host)
                   (app.py, Podman)                            (metrics-exporter.py, runs on Mac)
                         │                                            │
                         └─── reads /hosttmp/ai-metrics.json ◀────────┘ writes /tmp/ai-metrics.json
                              (bind mount of /private/tmp)
```

Key points:
- The **browser never holds the token** — it calls `/control` on :9090 and
  `app.py` server-side adds the `Authorization: Bearer <token>` header.
- The exporter is the **only thing allowed to shell out** on the host (Ollama,
  Podman, Tailscale). The container can only do HTTP round-trips to :9091.
- `metrics-exporter.py` binds the control server to `127.0.0.1` by default.
  Stack scripts set `CONTROL_BIND=0.0.0.0` only when the Podman dashboard needs
  to reach it, and bearer auth is still required.
- Metrics flow is **file-based**, not HTTP: exporter writes JSON atomically
  (`.tmp` + `os.replace`) to `/tmp/ai-metrics.json`; dashboard reads it from
  `/hosttmp/ai-metrics.json` (the bind-mounted view).

### Rebuilding the Dashboard Image

```bash
cd ~/Documents/AI/Local-AI/dashboard
podman rm -f local-ai-dashboard 2>/dev/null
podman rmi localhost/local-ai-dashboard 2>/dev/null
podman build -t localhost/local-ai-dashboard .
# Then re-run ai-stack-start to recreate the container with correct env + mounts
```

Any change to `app.py`, `config.json`, or `Dockerfile` requires a rebuild.
**The container does not hot-reload.**

### Known Gotchas (each one cost real debugging time)

1. **Podman virtiofs single-file bind mounts are broken on macOS.**
   `-v /private/tmp/ai-metrics.json:/metrics/host.json:ro` silently fails to
   surface the file inside the container. **Always mount the parent directory**:
   `-v /private/tmp:/hosttmp:ro`. Source path must be `/private/tmp` not `/tmp`
   (macOS symlinks `/tmp` → `/private/tmp` and Podman rejects the symlink).

2. **`BaseHTTPRequestHandler` header ordering matters.**
   `send_response()` **must** come before any `send_header()` calls, and
   `end_headers()` must come last. Getting this wrong produces cryptic errors
   like "Access-Control-Allow-Origin: got extra header" 502s.

3. **`osascript do shell script` runs `/bin/sh`, not zsh.**
   If a shell one-liner uses zsh features (process substitution, `**` globs),
   wrap it: `zsh -c '<command>'`. Same applies to `subprocess.Popen(['zsh','-c', …])`
   in `metrics-exporter.py` — the control server uses this.

4. **`ai-stack-start` kills and restarts the metrics-exporter.**
   Therefore the exporter's control server **cannot invoke `ai-stack-start`**
   (it would kill itself mid-request). The `_stack_start` / `_stack_stop`
   functions in `metrics-exporter.py` inline the equivalent commands directly
   via `subprocess.Popen(['zsh','-c', ...])` to avoid this.

5. **GitHub Pages (`docs/index.html`) — do NOT use `display:none` + JS tab
   switching for sections.** The user asked for smooth-scroll nav. Current
   implementation: all sections always visible, nav uses `href="#s-..."`,
   `html { scroll-behavior: smooth }`, `.section { scroll-margin-top: 54px }`,
   and an `IntersectionObserver` highlights the active link.

6. **Fonts: use the system font stack only.** The user rejected Syne, Plus
   Jakarta Sans, Oxanium, and Nunito Sans. Current stack:
   `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`.
   **Do not add Google Fonts `<link>` tags.**

7. **Stale `.git/index.lock`** sometimes lingers after interrupted commits.
   If `git add` hangs or errors, `rm -f .git/index.lock` and retry.

8. **The dashboard's "start/stop whole stack" toggle button** in the header
   changes color based on the LM Studio API readiness status, not just the app process.
   The LM Studio app and `:1234` API are shown separately because the app can be
   running while the OpenAI-compatible API is unavailable, or while the API is
   reachable but exposes only embedding/no chat models. It
   calls the `stack_start` / `stack_stop` actions on the control server — not
   the shell aliases — for the reason in gotcha #4.

### Metrics Exporter Cheat Sheet

Lives at `scripts/metrics-exporter.py`, started by `ai-stack-start`:

- Runs on the **host**, not in a container (needs `top`, `vm_stat`, `du`, `tailscale`, `podman`).
- Writes `/tmp/ai-metrics.json` every 3s with `cpu_pct`, `ram`, `disk`, `services`.
- HTTP control server on :9091, accepts `POST /control` with
  `{"action": "<name>"}` and `Authorization: Bearer <CONTROL_TOKEN>`.
- Supported actions: `stack_start`, `stack_stop`, `ollama_start/stop`,
  `webui_start/stop`, `pipelines_start/stop`, `podman_start/stop`,
  `tailscale_up/down`, `lmstudio_start/stop`. Extend `ACTIONS` dict to add new ones.
- Logs to `/tmp/ai-stack.log` (subprocess output) and `/tmp/ai-metrics-exporter.log` (stdout).

### GitHub Pages Site (`docs/index.html`)

- Single-file HTML; inline `<style>` and `<script>`.
- Hosted on the repository's GitHub Pages site, if enabled.
- Structure: top nav + stacked `<section id="s-...">` blocks, one per topic.
- Deploy: commit to `main`, push — GitHub Pages auto-rebuilds within ~1 min.

### Git Workflow

- Default branch: `main`. Remote: `origin` on GitHub.
- For public GitHub operations, always try to use the `simoneiaci` GitHub account/username first.
  If the active credentials belong to another account, switch or re-authenticate before pushing.
- Always `git pull --rebase` before pushing to avoid merge commits.
- Commit messages: `<type>: <short summary>`, types: `feat`, `fix`, `docs`, `refactor`, `chore`.
- Never force-push to `main`. Never commit `.secrets` or any file containing tokens.

### Docs-sync rule — MANDATORY

**Anytime code changes, check whether `docs/index.html` (the GitHub Pages site)
needs a matching update.** The docs site is the public-facing description of
this stack — if it drifts from reality, users hit setup instructions that no
longer match the repo.

Before finishing any task that modifies code, run through this checklist:

1. **Model changes** (added/removed/swapped a model in scripts, aliases,
   `CLAUDE.md`, `AGENTS.md`, or `dashboard/config.json`):
   → update the Models table, Task→Model guide, dashboard mockup, and any
     code examples in `docs/index.html` that reference the old model name.
2. **Port, URL, or container-name changes** (anything in `dashboard/`,
   `scripts/`, `stack-aliases-v2.sh`): → update matching references in the
   Dashboard / Architecture sections.
3. **New shell alias / removed alias** in `stack-aliases-v2.sh`:
   → update the Commands & Aliases table.
4. **New service / removed service** (e.g. SearXNG, Pipelines, Tailscale):
   → update the Overview cards, Architecture diagram, and relevant section.
5. **Environment variables added/changed**: → update the Environment Variables
   table in the Commands section.
6. **Setup-script behavior changes** (phase1–5 scripts): → update the matching
   Setup step and any example commands.

If the change is purely internal (refactor, bug fix with no user-visible
surface), say so explicitly in the commit / PR summary: "docs-sync: N/A —
internal refactor only."

Grep the docs for any renamed model/port/alias before committing:

```bash
grep -n "<old-name>" docs/index.html
```

If `grep` finds a hit, fix it in the same commit as the code change — not a
follow-up. A drifted docs site is worse than an outdated comment.

### End-to-End Smoke Test

After any infrastructure change:

1. `ai-stack-off` (clean slate)
2. `ai-stack-start` — watch for errors; browser opens http://localhost:3000
3. Open http://localhost:9090 — dashboard must show live CPU/RAM/disk and
   the default services (Podman, LM Studio app, LM Studio API, Open WebUI,
   Pipelines) as "up".
4. Click the header Stack toggle — it should turn red and services should go down.
5. Click again — services should come back up; metrics keep updating throughout.
6. `ai-stack-stop` from terminal — dashboard stays up, shows services as down,
   start buttons still functional.
7. `ai-stack-off` — everything down cleanly.

### How to Think About the User

- Simone wants things that **just work** and look good. Prefer polish over features.
- Prefers **minimal fonts, system stack, no Google Fonts**.
- Prefers **direct answers and working code** over long explanations.
- When he says "commit and push", do it — no extra prompts.
- When he reports a bug, reproduce the cause before patching; don't guess.
