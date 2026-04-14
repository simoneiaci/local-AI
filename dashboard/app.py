#!/usr/bin/env python3
"""
Local-AI Dashboard — lightweight container web server.
Reads /metrics/host.json (bind-mounted from host) + queries Ollama API.
No external dependencies.
"""
import json, os, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

OLLAMA = os.getenv('OLLAMA_BASE_URL', 'http://host.containers.internal:11434')
METRICS_FILE = '/hostmetrics/ai-metrics.json'
PORT = int(os.getenv('PORT', 9090))

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

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Local-AI Dashboard</title>
<style>
  :root {
    --bg: #0d1117; --surface: #161b22; --surface2: #1c2128; --border: #30363d;
    --text: #e6edf3; --muted: #8b949e; --muted2: #6e7681;
    --green: #3fb950; --yellow: #d29922; --red: #f85149; --blue: #58a6ff;
    --purple: #bc8cff; --accent: #58a6ff;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 15px; min-height: 100vh;
  }
  header {
    background: var(--surface); border-bottom: 1px solid var(--border);
    padding: 18px 32px; display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 10;
  }
  header h1 { font-size: 1.25rem; font-weight: 700; color: var(--accent); letter-spacing: -.01em; }
  .ts-wrap { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 0.85rem; }
  .refresh-ring {
    display: inline-block; width: 10px; height: 10px;
    border: 2px solid var(--muted2); border-top-color: var(--accent);
    border-radius: 50%; animation: spin 1s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .page { max-width: 1300px; margin: 0 auto; padding: 28px 32px; }

  /* ── Top row: System + Services ── */
  .top-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
  /* ── Bottom row: Models full width ── */
  .bottom-row { }

  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px;
  }
  .card-title {
    font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .1em; color: var(--muted); margin-bottom: 20px;
  }

  /* System stats */
  .stat-block { margin-bottom: 18px; }
  .stat-block:last-child { margin-bottom: 0; }
  .stat-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
  .stat-label { color: var(--muted); font-size: 0.9rem; }
  .stat-value { font-weight: 700; font-size: 1.05rem; }
  .stat-sub { color: var(--muted2); font-size: 0.78rem; margin-top: 2px; }
  .bar-wrap { background: var(--border); border-radius: 6px; height: 8px; overflow: hidden; }
  .bar { height: 8px; border-radius: 6px; transition: width .5s ease; }
  .bar.green  { background: var(--green); }
  .bar.yellow { background: var(--yellow); }
  .bar.red    { background: var(--red); }
  .big-num { font-size: 2.2rem; font-weight: 800; line-height: 1; margin-bottom: 4px; }
  .big-unit { font-size: 0.9rem; color: var(--muted); font-weight: 400; }

  /* Services */
  .svc-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;
    background: var(--surface2);
  }
  .svc-row:last-child { margin-bottom: 0; }
  .svc-left { display: flex; align-items: center; gap: 10px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .dot.up   { background: var(--green); box-shadow: 0 0 8px rgba(63,185,80,.6); }
  .dot.down { background: var(--red);   box-shadow: 0 0 8px rgba(248,81,73,.4); }
  .dot.unknown { background: var(--muted2); }
  .svc-name { font-weight: 600; font-size: 0.95rem; }
  .svc-detail { color: var(--muted); font-size: 0.78rem; }
  .svc-link {
    color: var(--accent); text-decoration: none; font-size: 0.8rem; font-weight: 500;
    padding: 3px 10px; border: 1px solid rgba(88,166,255,.3); border-radius: 6px;
  }
  .svc-link:hover { background: rgba(88,166,255,.1); }

  /* Models */
  .models-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
  .models-subtitle { color: var(--muted); font-size: 0.85rem; }
  .model-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; }
  .model-card {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 8px; padding: 14px 16px;
    display: flex; flex-direction: column; gap: 6px;
  }
  .model-card.active { border-color: rgba(63,185,80,.4); background: rgba(63,185,80,.05); }
  .model-name { font-weight: 600; font-size: 0.92rem; word-break: break-all; }
  .model-meta { display: flex; align-items: center; justify-content: space-between; }
  .model-size { color: var(--muted2); font-size: 0.78rem; }
  .badge { font-size: 0.7rem; padding: 2px 9px; border-radius: 10px; font-weight: 700; }
  .badge.loaded { background: rgba(63,185,80,.15);  color: var(--green);  border: 1px solid rgba(63,185,80,.4); }
  .badge.idle   { background: rgba(88,166,255,.08); color: var(--blue);   border: 1px solid rgba(88,166,255,.2); }
  .badge.embed  { background: rgba(188,140,255,.1); color: var(--purple); border: 1px solid rgba(188,140,255,.3); }
  .model-vram { color: var(--muted2); font-size: 0.75rem; }

  .empty { color: var(--muted); font-size: 0.9rem; padding: 12px 0; }

  @media (max-width: 860px) {
    .top-row { grid-template-columns: 1fr; }
    .page { padding: 16px; }
  }
