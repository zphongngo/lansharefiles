#!/usr/bin/env python3
"""
LAN File Transfer — GUI Edition (Improved)
Requires Python 3.8+ with tkinter (standard on Windows/macOS, install python3-tk on Linux)
"""
import http.server
import socket
import os
import io
import sys
import json
import zipfile
import threading
import urllib.parse
import mimetypes
import secrets
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
import webbrowser

try:
    import winreg
except ImportError:
    winreg = None

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    sys.exit("tkinter is required. On Linux run: sudo apt install python3-tk")

# ─────────────────────────────────────────────────────────────────────────────
# HTML Templates (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAN Transfer</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
  :root{--bg:#0f1117;--surface:#181c27;--border:#262d3f;--accent:#4f8ef7;--accent-dim:#1e2d4f;--green:#3ecf8e;--green-dim:#0d2e20;--red:#f7614f;--text:#e2e8f0;--muted:#64748b;--mono:'IBM Plex Mono',monospace;--sans:'IBM Plex Sans',sans-serif}
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:14px;min-height:100vh}
  header{border-bottom:1px solid var(--border);padding:16px 28px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:var(--bg);z-index:10}
  .logo{font-family:var(--mono);font-weight:600;font-size:15px;color:var(--accent);letter-spacing:.04em;display:flex;align-items:center;gap:8px}
  .logo-icon{width:28px;height:28px;background:var(--accent);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:14px}
  .server-info{font-family:var(--mono);font-size:12px;color:var(--muted)}
  .server-info span{color:var(--green)}
  main{max-width:860px;margin:0 auto;padding:32px 24px}
  .upload-zone{border:2px dashed var(--border);border-radius:12px;padding:40px 24px;text-align:center;cursor:pointer;transition:border-color .2s,background .2s;margin-bottom:28px;position:relative}
  .upload-zone:hover,.upload-zone.drag{border-color:var(--accent);background:var(--accent-dim)}
  .upload-zone input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
  .upload-icon{font-size:32px;margin-bottom:10px}
  .upload-zone p{color:var(--muted);font-size:13px;margin-top:6px}
  .upload-zone strong{color:var(--text);font-size:15px}
  #progress-wrap{display:none;margin-bottom:20px}
  .progress-bar-bg{height:6px;background:var(--border);border-radius:99px;overflow:hidden}
  .progress-bar-fill{height:100%;background:var(--accent);border-radius:99px;transition:width .2s;width:0%}
  .progress-label{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11px;color:var(--muted);margin-bottom:6px}
  #toast{position:fixed;bottom:28px;right:28px;background:var(--surface);border:1px solid var(--border);padding:12px 18px;border-radius:8px;font-size:13px;display:none;z-index:100;box-shadow:0 8px 32px rgba(0,0,0,.4)}
  #toast.ok{border-color:var(--green);color:var(--green)}
  #toast.err{border-color:var(--red);color:var(--red)}
  .section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
  .section-title{font-family:var(--mono);font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
  .count-badge{background:var(--border);color:var(--muted);font-family:var(--mono);font-size:11px;padding:2px 8px;border-radius:99px}
  .btn-zip{background:none;border:1px solid var(--border);color:var(--muted);font-family:var(--mono);font-size:11px;padding:4px 12px;border-radius:6px;cursor:pointer;transition:border-color .15s,color .15s}
  .btn-zip:hover{border-color:var(--accent);color:var(--accent)}
  .file-table{width:100%;border-collapse:collapse}
  .file-table th{font-family:var(--mono);font-size:11px;color:var(--muted);text-align:left;padding:6px 10px;border-bottom:1px solid var(--border);text-transform:uppercase;letter-spacing:.06em}
  .file-table td{padding:10px 10px;vertical-align:middle}
  .file-row{border-bottom:1px solid var(--border);transition:background .12s}
  .file-row:hover{background:var(--surface)}
  .file-row:last-child{border-bottom:none}
  .file-name{font-family:var(--mono);font-size:13px;display:flex;align-items:center;gap:8px}
  .file-ext{font-size:10px;background:var(--border);color:var(--muted);padding:1px 6px;border-radius:4px;text-transform:uppercase;letter-spacing:.05em;flex-shrink:0}
  .file-size{color:var(--muted);font-family:var(--mono);font-size:12px}
  .file-date{color:var(--muted);font-size:12px}
  .dl-btn{background:none;border:1px solid var(--border);color:var(--muted);font-size:12px;padding:4px 12px;border-radius:6px;cursor:pointer;text-decoration:none;display:inline-block;transition:all .15s;font-family:var(--mono)}
  .dl-btn:hover{border-color:var(--green);color:var(--green);background:var(--green-dim)}
  .empty-state{text-align:center;padding:48px 24px;color:var(--muted);font-size:13px}
  .empty-state .icon{font-size:36px;margin-bottom:12px}
  .qr-hint{margin-top:32px;border:1px solid var(--border);border-radius:10px;padding:16px 20px;display:flex;gap:16px;align-items:center}
  .qr-hint canvas{flex-shrink:0}
  .qr-info p{color:var(--muted);font-size:12px;margin-top:4px}
  .qr-url{font-family:var(--mono);font-size:13px;color:var(--accent);word-break:break-all}
  @media(max-width:600px){.file-table .file-date,.file-table th:nth-child(3){display:none}header{padding:12px 16px}main{padding:20px 14px}}
</style>
</head>
<body>
<header>
  <div class="logo"><div class="logo-icon">⇄</div>LAN Transfer</div>
  <div class="server-info">serving <span>{{ROOT}}</span> · <span>{{LAN_URL}}</span></div>
</header>
<main>
  <div class="upload-zone" id="dropzone">
    <input type="file" id="fileInput" multiple>
    <div class="upload-icon">📁</div>
    <strong>Drop files here or click to upload</strong>
    <p>Files are saved to the shared folder</p>
  </div>
  <div id="progress-wrap">
    <div class="progress-label"><span id="progress-name">Uploading…</span><span id="progress-pct">0%</span></div>
    <div class="progress-bar-bg"><div class="progress-bar-fill" id="progress-fill"></div></div>
  </div>
  <div class="section-header">
    <span class="section-title">Shared files</span>
    <div style="display:flex;gap:8px;align-items:center;">
      <span class="count-badge" id="file-count">0</span>
      <button class="btn-zip" id="btn-zip">⬇ Download all as ZIP</button>
    </div>
  </div>
  <div id="file-list-wrap">
    <div class="empty-state"><div class="icon">📂</div><p>No files yet — upload something above</p></div>
  </div>
  <div class="qr-hint" id="qr-hint">
    <canvas id="qr-canvas" width="80" height="80"></canvas>
    <div class="qr-info">
      <div class="qr-url" id="qr-url"></div>
      <p>Scan from any device on this Wi-Fi network</p>
    </div>
  </div>
</main>
<div id="toast"></div>
<script>
function drawQR(canvas,url){const ctx=canvas.getContext('2d');ctx.fillStyle='#181c27';ctx.fillRect(0,0,80,80);const img=new Image();img.crossOrigin='anonymous';img.onload=()=>{ctx.clearRect(0,0,80,80);ctx.drawImage(img,0,0,80,80)};img.src=`https://api.qrserver.com/v1/create-qr-code/?size=80x80&data=${encodeURIComponent(url)}&bgcolor=0f1117&color=4f8ef7&margin=2`}
const LAN_URL="{{LAN_URL}}";
document.getElementById('qr-url').textContent=LAN_URL;
drawQR(document.getElementById('qr-canvas'),LAN_URL);
let toastTimer;
function toast(msg,type='ok'){const el=document.getElementById('toast');el.textContent=msg;el.className=type;el.style.display='block';clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.style.display='none',3000)}
function formatSize(b){if(b<1024)return b+' B';if(b<1024**2)return(b/1024).toFixed(1)+' KB';if(b<1024**3)return(b/1024**2).toFixed(1)+' MB';return(b/1024**3).toFixed(2)+' GB'}
function ext(n){const p=n.lastIndexOf('.');return p>0?n.slice(p+1):'—'}
async function loadFiles(){try{const r=await fetch('/api/files');const files=await r.json();const wrap=document.getElementById('file-list-wrap');document.getElementById('file-count').textContent=files.length;if(!files.length){wrap.innerHTML='<div class="empty-state"><div class="icon">📂</div><p>No files yet — upload something above</p></div>';return}const rows=files.map(f=>`<tr class="file-row"><td class="file-name"><span class="file-ext">${ext(f.name)}</span>${f.name}</td><td class="file-size">${formatSize(f.size)}</td><td class="file-date">${f.modified}</td><td><a class="dl-btn" href="/download/${encodeURIComponent(f.name)}">↓ Save</a></td></tr>`).join('');wrap.innerHTML=`<table class="file-table"><thead><tr><th>Name</th><th>Size</th><th>Modified</th><th></th></tr></thead><tbody>${rows}</tbody></table>`}catch(e){console.error(e)}}
async function uploadFile(file){const wrap=document.getElementById('progress-wrap');const fill=document.getElementById('progress-fill');const name=document.getElementById('progress-name');const pct=document.getElementById('progress-pct');wrap.style.display='block';name.textContent=file.name;return new Promise((resolve,reject)=>{const xhr=new XMLHttpRequest();xhr.open('POST',`/upload/${encodeURIComponent(file.name)}`);xhr.upload.onprogress=e=>{if(e.lengthComputable){const p=Math.round(e.loaded/e.total*100);fill.style.width=p+'%';pct.textContent=p+'%'}};xhr.onload=()=>{wrap.style.display='none';fill.style.width='0%';if(xhr.status===200)resolve();else reject(new Error(xhr.responseText))};xhr.onerror=()=>{wrap.style.display='none';reject(new Error('Network error'))};xhr.send(file)})}
async function handleFiles(files){for(const file of files){try{await uploadFile(file);toast(`✓ ${file.name} uploaded`);loadFiles()}catch(e){toast(`✗ ${file.name}: ${e.message}`,'err')}}}
document.getElementById('fileInput').addEventListener('change',e=>{handleFiles([...e.target.files]);e.target.value=''});
const zone=document.getElementById('dropzone');
zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('drag')});
zone.addEventListener('dragleave',()=>zone.classList.remove('drag'));
zone.addEventListener('drop',e=>{e.preventDefault();zone.classList.remove('drag');handleFiles([...e.dataTransfer.files])});
document.getElementById('btn-zip').addEventListener('click',()=>{window.location.href='/download-all'});
loadFiles();setInterval(loadFiles,5000);
</script>
</body>
</html>
"""
LOGIN_HTML = """
<!doctype html>
<html>
<body style="
background:#0f1117;
color:white;
font-family:sans-serif;
display:flex;
justify-content:center;
align-items:center;
height:100vh;
">
<form method="POST" action="/login">
    <h2>LAN Transfer Login</h2>

    <input
        type="password"
        name="password"
        placeholder="Password"
        style="padding:10px;width:250px;"
    >

    <br><br>

    <button type="submit">
        Login
    </button>

