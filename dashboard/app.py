#!/usr/bin/env python3
"""
Local-AI Dashboard — lightweight container web server.
Reads /metrics/host.json (bind-mounted from host) + queries Ollama API.
No external dependencies.
"""
import json, os, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

OLLAMA = os.getenv('OLLAMA_BASE_URL', 'http://host.containers.internal:11434')
METRICS_FILE = '/metrics/host.json'
PORT = int(os.getenv('PORT', 9090))

# ── API helpers ───────────────────────────────────────────────────────────────

def fetch_json(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return json.loads(r.read())
    except Exception:
        return {}

def host_metrics():
    try:
        with open(METRICS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def api_data():
    ps   = fetch_json(f'{OLLAMA}/api/ps')
    tags = fetch_json(f'{OLLAMA}/api/tags')
    host = host_metrics()
    return {'ps': ps, 'tags': tags, 'host': host}

# ── Embedded HTML dashboard ───────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Local-AI Dashboard</title>
<style>
  :root {
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --muted: #8b949e;
    --green: #3fb950; --yellow: #d29922; --red: #f85149; --blue: #58a6ff;
    --accent: #58a6ff;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-size: 14px; }
  header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; }
  header h1 { font-size: 1.1rem; font-weight: 600; color: var(--accent); }
  header .ts { color: var(--muted); font-size: 0.8rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; padding: 20px 24px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
  .card h3 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: 12px; }
  .stat { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .stat-label { color: var(--muted); font-size: 0.85rem; }
  .stat-value { font-weight: 600; font-size: 0.95rem; }
  .bar-wrap { background: var(--border); border-radius: 4px; height: 6px; margin-top: 4px; }
  .bar { height: 6px; border-radius: 4px; transition: width .4s; }
  .bar.green { background: var(--green); }
  .bar.yellow { background: var(--yellow); }
  .bar.red { background: var(--red); }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .dot.up   { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .dot.down { background: var(--red); }
  .model-row { display: flex; justify-content: space-between; align-items: center;
               padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
  .model-row:last-child { border-bottom: none; }
  .badge { font-size: 0.7rem; padding: 2px 7px; border-radius: 10px; font-weight: 600; }
  .badge.loaded { background: rgba(63,185,80,.15); color: var(--green); border: 1px solid rgba(63,185,80,.3); }
  .badge.idle   { background: rgba(88,166,255,.1);  color: var(--blue);  border: 1px solid rgba(88,166,255,.2); }
  .refresh-ring { display: inline-block; width: 8px; height: 8px; border: 2px solid var(--muted); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; margin-right: 6px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .empty { color: var(--muted); font-size: 0.85rem; padding: 8px 0; }
  .svc-row { display: flex; align-items: center; justify-content: space-between; padding: 5px 0; font-size: 0.85rem; }
  .svc-ip { color: var(--muted); font-size: 0.75rem; }
</style>
</head>
<body>
<header>
  <h1>⚡ Local-AI Dashboard</h1>
  <span class="ts" id="ts">–</span>
</header>
<div class="grid" id="grid">
  <div class="card"><p class="empty">Loading…</p></div>
</div>
<script>
function pct2color(p) { return p > 85 ? 'red' : p > 65 ? 'yellow' : 'green'; }
function bar(pct) {
  const c = pct2color(pct);
  return `<div class="bar-wrap"><div class="bar ${c}" style="width:${Math.min(pct,100)}%"></div></div>`;
}
function gb(v) { return v != null ? v.toFixed(1) + ' GB' : '–'; }
function pctStr(v) { return v != null ? v.toFixed(1) + '%' : '–'; }
function sizeStr(bytes) {
  if (!bytes) return '–';
  const gb = bytes / 1073741824;
  return gb >= 1 ? gb.toFixed(1) + ' GB' : (bytes/1048576).toFixed(0) + ' MB';
}

function renderSystem(host) {
  const cpu  = host.cpu_pct;
  const ram  = host.ram  || {};
  const disk = host.disk || {};
  return `<div class="card">
    <h3>System</h3>
    <div class="stat"><span class="stat-label">CPU</span><span class="stat-value">${pctStr(cpu)}</span></div>
    ${cpu != null ? bar(cpu) : ''}
    <div style="margin-top:10px">
    <div class="stat"><span class="stat-label">RAM</span><span class="stat-value">${gb(ram.used_gb)} / ${gb(ram.total_gb)}</span></div>
    ${ram.pct != null ? bar(ram.pct) : ''}
    </div>
    <div style="margin-top:10px">
    <div class="stat"><span class="stat-label">Disk free</span><span class="stat-value">${gb(disk.free_gb)}</span></div>
    <div class="stat"><span class="stat-label">Ollama models</span><span class="stat-value">${gb(disk.ollama_gb)}</span></div>
    ${disk.pct != null ? bar(disk.pct) : ''}
    </div>
  </div>`;
}

function renderModels(ps, tags) {
  const loadedMap = {};
  (ps.models || []).forEach(m => { loadedMap[m.name] = m; });
  const allModels = (tags.models || []).map(m => m.name);
  if (!allModels.length) return `<div class="card"><h3>Models</h3><p class="empty">No models found</p></div>`;

  const rows = allModels.map(name => {
    const loaded = loadedMap[name];
    const badge  = loaded
      ? `<span class="badge loaded">● loaded</span>`
      : `<span class="badge idle">idle</span>`;
    const size   = loaded ? `<span style="color:var(--muted);font-size:.75rem">${sizeStr(loaded.size)}</span>` : '';
    return `<div class="model-row"><span>${name}</span><span style="display:flex;align-items:center;gap:8px">${size}${badge}</span></div>`;
  }).join('');

  const loadedCount = Object.keys(loadedMap).length;
  return `<div class="card">
    <h3>Models — ${loadedCount} loaded / ${allModels.length} available</h3>
    ${rows}
  </div>`;
}

function renderServices(svc) {
  const items = [
    { key: 'ollama',    label: 'Ollama',      url: 'http://localhost:11434' },
    { key: 'open_webui',label: 'Open WebUI',  url: 'http://localhost:3000' },
    { key: 'podman',    label: 'Podman VM',   url: null },
    { key: 'tailscale', label: 'Tailscale',   url: null },
  ];
  const rows = items.map(i => {
    const st  = svc[i.key] || 'unknown';
    const ip  = i.key === 'tailscale' && svc.tailscale_ip ? `<span class="svc-ip">${svc.tailscale_ip}</span>` : '';
    const lnk = i.url && st === 'up' ? `<a href="${i.url}" target="_blank" style="color:var(--accent);text-decoration:none;font-size:.75rem">open ↗</a>` : '';
    return `<div class="svc-row">
      <span><span class="dot ${st}"></span>${i.label}</span>
      <span style="display:flex;align-items:center;gap:8px">${ip}${lnk}</span>
    </div>`;
  }).join('');
  return `<div class="card"><h3>Services</h3>${rows}</div>`;
}

async function refresh() {
  try {
    const r = await fetch('/api/data');
    const d = await r.json();
    const host = d.host || {};
    const svc  = host.services || {};
    document.getElementById('grid').innerHTML =
      renderSystem(host) + renderModels(d.ps, d.tags) + renderServices(svc);
    document.getElementById('ts').innerHTML =
      `<span class="refresh-ring"></span>updated ${new Date().toLocaleTimeString()}`;
  } catch(e) {
    document.getElementById('ts').textContent = 'error fetching data';
  }
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""

# ── HTTP handler ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self._send(200, 'text/html', HTML.encode())
        elif self.path == '/api/data':
            data = api_data()
            self._send(200, 'application/json', json.dumps(data).encode())
        else:
            self._send(404, 'text/plain', b'Not found')

    def _send(self, code, ct, body):
        self.send_response(code)
        self.send_header('Content-Type', ct)
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass  # silence access logs

if __name__ == '__main__':
    print(f'Local-AI Dashboard → http://localhost:{PORT}')
    HTTPServer(('', PORT), Handler).serve_forever()
