#!/usr/bin/env python3
"""
Local-AI Dashboard — lightweight container web server.
Reads /hostmetrics/ai-metrics.json + queries Ollama API.
No external dependencies.
"""
import json, os, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

OLLAMA   = os.getenv('OLLAMA_BASE_URL', 'http://host.containers.internal:11434')
CONTROL  = os.getenv('CONTROL_URL', 'http://host.containers.internal:9091')
METRICS  = '/hostmetrics/ai-metrics.json'
PORT     = int(os.getenv('PORT', 9090))

def fetch_json(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return json.loads(r.read())
    except Exception:
        return {}

def host_metrics():
    try:
        with open(METRICS) as f:
            return json.load(f)
    except Exception:
        return {}

def api_data():
    ps   = fetch_json(f'{OLLAMA}/api/ps')
    tags = fetch_json(f'{OLLAMA}/api/tags')
    host = host_metrics()
    return {'ps': ps, 'tags': tags, 'host': host}

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Local-AI Dashboard</title>
<style>
  :root {
    --bg:#0d1117; --surface:#161b22; --surface2:#1c2128; --border:#30363d;
    --text:#e6edf3; --muted:#8b949e; --muted2:#6e7681;
    --green:#3fb950; --yellow:#d29922; --red:#f85149; --blue:#58a6ff;
    --purple:#bc8cff; --accent:#58a6ff;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px;min-height:100vh}

  header{background:var(--surface);border-bottom:1px solid var(--border);padding:16px 32px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}
  header h1{font-size:1.2rem;font-weight:700;color:var(--accent)}
  .ts-wrap{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:0.85rem}
  .ring{display:inline-block;width:10px;height:10px;border:2px solid var(--muted2);border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite}
  @keyframes spin{to{transform:rotate(360deg)}}

  .page{max-width:1300px;margin:0 auto;padding:24px 28px}
  .top-row{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px}
  .card-title{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:18px}

  /* System */
  .stat-block{margin-bottom:16px}
  .stat-block:last-child{margin-bottom:0}
  .stat-row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px}
  .stat-label{color:var(--muted);font-size:.9rem}
  .stat-value{font-weight:700;font-size:1.05rem}
  .stat-sub{color:var(--muted2);font-size:.75rem;margin-top:3px}
  .bar-wrap{background:var(--border);border-radius:6px;height:7px;overflow:hidden}
  .bar{height:7px;border-radius:6px;transition:width .5s ease}
  .bar.green{background:var(--green)} .bar.yellow{background:var(--yellow)} .bar.red{background:var(--red)}
  .metrics-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px;padding-top:16px;border-top:1px solid var(--border)}
  .mini-stat{background:var(--surface2);border-radius:8px;padding:10px 12px}
  .mini-label{font-size:.72rem;color:var(--muted2);margin-bottom:3px}
  .mini-value{font-size:1rem;font-weight:700}

  /* Services */
  .svc-row{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-radius:8px;margin-bottom:8px;background:var(--surface2)}
  .svc-row:last-child{margin-bottom:0}
  .svc-left{display:flex;align-items:center;gap:10px}
  .dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
  .dot.up{background:var(--green);box-shadow:0 0 8px rgba(63,185,80,.6)}
  .dot.down{background:var(--red);box-shadow:0 0 8px rgba(248,81,73,.4)}
  .dot.unknown{background:var(--muted2)}
  .svc-name{font-weight:600;font-size:.95rem}
  .svc-detail{color:var(--muted);font-size:.75rem;margin-top:1px}
  .svc-actions{display:flex;align-items:center;gap:6px}
  .btn{border:none;border-radius:6px;padding:4px 12px;font-size:.75rem;font-weight:600;cursor:pointer;transition:opacity .15s}
  .btn:hover{opacity:.8} .btn:active{opacity:.6}
  .btn:disabled{opacity:.35;cursor:not-allowed}
  .btn-open{background:rgba(88,166,255,.12);color:var(--blue);border:1px solid rgba(88,166,255,.3);text-decoration:none;padding:4px 10px;border-radius:6px;font-size:.75rem;font-weight:600}
  .btn-open:hover{background:rgba(88,166,255,.2)}
  .btn-stop{background:rgba(248,81,73,.12);color:var(--red);border:1px solid rgba(248,81,73,.3)}
  .btn-start{background:rgba(63,185,80,.12);color:var(--green);border:1px solid rgba(63,185,80,.3)}
  .btn-ts-up{background:rgba(88,166,255,.12);color:var(--blue);border:1px solid rgba(88,166,255,.3)}

  /* Models */
  .models-header{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:18px}
  .models-sub{color:var(--muted);font-size:.85rem}
  .model-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}
  .model-card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:14px 16px}
  .model-card.active{border-color:rgba(63,185,80,.4);background:rgba(63,185,80,.05)}
  .model-name{font-weight:600;font-size:.9rem;word-break:break-all;margin-bottom:6px}
  .model-meta{display:flex;align-items:center;justify-content:space-between}
  .model-size{color:var(--muted2);font-size:.78rem}
  .badge{font-size:.68rem;padding:2px 8px;border-radius:10px;font-weight:700}
  .badge.loaded{background:rgba(63,185,80,.15);color:var(--green);border:1px solid rgba(63,185,80,.4)}
  .badge.idle{background:rgba(88,166,255,.08);color:var(--blue);border:1px solid rgba(88,166,255,.2)}
  .badge.embed{background:rgba(188,140,255,.1);color:var(--purple);border:1px solid rgba(188,140,255,.3)}
  .model-extra{margin-top:6px;font-size:.75rem;color:var(--muted2);display:flex;gap:12px}

  .toast{position:fixed;bottom:24px;right:24px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 16px;font-size:.85rem;color:var(--text);box-shadow:0 4px 20px rgba(0,0,0,.4);transform:translateY(80px);transition:transform .3s;z-index:100}
  .toast.show{transform:translateY(0)}

  @media(max-width:860px){.top-row{grid-template-columns:1fr}.page{padding:14px}.metrics-grid{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<header>
  <div style="display:flex;align-items:center;gap:14px">
    <h1>⚡ Local-AI Dashboard</h1>
    <a href="https://github.com/simoneiaci/local-AI" target="_blank"
       style="display:flex;align-items:center;gap:5px;color:var(--muted);text-decoration:none;font-size:.8rem;border:1px solid var(--border);border-radius:6px;padding:3px 9px;transition:color .15s"
       onmouseover="this.style.color='var(--text)'" onmouseout="this.style.color='var(--muted)'">
      <svg height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
      simoneiaci/local-AI
    </a>
    <a href="https://simoneiaci.github.io/local-AI/" target="_blank"
       style="display:flex;align-items:center;gap:5px;color:var(--muted);text-decoration:none;font-size:.8rem;border:1px solid var(--border);border-radius:6px;padding:3px 9px;transition:color .15s"
       onmouseover="this.style.color='var(--text)'" onmouseout="this.style.color='var(--muted)'">
      <svg height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
      Docs
    </a>
  </div>
  <div class="ts-wrap"><span class="ring"></span><span id="ts">connecting…</span></div>
</header>
<div class="page">
  <div class="top-row">
    <div class="card" id="card-system"><p style="color:var(--muted)">Loading…</p></div>
    <div class="card" id="card-services"><p style="color:var(--muted)">Loading…</p></div>
  </div>
  <div class="card" id="card-models"><p style="color:var(--muted)">Loading…</p></div>
</div>
<div class="toast" id="toast"></div>

<script>
const CONTROL = 'CONTROL_PLACEHOLDER';

function pct2c(p){return p>85?'red':p>65?'yellow':'green'}
function bar(p){
  if(p==null)return '';
  return `<div class="bar-wrap"><div class="bar ${pct2c(p)}" style="width:${Math.min(p,100)}%"></div></div>`;
}
function gb(v){return v!=null?v.toFixed(1)+' GB':'–'}
function pctStr(v){return v!=null?v.toFixed(1)+'%':'–'}
function sizeStr(bytes){
  if(!bytes)return '';
  const g=bytes/1073741824;
  return g>=1?g.toFixed(1)+' GB':(bytes/1048576).toFixed(0)+' MB';
}
function timeUntil(iso){
  if(!iso)return '';
  const s=Math.round((new Date(iso)-Date.now())/1000);
  if(s<=0)return 'expiring…';
  if(s<60)return `expires in ${s}s`;
  return `expires in ${Math.round(s/60)}m`;
}

// Toast notification
let toastTimer;
function toast(msg,color='var(--text)'){
  const el=document.getElementById('toast');
  el.textContent=msg; el.style.color=color;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>el.classList.remove('show'),3000);
}

// Control API
async function control(action,label){
  try{
    const r=await fetch(CONTROL+'/control',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({action})
    });
    const d=await r.json();
    if(d.ok) toast(`${label}…`,'var(--green)');
    else toast(`Error: ${d.error}`,'var(--red)');
  }catch(e){
    toast('Control server unreachable','var(--red)');
  }
}

