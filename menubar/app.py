#!/usr/bin/env python3
"""Local-AI menu bar controller for macOS."""
import json
import math
import os
import struct
import subprocess
import threading
import time
import urllib.request
import zlib
from pathlib import Path

import rumps

SECRETS_PATH = Path.home() / 'Documents/AI/Local-AI/.secrets'
METRICS_PATH = '/tmp/ai-metrics.json'
CONTROL_URL  = 'http://localhost:9091/control'
OLLAMA_API   = 'http://localhost:11434'
LMSTUDIO_API = 'http://localhost:1234/v1'
PODMAN       = '/opt/homebrew/bin/podman'
EXPORTER     = str(Path.home() / 'Documents/AI/Local-AI/scripts/metrics-exporter.py')
BACKEND_FILE = Path.home() / '.config/local-ai/active-backend'


# ── Icons ─────────────────────────────────────────────────────────────────────

def _dot_png(r, g, b, size=32, path=None):
    cx = cy = size / 2.0
    radius = size / 2.0 - 2
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            d = math.sqrt((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2)
            a = 255 if d <= radius - 0.5 else (
                int(255 * (radius + 0.5 - d)) if d <= radius + 0.5 else 0
            )
            row += bytes([r, g, b, a])
        rows.append(bytes(row))
    raw = b''.join(rows)

    def chunk(tag, data):
        body = tag + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xffffffff)

    png = (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(raw))
        + chunk(b'IEND', b'')
    )
    with open(path, 'wb') as f:
        f.write(png)
    return path


ICON_GREEN  = _dot_png(52,  199, 89,  path='/tmp/localai-green.png')
ICON_YELLOW = _dot_png(255, 204, 0,   path='/tmp/localai-yellow.png')
ICON_RED    = _dot_png(255, 59,  48,  path='/tmp/localai-red.png')
ICON_GREY   = _dot_png(142, 142, 147, path='/tmp/localai-grey.png')


def _ram_icon(pct):
    if pct is None: return ICON_GREY
    if pct < 60:    return ICON_GREEN
    if pct < 80:    return ICON_YELLOW
    return ICON_RED


def _ram_dot(pct):
    if pct is None: return '⚪'
    if pct < 60:    return '🟢'
    if pct < 80:    return '🟡'
    return '🔴'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_token() -> str:
    try:
        for line in SECRETS_PATH.read_text().splitlines():
            line = line.strip()
            if line.startswith('CONTROL_TOKEN='):
                return line.partition('=')[2].strip()
    except Exception:
        pass
    return ''


