# Antigravity Analysis: Local-AI

## Architecture Gaps & Risks

1.  **Service Management Brittleness**: 
    - `metrics-exporter.py` uses `pkill` and direct binary execution (`ollama serve`) which can conflict with `brew services`. If a user started Ollama via `brew services start ollama`, the dashboard's "Stop" button (using `pkill`) might cause the service to be immediately restarted by macOS `launchd`, or leave `brew services` in an inconsistent "started but not running" state.
    - Hardcoded binary paths (e.g., `/opt/homebrew/bin/ollama`) assume a specific setup that might fail if Homebrew is installed elsewhere or if the user uses a different installation method.

2.  **Security Gap (Control Plane)**:
    - The control server on port 9091 (`metrics-exporter.py`) has no authentication. Any process on the Mac (or potentially on the network if port 9091 is exposed) can stop/start services by hitting the `/control` endpoint. Given that the project encourages remote access via Tailscale/Caddy, this is a significant risk if not carefully isolated.

3.  **Metrics Exporter Performance**:
    - `cpu_pct()` uses `top -l 1`, which is relatively heavy on macOS. While it avoids external dependencies like `psutil`, it might contribute to higher "baseline" CPU usage than necessary for a monitoring tool.

4.  **Configuration Management**:
    - Dashboard hints (`MODEL_HINTS` in `app.py`) are hardcoded. Adding new models requires modifying the code.

## Potential Bugs

1.  **Race Conditions in Status Writing**: `metrics-exporter.py` writes to `/tmp/ai-metrics.json` using `os.replace(tmp, OUT)`. While atomic, there's no locking mechanism if multiple consumers were to read it (though currently only one does).
2.  **Ollama Binary Persistence**: If `ollama serve` is started by the exporter, it may continue running even if the exporter is killed, unless explicitly handled.

## Recommended Improvements

1.  **Smart Service Control**: Update `ACTIONS` to detect if `brew` is available and use `brew services stop/start` where appropriate.
2.  **Add Authentication**: Implement a simple token-based authentication for the control server (shared secret in `.env` or `.secrets`).
3.  **Externalize Configuration**: Move `MODEL_HINTS` and service definitions to a JSON configuration file.
4.  **Health Check Robustness**: Improve `services()` in `metrics-exporter.py` to check specific health endpoints (like `/api/tags` for Ollama) rather than just a TCP connect/minimal GET.
5.  **Dashboard UI**: Add a "Logs" view to the dashboard to see output from Ollama or the WebUI container.