function renderSystem(host){
  const cpu=host.cpu_pct, ram=host.ram||{}, disk=host.disk||{};
  const cpuC=cpu!=null?`color:var(--${pct2c(cpu)})`:'';
  const ramC=ram.pct!=null?`color:var(--${pct2c(ram.pct)})`:'';
  const dskC=disk.pct!=null?`color:var(--${pct2c(disk.pct)})`:'';
  const swap=ram.swap_gb!=null && ram.swap_gb>0
    ?`<div class="mini-stat"><div class="mini-label">Swap used</div><div class="mini-value" style="color:var(--yellow)">${ram.swap_gb.toFixed(2)} GB</div></div>`
    :`<div class="mini-stat"><div class="mini-label">Swap used</div><div class="mini-value">none</div></div>`;
  return `<div class="card-title">System</div>
    <div class="stat-block">
      <div class="stat-row"><span class="stat-label">CPU Usage</span><span class="stat-value" style="${cpuC}">${pctStr(cpu)}</span></div>
      ${bar(cpu)}
    </div>
    <div class="stat-block">
      <div class="stat-row"><span class="stat-label">RAM</span><span class="stat-value" style="${ramC}">${gb(ram.used_gb)} <span style="color:var(--muted);font-weight:400;font-size:.85rem">/ ${gb(ram.total_gb)}</span></span></div>
      ${bar(ram.pct)}
      <div class="stat-sub">${ram.pct!=null?ram.pct.toFixed(1)+'% used':''}</div>
    </div>
    <div class="stat-block">
      <div class="stat-row"><span class="stat-label">Disk free</span><span class="stat-value" style="${dskC}">${gb(disk.free_gb)}</span></div>
      ${bar(disk.pct)}
      <div class="stat-sub">${disk.used_gb!=null?gb(disk.used_gb)+' used of '+gb(disk.total_gb):''}</div>
    </div>
    <div class="metrics-grid">
      <div class="mini-stat"><div class="mini-label">Ollama models on disk</div><div class="mini-value">${gb(disk.ollama_gb)}</div></div>
      ${swap}
    </div>`;
}