def _control(action: str, token: str):
    try:
        body = json.dumps({'action': action}).encode()
        req = urllib.request.Request(
            CONTROL_URL,
            data=body,
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
            method='POST',
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        rumps.notification('Local-AI', f'Action failed: {action}', str(e), sound=False)


def _ollama_get(path):
    try:
        with urllib.request.urlopen(f'{OLLAMA_API}{path}', timeout=3) as resp:
            return json.load(resp)
    except Exception:
        return None


def _ollama_post(path, body):
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            f'{OLLAMA_API}{path}', data=data,
            headers={'Content-Type': 'application/json'}, method='POST',
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except Exception:
        return None


def _lmstudio_get(path):
    try:
        with urllib.request.urlopen(f'{LMSTUDIO_API}{path}', timeout=3) as resp:
            return json.load(resp)
    except Exception:
        return None


def _ensure_exporter():
    result = subprocess.run(['pgrep', '-f', 'metrics-exporter.py'], capture_output=True)
    if result.returncode == 0:
        return
    token = _load_token()
    env = os.environ.copy()
    if token:
        env['CONTROL_TOKEN'] = token
    with open('/tmp/ai-metrics-exporter.log', 'a') as logf:
        subprocess.Popen(
            ['python3', EXPORTER],
            stdout=logf, stderr=subprocess.STDOUT, env=env,
        )
    time.sleep(2)


# ── App ───────────────────────────────────────────────────────────────────────

class LocalAIApp(rumps.App):
    def __init__(self):
        self._token        = _load_token()
        self._model_tick   = 0
        self._active_model = None
        self._known_models = []
        self._models_dirty = False
        self._lock         = threading.Lock()

        self._mi_cpu    = rumps.MenuItem('CPU: —')
        self._mi_ram    = rumps.MenuItem('⚪ RAM: —')
        self._mi_disk   = rumps.MenuItem('Disk: —')
        self._mi_lmstudio = rumps.MenuItem('⚪ LM Studio app (default)')
        self._mi_ollama = rumps.MenuItem('⚪ Ollama (alternate)')
        self._mi_webui  = rumps.MenuItem('⚪ Open WebUI')
        self._mi_pipes  = rumps.MenuItem('⚪ Pipelines')
        self._mi_podman = rumps.MenuItem('⚪ Podman')
        self._mi_ts     = rumps.MenuItem('⚪ Tailscale')
        self._mi_model  = rumps.MenuItem('Model: —')
        # Seed one item so the submenu arrow is visible immediately
        self._mi_model.add(rumps.MenuItem('Loading…'))

        # Runtime switcher submenu. Selecting one persists the backend and
        # starts it while stopping the other runtime to avoid memory pressure.
        self._mi_backend = rumps.MenuItem('Runtime: —')
        self._mi_backend.add(rumps.MenuItem('Use LM Studio (MLX)',
                             callback=lambda _: self._set_backend('lmstudio')))
        self._mi_backend.add(rumps.MenuItem('Use Ollama',
                             callback=lambda _: self._set_backend('ollama')))

        super().__init__(
            name='LocalAI',
            title='',
            icon=ICON_GREY,
            template=False,
            menu=[
                self._mi_cpu,
                self._mi_ram,
                self._mi_disk,
                None,
                self._mi_lmstudio,
                self._mi_ollama,
                self._mi_webui,
                self._mi_pipes,
                self._mi_podman,
                self._mi_ts,
                None,
                self._mi_model,
                self._mi_backend,
                None,
                rumps.MenuItem('Start Stack', callback=self._start),
                rumps.MenuItem('Stop Stack',  callback=self._stop),
                rumps.MenuItem('Full Off',    callback=self._off),
                None,
                rumps.MenuItem('Start LM Studio', callback=self._lmstudio_start),
                rumps.MenuItem('Stop LM Studio',  callback=self._lmstudio_stop),
                None,
                rumps.MenuItem('Open WebUI ↗',
                               callback=lambda _: subprocess.Popen(['open', 'http://localhost:3000'])),
                rumps.MenuItem('Dashboard ↗',
                               callback=lambda _: subprocess.Popen(['open', 'http://localhost:9090'])),
                rumps.MenuItem('LM Studio ↗',
                               callback=lambda _: subprocess.Popen(['open', '-a', 'LM Studio'])),
            ],
        )

        # Populate model list immediately in background; first poll will apply it
        threading.Thread(target=self._fetch_models, daemon=True).start()

        rumps.Timer(self._poll, 3).start()
        self._poll(None)

    # ── Polling ───────────────────────────────────────────────────────────────

    def _poll(self, _):
        try:
            stat = os.stat(METRICS_PATH)
            if time.time() - stat.st_mtime > 10:
                raise FileNotFoundError('stale')
            with open(METRICS_PATH) as f:
                data = json.load(f)
            self._apply(data)
        except Exception:
            self._apply(None)

        with self._lock:
            dirty = self._models_dirty
            self._models_dirty = False
        if dirty:
            self._apply_model_menu()

        self._model_tick += 1
        if self._model_tick % 5 == 0:   # every ~15 s
            threading.Thread(target=self._fetch_models, daemon=True).start()

    def _apply(self, data):
        if data is None:
            self.icon  = ICON_GREY
            self.title = ''
            self._mi_cpu.title  = 'CPU: —'
            self._mi_ram.title  = '⚪ RAM: —'
            self._mi_disk.title = 'Disk: —'
            for mi, label in [
                (self._mi_lmstudio, 'LM Studio app (default)'),
                (self._mi_ollama,   'Ollama (alternate)'),
                (self._mi_webui,    'Open WebUI'),
                (self._mi_pipes,    'Pipelines'),
                (self._mi_podman,   'Podman'),
                (self._mi_ts,       'Tailscale'),
            ]:
                mi.title = f'⚪ {label}'
            self._mi_backend.title = f'Runtime: {self._read_backend()}'
            return

        cpu  = data.get('cpu_pct')
        ram  = data.get('ram')  or {}
        disk = data.get('disk') or {}
        svc  = data.get('services') or {}

        pct        = ram.get('pct') if ram else None
        self.icon  = _ram_icon(pct)
        self.title = ''

        self._mi_cpu.title = f'CPU: {cpu:.1f}%' if cpu is not None else 'CPU: —'

        if ram:
            dot  = _ram_dot(pct)
            swap = f'  swap {ram["swap_gb"]} GB' if ram.get('swap_gb', 0) > 0.1 else ''
            self._mi_ram.title = f'{dot} RAM: {ram["used_gb"]}/{ram["total_gb"]} GB  ({pct:.0f}%){swap}'

        if disk:
            models = f'  · models {disk["ollama_gb"]} GB' if disk.get('ollama_gb') else ''
            self._mi_disk.title = f'Disk: {disk["free_gb"]} GB free{models}'

        def sdot(key): return '🟢' if svc.get(key) == 'up' else '🔴'

        lm_api = ' · API :1234' if svc.get('lmstudio_api') == 'up' else ' · API off'
        self._mi_lmstudio.title = f'{sdot("lmstudio")} LM Studio app (default){lm_api}'
        self._mi_ollama.title = f'{sdot("ollama")} Ollama (alternate)'
        self._mi_webui.title  = f'{sdot("open_webui")} Open WebUI'
        self._mi_pipes.title  = f'{sdot("pipelines")} Pipelines'
        self._mi_podman.title = f'{sdot("podman")} Podman'
        ts_ip = svc.get('tailscale_ip', '')
        self._mi_ts.title = f'{sdot("tailscale")} Tailscale' + (f'  {ts_ip}' if ts_ip else '')
        self._mi_backend.title = f'Runtime: {self._read_backend()}'

    # ── Model Management ──────────────────────────────────────────────────────

    @staticmethod
    def _is_chat_model(name):
        # Filter out embedding-only models — they fail on /api/generate
        n = name.lower()
        return not ('embed' in n or 'embedding' in n)

    def _fetch_models(self):
        backend = self._read_backend()
        if backend == 'lmstudio':
            models_payload = _lmstudio_get('/models')
            if models_payload is None:
                with self._lock:
                    if self._known_models or self._active_model != 'lmstudio-offline':
                        self._known_models = []
                        self._active_model = 'lmstudio-offline'
                        self._models_dirty = True
                return
            models = sorted(m.get('id', '') for m in models_payload.get('data', []) if m.get('id'))
            active = models[0] if models else None
            with self._lock:
                if models != self._known_models or active != self._active_model:
                    self._known_models = models
                    self._active_model = active
                    self._models_dirty = True
            return

        tags    = _ollama_get('/api/tags')
        ps      = _ollama_get('/api/ps')
        if tags is None:
            return  # Ollama unreachable; keep current state
        models  = sorted(
            n for n in (m['name'] for m in tags.get('models', []))
            if self._is_chat_model(n)
        )
        running = [m['name'] for m in (ps or {}).get('models', [])]
        active  = next((n for n in running if self._is_chat_model(n)), None)
        with self._lock:
            if models != self._known_models or active != self._active_model:
                self._known_models = models
                self._active_model = active
                self._models_dirty = True

    def _apply_model_menu(self):
        with self._lock:
            models = list(self._known_models)
            active = self._active_model
        backend = self._read_backend()

        for key in list(self._mi_model.keys()):
            del self._mi_model[key]

        if backend == 'lmstudio':
            if not models:
                self._mi_model.title = 'LM Studio: —'
                self._mi_model.add(rumps.MenuItem('(server offline or no model loaded)'))
                self._mi_model.add(None)
                self._mi_model.add(rumps.MenuItem('Refresh', callback=self._refresh_models_now))
                self._mi_model.add(rumps.MenuItem('Open LM Studio',
                                   callback=lambda _: subprocess.Popen(['open', '-a', 'LM Studio'])))
                return

            short = active.rsplit('/', 1)[-1].rsplit(':', 1)[0] if active else 'loaded'
            self._mi_model.title = f'LM Studio: {short}'
            for name in models:
                self._mi_model.add(rumps.MenuItem(f'✓  {name}' if name == active else f'    {name}'))
            self._mi_model.add(None)
            self._mi_model.add(rumps.MenuItem('Refresh', callback=self._refresh_models_now))
            self._mi_model.add(rumps.MenuItem('Open LM Studio',
                               callback=lambda _: subprocess.Popen(['open', '-a', 'LM Studio'])))
            return

        if not models:
            self._mi_model.title = 'Ollama: —'
            self._mi_model.add(rumps.MenuItem('(Ollama offline)'))
            self._mi_model.add(None)
            self._mi_model.add(rumps.MenuItem('Refresh', callback=self._refresh_models_now))
            return

        short = active.rsplit(':', 1)[0] if active else 'none'
        self._mi_model.title = f'Ollama: {short}'

        for name in models:
            label = f'✓  {name}' if name == active else f'    {name}'
            def make_cb(m):
                def cb(_):
                    self._mi_model.title = f'Ollama: ⏳ loading {m.rsplit(":", 1)[0]}…'
                    threading.Thread(target=self._switch_model, args=(m,), daemon=True).start()
                return cb
            self._mi_model[label] = rumps.MenuItem(label, callback=make_cb(name))

        self._mi_model.add(None)
        if active:
            self._mi_model.add(rumps.MenuItem(f'Unload {active}', callback=self._unload_active))
        self._mi_model.add(rumps.MenuItem('Refresh', callback=self._refresh_models_now))

    def _refresh_models_now(self, _):
        threading.Thread(target=self._fetch_models, daemon=True).start()

    def _unload_active(self, _):
        with self._lock:
            current = self._active_model
        if not current:
            return
        self._mi_model.title = f'Model: ⏳ unloading {current.rsplit(":", 1)[0]}…'
        def do():
            _ollama_post('/api/generate', {'model': current, 'keep_alive': 0})
            self._fetch_models()
        threading.Thread(target=do, daemon=True).start()

    def _switch_model(self, model):
        with self._lock:
            current = self._active_model
        if current == model:
            self._mi_model.title = f'Ollama: {model.rsplit(":", 1)[0]} (already loaded)'
            with self._lock:
                self._models_dirty = True
            return
        if current:
            _ollama_post('/api/generate', {'model': current, 'keep_alive': 0})
        result = _ollama_post('/api/generate', {
            'model': model, 'prompt': '', 'keep_alive': '1h', 'stream': False,
        })
        if result is not None:
            with self._lock:
                self._active_model = model
                self._models_dirty = True
        else:
            self._mi_model.title = f'Ollama: ⚠ failed to load {model.rsplit(":", 1)[0]}'
            self._fetch_models()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _start(self, _):
        def do():
            _ensure_exporter()
            _control('stack_start', self._token)
        threading.Thread(target=do, daemon=True).start()

    def _stop(self, _):
        threading.Thread(
            target=_control, args=('stack_stop', self._token), daemon=True
        ).start()

    def _off(self, _):
        def do():
            _control('stack_stop', self._token)
            time.sleep(3)
            subprocess.Popen(['zsh', '-c',
                'pkill -f "metrics-exporter.py" 2>/dev/null; '
                f'{PODMAN} stop local-ai-dashboard 2>/dev/null; '
                f'{PODMAN} machine stop 2>/dev/null'])
        threading.Thread(target=do, daemon=True).start()

    def _lmstudio_start(self, _):
        threading.Thread(
            target=_control, args=('lmstudio_start', self._token), daemon=True
        ).start()

    def _lmstudio_stop(self, _):
        threading.Thread(
            target=_control, args=('lmstudio_stop', self._token), daemon=True
        ).start()

    def _read_backend(self):
        try:
            return BACKEND_FILE.read_text().strip() or 'lmstudio'
        except Exception:
            return 'lmstudio'

    def _set_backend(self, backend):
        try:
            BACKEND_FILE.parent.mkdir(parents=True, exist_ok=True)
            BACKEND_FILE.write_text(backend + '\n')
            self._mi_backend.title = f'Runtime: {backend}'
            if backend == 'lmstudio':
                _control('ollama_stop', self._token)
                _control('lmstudio_start', self._token)
            else:
                _control('lmstudio_stop', self._token)
                _control('ollama_start', self._token)
            rumps.notification('Local-AI', 'Runtime switched',
                               f'Active runtime: {backend}. New shells will use this backend.',
                               sound=False)
            threading.Thread(target=self._fetch_models, daemon=True).start()
        except Exception as e:
            rumps.notification('Local-AI', 'Runtime switch failed', str(e), sound=False)


if __name__ == '__main__':
    LocalAIApp().run()
