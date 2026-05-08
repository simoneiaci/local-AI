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
   `AGENTS.md`, `CLAUDE.md`, `stack-aliases-v2.sh`, and `dashboard/config.json`.**
   See §10 (Docs-sync rule).
7. **Never invent file paths, command names, model tags, or env vars.**
   If you don't know it, grep for it or run `ls` — do not guess.
8. **If a step is unclear or risky, stop and ask the user** rather than
   guessing. Simone prefers a 1-line clarifying question to silent damage.

---

## 1. Project Overview

This repo manages a fully local AI stack on a single MacBook. The user has
zero cloud dependencies; everything runs on `localhost`.

| Component       | Purpose                                  | Port    |
|-----------------|------------------------------------------|---------|
| **LM Studio**   | **Default LLM runtime** (MLX/GGUF)       | 1234    |
| Ollama          | Alternate runtime + model manager        | 11434   |
| Open WebUI      | ChatGPT-style UI (Podman container)      | 3000    |
| Pipelines       | Open WebUI middleware (Podman)           | 9099    |
| Dashboard       | Stack monitoring UI (Podman)             | 9090    |
| Metrics exporter| Host-side metrics + control server       | 9091    |
| SearXNG         | Self-hosted web search                   | 8080    |
| Tailscale       | Encrypted remote access                  | —       |

All LLM endpoints are **OpenAI-compatible** at `<host>:<port>/v1`.

The full project plan lives in `PROJECT-PLAN.md`. The public-facing docs
site lives in `docs/index.html`.

### Remote access
Open WebUI is reachable from iPhone via Tailscale at
`http://<tailscale-ip>:3000`. Ollama at `http://<tailscale-ip>:11434/v1`
requires `OLLAMA_HOST=0.0.0.0:11434`. Mac must be awake (`caffeinate -s &`).

---

## 2. Memory Budget — the constraint that drives every decision

```
24 GB total
−  8 GB macOS + Finder + system services
= 16 GB available for models, browsers, IDEs, Docker/Podman
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

### Configured local inventory (verify with `lms ls`, `ollama list`, and LM Studio `/v1/models`)

| Model                              | Size      | Runtime    | Role                                 |
|------------------------------------|-----------|------------|--------------------------------------|
| `google/gemma-4-e4b` (gemma4 arch) | 6.33 GB   | LM Studio  | **Primary** — chat, code (LOADED)    |
| `phi4-reasoning` (15B)             | 11.12 GB  | LM Studio  | Chain-of-thought reasoning           |
| `granite-3.3-8b-instruct`          | 4.94 GB   | LM Studio  | Tool calling, RAG, 128K context      |
| `smollm2-1.7b-instruct`            | 1.82 GB   | LM Studio  | Tab autocomplete (Continue.dev)      |
| `text-embedding-nomic-embed-text-v1.5` | 84 MB | LM Studio  | Embeddings (RAG)                     |
| `phi4-mini`                        | ~3 GB     | Ollama     | Fast chat fallback (when Ollama up)  |

### Task → Best Model

| Task                         | Best                          | Runner-up              |
|------------------------------|-------------------------------|------------------------|
| Quick Q&A / brainstorm       | `phi4-mini`                   | `gemma3:4b`            |
| General writing / emails     | `Gemma4 BF16 e4b`           | `granite3.3:8b`        |
| Code generation / debugging  | `Gemma4 BF16 e4b`           | `granite3.3:8b`        |
| Tool / function calling      | `granite3.3:8b`               | `Gemma4 BF16 e4b`    |
| Reasoning / math / logic     | `phi4-reasoning`              | `Gemma4 BF16 e4b`    |
| Summarization                | `Gemma4 BF16 e4b`           | `granite3.3:8b`        |
| RAG / document Q&A           | `granite3.3:8b` (128K ctx)    | `Gemma4 BF16 e4b`    |
| Multilingual                 | `granite3.3:8b` (12 langs)    | `Gemma4 BF16 e4b`    |
| Multimodal (text + images)   | `gemma3:4b`                 | `Gemma4 BF16 e4b`      |
| Tab autocomplete             | `smollm2:1.7b`                | `phi4-mini-reasoning`  |
| Embeddings                   | `nomic-embed-text`            | —                      |

### Models that fit in 24 GB

- `google/gemma-4-e4b` (6.33 GB) — **current primary**, BF16 quality, gemma4 arch
- `granite-3.3-8b-instruct` (4.94 GB) — tool calling, 128K context
- `phi4-reasoning` (11.12 GB) — chain-of-thought, fits with headroom
- `smollm2-1.7b-instruct` (1.82 GB) — autocomplete only
- `phi4-mini` (~3 GB via Ollama) — fast chat fallback

### Models that do NOT fit — never load

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
   **LM Studio** (port 1234). Use Open WebUI or OpenCode as the client.
2. Is the request a **quick terminal chat with a small model**
   (`phi4-mini`, `granite3.3:8b`, `phi4-reasoning`)? → **Ollama**
   (`ollama run <name>`).
3. Is the user explicitly wiring up an OpenAI-compatible client? →
   Default to **LM Studio** (`http://localhost:1234/v1`) unless they
   specifically named Ollama.