</form>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Global state (managed by GUI)
# ─────────────────────────────────────────────────────────────────────────────
SESSIONS = {}
APP_PASSWORD = "80810812"   # will be overwritten by config
_log_callback = None        # set by GUI

# ─────────────────────────────────────────────────────────────────────────────
# HTTP Server Handler (enhanced error handling)
# ─────────────────────────────────────────────────────────────────────────────
class LanHandler(http.server.BaseHTTPRequestHandler):
    ROOT: Path = Path(".")

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {self.client_address[0]}  {fmt % args}"
        if _log_callback:
            _log_callback(line)

    def do_GET(self):
        p = urllib.parse.unquote(self.path)
        if p == "/login":
            return self._serve_login()
        if p != "/favicon.ico" and not self._is_authenticated():
            self.send_response(302)
            self.send_header("Location", "/login")
            self.end_headers()
            return
        if p in ("/", "/index.html"):
            return self._serve_html()
        if p == "/api/files":
            return self._serve_file_list()
        if p == "/download-all":
            return self._serve_zip()
        if p.startswith("/download/"):
            return self._serve_file(p[len("/download/"):])
        self.send_error(404, "Not found")

    def do_POST(self):
        p = urllib.parse.unquote(self.path)
        if p == "/login":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            params = urllib.parse.parse_qs(body)
            password = params.get("password", [""])[0]
            if password == APP_PASSWORD:
                token = secrets.token_hex(32)
                SESSIONS[token] = True
                self.send_response(302)
                self.send_header("Set-Cookie", f"session={token}; Path=/")
                self.send_header("Location", "/")
                self.end_headers()
            else:
                self.send_error(403, "Invalid password")
            return
        if p.startswith("/upload/"):
            return self._receive_upload(p[len("/upload/"):])
        self.send_error(404, "Not found")

    def _serve_login(self):
        data = LOGIN_HTML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_html(self):
        ip = get_local_ip()
        port = self.server.server_address[1]
        page = (HTML
                .replace("{{ROOT}}", str(self.ROOT))
                .replace("{{LAN_URL}}", f"http://{ip}:{port}"))
        data = page.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_file_list(self):
        files = []
        for p in sorted(self.ROOT.iterdir()):
            if p.is_file() and not p.name.startswith("."):
                s = p.stat()
                files.append({
                    "name": p.name,
                    "size": s.st_size,
                    "modified": datetime.fromtimestamp(s.st_mtime).strftime("%b %d, %H:%M"),
                })
        data = json.dumps(files).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_file(self, name):
        safe = Path(name).name
        target = self.ROOT / safe
        if not target.is_file():
            return self.send_error(404, "File not found")
        try:
            mime, _ = mimetypes.guess_type(str(target))
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{safe}"')
            self.send_header("Content-Length", str(target.stat().st_size))
            self.end_headers()
            with open(target, "rb") as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def _serve_zip(self):
        # Build zip in memory – for many/large files consider streaming
        buf = io.BytesIO()
        files = [p for p in self.ROOT.iterdir() if p.is_file() and not p.name.startswith(".")]
        if not files:
            self.send_error(404, "No files to zip")
            return
        try:
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for p in files:
                    zf.write(p, p.name)
            data = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="transfer.zip"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, f"ZIP error: {e}")

    def _receive_upload(self, name):
        safe = Path(name).name
        if not safe:
            return self.send_error(400, "Invalid filename")
        length = int(self.headers.get("Content-Length", 0))
        target = self.ROOT / safe
        try:
            with open(target, "wb") as f:
                remaining = length
                while remaining > 0:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
        except Exception as e:
            self.send_error(500, f"Upload failed: {e}")

    def _is_authenticated(self):
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("session="):
                token = part.split("=", 1)[1]
                return token in SESSIONS
        return False