</style>
</head>
<body>
<header>
  <h1>⚡ Local-AI Dashboard</h1>
  <div class="ts-wrap"><span class="refresh-ring"></span><span id="ts">connecting…</span></div>
</header>

<div class="page">
  <div class="top-row">
    <div class="card" id="card-system"><p class="empty">Loading…</p></div>
    <div class="card" id="card-services"><p class="empty">Loading…</p></div>
  </div>
  <div class="bottom-row">
    <div class="card" id="card-models"><p class="empty">Loading…</p></div>
  </div>
</div>

<script>
function pct2color(p) { return p > 85 ? 'red' : p > 65 ? 'yellow' : 'green'; }
function bar(pct, label) {
  if (pct == null) return '';
  const c = pct2color(pct);
  return `<div class="bar-wrap" title="${label||''}: ${pct.toFixed(1)}%">
    <div class="bar ${c}" style="width:${Math.min(pct,100)}%"></div></div>`;
}
function gb(v)  { return v != null ? v.toFixed(1) + ' GB' : '–'; }
function pct(v) { return v != null ? v.toFixed(1) + '%'  : '–'; }
function sizeStr(bytes) {
  if (!bytes) return '';
  const g = bytes / 1073741824;
  return g >= 1 ? g.toFixed(1) + ' GB' : (bytes/1048576).toFixed(0) + ' MB';
}

function renderSystem(host) {
  const cpu  = host.cpu_pct;
  const ram  = host.ram  || {};
  const disk = host.disk || {};
  const cpuColor = cpu != null ? `color:var(--${pct2color(cpu)})` : '';
  const ramColor = ram.pct != null ? `color:var(--${pct2color(ram.pct)})` : '';
  const dskColor = disk.pct != null ? `color:var(--${pct2color(disk.pct)})` : '';

  return `<div class="card-title">System</div>

    <div class="stat-block">
      <div class="stat-row">
        <span class="stat-label">CPU Usage</span>
        <span class="stat-value" style="${cpuColor}">${pct(cpu)}</span>
      </div>
      ${bar(cpu, 'CPU')}
    </div>

    <div class="stat-block">
      <div class="stat-row">
        <span class="stat-label">RAM</span>
        <span class="stat-value" style="${ramColor}">${gb(ram.used_gb)} <span style="color:var(--muted);font-weight:400;font-size:.85rem">/ ${gb(ram.total_gb)}</span></span>
      </div>
      ${bar(ram.pct, 'RAM')}
      <div class="stat-sub">${ram.pct != null ? ram.pct.toFixed(1)+'% used' : ''}</div>
    </div>

    <div class="stat-block">
      <div class="stat-row">
        <span class="stat-label">Disk free</span>
        <span class="stat-value" style="${dskColor}">${gb(disk.free_gb)}</span>
      </div>
      ${bar(disk.pct, 'Disk')}
      <div class="stat-sub">${disk.used_gb != null ? gb(disk.used_gb)+' used of '+gb(disk.total_gb) : ''}</div>
    </div>

    <div class="stat-block">
      <div class="stat-row">
        <span class="stat-label">Ollama models on disk</span>
        <span class="stat-value">${gb(disk.ollama_gb)}</span>
      </div>
    </div>`;
}

