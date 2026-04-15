#!/usr/bin/env python3
"""
Local-AI Dashboard — lightweight container web server.
Reads /hostmetrics/ai-metrics.json + queries Ollama API.
No external dependencies.
"""
import json, os, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

OLLAMA   = os.getenv('OLLAMA_BASE_URL', 'http://host.containers.internal:11434')
CONTROL  = os.getenv('CONTROL_URL', 'http://host.containers.internal:9091')
CONTROL_TOKEN = os.getenv('CONTROL_TOKEN', '')
METRICS  = '/hosttmp/ai-metrics.json'
PORT     = int(os.getenv('PORT', 9090))

# Load model hints from config.json (next to app.py)
_config_path = os.path.join(os.path.dirname(__file__), 'config.json')
try:
    with open(_config_path) as _f:
        _config = json.load(_f)
    MODEL_HINTS = _config.get('model_hints', {})
except Exception:
    MODEL_HINTS = {}

def fetch_json(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return json.loads(r.read())
    except Exception:
        return {}

def host_metrics():
    """Read metrics JSON with a short retry to handle virtiofs cache races."""
    import time as _t
    for attempt in range(3):
        try:
            with open(METRICS) as f:
                data = json.load(f)
            # Accept only if at least one real field is present
            if data and any(k in data for k in ('cpu_pct', 'ram', 'services')):
                return data
        except Exception:
            pass
        if attempt < 2:
            _t.sleep(0.08)
    return {}

def api_data():
    ps   = fetch_json(f'{OLLAMA}/api/ps')
    tags = fetch_json(f'{OLLAMA}/api/tags')
    host = host_metrics()
    return {'ps': ps, 'tags': tags, 'host': host}

def proxy_control(body_bytes: bytes) -> tuple[int, bytes]:
    """Forward a control action to the host control server with Bearer auth."""
    req = urllib.request.Request(
        f'{CONTROL}/control',
        data=body_bytes,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CONTROL_TOKEN}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 502, json.dumps({'ok': False, 'error': str(e)}).encode()

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Local-AI Dashboard</title>
<style>
  :root {
    --bg:#07090e; --bg2:#0a0c15;
    --surface:rgba(255,255,255,.028); --surface2:rgba(255,255,255,.045);
    --border:rgba(255,255,255,.07); --border-hi:rgba(74,116,244,.3);
    --text:#dce4ff; --muted:#6a7799; --muted2:#38435e;
    --green:#2dca72; --green-soft:rgba(45,202,114,.1);
    --yellow:#d4a843; --yellow-soft:rgba(212,168,67,.1);
    --red:#f06b6b; --red-soft:rgba(240,107,107,.1);
    --blue:#8aaeff; --blue-soft:rgba(138,170,255,.1);
    --purple:#9b7fe8;
    --accent:#4a74f4; --accent-soft:rgba(74,116,244,.1);
    --amber:#e8943a; --amber-soft:rgba(232,148,58,.1);
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',-apple-system,sans-serif;font-size:15px;min-height:100vh}
  h1,h2,h3,h4,h5{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:-.01em}

  header{background:rgba(7,9,14,.9);backdrop-filter:blur(20px) saturate(160%);-webkit-backdrop-filter:blur(20px);border-bottom:1px solid var(--border);padding:14px 28px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}
  .header-left{display:flex;align-items:center;gap:16px}
  .logo{display:flex;align-items:center;gap:10px}
  .logo-bolt{color:var(--amber);font-size:1.1rem}
  .logo-text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:1.05rem;font-weight:700;color:var(--text);letter-spacing:.01em}
  .header-link{display:flex;align-items:center;gap:5px;color:var(--muted);text-decoration:none;font-size:.78rem;font-family:'SF Mono',Menlo,Consolas,monospace;border:1px solid var(--border);border-radius:6px;padding:4px 10px;transition:color .15s,border-color .15s}
  .header-link:hover{color:var(--text);border-color:rgba(255,255,255,.14)}
  .stack-btn{border:none;border-radius:8px;padding:7px 16px;font-size:.8rem;font-weight:600;cursor:pointer;transition:all .2s;letter-spacing:.01em}
  .stack-btn.start{background:var(--green-soft);color:var(--green);border:1px solid rgba(45,202,114,.3)}
  .stack-btn.start:hover{background:rgba(45,202,114,.18);transform:translateY(-1px)}
  .stack-btn.stop{background:var(--red-soft);color:var(--red);border:1px solid rgba(240,107,107,.3)}
  .stack-btn.stop:hover{background:rgba(240,107,107,.18);transform:translateY(-1px)}
  .stack-btn:disabled{opacity:.4;cursor:not-allowed;transform:none}
  .ts-wrap{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:.78rem;font-family:'SF Mono',Menlo,Consolas,monospace}
  .ring{display:inline-block;width:8px;height:8px;border:1.5px solid var(--muted2);border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite}
  @keyframes spin{to{transform:rotate(360deg)}}

  .page{max-width:1280px;margin:0 auto;padding:24px 28px}
  .top-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}

  .card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:22px;position:relative;overflow:hidden;transition:border-color .2s}
  .card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(74,116,244,.4),transparent);opacity:0;transition:opacity .2s}
  .card:hover{border-color:var(--border-hi)}
  .card:hover::before{opacity:1}
  .card-title{font-family:'SF Mono',Menlo,Consolas,monospace;font-size:.65rem;font-weight:500;text-transform:uppercase;letter-spacing:.18em;color:var(--amber);margin-bottom:20px}

  /* System */
  .stat-block{margin-bottom:18px}
  .stat-block:last-child{margin-bottom:0}
  .stat-row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}
  .stat-label{color:var(--muted);font-size:.88rem}
  .stat-value{font-weight:700;font-size:1.05rem;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
  .stat-sub{color:var(--muted2);font-size:.73rem;margin-top:4px;font-family:'SF Mono',Menlo,Consolas,monospace}
  .bar-wrap{background:rgba(255,255,255,.06);border-radius:6px;height:5px;overflow:hidden}
  .bar{height:5px;border-radius:6px;transition:width .6s cubic-bezier(.4,0,.2,1)}
  .bar.green{background:var(--green)} .bar.yellow{background:var(--yellow)} .bar.red{background:var(--red)}
  .metrics-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:18px;padding-top:18px;border-top:1px solid var(--border)}
  .mini-stat{background:var(--surface2);border-radius:10px;padding:12px 14px}
  .mini-label{font-family:'SF Mono',Menlo,Consolas,monospace;font-size:.65rem;text-transform:uppercase;letter-spacing:.12em;color:var(--muted2);margin-bottom:5px}
  .mini-value{font-size:1rem;font-weight:700;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}

  /* Services */
  .svc-row{display:flex;align-items:center;justify-content:space-between;padding:11px 14px;border-radius:10px;margin-bottom:8px;background:var(--surface2);border:1px solid transparent;transition:border-color .2s}
  .svc-row:last-child{margin-bottom:0}
  .svc-row:hover{border-color:var(--border)}
  .svc-left{display:flex;align-items:center;gap:12px}
  .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
  .dot.up{background:var(--green);box-shadow:0 0 8px rgba(45,202,114,.55)}
  .dot.down{background:var(--red);box-shadow:0 0 6px rgba(240,107,107,.4)}
  .dot.unknown{background:var(--muted2)}
  .svc-name{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-weight:600;font-size:.88rem;color:var(--text)}
  .svc-detail{color:var(--muted2);font-size:.72rem;margin-top:2px;font-family:'SF Mono',Menlo,Consolas,monospace}
  .svc-actions{display:flex;align-items:center;gap:6px}
  .btn{border:none;border-radius:6px;padding:4px 12px;font-size:.72rem;font-weight:600;cursor:pointer;transition:opacity .15s;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
  .btn:hover{opacity:.8} .btn:active{opacity:.55}
  .btn:disabled{opacity:.3;cursor:not-allowed}
  .btn-open{background:var(--blue-soft);color:var(--blue);border:1px solid rgba(138,170,255,.25);text-decoration:none;padding:4px 10px;border-radius:6px;font-size:.72rem;font-weight:600;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
  .btn-open:hover{background:rgba(138,170,255,.18)}
  .btn-stop{background:var(--red-soft);color:var(--red);border:1px solid rgba(240,107,107,.25)}
  .btn-start{background:var(--green-soft);color:var(--green);border:1px solid rgba(45,202,114,.25)}

  /* Models */
  .models-header{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:18px}
  .models-sub{color:var(--muted);font-size:.8rem;font-family:'SF Mono',Menlo,Consolas,monospace}
  .model-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(265px,1fr));gap:10px}
  .model-card{background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:14px 16px;transition:border-color .2s}
  .model-card:hover{border-color:rgba(255,255,255,.12)}
  .model-card.active{border-color:rgba(45,202,114,.35);background:rgba(45,202,114,.04)}
  .model-card.active:hover{border-color:rgba(45,202,114,.5)}
  .model-name{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-weight:700;font-size:.88rem;word-break:break-all;margin-bottom:7px;color:var(--text)}
  .model-meta{display:flex;align-items:center;justify-content:space-between}
  .model-size{color:var(--muted2);font-size:.75rem;font-family:'SF Mono',Menlo,Consolas,monospace}
  .badge{font-size:.65rem;padding:2px 8px;border-radius:10px;font-weight:700;font-family:'SF Mono',Menlo,Consolas,monospace}
  .badge.loaded{background:rgba(45,202,114,.12);color:var(--green);border:1px solid rgba(45,202,114,.35)}
  .badge.idle{background:var(--accent-soft);color:var(--blue);border:1px solid rgba(74,116,244,.2)}
  .badge.embed{background:rgba(155,127,232,.1);color:var(--purple);border:1px solid rgba(155,127,232,.3)}
  .model-extra{margin-top:7px;font-size:.72rem;color:var(--muted2);display:flex;gap:12px;font-family:'SF Mono',Menlo,Consolas,monospace}
  .model-hint{font-size:.72rem;color:var(--muted2);margin-top:6px;line-height:1.45}

  .toast{position:fixed;bottom:24px;right:24px;background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:11px 18px;font-size:.83rem;color:var(--text);box-shadow:0 8px 32px rgba(0,0,0,.5);transform:translateY(80px);transition:transform .3s cubic-bezier(.4,0,.2,1);z-index:100}
  .toast.show{transform:translateY(0)}

  @media(max-width:860px){.top-row{grid-template-columns:1fr}.page{padding:14px 16px}.metrics-grid{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<header>
  <div class="header-left">
    <div class="logo">
      <span class="logo-bolt">⚡</span>
      <span class="logo-text">Local-AI</span>
    </div>
    <a class="header-link" href="https://github.com/simoneiaci/local-AI" target="_blank">
      <svg height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
      GitHub
    </a>
    <a class="header-link" href="https://simoneiaci.github.io/local-AI/" target="_blank">
      <svg height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
      Docs
    </a>
  </div>
  <div style="display:flex;align-items:center;gap:14px">
    <button id="stack-btn" class="stack-btn start" onclick="stackToggle()" disabled>⚡ Start Stack</button>
    <div class="ts-wrap"><span class="ring"></span><span id="ts">connecting…</span></div>
  </div>
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
let _stackIsUp = false;
let _cooldownUntil = 0;   // timestamp — button locked until then

async function stackToggle(){
  const btn = document.getElementById('stack-btn');
  _cooldownUntil = Date.now() + 22000; // 22s — plenty for start/stop to propagate
  btn.disabled = true;
  if(_stackIsUp){
    btn.textContent = '■ Stopping…';
    control('stack_stop', 'Stopping AI services');
  } else {
    btn.textContent = '⚡ Starting…';
    control('stack_start', 'Starting AI services');
  }
}

function updateStackBtn(ollamaStatus){
  const btn = document.getElementById('stack-btn');
  _stackIsUp = ollamaStatus === 'up';
  if(Date.now() < _cooldownUntil) return; // keep the "…" state; don't flap
  btn.disabled = false;
  if(_stackIsUp){
    btn.className = 'stack-btn stop';
    btn.textContent = '■ Stop Stack';
  } else {
    btn.className = 'stack-btn start';
    btn.textContent = '⚡ Start Stack';
  }
}

// Control actions go through the dashboard proxy — token stays server-side
async function control(action,label){
  try{
    const r=await fetch('/proxy/control',{
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
    {key:'podman',    label:'Podman VM', sub:'Container runtime',      url:null,                     stop:'podman_stop',  start:'podman_start'},
    {key:'ollama',    label:'Ollama',    sub:'API · port 11434',       url:'http://localhost:11434', stop:'ollama_stop',  start:'ollama_start'},
    {key:'open_webui',label:'Open WebUI',sub:'Chat UI · port 3000',    url:'http://localhost:3000',  stop:'webui_stop',   start:'webui_start'},
    {key:'pipelines', label:'Pipelines', sub:'Middleware · port 9099', url:'http://localhost:9099',  stop:'pipelines_stop', start:'pipelines_start'},
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

const MODEL_HINTS = MODEL_HINTS_PLACEHOLDER;
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
    const hintHtml=hint?`<div class="model-hint">${hint}</div>`:'';
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

// Last-known-good values — prevents a single bad poll from blanking the whole UI
let _lastHost = null;
let _lastSvc  = null;
let _lastModels = {ps:{}, tags:{}};

async function refresh(){
  try{
    const r=await fetch('/api/data');
    const d=await r.json();
    const host=d.host||{}, svc=host.services||{};

    // Only promote to "last good" when the data is meaningfully populated
    if(host.cpu_pct != null || (host.ram && host.ram.used_gb != null)) _lastHost=host;
    if(Object.keys(svc).length > 0) _lastSvc=svc;
    if((d.ps && d.ps.models) || (d.tags && d.tags.models)) _lastModels={ps:d.ps||{},tags:d.tags||{}};

    const dispHost = _lastHost || host;
    const dispSvc  = _lastSvc  || svc;

    document.getElementById('card-system').innerHTML=renderSystem(dispHost);
    document.getElementById('card-services').innerHTML=renderServices(dispSvc);
    document.getElementById('card-models').innerHTML=renderModels(_lastModels.ps,_lastModels.tags);
    updateStackBtn(dispSvc.ollama);
    document.getElementById('ts').textContent='updated '+new Date().toLocaleTimeString();
  }catch(e){
    document.getElementById('ts').textContent='error – retrying…';
  }
}
refresh();
setInterval(refresh,4000);
</script>
</body>
</html>"""

def build_html():
    return HTML.replace('MODEL_HINTS_PLACEHOLDER', json.dumps(MODEL_HINTS, ensure_ascii=False))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            body = build_html().encode()
            self._send(200, 'text/html', body)
        elif self.path == '/api/data':
            self._send(200, 'application/json', json.dumps(api_data()).encode())
        else:
            self._send(404, 'text/plain', b'Not found')

    def do_POST(self):
        if self.path == '/proxy/control':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            status, resp = proxy_control(body)
            self._send(status, 'application/json', resp)
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