function renderServices(svc){
  const items=[
    {key:'ollama',    label:'Ollama',    sub:'API · port 11434',       url:'http://localhost:11434', stop:'ollama_stop',  start:'ollama_start'},
    {key:'open_webui',label:'Open WebUI',sub:'Chat UI · port 3000',    url:'http://localhost:3000',  stop:'webui_stop',   start:'webui_start'},
    {key:'pipelines', label:'Pipelines', sub:'Middleware · port 9099', url:'http://localhost:9099',  stop:'pipelines_stop', start:'pipelines_start'},
    {key:'podman',    label:'Podman VM', sub:'Container runtime',      url:null,                     stop:'podman_stop',  start:'podman_start'},
    {key:'tailscale', label:'Tailscale', sub:svc.tailscale_ip||'VPN · not connected', url:null, stop:'tailscale_down', start:'tailscale_up', startLabel:'Connect'},
  ];
  return `<div class="card-title">Services</div>`+items.map(i=>{
    const st=svc[i.key]||'unknown';
    const isUp=st==='up';
    const openBtn=i.url&&isUp?`<a class="btn-open" href="${i.url}" target="_blank">open ↗</a>`:'';
    const stopBtn=`<button class="btn btn-stop" onclick="control('${i.stop}','Stopping ${i.label}')" ${!isUp?'disabled':''}>Stop</button>`;
    const startBtn=`<button class="btn btn-start" onclick="control('${i.start}','Starting ${i.label}')" ${isUp?'disabled':''} >${i.startLabel||'Start'}</button>`;
    return `<div class="svc-row">
      <div class="svc-left">
        <div class="dot ${st}"></div>
        <div><div class="svc-name">${i.label}</div><div class="svc-detail">${i.key==='tailscale'&&svc.tailscale_ip?svc.tailscale_ip:i.sub}</div></div>
      </div>
      <div class="svc-actions">${openBtn}${stopBtn}${startBtn}</div>
    </div>`;
  }).join('');
}