function renderServices(svc) {
  const items = [
    { key:'ollama',     label:'Ollama',     sub:'API · port 11434', url:'http://localhost:11434' },
    { key:'open_webui', label:'Open WebUI', sub:'Chat UI · port 3000', url:'http://localhost:3000' },
    { key:'podman',     label:'Podman VM',  sub:'Container runtime', url:null },
    { key:'tailscale',  label:'Tailscale',  sub: svc.tailscale_ip || 'VPN · not connected', url:null },
  ];
  const rows = items.map(i => {
    const st  = svc[i.key] || 'unknown';
    const sub = i.key==='tailscale' && svc.tailscale_ip ? svc.tailscale_ip : i.sub;
    const lnk = i.url && st==='up'
      ? `<a class="svc-link" href="${i.url}" target="_blank">open ↗</a>`
      : `<span style="color:var(--muted2);font-size:.78rem">${st==='up'?'running':st}</span>`;
    return `<div class="svc-row">
      <div class="svc-left">
        <div class="dot ${st}"></div>
        <div>
          <div class="svc-name">${i.label}</div>
          <div class="svc-detail">${sub}</div>
        </div>
      </div>
      ${lnk}
    </div>`;
  }).join('');
  return `<div class="card-title">Services</div>${rows}`;
}

function renderModels(ps, tags) {
  const loadedMap = {};
  (ps.models || []).forEach(m => { loadedMap[m.name] = m; });
  const allModels = (tags.models || []);
  if (!allModels.length) return `<div class="models-header"><div class="card-title">Models</div></div><p class="empty">No models found — is Ollama running?</p>`;

  const loadedCount = Object.keys(loadedMap).length;

  const cards = allModels.map(m => {
    const name    = m.name;
    const loaded  = loadedMap[name];
    const isEmbed = name.includes('embed');
    const sizeGb  = m.size ? (m.size/1073741824).toFixed(1)+' GB' : '';
    let badge, extra = '';
    if (loaded) {
      badge = `<span class="badge loaded">● loaded</span>`;
      if (loaded.size_vram) {
        extra = `<div class="model-vram">VRAM: ${sizeStr(loaded.size_vram)}</div>`;
      }
    } else if (isEmbed) {
      badge = `<span class="badge embed">embed</span>`;
    } else {
      badge = `<span class="badge idle">idle</span>`;
    }
    return `<div class="model-card ${loaded?'active':''}">
      <div class="model-name">${name}</div>
      <div class="model-meta">
        <span class="model-size">${sizeGb}</span>
        ${badge}
      </div>
      ${extra}
    </div>`;
  }).join('');

  return `<div class="models-header">
    <div class="card-title">Models</div>
    <span class="models-subtitle">${loadedCount} loaded · ${allModels.length} available</span>
  </div>
  <div class="model-grid">${cards}</div>`;
}

async function refresh() {
  try {
    const r = await fetch('/api/data');
    const d = await r.json();
    const host = d.host || {};
    const svc  = host.services || {};
    document.getElementById('card-system').innerHTML   = renderSystem(host);
    document.getElementById('card-services').innerHTML = renderServices(svc);
    document.getElementById('card-models').innerHTML   = renderModels(d.ps, d.tags);
    document.getElementById('ts').textContent = 'updated ' + new Date().toLocaleTimeString();
  } catch(e) {
    document.getElementById('ts').textContent = 'error – retrying…';
  }
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""

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
        pass

if __name__ == '__main__':
    print(f'Local-AI Dashboard → http://localhost:{PORT}')
    HTTPServer(('', PORT), Handler).serve_forever()