4. Embeddings (`nomic-embed-text`) → **Ollama** (the embedder lives there).

**Switch OpenCode between backends:**
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
- **API key: requires a real LM Studio token** (not a dummy string). Generate in LM Studio → Developer → API Keys. Store as `LM_STUDIO_API_KEY` in `.secrets`.
- Models live on disk under `~/.lmstudio/models/<vendor>/<model>/`
- The app must be **running with Developer → Start Server** for the API
- Verify the API is up: `curl -s http://localhost:1234/v1/models -H "Authorization: Bearer $LM_STUDIO_API_KEY"`
- List models without API: `lms ls`
- Set per-model default load settings in **My Models → gear icon**.
  For `granite-3.3-8b-instruct`, use **32K context** by default; use **64K** only
  for long-document sessions. Do not use **128K** as the default on this
  24 GB laptop because KV cache memory can push the system into swap.
- CLI equivalent: `lms load granite-3.3-8b-instruct --context-length 32768`

### Continue.dev
- Config: `~/.continue/config.json`
- Provider: OpenAI-compatible (LM Studio default) or Ollama
- Separate models for chat (`Gemma4 BF16 e4b`) vs autocomplete (`smollm2:1.7b`)

### OpenCode
- `OPENCODE_API_BASE=http://localhost:1234/v1` (default — LM Studio)
- Alternate: `http://localhost:11434/v1` (Ollama)
- Recommended model: `Gemma4 BF16 e4b`
- Requires tool-calling + 64K+ context

### Open WebUI
- Container: `open-webui` in Podman, port 3000
- Connects to LM Studio via `OPENAI_API_BASE_URL=http://host.containers.internal:1234/v1`
- Ollama alternate: `OLLAMA_BASE_URL=http://host.containers.internal:11434`
- Manage: `podman start|stop|logs open-webui`

### LiteLLM (proxy, optional)
- `litellm --model ollama/<model> --port 4000`
- Exposes OpenAI API at `http://localhost:4000/v1`

---

## 6. Repo Layout

```
Local-AI/
├── AGENTS.md                ← this file (authoritative)
├── CLAUDE.md                ← thin pointer to AGENTS.md
├── README.md                ← human-facing overview
├── PROJECT-PLAN.md          ← architectural plan, hardware notes
├── stack-aliases-v2.sh      ← shell functions: ai-stack-* / ai-use-* / ai-chat etc.
├── scripts/
│   ├── phase1-setup.sh      ← Ollama + core models + zshrc aliases
│   ├── phase2-coding-tools.sh  ← Continue.dev + OpenCode + Aider
│   ├── phase3-webui.sh      ← Open WebUI in Podman
│   ├── phase4-dashboard.sh  ← Dashboard container + metrics exporter
│   ├── phase5-remote.sh     ← Tailscale / Caddy / Cloudflare Tunnel
│   ├── phase6-improvements.sh  ← LM Studio install, mlx-lm, Pi
│   ├── metrics-exporter.py  ← runs on HOST; writes /tmp/ai-metrics.json
│   ├── status.sh            ← quick health check
│   └── mcp-with-secrets.sh  ← MCP launcher with .secrets sourced
├── dashboard/
│   ├── app.py               ← stdlib HTTP server, runs in Podman :9090
│   ├── Dockerfile           ← python:3.11-alpine
│   └── config.json          ← dashboard config (services + models list)
├── menubar/
│   ├── app.py               ← rumps menu-bar app (host-side)
│   └── requirements.txt
└── docs/
    └── index.html           ← GitHub Pages site (single-file HTML)
```