# ─────────────────────────────────────────────────────────────────────────────
# Network helpers (unchanged, but with improved docstrings)
# ─────────────────────────────────────────────────────────────────────────────
def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_all_local_ips() -> list[str]:
    ips = set()
    primary = get_local_ip()
    if primary != "127.0.0.1":
        ips.add(primary)
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            addr = info[4][0]
            if not addr.startswith("127."):
                ips.add(addr)
    except Exception:
        pass
    try:
        import psutil
        for addrs in psutil.net_if_addrs().values():
            for a in addrs:
                if a.family == socket.AF_INET and not a.address.startswith("127."):
                    ips.add(a.address)
    except ImportError:
        pass
    return sorted(ips) if ips else ["127.0.0.1"]

# ─────────────────────────────────────────────────────────────────────────────
# Firewall helpers (enhanced with fallback and threading)
# ─────────────────────────────────────────────────────────────────────────────
APP_NAME = "LANFileTransfer"

def add_firewall_rule(port: int) -> bool:
    """Attempt to open the port in the OS firewall. Returns success."""
    rule_name = f"{APP_NAME}_{port}"
    if sys.platform == "win32":
        try:
            check = subprocess.run(
                ["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name}"],
                capture_output=True, text=True
            )
            if "No rules match" in check.stdout or check.returncode != 0:
                add = subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule",
                     f"name={rule_name}", "dir=in", "action=allow",
                     "protocol=TCP", f"localport={port}"],
                    capture_output=True, text=True
                )
                return add.returncode == 0
            return True
        except Exception:
            return False
    elif sys.platform.startswith("linux"):
        # Try ufw, then firewall-cmd (firewalld)
        for cmd in [["ufw", "allow", f"{port}/tcp"],
                    ["firewall-cmd", "--add-port", f"{port}/tcp", "--permanent"]]:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    # If using firewalld, reload
                    if "firewall-cmd" in cmd[0]:
                        subprocess.run(["firewall-cmd", "--reload"], capture_output=True)
                    return True
            except FileNotFoundError:
                continue
            except Exception:
                continue
        return False
    elif sys.platform == "darwin":
        # macOS: no scriptable firewall rule addition; assume success
        return True
    return False

