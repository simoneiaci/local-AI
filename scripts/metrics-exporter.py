#!/usr/bin/env python3
"""
Local-AI Metrics Exporter — runs on the HOST Mac.
Writes /tmp/ai-metrics.json every 3 seconds for the dashboard container to read.
No external dependencies — uses only stdlib + macOS built-ins.
"""
import subprocess, json, re, time, shutil, os

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
        # Total RAM from sysctl
        out = subprocess.check_output(['sysctl', 'hw.memsize'], text=True)
        total_bytes = int(re.search(r'hw.memsize:\s*(\d+)', out).group(1))
        total_gb = round(total_bytes / 1024**3, 1)

        # Used RAM from vm_stat
        out = subprocess.check_output(['vm_stat'], text=True)
        page_size = int(re.search(r'page size of (\d+) bytes', out).group(1))

        def pages(key):
            m = re.search(rf'{key}:\s+(\d+)', out)
            return int(m.group(1)) if m else 0

        active   = pages('Pages active')
        wired    = pages('Pages wired down')
        occupied = pages('Pages occupied by compressor')
        used_gb  = round((active + wired + occupied) * page_size / 1024**3, 1)
        return {'used_gb': used_gb, 'total_gb': total_gb,
                'pct': round(used_gb / total_gb * 100, 1)}
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
    status = {}

    # Ollama
    try:
        import urllib.request
        urllib.request.urlopen('http://localhost:11434', timeout=2)
        status['ollama'] = 'up'
    except Exception:
        status['ollama'] = 'down'

    # Open WebUI
    try:
        urllib.request.urlopen('http://localhost:3000', timeout=2)
        status['open_webui'] = 'up'
    except Exception:
        status['open_webui'] = 'down'

    # Tailscale
    try:
        out = subprocess.check_output(['tailscale', 'status', '--json'],
                                      text=True, timeout=3)
        data = json.loads(out)
        status['tailscale'] = 'up' if data.get('BackendState') == 'Running' else 'down'
        status['tailscale_ip'] = ''
        self_node = data.get('Self', {})
        ips = self_node.get('TailscaleIPs', [])
        if ips:
            status['tailscale_ip'] = ips[0]
    except Exception:
        status['tailscale'] = 'down'
        status['tailscale_ip'] = ''

    # Podman machine
    try:
        out = subprocess.check_output(
            ['podman', 'machine', 'list', '--format', '{{.Running}}'],
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

OUT = '/tmp/ai-metrics.json'

if __name__ == '__main__':
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