const MODEL_HINTS = {
  'qwen3:14b':        '🇮🇹 Italian · tax docs · reasoning · thinking mode (/think)',
  'devstral':         '💻 Coding · code gen · refactors · terminal agent',
  'gemma3:12b':       '💬 Daily chat · multimodal · vision · balanced',
  'smollm2:1.7b':     '⚡ Tab autocomplete · tiny · always loaded',
  'nomic-embed-text': '🔍 Embeddings · RAG pipelines · semantic search',
  'swift-mentor':     '🍎 iOS/macOS · Swift 6 · SwiftUI · TCA',
};
function modelHint(name){
  if(MODEL_HINTS[name]) return MODEL_HINTS[name];
  // fuzzy match on prefix
  for(const [k,v] of Object.entries(MODEL_HINTS)){
    if(name.startsWith(k.split(':')[0])) return v;
  }
  return '';
}

function renderModels(ps,tags){
  const loadedMap={};
  (ps.models||[]).forEach(m=>{loadedMap[m.name]=m});
  const all=tags.models||[];
  if(!all.length)return `<div class="models-header"><div class="card-title">Models</div></div><p style="color:var(--muted);padding:8px 0">No models found — is Ollama running?</p>`;
  const lc=Object.keys(loadedMap).length;
  const cards=all.map(m=>{
    const name=m.name, loaded=loadedMap[name];
    const isEmbed=name.includes('embed');
    const sizeGb=m.size?(m.size/1073741824).toFixed(1)+' GB':'';
    let badge=isEmbed?`<span class="badge embed">embed</span>`:`<span class="badge idle">idle</span>`;
    let extra='';
    if(loaded){
      badge=`<span class="badge loaded">● loaded</span>`;
      const parts=[];
      if(loaded.size_vram) parts.push('VRAM: '+sizeStr(loaded.size_vram));
      if(loaded.expires_at) parts.push(timeUntil(loaded.expires_at));
      if(parts.length) extra=`<div class="model-extra">${parts.map(p=>`<span>${p}</span>`).join('')}</div>`;
    }
    const hint=modelHint(name);
    const hintHtml=hint?`<div style="font-size:.72rem;color:var(--muted2);margin-top:5px;line-height:1.4">${hint}</div>`:'';
    return `<div class="model-card ${loaded?'active':''}">
      <div class="model-name">${name}</div>
      <div class="model-meta"><span class="model-size">${sizeGb}</span>${badge}</div>
      ${hintHtml}
      ${extra}
    </div>`;
  }).join('');
  return `<div class="models-header"><div class="card-title">Models</div><span class="models-sub">${lc} loaded · ${all.length} available</span></div>
  <div class="model-grid">${cards}</div>`;
}

async function refresh(){
  try{
    const r=await fetch('/api/data');
    const d=await r.json();
    const host=d.host||{}, svc=host.services||{};
    document.getElementById('card-system').innerHTML=renderSystem(host);
    document.getElementById('card-services').innerHTML=renderServices(svc);
    document.getElementById('card-models').innerHTML=renderModels(d.ps,d.tags);
    document.getElementById('ts').textContent='updated '+new Date().toLocaleTimeString();
  }catch(e){
    document.getElementById('ts').textContent='error – retrying…';
  }
}
refresh();
setInterval(refresh,5000);
</script>
</body>
</html>"""

# Inject control URL at serve time
def build_html():
    return HTML.replace('CONTROL_PLACEHOLDER', CONTROL)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            body = build_html().encode()
            self._send(200, 'text/html', body)
        elif self.path == '/api/data':
            self._send(200, 'application/json', json.dumps(api_data()).encode())
        else:
            self._send(404, 'text/plain', b'Not found')

    def _send(self, code, ct, body):
        self.send_response(code)
        self.send_header('Content-Type', ct)
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_): pass

if __name__ == '__main__':
    print(f'Local-AI Dashboard → http://localhost:{PORT}')
    HTTPServer(('', PORT), Handler).serve_forever()
