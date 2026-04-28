#!/usr/bin/env python3
"""
Local-AI Dashboard — lightweight container web server.
Reads /hosttmp/ai-metrics.json (bind-mounted /private/tmp) + queries Ollama API.
No external dependencies; single-file HTML rendered inline.
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
<title>Local-AI · Instrument Panel</title>
<style>
  :root {
    --bg:#07090e; --bg2:#0a0c15; --bg3:#10131d;
    --surface:rgba(255,255,255,.028); --surface2:rgba(255,255,255,.045); --surface3:rgba(255,255,255,.065);
    --border:rgba(255,255,255,.07); --border2:rgba(255,255,255,.12); --border-hi:rgba(74,116,244,.35);
    --text:#dce4ff; --text-hi:#eef2ff; --muted:#6a7799; --muted2:#38435e;
    --green:#2dca72; --green-soft:rgba(45,202,114,.1);
    --yellow:#d4a843; --yellow-soft:rgba(212,168,67,.1);
    --red:#f06b6b; --red-soft:rgba(240,107,107,.1);
    --blue:#8aaeff; --blue-soft:rgba(138,170,255,.1);
    --purple:#9b7fe8;
    --accent:#4a74f4; --accent-soft:rgba(74,116,244,.12);
    --amber:#e8943a; --amber-soft:rgba(232,148,58,.1);
    --mono:'SF Mono',ui-monospace,Menlo,Consolas,monospace;
    --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%}
  body{
    background:var(--bg);color:var(--text);font-family:var(--sans);font-size:14.5px;min-height:100vh;
    font-variant-numeric:tabular-nums;
    background-image:
      linear-gradient(rgba(255,255,255,.014) 1px,transparent 1px),
      linear-gradient(90deg,rgba(255,255,255,.014) 1px,transparent 1px),
      radial-gradient(1000px 600px at 88% -10%,rgba(232,148,58,.05),transparent 60%),
      radial-gradient(900px 500px at -8% 108%,rgba(74,116,244,.05),transparent 55%);
    background-size:48px 48px,48px 48px,100% 100%,100% 100%;
    background-attachment:fixed;
  }
  h1,h2,h3,h4,h5{font-family:var(--sans);letter-spacing:-.01em}
  ::selection{background:rgba(74,116,244,.3);color:var(--text-hi)}

  /* ── Header ── */
  header{
    position:sticky;top:0;z-index:20;
    background:rgba(7,9,14,.82);
    backdrop-filter:blur(18px) saturate(160%);-webkit-backdrop-filter:blur(18px) saturate(160%);
    border-bottom:1px solid var(--border);
    padding:12px 24px;display:flex;align-items:center;justify-content:space-between;gap:16px;
  }
  .header-left{display:flex;align-items:center;gap:14px;min-width:0}
  .logo{display:flex;align-items:center;gap:9px;font-family:var(--mono);font-size:.82rem;letter-spacing:.04em;color:var(--text-hi);font-weight:600}
  .logo .br{color:var(--muted2)}
  .logo .bolt{color:var(--amber);text-shadow:0 0 10px rgba(232,148,58,.45)}
  .header-meta{display:none;align-items:center;gap:6px;font-family:var(--mono);font-size:.68rem;color:var(--muted);letter-spacing:.08em;text-transform:uppercase}
  @media(min-width:720px){.header-meta{display:flex}}
  .header-meta .sep{color:var(--muted2)}
  .header-link{display:flex;align-items:center;gap:5px;color:var(--muted);text-decoration:none;font-size:.72rem;font-family:var(--mono);border:1px solid var(--border);border-radius:6px;padding:4px 9px;transition:color .15s,border-color .15s,background .15s}
  .header-link:hover{color:var(--text-hi);border-color:var(--border2);background:var(--surface)}
  .header-right{display:flex;align-items:center;gap:12px;flex-shrink:0}

  .stack-btn{
    display:inline-flex;align-items:center;gap:8px;
    border:1px solid transparent;border-radius:7px;padding:6px 13px 6px 11px;
    font-size:.76rem;font-weight:600;cursor:pointer;letter-spacing:.02em;
    font-family:var(--sans);transition:transform .15s,background .2s,border-color .2s,color .2s;
  }
  .stack-btn .sq{width:7px;height:7px;border-radius:1.5px;background:currentColor;box-shadow:0 0 8px currentColor}
  .stack-btn.start{background:var(--green-soft);color:var(--green);border-color:rgba(45,202,114,.3)}
  .stack-btn.start:hover{background:rgba(45,202,114,.18);transform:translateY(-1px)}
  .stack-btn.stop{background:var(--red-soft);color:var(--red);border-color:rgba(240,107,107,.3)}
  .stack-btn.stop:hover{background:rgba(240,107,107,.18);transform:translateY(-1px)}
  .stack-btn.pending{background:var(--accent-soft);color:var(--blue);border-color:rgba(74,116,244,.3)}
  .stack-btn:disabled{opacity:.55;cursor:wait;transform:none}

  .ts-wrap{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:.7rem;font-family:var(--mono);letter-spacing:.03em}
  .pulse{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 0 var(--accent);animation:pulse 1.6s ease-out infinite}
  .pulse.err{background:var(--yellow);animation-duration:2.4s}
  @keyframes pulse{
    0%{box-shadow:0 0 0 0 rgba(74,116,244,.55)}
    100%{box-shadow:0 0 0 10px rgba(74,116,244,0)}
  }

  /* Scan-line beneath header — pulses green on successful poll, amber on error */
  .scanline{position:sticky;top:49px;z-index:19;height:1px;background:var(--border);overflow:hidden}
  .scanline::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,var(--accent),transparent);width:30%;transform:translateX(-100%);opacity:0}
  .scanline.tick::after{animation:sweep .9s ease-out forwards;opacity:1}
  .scanline.err::after{background:linear-gradient(90deg,transparent,var(--yellow),transparent)}
  @keyframes sweep{from{transform:translateX(-100%)}to{transform:translateX(380%)}}

  /* ── Layout ── */
  .page{max-width:1280px;margin:0 auto;padding:22px 24px 64px}
  .top-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}

  /* ── Cards ── */
  .card{
    background:linear-gradient(180deg,var(--surface),rgba(255,255,255,.015));
    border:1px solid var(--border);border-radius:10px;padding:20px 20px 18px;
    position:relative;overflow:hidden;transition:border-color .2s;
  }
  .card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(74,116,244,.55),transparent);opacity:.0;transition:opacity .5s}
  .card.live::before{opacity:.9;animation:fadeOut 1.2s ease-out forwards}
  @keyframes fadeOut{to{opacity:0}}
  .card:hover{border-color:var(--border2)}

  .card-head{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:18px;gap:12px}
  .card-title{font-family:var(--mono);font-size:.64rem;font-weight:600;text-transform:uppercase;letter-spacing:.22em;color:var(--amber);display:flex;align-items:center;gap:10px}
  .card-title::before{content:'';display:inline-block;width:6px;height:6px;background:var(--amber);border-radius:1px;box-shadow:0 0 8px rgba(232,148,58,.55)}
  .card-sub{font-family:var(--mono);font-size:.68rem;color:var(--muted);letter-spacing:.06em}

  /* ── System card ── */
  .stat-block{margin-bottom:16px}
  .stat-block:last-child{margin-bottom:0}
  .stat-row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;gap:12px}
  .stat-label{color:var(--muted);font-size:.8rem;font-family:var(--mono);text-transform:uppercase;letter-spacing:.1em}
  .stat-value{font-weight:700;font-size:1.35rem;font-family:var(--sans);color:var(--text-hi);line-height:1}
  .stat-value .unit{font-size:.72rem;color:var(--muted);font-weight:500;margin-left:3px}
  .stat-sub{color:var(--muted2);font-size:.68rem;margin-top:5px;font-family:var(--mono);letter-spacing:.04em}

  .bar-wrap{background:rgba(255,255,255,.05);border-radius:2px;height:3px;overflow:hidden;position:relative}
  .bar{height:3px;border-radius:2px;transition:width .6s cubic-bezier(.4,0,.2,1);position:relative}
  .bar::after{content:'';position:absolute;top:0;right:0;width:14px;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.22));border-radius:2px}
  .bar.green{background:var(--green)} .bar.yellow{background:var(--yellow)} .bar.red{background:var(--red)}

  .metrics-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:16px;padding-top:16px;border-top:1px dashed var(--border)}
  .mini-stat{background:var(--bg3);border:1px solid var(--border);border-radius:7px;padding:10px 12px}
  .mini-label{font-family:var(--mono);font-size:.6rem;text-transform:uppercase;letter-spacing:.14em;color:var(--muted2);margin-bottom:4px}
  .mini-value{font-size:.92rem;font-weight:700;font-family:var(--sans);color:var(--text-hi)}

  /* ── Services card ── */
  .svc-list{display:flex;flex-direction:column;gap:6px}
  .svc-row{
    display:flex;align-items:center;justify-content:space-between;gap:10px;
    padding:10px 12px;border-radius:7px;
    background:var(--bg3);border:1px solid var(--border);transition:border-color .2s;
  }
  .svc-row:hover{border-color:var(--border2)}
  .svc-row.up{border-left:2px solid var(--green)}
  .svc-row.down{border-left:2px solid var(--muted2)}
  .svc-left{display:flex;align-items:center;gap:11px;min-width:0}
  .dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
  .dot.up{background:var(--green);box-shadow:0 0 8px rgba(45,202,114,.6)}
  .dot.down{background:var(--muted2)}
  .dot.unknown{background:var(--muted2);opacity:.4}
  .svc-name{font-family:var(--sans);font-weight:600;font-size:.84rem;color:var(--text-hi);letter-spacing:.005em}
  .svc-detail{color:var(--muted);font-size:.68rem;margin-top:2px;font-family:var(--mono);letter-spacing:.03em}

  .svc-actions{display:flex;align-items:stretch;gap:0;border:1px solid var(--border);border-radius:6px;overflow:hidden;flex-shrink:0}
  .svc-actions > *{border:none;background:transparent;padding:5px 11px;font-size:.68rem;font-weight:600;font-family:var(--mono);letter-spacing:.06em;text-transform:uppercase;cursor:pointer;color:var(--muted);transition:background .15s,color .15s;text-decoration:none;display:inline-flex;align-items:center}
  .svc-actions > * + *{border-left:1px solid var(--border)}
  .svc-actions > *:hover:not(:disabled){background:var(--surface);color:var(--text-hi)}
  .svc-actions > *:disabled{opacity:.35;cursor:not-allowed}
  .svc-actions .act-start:not(:disabled){color:var(--green)}
  .svc-actions .act-stop:not(:disabled){color:var(--red)}
  .svc-actions .act-open{color:var(--blue)}

  /* ── Models card ── */
  .model-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));gap:8px}
  .model-card{
    background:var(--bg3);border:1px solid var(--border);border-radius:8px;
    padding:12px 14px;transition:border-color .2s,transform .2s;position:relative;
  }
  .model-card:hover{border-color:var(--border2);transform:translateY(-1px)}
  .model-card.active{box-shadow:inset 3px 0 0 var(--green);border-color:rgba(45,202,114,.3);background:linear-gradient(180deg,rgba(45,202,114,.04),var(--bg3))}
  .model-name{font-family:var(--mono);font-weight:600;font-size:.82rem;word-break:break-all;margin-bottom:6px;color:var(--text-hi);letter-spacing:-.005em}
  .model-meta{display:flex;align-items:center;justify-content:space-between;gap:8px}
  .model-size{color:var(--muted);font-size:.7rem;font-family:var(--mono);letter-spacing:.04em}
  .badge{font-size:.58rem;padding:2px 7px;border-radius:3px;font-weight:700;font-family:var(--mono);text-transform:uppercase;letter-spacing:.12em}
  .badge.loaded{background:rgba(45,202,114,.14);color:var(--green);border:1px solid rgba(45,202,114,.4)}
  .badge.idle{background:rgba(106,119,153,.1);color:var(--muted);border:1px solid var(--border2)}
  .badge.embed{background:rgba(155,127,232,.1);color:var(--purple);border:1px solid rgba(155,127,232,.35)}
  .model-extra{margin-top:7px;font-size:.66rem;color:var(--muted2);display:flex;gap:10px;font-family:var(--mono);letter-spacing:.04em}
  .model-hint{font-size:.7rem;color:var(--muted);margin-top:7px;line-height:1.5;border-top:1px dashed var(--border);padding-top:7px}

  .empty{color:var(--muted);padding:24px 0;text-align:center;font-family:var(--mono);font-size:.78rem;letter-spacing:.04em}

  /* ── Toast ── */
  .toast{
    position:fixed;bottom:22px;right:22px;
    background:var(--bg2);border:1px solid var(--border2);border-radius:8px;
    padding:10px 16px 10px 14px;font-size:.78rem;color:var(--text);
    font-family:var(--mono);letter-spacing:.03em;
    box-shadow:0 10px 32px rgba(0,0,0,.6);
    transform:translateY(80px);opacity:0;transition:transform .3s cubic-bezier(.4,0,.2,1),opacity .2s;
    z-index:100;display:flex;align-items:center;gap:10px;
  }
  .toast.show{transform:translateY(0);opacity:1}
  .toast::before{content:'';width:5px;height:5px;border-radius:50%;background:currentColor;box-shadow:0 0 6px currentColor}

  @media(max-width:860px){
    .top-row{grid-template-columns:1fr}
    .page{padding:16px 14px 48px}
    header{padding:10px 14px}
    .metrics-grid{grid-template-columns:1fr 1fr}
    .svc-actions{flex-wrap:wrap}
  }
</style>
</head>
<body>
<header>
  <div class="header-left">
    <div class="logo"><span class="br">[</span><span class="bolt">⚡</span>&nbsp;LOCAL-AI<span class="br">]</span></div>
    <div class="header-meta">
      <span>M4 PRO</span><span class="sep">·</span><span>24&nbsp;GB</span><span class="sep">·</span><span>METAL</span>
    </div>
    <a class="header-link" href="https://github.com/your-org/local-ai" target="_blank" rel="noopener">
      <svg height="11" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
      github
    </a>
    <a class="header-link" href="https://your-org.github.io/local-ai/" target="_blank" rel="noopener">
      <svg height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
      docs
    </a>
  </div>
  <div class="header-right">
    <button id="stack-btn" class="stack-btn start" onclick="stackToggle()" disabled><span class="sq"></span><span id="stack-lbl">start&nbsp;stack</span></button>
    <div class="ts-wrap"><span class="pulse" id="pulse"></span><span id="ts">connecting…</span></div>
  </div>
</header>
<div class="scanline" id="scanline"></div>

<div class="page">
  <div class="top-row">
    <div class="card" id="card-system"><div class="empty">booting telemetry…</div></div>
    <div class="card" id="card-services"><div class="empty">booting telemetry…</div></div>
  </div>
  <div class="card" id="card-models"><div class="empty">booting telemetry…</div></div>
</div>
<div class="toast" id="toast"></div>

<script id="model-hints" type="application/json">MODEL_HINTS_JSON</script>
<script>
const MODEL_HINTS = (() => {
  try { return JSON.parse(document.getElementById('model-hints').textContent); }
  catch(e){ return {}; }
})();

let _stackIsUp = false;
let _cooldownUntil = 0;   // ms timestamp — button locked until then

function $(id){ return document.getElementById(id); }

async function stackToggle(){
  const btn=$('stack-btn'), lbl=$('stack-lbl');
  _cooldownUntil = Date.now() + 22000; // 22s — plenty for start/stop to propagate
  btn.disabled = true;
  btn.className = 'stack-btn pending';
  if(_stackIsUp){
    lbl.textContent = 'stopping…';
    control('stack_stop', 'Stopping AI services');
  } else {
    lbl.textContent = 'starting…';
    control('stack_start', 'Starting AI services');
  }
}

function updateStackBtn(runtimeStatus){
  const btn=$('stack-btn'), lbl=$('stack-lbl');
  _stackIsUp = runtimeStatus === 'up';
  if(Date.now() < _cooldownUntil) return; // keep the "…" state; don't flap
  btn.disabled = false;
  if(_stackIsUp){
    btn.className = 'stack-btn stop';
    lbl.textContent = 'stop\u00a0stack';
  } else {
    btn.className = 'stack-btn start';
    lbl.textContent = 'start\u00a0stack';
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
    else toast(`error: ${d.error}`,'var(--red)');
  }catch(e){
    toast('control server unreachable','var(--red)');
  }
}

// ── Formatters ──
function pct2c(p){return p>85?'red':p>65?'yellow':'green'}
function bar(p){
  if(p==null)return '';
  return `<div class="bar-wrap"><div class="bar ${pct2c(p)}" style="width:${Math.min(p,100)}%"></div></div>`;
}
function gb(v){return v!=null?v.toFixed(1):'–'}
function pctStr(v){return v!=null?v.toFixed(1):'–'}
function sizeStr(bytes){
  if(!bytes)return '';
  const g=bytes/1073741824;
  return g>=1?g.toFixed(1)+' GB':(bytes/1048576).toFixed(0)+' MB';
}
function timeUntil(iso){
  if(!iso)return '';
  const s=Math.round((new Date(iso)-Date.now())/1000);
  if(s<=0)return 'expiring…';
  if(s<60)return `${s}s left`;
  return `${Math.round(s/60)}m left`;
}
function esc(s){
  if(s==null) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// ── Toast ──
let toastTimer;
function toast(msg,color='var(--text)'){
  const el=$('toast');
  el.textContent=msg; el.style.color=color;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>el.classList.remove('show'),3000);
}

function flashCard(id){
  const el=$(id); if(!el) return;
  el.classList.remove('live'); void el.offsetWidth; el.classList.add('live');
}
function flashScan(err=false){
  const el=$('scanline'); if(!el) return;
  el.classList.remove('tick','err'); void el.offsetWidth;
  el.classList.add('tick'); if(err) el.classList.add('err');
}

// ── Renderers ──
function renderSystem(host){
  const cpu=host.cpu_pct, ram=host.ram||{}, disk=host.disk||{};
  const cpuC=cpu!=null?`color:var(--${pct2c(cpu)})`:'';
  const ramC=ram.pct!=null?`color:var(--${pct2c(ram.pct)})`:'';
  const dskC=disk.pct!=null?`color:var(--${pct2c(disk.pct)})`:'';
  const swap=ram.swap_gb!=null && ram.swap_gb>0
    ?`<div class="mini-stat"><div class="mini-label">swap&nbsp;used</div><div class="mini-value" style="color:var(--yellow)">${ram.swap_gb.toFixed(2)}<span class="unit" style="color:var(--muted);font-weight:500;font-size:.7rem;margin-left:3px">GB</span></div></div>`
    :`<div class="mini-stat"><div class="mini-label">swap&nbsp;used</div><div class="mini-value">none</div></div>`;
  return `<div class="card-head"><div class="card-title">system</div><div class="card-sub">host · live</div></div>
    <div class="stat-block">
      <div class="stat-row"><span class="stat-label">cpu</span><span class="stat-value" style="${cpuC}">${pctStr(cpu)}<span class="unit">%</span></span></div>
      ${bar(cpu)}
    </div>
    <div class="stat-block">
      <div class="stat-row"><span class="stat-label">ram</span><span class="stat-value" style="${ramC}">${gb(ram.used_gb)}<span class="unit">/ ${gb(ram.total_gb)} GB</span></span></div>
      ${bar(ram.pct)}
      <div class="stat-sub">${ram.pct!=null?ram.pct.toFixed(1)+'% used':''}</div>
    </div>
    <div class="stat-block">
      <div class="stat-row"><span class="stat-label">disk</span><span class="stat-value" style="${dskC}">${gb(disk.free_gb)}<span class="unit">GB free</span></span></div>
      ${bar(disk.pct)}
      <div class="stat-sub">${disk.used_gb!=null?gb(disk.used_gb)+' used of '+gb(disk.total_gb)+' GB':''}</div>
    </div>
    <div class="metrics-grid">
      <div class="mini-stat"><div class="mini-label">models&nbsp;on&nbsp;disk</div><div class="mini-value">${gb(disk.ollama_gb)}<span class="unit" style="color:var(--muted);font-weight:500;font-size:.7rem;margin-left:3px">GB</span></div></div>
      ${swap}
    </div>`;
}

function renderServices(svc){
  const items=[
    {key:'podman',    label:'Podman VM', sub:'container runtime',      url:null,                     stop:'podman_stop',  start:'podman_start'},
    {key:'lmstudio',  label:'LM Studio', sub:'mlx api · :1234',        url:null,                     stop:'lmstudio_stop', start:'lmstudio_start'},
    {key:'ollama',    label:'Ollama',    sub:'api · :11434',           url:'http://localhost:11434', stop:'ollama_stop',  start:'ollama_start'},
    {key:'open_webui',label:'Open WebUI',sub:'chat · :3000',           url:'http://localhost:3000',  stop:'webui_stop',   start:'webui_start'},
    {key:'pipelines', label:'Pipelines', sub:'middleware · :9099',     url:'http://localhost:9099',  stop:'pipelines_stop', start:'pipelines_start'},
    {key:'tailscale', label:'Tailscale', sub:svc.tailscale_ip||'vpn · not connected', url:null, stop:'tailscale_down', start:'tailscale_up', startLabel:'connect'},
  ];
  const rows=items.map(i=>{
    const st=svc[i.key]||'unknown';
    const isUp=st==='up';
    const detail=i.key==='tailscale'&&svc.tailscale_ip?svc.tailscale_ip:i.sub;
    const openBtn=i.url&&isUp?`<a class="act-open" href="${i.url}" target="_blank" rel="noopener">open&nbsp;↗</a>`:'';
    const startBtn=`<button class="act-start" onclick="control('${i.start}','Starting ${i.label}')" ${isUp?'disabled':''}>${i.startLabel||'start'}</button>`;
    const stopBtn=`<button class="act-stop" onclick="control('${i.stop}','Stopping ${i.label}')" ${!isUp?'disabled':''}>stop</button>`;
    return `<div class="svc-row ${st}">
      <div class="svc-left">
        <div class="dot ${st}"></div>
        <div><div class="svc-name">${esc(i.label)}</div><div class="svc-detail">${esc(detail)}</div></div>
      </div>
      <div class="svc-actions">${startBtn}${stopBtn}${openBtn}</div>
    </div>`;
  }).join('');
  const up=items.filter(i=>svc[i.key]==='up').length;
  return `<div class="card-head"><div class="card-title">services</div><div class="card-sub">${up}/${items.length} up</div></div>
    <div class="svc-list">${rows}</div>`;
}

function modelHint(name){
  if(MODEL_HINTS[name]) return MODEL_HINTS[name];
  for(const [k,v] of Object.entries(MODEL_HINTS)){
    if(name.startsWith(k.split(':')[0])) return v;
  }
  return '';
}

function renderModels(ps,tags){
  const loadedMap={};
  (ps.models||[]).forEach(m=>{loadedMap[m.name]=m});
  const all=tags.models||[];
  if(!all.length)return `<div class="card-head"><div class="card-title">models</div></div><div class="empty">no models found — is ollama running?</div>`;
  // Sort: loaded first, then by size desc
  const sorted=[...all].sort((a,b)=>{
    const la=loadedMap[a.name]?1:0, lb=loadedMap[b.name]?1:0;
    if(la!==lb) return lb-la;
    return (b.size||0)-(a.size||0);
  });
  const lc=Object.keys(loadedMap).length;
  const cards=sorted.map(m=>{
    const name=m.name, loaded=loadedMap[name];
    const isEmbed=name.includes('embed');
    const sizeGb=m.size?(m.size/1073741824).toFixed(1)+'\u00a0GB':'';
    let badge=isEmbed?`<span class="badge embed">embed</span>`:`<span class="badge idle">idle</span>`;
    let extra='';
    if(loaded){
      badge=`<span class="badge loaded">● loaded</span>`;
      const parts=[];
      if(loaded.size_vram) parts.push('vram&nbsp;'+sizeStr(loaded.size_vram));
      if(loaded.expires_at) parts.push(timeUntil(loaded.expires_at));
      if(parts.length) extra=`<div class="model-extra">${parts.map(p=>`<span>${p}</span>`).join('')}</div>`;
    }
    const hint=modelHint(name);
    const hintHtml=hint?`<div class="model-hint">${esc(hint)}</div>`:'';
    return `<div class="model-card ${loaded?'active':''}">
      <div class="model-name">${esc(name)}</div>
      <div class="model-meta"><span class="model-size">${sizeGb}</span>${badge}</div>
      ${hintHtml}
      ${extra}
    </div>`;
  }).join('');
  return `<div class="card-head"><div class="card-title">models</div><div class="card-sub">${lc} loaded · ${all.length} available</div></div>
  <div class="model-grid">${cards}</div>`;
}

// Last-known-good values — prevents a single bad poll from blanking the whole UI
let _lastHost = null;
let _lastSvc  = null;
let _lastModels = {ps:{}, tags:{}};
let _lastSig   = '';

function sigOf(host,svc,models){
  try{
    return JSON.stringify([host.cpu_pct,host.ram&&host.ram.used_gb,host.disk&&host.disk.free_gb,svc,Object.keys(models.ps.models||{}).length,Object.keys(models.tags.models||{}).length]);
  }catch{ return Math.random().toString(); }
}

async function refresh(){
  try{
    const r=await fetch('/api/data');
    const d=await r.json();
    const host=d.host||{}, svc=host.services||{};

    if(host.cpu_pct != null || (host.ram && host.ram.used_gb != null)) _lastHost=host;
    if(Object.keys(svc).length > 0) _lastSvc=svc;
    if((d.ps && d.ps.models) || (d.tags && d.tags.models)) _lastModels={ps:d.ps||{},tags:d.tags||{}};

    const dispHost = _lastHost || host;
    const dispSvc  = _lastSvc  || svc;

    $('card-system').innerHTML=renderSystem(dispHost);
    $('card-services').innerHTML=renderServices(dispSvc);
    $('card-models').innerHTML=renderModels(_lastModels.ps,_lastModels.tags);
    updateStackBtn(dispSvc.lmstudio);

    // Pulse cards whose contents actually changed
    const sig=sigOf(dispHost,dispSvc,_lastModels);
    if(sig!==_lastSig){ flashCard('card-system'); flashCard('card-services'); flashCard('card-models'); _lastSig=sig; }

    $('ts').textContent='sync '+new Date().toLocaleTimeString();
    $('pulse').classList.remove('err');
    flashScan(false);
  }catch(e){
    $('ts').textContent='error · retrying…';
    $('pulse').classList.add('err');
    flashScan(true);
  }
}
refresh();
setInterval(refresh,4000);
</script>
</body>
</html>"""

def build_html():
    # Inject model hints as a JSON script tag — robust against any literal content
    # (no string-replace collision risk).
    return HTML.replace('MODEL_HINTS_JSON', json.dumps(MODEL_HINTS, ensure_ascii=False).replace('</', '<\\/'))

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