---

## 7. Stack Lifecycle

Three shell functions in `stack-aliases-v2.sh`, sourced by `~/.zshrc`:

| Command            | What it does                                                                  |
|--------------------|-------------------------------------------------------------------------------|
| `ai-stack-start`   | Starts LM Studio app, Podman machine, Open WebUI, Pipelines, dashboard, metrics exporter. Opens http://localhost:3000. |
| `ai-stack-stop`    | Unloads models, stops WebUI/Pipelines/runtimes. **Leaves dashboard + exporter running** so the user can still see stats and click "start". |
| `ai-stack-off`     | Full shutdown: everything `ai-stack-stop` does PLUS kills exporter, dashboard, Podman machine. |

Smaller helpers (also in `stack-aliases-v2.sh`):
- `ai-mlx-up` / `ai-mlx-down` / `ai-mlx-status` — LM Studio only
- `ai-menubar-start` / `ai-menubar-stop` — rumps menu bar app
- `ai-use-mlx` / `ai-use-ollama` — switch OpenCode backend
- `ai-secrets` — load `.secrets` into the current shell
- `ai-health-phase6` — verify LM Studio + Pi + mlx-lm + web search key

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

`CONTROL_TOKEN` is bearer auth between dashboard container (:9090) and
metrics-exporter control server (:9091). It is generated automatically by
`ai-stack-start`, `phase4-dashboard.sh`, and the menu bar app if missing.
The control server rejects all POST actions without it.

---

## 9. Dashboard Architecture

```
Browser ──HTTP──▶ dashboard :9090 ──HTTP+Bearer──▶ metrics-exporter :9091 (host)
                  (Podman, app.py)                  (metrics-exporter.py)
                       │                                   │
                       └── reads /hosttmp/ai-metrics.json ─┘ writes /tmp/ai-metrics.json
                            (bind mount of /private/tmp)
```

**Invariants:**
- Browser **never** holds the token. `app.py` server-side adds the
  `Authorization: Bearer <token>` header when proxying to :9091.
- The exporter is the **only thing allowed to shell out** on the host
  (Ollama/Podman/Tailscale CLIs). The container can only HTTP to :9091.
- `metrics-exporter.py` binds the control server to `127.0.0.1` by default.
  Stack scripts set `CONTROL_BIND=0.0.0.0` only when the Podman dashboard
  needs to reach it; bearer auth still required.
- Metrics flow is **file-based**, not HTTP. Exporter writes JSON atomically
  (`.tmp` + `os.replace`) to `/tmp/ai-metrics.json`; container reads from
  `/hosttmp/ai-metrics.json`.

### Rebuilding the dashboard image
```bash
cd ~/Documents/AI/Local-AI/dashboard
podman rm -f local-ai-dashboard 2>/dev/null
podman rmi localhost/local-ai-dashboard 2>/dev/null
podman build -t localhost/local-ai-dashboard .
# Then re-run ai-stack-start to recreate with correct env + mounts
```
**The container does not hot-reload.** Any change to `app.py`,
`config.json`, or `Dockerfile` requires rebuild.

### Metrics exporter cheat sheet
- Lives at `scripts/metrics-exporter.py`, started by `ai-stack-start`.
- Runs on the **host** (needs `top`, `vm_stat`, `du`, `tailscale`, `podman`).
- Writes `/tmp/ai-metrics.json` every 3 s (`cpu_pct`, `ram`, `disk`, `services`).
- Control server: `POST /control` with `{"action":"<name>"}` and bearer auth.
- Actions: `stack_start`, `stack_stop`, `ollama_start`/`stop`,
  `webui_start`/`stop`, `pipelines_start`/`stop`, `podman_start`/`stop`,
  `tailscale_up`/`down`, `lmstudio_start`/`stop`. Add to the `ACTIONS` dict.
- Logs: `/tmp/ai-stack.log` (subprocess) and `/tmp/ai-metrics-exporter.log` (stdout).

---

## 10. Docs-sync Rule — MANDATORY

**Every code change must consider whether `docs/index.html` needs an update.**
The docs site is the public-facing description; if it drifts, users hit
broken setup steps.

Run this checklist before finishing any task:

| If you changed…                                | Then update…                                                       |
|------------------------------------------------|--------------------------------------------------------------------|
| Model name / size / role                       | Models table, Task→Model guide, dashboard mockup, code examples in `docs/index.html` |
| Port, URL, container name                      | Dashboard / Architecture sections in `docs/index.html`             |
| Shell alias added/removed/renamed              | Commands & Aliases table in `docs/index.html`                      |
| Service added/removed (SearXNG, Pipelines, …)  | Overview cards + Architecture diagram in `docs/index.html`         |
| Env var added/changed                          | Environment Variables table in `docs/index.html`                   |
| Phase script behavior                          | Matching Setup step + example commands in `docs/index.html`        |

Always grep before committing:
```bash
grep -n "<old-name>" docs/index.html AGENTS.md CLAUDE.md \
                    stack-aliases-v2.sh dashboard/config.json
```
If grep finds a hit, fix it in the **same commit** as the code change.

If the change is purely internal (refactor, no user-visible surface),
say so explicitly in the commit/PR: `docs-sync: N/A — internal refactor only.`

---

## 11. Coding Guidelines

1. **Shell scripts:** target `zsh` (macOS default), shebang `#!/bin/zsh`.
2. **Python:** 3.11+ (system Python). Use `pip install --break-system-packages`
   when needed. Stdlib-first; avoid heavy deps for small tools.
