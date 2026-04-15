#!/usr/bin/env python3
"""
Local-AI Metrics Exporter — runs on the HOST Mac.
Writes /tmp/ai-metrics.json every 3 seconds for the dashboard container to read.
Also runs a control server on port 9091 so the dashboard can start/stop services.
No external dependencies — uses only stdlib + macOS built-ins.
"""
import subprocess, json, re, time, shutil, os, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# ── Token auth ────────────────────────────────────────────────────────────────
def _load_secrets() -> dict:
    secrets_path = Path(__file__).parent.parent / '.secrets'
    result = {}
    try:
        for line in secrets_path.read_text().splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, _, v = line.partition('=')
                result[k.strip()] = v.strip()
    except Exception:
        pass
    return result

_SECRETS = _load_secrets()
CONTROL_TOKEN = os.getenv('CONTROL_TOKEN') or _SECRETS.get('CONTROL_TOKEN', '')

# ── Metric collectors ─────────────────────────────────────────────────────────

def cpu_pct():
    try:
        out = subprocess.check_output(
            ['top', '-l', '1', '-s', '0', '-n', '0'], text=True, timeout=5)
        m = re.search(r'CPU usage:\s*([\d.]+)%\s*user,\s*([\d.]+)%\s*sys', out)
        if m:
            return round(float(m.group(1)) + float(m.group(2)), 1)
    except Exception:
        pass
    return None

def ram_stats():
    try:
        out = subprocess.check_output(['sysctl', 'hw.memsize'], text=True)
        total_bytes = int(re.search(r'hw.memsize:\s*(\d+)', out).group(1))
        total_gb = round(total_bytes / 1024**3, 1)

        out = subprocess.check_output(['vm_stat'], text=True)
        page_size = int(re.search(r'page size of (\d+) bytes', out).group(1))

        def pages(key):
            m = re.search(rf'{key}:\s+(\d+)', out)
            return int(m.group(1)) if m else 0

        active   = pages('Pages active')
        wired    = pages('Pages wired down')
        occupied = pages('Pages occupied by compressor')
        swapped  = pages('Pages swapped out')
        used_gb  = round((active + wired + occupied) * page_size / 1024**3, 1)
        swap_gb  = round(swapped * page_size / 1024**3, 2)
        return {
            'used_gb':  used_gb,
            'total_gb': total_gb,
            'pct':      round(used_gb / total_gb * 100, 1),
            'swap_gb':  swap_gb,
        }
    except Exception:
        return None

def disk_stats():
    try:
        usage = shutil.disk_usage('/')
        ollama_size = 0
        ollama_path = os.path.expanduser('~/.ollama/models')
        if os.path.exists(ollama_path):
            out = subprocess.check_output(['du', '-sk', ollama_path],
                                          text=True, stderr=subprocess.DEVNULL)
            ollama_size = round(int(out.split()[0]) / 1024 / 1024, 1)
        return {
            'free_gb':   round(usage.free  / 1024**3, 1),
            'used_gb':   round(usage.used  / 1024**3, 1),
            'total_gb':  round(usage.total / 1024**3, 1),
            'pct':       round(usage.used  / usage.total * 100, 1),
            'ollama_gb': ollama_size,
        }
    except Exception:
        return None

def services():
    import urllib.request
    status = {}

    # Use specific health endpoints rather than bare TCP connects
    health_urls = [
        ('ollama',     'http://localhost:11434/api/tags'),
        ('open_webui', 'http://localhost:3000'),
        ('pipelines',  'http://localhost:9099'),
    ]
    for key, url in health_urls:
        try:
            urllib.request.urlopen(url, timeout=2)
            status[key] = 'up'
        except Exception:
            status[key] = 'down'

    try:
        out = subprocess.check_output(['tailscale', 'status', '--json'],
                                      text=True, timeout=3)
        data = json.loads(out)
        status['tailscale'] = 'up' if data.get('BackendState') == 'Running' else 'down'
        ips = data.get('Self', {}).get('TailscaleIPs', [])
        status['tailscale_ip'] = ips[0] if ips else ''
    except Exception:
        status['tailscale'] = 'down'
        status['tailscale_ip'] = ''

    try:
        out = subprocess.check_output(
            ['/opt/homebrew/bin/podman', 'machine', 'list', '--format', '{{.Running}}'],
            text=True, stderr=subprocess.DEVNULL)
        status['podman'] = 'up' if 'true' in out.lower() else 'down'
    except Exception:
        status['podman'] = 'down'

    return status