def remove_firewall_rule(port: int) -> bool:
    rule_name = f"{APP_NAME}_{port}"
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}"],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    elif sys.platform.startswith("linux"):
        # Try both removal methods
        for cmd in [["ufw", "delete", "allow", f"{port}/tcp"],
                    ["firewall-cmd", "--remove-port", f"{port}/tcp", "--permanent"]]:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    if "firewall-cmd" in cmd[0]:
                        subprocess.run(["firewall-cmd", "--reload"], capture_output=True)
                    return True
            except FileNotFoundError:
                continue
            except Exception:
                continue
        return False
    return True

# ─────────────────────────────────────────────────────────────────────────────
# Startup (Windows only)
# ─────────────────────────────────────────────────────────────────────────────
STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

def _get_startup_script_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return str(Path(sys.argv[0]).resolve())

def set_startup(enable: bool) -> bool:
    if winreg is None:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
        if enable:
            cmd = f'"{sys.executable}" "{_get_startup_script_path()}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def get_startup() -> bool:
    if winreg is None:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

# ─────────────────────────────────────────────────────────────────────────────
# Config Manager
# ─────────────────────────────────────────────────────────────────────────────
CONFIG_FILE = "config.json"

@dataclass
class AppConfig:
    folder: str = str(Path.home() / "Downloads")
    port: int = 8000
    password: str = "123456"
    startup: bool = True