3. **Containers:** use `podman`, **not** `docker` (Podman Desktop is what's installed).
4. **Package manager:** Homebrew. Prefer `brew install` over manual installs.
5. **Config files:** `~/.config/local-ai/` or in this project directory.
6. **API format:** OpenAI-compatible everywhere — easier tool integration.
7. **Plan-then-build:** for non-trivial coding tasks, plan with
   `phi4-reasoning`, implement with `Gemma4 BF16 e4b`.
8. **Context budget:** model max context is not the same as loaded context.
   LM Studio can expose `granite3.3:8b` as a 128K-capable model while it is
   loaded at only 4K, which will fail on long prompts. Default Granite to
   32K context in LM Studio; use 64K for long documents; avoid 128K as an
   everyday default on 24 GB RAM. Keep prompt + context under ~100K tokens
   even for 128K-capable models because quality degrades near the limit.
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
For OpenCode/Aider via LM Studio:
```bash
ai-use-mlx                          # LM Studio backend
# Then in LM Studio: load Gemma4 BF16 e4b (or whichever)
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
curl -s http://localhost:1234/v1/models | python3 -m json.tool   # LM Studio
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

### Add documents to RAG
Open WebUI → upload via the chat input or the Workspace → Documents view.
Programmatic: Open WebUI's `/api/v1/files` endpoint.

### Benchmark a model
```bash
ollama run <model> "Write binary search in Python" --verbose
# --verbose prints tokens/sec
```

---

## 13. Troubleshooting

| Symptom                              | Cause                          | Fix                                                  |
|--------------------------------------|--------------------------------|------------------------------------------------------|
| Generation very slow                 | Memory swap — model too large  | Use smaller model or Q4_K_M; close apps              |
| `out of memory` error                | Total exceeds 24 GB            | Unload models; close Chrome/Slack; smaller quant     |
| Tool can't reach Ollama              | Ollama not running             | `ollama serve` or `brew services start ollama`       |
| Tool can't reach LM Studio API       | App running but server isn't   | LM Studio → Developer tab → Start Server (:1234)     |
| Podman can't reach host services     | Network isolation              | Use `host.containers.internal` (not `localhost`)     |
| Podman bind mount missing in container| macOS virtiofs single-file bug | Mount the **parent dir**, not the file (see §14 #1) |
| Poor code quality                    | Wrong model for task           | Switch to `Gemma4 BF16 e4b` or `granite3.3:8b`     |
| Continue.dev autocomplete laggy      | Autocomplete model too large   | Use `smollm2:1.7b` for autocomplete only             |
| `git add` hangs                      | Stale `.git/index.lock`        | `rm -f .git/index.lock` and retry                    |
| Dashboard "start" button does nothing| Token mismatch                 | Check `.secrets` CONTROL_TOKEN matches container env  |

---

## 14. Known Gotchas (each cost real debugging time)

1. **Podman virtiofs single-file bind mounts are broken on macOS.**
   `-v /private/tmp/ai-metrics.json:/metrics/host.json:ro` silently fails
   to surface the file inside the container. **Always mount the parent
   directory:** `-v /private/tmp:/hosttmp:ro`. Source path must be
   `/private/tmp` (not `/tmp` — Podman rejects the symlink).

2. **`BaseHTTPRequestHandler` header order matters.** `send_response()`
   must come before any `send_header()`, and `end_headers()` must come
   last. Wrong order produces cryptic 502s like
   `"Access-Control-Allow-Origin: got extra header"`.

3. **`osascript do shell script` runs `/bin/sh`, not zsh.** If a one-liner
   uses zsh features (process substitution, `**` globs), wrap with
   `zsh -c '<command>'`. Same applies to `subprocess.Popen(['zsh','-c',…])`
   in `metrics-exporter.py`.

4. **`ai-stack-start` kills and restarts the metrics-exporter.** Therefore
   the exporter's control server **cannot invoke `ai-stack-start`** (it
   would kill itself mid-request). The `_stack_start` / `_stack_stop`
   functions in `metrics-exporter.py` inline the equivalent commands via
   `subprocess.Popen(['zsh','-c', …])` to avoid this.

5. **`docs/index.html` — do NOT use `display:none` + JS tab switching.**
   Sections must always be visible; nav uses `href="#s-..."` with
   `html { scroll-behavior: smooth }`, `.section { scroll-margin-top: 54px }`,
   and an `IntersectionObserver` highlights the active link.

6. **Fonts: system stack only.** The user rejected Syne, Plus Jakarta Sans,
   Oxanium, Nunito Sans. Current stack:
   `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`.
   **Do not add Google Fonts `<link>` tags.**

7. **The dashboard's stack toggle uses the LM Studio API readiness, not
   just the app process.** App and `:1234` API are shown separately —
   the app can be running while the API is unavailable (server not started)
   or while the API is reachable but only embedding models are loaded.
   The toggle calls `stack_start` / `stack_stop` on the control server,
   not the shell aliases (see gotcha #4).

8. **LM Studio model IDs include the full path on disk.** Do not assume
   `Gemma4 BF16 e4b` is the literal API model ID — query
   `GET /v1/models` to see what LM Studio actually exposes, then use that
   exact ID in OpenAI-compatible clients.

---

## 15. Environment Variables

Add to `~/.zshrc`:

```bash
# Ollama
export OLLAMA_KEEP_ALIVE=5m           # auto-unload after 5 min idle
export OLLAMA_MAX_LOADED_MODELS=1     # 1 model at a time (24 GB constraint)
export OLLAMA_NUM_GPU=99              # use all GPU layers (Metal)
export OLLAMA_HOST=0.0.0.0:11434      # allow Tailscale + Podman to connect

# OpenCode (LM Studio default)
export OPENCODE_API_BASE=http://localhost:1234/v1
export OPENCODE_MODEL="Gemma4 BF16 e4b"
```

Convenience aliases (already in `stack-aliases-v2.sh`):

```bash
alias ai-chat="ollama run phi4-mini"          # ~3 GB, ultra-fast
alias ai-general="ollama run granite3.3:8b"   # ~6 GB, Ollama fallback
alias ai-code="ollama run granite3.3:8b"      # ~6 GB, tool-calling + 128K
alias ai-reason="ollama run phi4-reasoning"   # ~9 GB, reasoning
alias ai-status="ollama ps"
# Primary (Gemma4 BF16 e4b, ~8 GB) is in LM Studio — use Open WebUI / OpenCode.
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
2. `ai-stack-start` — watch for errors; browser opens http://localhost:3000
3. Open http://localhost:9090 — dashboard shows live CPU/RAM/disk and the
   default services (Podman, LM Studio app, LM Studio API, Open WebUI,
   Pipelines) as **up**.
4. Click the header **Stack** toggle — turns red, services go down.
5. Click again — services come back; metrics keep updating throughout.
6. `ai-stack-stop` from terminal — dashboard stays up, services show down,
   start buttons still functional.
7. `ai-stack-off` — everything down cleanly.

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
4. Check the dashboard (http://localhost:9090) for live service state.
5. Read `/tmp/ai-metrics-exporter.log` and `/tmp/ai-stack.log` for errors.
6. **If still unclear, ask the user a single specific question.** Do not
   guess and do not make destructive changes.