def collect():
    return {
        'ts':       time.time(),
        'cpu_pct':  cpu_pct(),
        'ram':      ram_stats(),
        'disk':     disk_stats(),
        'services': services(),
    }

# ── Control server (port 9091) ────────────────────────────────────────────────

OLLAMA_BIN  = '/opt/homebrew/bin/ollama'
PODMAN_BIN  = '/opt/homebrew/bin/podman'
TS_BIN      = '/usr/local/bin/tailscale'

ACTIONS = {
    'ollama_stop':       lambda: subprocess.Popen(['pkill', '-x', 'ollama']),
    'ollama_start':      lambda: subprocess.Popen([OLLAMA_BIN, 'serve'],
                             stdout=open('/tmp/ollama.log','a'), stderr=subprocess.STDOUT),
    'webui_stop':        lambda: subprocess.Popen([PODMAN_BIN, 'stop', 'open-webui']),
    'webui_start':       lambda: subprocess.Popen([PODMAN_BIN, 'start', 'open-webui']),
    'pipelines_stop':    lambda: subprocess.Popen([PODMAN_BIN, 'stop', 'open-webui-pipelines']),
    'pipelines_start':   lambda: subprocess.Popen([PODMAN_BIN, 'start', 'open-webui-pipelines']),
    'podman_stop':       lambda: subprocess.Popen([PODMAN_BIN, 'machine', 'stop']),
    'podman_start':      lambda: subprocess.Popen([PODMAN_BIN, 'machine', 'start']),
    'tailscale_up':      lambda: subprocess.Popen([TS_BIN, 'up']),
    'tailscale_down':    lambda: subprocess.Popen([TS_BIN, 'down']),
}

def _authorized(handler) -> bool:
    """Return True if the request carries a valid Bearer token (or no token is configured)."""
    if not CONTROL_TOKEN:
        return True  # token auth disabled — no token configured
    auth = handler.headers.get('Authorization', '')
    return auth == f'Bearer {CONTROL_TOKEN}'

class ControlHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != '/control':
            self.send_response(404); self.end_headers(); return
        if not _authorized(self):
            resp = json.dumps({'ok': False, 'error': 'unauthorized'}).encode()
            self.send_response(401)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(resp))
            self.end_headers()
            self.wfile.write(resp)
            return
        try:
            length = int(self.headers.get('Content-Length', 0))
            body   = json.loads(self.rfile.read(length))
            action = body.get('action', '')
            if action in ACTIONS:
                ACTIONS[action]()
                resp = json.dumps({'ok': True, 'action': action}).encode()
            else:
                resp = json.dumps({'ok': False, 'error': f'unknown action: {action}'}).encode()
        except Exception as e:
            resp = json.dumps({'ok': False, 'error': str(e)}).encode()
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(resp))
        self.end_headers()
        self.wfile.write(resp)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def log_message(self, *_): pass

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

def run_control_server():
    server = ReusableHTTPServer(('', 9091), ControlHandler)
    auth_status = 'token auth enabled' if CONTROL_TOKEN else 'NO TOKEN — auth disabled'
    print(f'Control server -> http://localhost:9091/control ({auth_status})', flush=True)
    server.serve_forever()

# ── Main loop ─────────────────────────────────────────────────────────────────

OUT = '/tmp/ai-metrics.json'

if __name__ == '__main__':
    # Start control server in background thread
    t = threading.Thread(target=run_control_server, daemon=True)
    t.start()

    print(f'metrics-exporter started → writing {OUT} every 3s')
    while True:
        try:
            data = collect()
            tmp = OUT + '.tmp'
            with open(tmp, 'w') as f:
                json.dump(data, f)
            os.replace(tmp, OUT)
        except Exception as e:
            print(f'error: {e}')
        time.sleep(3)