def load_config() -> tuple[AppConfig, bool]:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return AppConfig(**data), False
    except Exception:
        return AppConfig(), True

def save_config(cfg: AppConfig):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(asdict(cfg), f, indent=2)

# ─────────────────────────────────────────────────────────────────────────────
# GUI Application
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg":      "#0f1117",
    "surface": "#181c27",
    "border":  "#262d3f",
    "accent":  "#4f8ef7",
    "green":   "#3ecf8e",
    "red":     "#f7614f",
    "text":    "#e2e8f0",
    "muted":   "#64748b",
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LAN File Transfer")
        self.resizable(False, False)
        self.configure(bg=C["bg"])

        self._server = None
        self._server_thread = None
        self._running = False
        self._fw_port = None

        # Load config
        self.cfg, first_run = load_config()
        global APP_PASSWORD
        APP_PASSWORD = self.cfg.password

        self._folder = tk.StringVar(value=self.cfg.folder)
        self._port = tk.StringVar(value=str(self.cfg.port))
        self._startup = tk.BooleanVar(value=self.cfg.startup)
        self._password = tk.StringVar(value=self.cfg.password)

        # On first run, set startup if requested
        if first_run and self.cfg.startup:
            if not set_startup(True):
                self.cfg.startup = False
                self._startup.set(False)
            save_config(self.cfg)

        # Trace for auto-save and dynamic password update
        self._folder.trace_add("write", lambda *_: self._save_settings())
        self._port.trace_add("write", lambda *_: self._save_settings())
        self._startup.trace_add("write", lambda *_: self._save_settings())
        self._password.trace_add("write", self._on_password_change)

        self._build_ui()
        self._update_status(False)

        global _log_callback
        _log_callback = self._append_log

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        pad = dict(padx=16, pady=8)

        # Header
        hdr = tk.Frame(self, bg=C["surface"], pady=12)
        hdr.pack(fill="x")
        logo_box = tk.Frame(hdr, bg=C["accent"], width=32, height=32)
        logo_box.pack(side="left", padx=(16, 8))
        logo_box.pack_propagate(False)
        tk.Label(logo_box, text="⇄", bg=C["accent"], fg="white",
                 font=("Segoe UI", 14, "bold")).pack(expand=True)
        tk.Label(hdr, text="LAN File Transfer", bg=C["surface"],
                 fg=C["accent"], font=("Consolas", 13, "bold")).pack(side="left")

        # Status pill
        self._status_dot = tk.Label(hdr, text="●", bg=C["surface"], font=("Segoe UI", 11))
        self._status_label = tk.Label(hdr, text="Stopped", bg=C["surface"],
                                      fg=C["muted"], font=("Segoe UI", 10))
        self._status_label.pack(side="right", padx=(0, 16))
        self._status_dot.pack(side="right", padx=(0, 4))

        # Settings frame
        sf = tk.Frame(self, bg=C["bg"], padx=16, pady=14)
        sf.pack(fill="x")

        # Folder row
        tk.Label(sf, text="Shared folder", bg=C["bg"], fg=C["muted"],
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        folder_row = tk.Frame(sf, bg=C["bg"])
        folder_row.grid(row=1, column=0, sticky="ew", pady=(2, 10))
        sf.columnconfigure(0, weight=1)

        self._folder_entry = tk.Entry(
            folder_row, textvariable=self._folder, width=46,
            bg=C["surface"], fg=C["text"], insertbackground=C["text"],
            relief="flat", font=("Consolas", 10),
            highlightthickness=1, highlightbackground=C["border"],
            highlightcolor=C["accent"]
        )
        self._folder_entry.pack(side="left", fill="x", expand=True, ipady=5, ipadx=6)
        self._browse_btn = tk.Button(
            folder_row, text="Browse…", command=self._browse,
            bg=C["surface"], fg=C["muted"], activebackground=C["border"],
            activeforeground=C["text"], relief="flat",
            font=("Segoe UI", 9), cursor="hand2",
            highlightthickness=1, highlightbackground=C["border"],
            pady=5, padx=10
        )
        self._browse_btn.pack(side="left", padx=(6, 0))

        # Port row
        port_row = tk.Frame(sf, bg=C["bg"])
        port_row.grid(row=2, column=0, sticky="w", pady=(0, 10))
        tk.Label(port_row, text="Port", bg=C["bg"], fg=C["muted"],
                 font=("Segoe UI", 9)).pack(side="left")

        # Port entry with validation
        vcmd = (self.register(self._validate_port), '%P')
        self._port_entry = tk.Entry(
            port_row, textvariable=self._port, width=6,
            bg=C["surface"], fg=C["text"], insertbackground=C["text"],
            relief="flat", font=("Consolas", 10),
            highlightthickness=1, highlightbackground=C["border"],
            highlightcolor=C["accent"],
            validate="key", validatecommand=vcmd
        )
        self._port_entry.pack(side="left", padx=(8, 0), ipady=4, ipadx=4)

        # Password row
        pwd_row = tk.Frame(sf, bg=C["bg"])
        pwd_row.grid(row=3, column=0, sticky="w", pady=(0, 10))
        tk.Label(pwd_row, text="Access Password", bg=C["bg"], fg=C["muted"],
                 font=("Segoe UI", 9)).pack(side="left")
        self._pwd_entry = tk.Entry(
            pwd_row, textvariable=self._password, show="*", width=20,
            bg=C["surface"], fg=C["text"], insertbackground=C["text"],
            relief="flat", font=("Consolas", 10),
            highlightthickness=1, highlightbackground=C["border"],
            highlightcolor=C["accent"]
        )
        self._pwd_entry.pack(side="left", padx=(8, 0), ipady=4, ipadx=4)
        # Show/hide toggle
        self._show_pwd = tk.Button(
            pwd_row, text="👁", command=self._toggle_password_visibility,
            bg=C["surface"], fg=C["muted"], relief="flat",
            cursor="hand2", padx=4, pady=2
        )
        self._show_pwd.pack(side="left", padx=(4, 0))

        # URL display
        self._url_var = tk.StringVar(value="—")
        tk.Label(port_row, text="Network URL:", bg=C["bg"], fg=C["muted"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(20, 4))
        self._url_label = tk.Label(
            port_row, textvariable=self._url_var,
            bg=C["bg"], fg=C["accent"], font=("Consolas", 10),
            cursor="hand2"
        )
        self._url_label.pack(side="left")
        self._url_label.bind("<Button-1>", self._open_browser)

        # Startup checkbox (Windows only)
        if sys.platform == "win32":
            startup_row = tk.Frame(sf, bg=C["bg"])
            startup_row.grid(row=4, column=0, sticky="w", pady=(0, 4))
            self._cb = tk.Checkbutton(
                startup_row,
                text="Start automatically when Windows starts",
                variable=self._startup,
                command=self._toggle_startup,
                bg=C["bg"], fg=C["text"],
                selectcolor=C["surface"],
                activebackground=C["bg"], activeforeground=C["text"],
                font=("Segoe UI", 9),
                cursor="hand2"
            )
            self._cb.pack(side="left")

        # Extra IPs row
        ips_row = tk.Frame(sf, bg=C["bg"])
        ips_row.grid(row=5, column=0, sticky="w", pady=(4, 0))
        tk.Label(ips_row, text="Other addresses:", bg=C["bg"], fg=C["muted"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self._extra_ips_var = tk.StringVar(value="—")
        self._extra_ips_label = tk.Label(
            ips_row, textvariable=self._extra_ips_var,
            bg=C["bg"], fg=C["muted"], font=("Consolas", 9), wraplength=420,
            justify="left"
        )
        self._extra_ips_label.pack(side="left")

        # Divider
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # Start/Stop button
        btn_frame = tk.Frame(self, bg=C["bg"], pady=14)
        btn_frame.pack(fill="x", padx=16)
        self._toggle_btn = tk.Button(
            btn_frame, text="▶  Start Server",
            command=self._toggle_server,
            bg=C["accent"], fg="white",
            activebackground="#3a6fd8", activeforeground="white",
            relief="flat", font=("Segoe UI", 10, "bold"),
            cursor="hand2", pady=8, padx=24,
            highlightthickness=0
        )
        self._toggle_btn.pack(side="left")
        self._open_btn = tk.Button(
            btn_frame, text="🌐  Open in Browser",
            command=self._open_browser,
            bg=C["surface"], fg=C["muted"],
            activebackground=C["border"], activeforeground=C["text"],
            relief="flat", font=("Segoe UI", 10),
            cursor="hand2", pady=8, padx=16,
            highlightthickness=1, highlightbackground=C["border"],
            state="disabled"
        )
        self._open_btn.pack(side="left", padx=(8, 0))

        # Log box
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")
        log_hdr = tk.Frame(self, bg=C["surface"], pady=6)
        log_hdr.pack(fill="x")
        tk.Label(log_hdr, text="ACTIVITY LOG", bg=C["surface"], fg=C["muted"],
                 font=("Consolas", 8), padx=16).pack(side="left")
        tk.Button(log_hdr, text="Clear", command=self._clear_log,
                  bg=C["surface"], fg=C["muted"],
                  activebackground=C["border"], activeforeground=C["text"],
                  relief="flat", font=("Segoe UI", 8), cursor="hand2",
                  padx=8).pack(side="right", padx=8)

        log_frame = tk.Frame(self, bg=C["bg"])
        log_frame.pack(fill="both", expand=True, padx=0)
        self._log = tk.Text(
            log_frame, height=10, width=64,
            bg=C["bg"], fg=C["muted"],
            insertbackground=C["text"],
            relief="flat", font=("Consolas", 9),
            state="disabled", wrap="none",
            padx=16, pady=10,
            highlightthickness=0
        )
        sb = tk.Scrollbar(log_frame, command=self._log.yview,
                          bg=C["border"], troughcolor=C["bg"], relief="flat")
        self._log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log.pack(side="left", fill="both", expand=True)

        self._log.tag_config("ts", foreground=C["border"])
        self._log.tag_config("green", foreground=C["green"])
        self._log.tag_config("red", foreground=C["red"])
        self._log.tag_config("accent", foreground=C["accent"])

    # ── Actions ───────────────────────────────────────────────────────────────
    def _validate_port(self, value):
        if value == "":
            return True
        try:
            port = int(value)
            return 1 <= port <= 65535
        except ValueError:
            return False

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self._folder.get(),
                                    title="Select folder to share")
        if d:
            self._folder.set(d)
            self._save_settings()

    def _toggle_startup(self):
        ok = set_startup(self._startup.get())
        if not ok:
            messagebox.showwarning(
                "Startup",
                "Could not update Windows startup registry.\n"
                "Try running the app as Administrator."
            )
            self._startup.set(not self._startup.get())  # revert
        self._save_settings()

    def _toggle_password_visibility(self):
        if self._pwd_entry.cget("show") == "*":
            self._pwd_entry.config(show="")
            self._show_pwd.config(text="🙈")
        else:
            self._pwd_entry.config(show="*")
            self._show_pwd.config(text="👁")

    def _on_password_change(self, *args):
        """Update global APP_PASSWORD and save config."""
        global APP_PASSWORD
        APP_PASSWORD = self._password.get()
        self._save_settings()

    def _toggle_server(self):
        if self._running:
            self._stop_server()
        else:
            self._start_server()
            self._save_settings()

    def _start_server(self):
        global APP_PASSWORD
        APP_PASSWORD = self._password.get()

        folder = Path(self._folder.get()).resolve()
        try:
            port = int(self._port.get())
        except ValueError:
            messagebox.showerror("Invalid port", "Port must be a number between 1 and 65535.")
            return

        if not folder.exists():
            folder.mkdir(parents=True)

        LanHandler.ROOT = folder

        try:
            self._server = http.server.ThreadingHTTPServer(("0.0.0.0", port), LanHandler)
        except OSError as e:
            messagebox.showerror("Cannot start", str(e))
            return

        self._server_thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()
        self._running = True
        self._fw_port = port

        # Firewall rule in background
        def add_fw():
            if add_firewall_rule(port):
                self._append_log(f"Firewall: allowed inbound TCP port {port}.", tag="accent")
            else:
                self._append_log(
                    f"Firewall: could not auto-configure port {port} "
                    "(may need to run as Administrator, or allow it manually).",
                    tag="red"
                )
        threading.Thread(target=add_fw, daemon=True).start()

        ip = get_local_ip()
        url = f"http://{ip}:{port}"
        self._url_var.set(url)

        all_ips = [a for a in get_all_local_ips() if a != ip]
        if all_ips:
            self._extra_ips_var.set(", ".join(f"{a}:{port}" for a in all_ips))
        else:
            self._extra_ips_var.set("—")

        self._update_status(True)
        self._append_log(f"Server started → {url}", tag="green")
        self._append_log(f"Sharing: {folder}", tag="accent")

    def _stop_server(self):
        if self._server:
            threading.Thread(target=self._server.shutdown, daemon=True).start()
            self._server = None
        if self._fw_port is not None:
            # Background removal
            threading.Thread(target=remove_firewall_rule, args=(self._fw_port,), daemon=True).start()
            self._fw_port = None
        self._running = False
        self._url_var.set("—")
        self._extra_ips_var.set("—")
        self._update_status(False)
        self._append_log("Server stopped.", tag="red")

    def _update_status(self, running: bool):
        if running:
            self._status_dot.config(fg=C["green"], text="●")
            self._status_label.config(text="Running", fg=C["green"])
            self._toggle_btn.config(text="■  Stop Server", bg=C["red"],
                                    activebackground="#c0392b")
            self._open_btn.config(state="normal", fg=C["text"])
            self._folder_entry.config(state="disabled")
            self._port_entry.config(state="disabled")
            self._browse_btn.config(state="disabled")
            if sys.platform == "win32":
                self._cb.config(state="disabled")
        else:
            self._status_dot.config(fg=C["muted"], text="●")
            self._status_label.config(text="Stopped", fg=C["muted"])
            self._toggle_btn.config(text="▶  Start Server", bg=C["accent"],
                                    activebackground="#3a6fd8")
            self._open_btn.config(state="disabled", fg=C["muted"])
            self._folder_entry.config(state="normal")
            self._port_entry.config(state="normal")
            self._browse_btn.config(state="normal")
            if sys.platform == "win32":
                self._cb.config(state="normal")

    def _open_browser(self, _event=None):
        if not self._running:
            return
        webbrowser.open(self._url_var.get())

    # ── Config persistence ────────────────────────────────────────────────────
    def _save_settings(self):
        self.cfg.folder = self._folder.get()
        try:
            self.cfg.port = int(self._port.get())
        except ValueError:
            pass
        self.cfg.startup = self._startup.get()
        self.cfg.password = self._password.get()
        save_config(self.cfg)

    # ── Log helpers ──────────────────────────────────────────────────────────
    def _append_log(self, line: str, tag: str = ""):
        def _do():
            self._log.config(state="normal")
            self._log.insert("end", line + "\n", tag or ())
            self._log.see("end")
            self._log.config(state="disabled")
        self.after(0, _do)

    def _clear_log(self):
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")

    # ── Window close ──────────────────────────────────────────────────────────
    def _on_close(self):
        if self._running:
            if not messagebox.askyesno("Quit", "Server is running. Stop it and quit?"):
                return
            self._stop_server()
        self.destroy()

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def _ensure_windows_admin():
    """Relaunch the app with administrator privileges when needed."""
    if sys.platform != "win32":
        return True

    try:
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True

        executable = sys.executable
        arguments = sys.argv[1:] if getattr(sys, "frozen", False) else sys.argv
        parameters = subprocess.list2cmdline(arguments)
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, parameters, None, 1
        )
        if result <= 32:
            messagebox.showerror(
                "Administrator privileges required",
                "LAN Transfer needs administrator permission to open firewall port 8000."
            )
        return False
    except Exception as exc:
        messagebox.showerror("Unable to elevate", str(exc))
        return False


if __name__ == "__main__":
    if not _ensure_windows_admin():
        sys.exit(0)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except Exception:
            pass
    app = App()
    app.mainloop()