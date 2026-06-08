---
name: lan-file-server
description: Create a local HTTP file server with upload/download/delete over WiFi LAN. Auto-detects LAN IP so other devices (phone, tablet, PCs) can browse, download, upload, and delete files. Features drag-and-drop upload, progress bar, and dark-themed web UI. Use when user wants to share files over local network, create a LAN file hub with upload support, or set up a simple HTTP file server with full CRUD.
---

# LAN File Hub — Download, Upload, Delete over WiFi

## Skill Overview

Deploy a Python-based HTTP file server that serves a modern web UI for browsing, downloading, **uploading**, and **deleting** files from a directory. The server **automatically detects the machine's LAN IP address**, so other devices on the same WiFi network can access the full file hub — no app needed, just a browser.

---

## Quick Start

1. Ask the user which directory to serve (default: current working directory).
2. Create `server.py` in that directory using the full template below.
3. Run `python server.py` — the LAN IP URL is printed on startup and browser opens automatically.
4. Other devices on the same WiFi open `http://<LAN_IP>:8080` to access the hub.

---

## Features

| Feature | Description |
|---------|-------------|
| 📥 **Download** | One-click download for any file |
| 📤 **Upload** | Click-to-browse or drag-and-drop, multi-file, progress bar |
| 🗑️ **Delete** | Delete button per file with confirmation |
| 🌐 **LAN Auto-Detect** | Automatically finds WiFi LAN IP, displays LAN URL |
| 🎨 **Dark UI** | Modern Tailwind-inspired dark theme |
| 🔄 **Auto-Refresh** | File list refreshes after upload/delete |
| 💬 **Toast Notifications** | Success/error feedback popups |
| 📏 **Size Limit** | Configurable max upload size (default 500 MB) |

---

## Server Script Template

Create `server.py` in the target directory:

```python
#!/usr/bin/env python3
"""
LAN File Server — browse, download, upload, delete over WiFi.
Auto-detects LAN IP, serves a modern web UI with drag-and-drop upload.
"""
import http.server
import os
import sys
import socket
import json
import threading
import webbrowser
from pathlib import Path
from datetime import datetime

# Fix Unicode on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PORT = 8080
ROOT = Path(__file__).parent
MAX_UPLOAD_MB = 500  # Max single file upload size in MB


def get_lan_ip() -> str:
    """Detect the LAN IP address by connecting a UDP socket."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


LAN_IP = get_lan_ip()
HOST = "0.0.0.0"

HTML = r"""\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>File Hub</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 40px 20px; }}
  .container {{ max-width: 800px; margin: 0 auto; }}
  h1 {{ font-size: 1.8rem; margin-bottom: 8px; color: #f1f5f9; }}
  .sub {{ color: #94a3b8; margin-bottom: 8px; font-size: 0.9rem; }}

  /* Info box */
  .info-box {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px;
              padding: 14px 20px; margin-bottom: 20px; font-size: 0.88rem; }}
  .info-box span {{ color: #94a3b8; }}
  .info-box code {{ color: #818cf8; font-size: 0.92rem; }}

  /* Upload zone */
  .upload-zone {{
    border: 2px dashed #334155; border-radius: 12px; padding: 28px 20px; text-align: center;
    margin-bottom: 20px; cursor: pointer; transition: border-color 0.2s, background 0.2s;
    position: relative; background: #1e293b;
  }}
  .upload-zone:hover, .upload-zone.drag-over {{ border-color: #6366f1; background: #1e293b80; }}
  .upload-zone.drag-over {{ border-color: #22c55e; background: #1e293b; }}
  .upload-icon {{ font-size: 2.5rem; margin-bottom: 8px; }}
  .upload-text {{ color: #94a3b8; font-size: 0.95rem; }}
  .upload-text strong {{ color: #c7d2fe; }}
  .upload-zone input[type=file] {{ position: absolute; inset: 0; opacity: 0; cursor: pointer; }}

  /* Upload progress */
  .progress-bar {{
    margin-top: 12px; height: 6px; background: #334155; border-radius: 3px;
    overflow: hidden; display: none;
  }}
  .progress-bar.active {{ display: block; }}
  .progress-fill {{ height: 100%; background: linear-gradient(90deg, #6366f1, #22c55e);
                    width: 0%; border-radius: 3px; transition: width 0.15s; }}

  /* File list */
  .section-title {{ font-size: 1rem; font-weight: 600; color: #94a3b8; margin-bottom: 10px;
                    display: flex; align-items: center; gap: 8px; }}
  .file-list {{ display: flex; flex-direction: column; gap: 8px; }}
  .file-item {{ display: flex; align-items: center; justify-content: space-between;
               background: #1e293b; border-radius: 10px; padding: 14px 20px;
               border: 1px solid #334155; transition: border-color 0.2s, background 0.2s;
               gap: 12px; }}
  .file-item:hover {{ border-color: #6366f1; }}
  .file-info {{ display: flex; align-items: center; gap: 14px; min-width: 0; flex: 1; }}
  .file-icon {{ font-size: 1.6rem; flex-shrink: 0; }}
  .file-name {{ font-weight: 600; font-size: 1.05rem; word-break: break-all; color: #f1f5f9; }}
  .file-meta {{ color: #94a3b8; font-size: 0.82rem; margin-top: 3px; }}

  /* Buttons */
  .btn-group {{ display: flex; gap: 8px; flex-shrink: 0; }}
  .btn {{ display: inline-flex; align-items: center; gap: 5px; padding: 8px 16px;
         border-radius: 8px; font-size: 0.88rem; font-weight: 600; border: none; cursor: pointer;
         text-decoration: none; white-space: nowrap; transition: all 0.2s; }}
  .btn-dl {{ background: #6366f1; color: #fff; }}
  .btn-dl:hover {{ background: #818cf8; transform: translateY(-1px); }}
  .btn-del {{ background: transparent; color: #ef4444; border: 1px solid #ef444420; }}
  .btn-del:hover {{ background: #ef4444; color: #fff; border-color: #ef4444; }}
  .btn-refresh {{ background: #334155; color: #94a3b8; border: none; }}
  .btn-refresh:hover {{ background: #475569; color: #e2e8f0; }}

  /* Toast */
  .toast-container {{ position: fixed; top: 20px; right: 20px; z-index: 9999;
                      display: flex; flex-direction: column; gap: 8px; }}
  .toast {{ padding: 12px 20px; border-radius: 10px; font-size: 0.9rem; font-weight: 600;
           color: #fff; animation: slideIn 0.3s ease; max-width: 360px;
           box-shadow: 0 4px 20px rgba(0,0,0,0.4); }}
  .toast.success {{ background: #16a34a; }}
  .toast.error {{ background: #dc2626; }}
  .toast.fade-out {{ animation: fadeOut 0.3s ease forwards; }}
  @keyframes slideIn {{ from {{ transform: translateX(120%); opacity: 0; }} to {{ transform: translateX(0); opacity: 1; }} }}
  @keyframes fadeOut {{ to {{ opacity: 0; transform: translateX(60px); }} }}

  .footer {{ margin-top: 36px; text-align: center; color: #475569; font-size: 0.8rem; }}

  /* Empty state */
  .empty {{ color: #475569; text-align: center; padding: 40px; font-size: 0.95rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>📦 File Hub</h1>
  <p class="sub">{file_count} file(s) · {total_size}</p>

  <div class="info-box">
    <span>🌐 LAN access:</span>
    <code>http://{lan_ip}:{port}</code>
  </div>

  <!-- Upload zone -->
  <div class="upload-zone" id="dropZone">
    <div class="upload-icon">📤</div>
    <div class="upload-text">
      <strong>Click to browse</strong> or drag &amp; drop files here<br>
      <span style="font-size:0.78rem;color:#64748b;">Max {max_upload} MB per file</span>
    </div>
    <input type="file" id="fileInput" multiple>
  </div>
  <div class="progress-bar" id="progressBar">
    <div class="progress-fill" id="progressFill"></div>
  </div>

  <!-- File list -->
  <div class="section-title">
    📋 Files
    <button class="btn btn-refresh" onclick="location.reload()" style="font-size:0.78rem;padding:4px 10px;">🔄 Refresh</button>
  </div>
  <div class="file-list" id="fileList">
{file_items}
  </div>
  <p class="footer">Powered by Python · <code>{lan_ip}:{port}</code></p>
</div>

<!-- Toast container -->
<div class="toast-container" id="toastContainer"></div>

<script>
const MAX_MB = {max_upload};
const MAX_BYTES = MAX_MB * 1024 * 1024;

// === Drag & Drop ===
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const progressBar = document.getElementById('progressBar');
const progressFill = document.getElementById('progressFill');

dropZone.addEventListener('dragover', e => {{
  e.preventDefault();
  dropZone.classList.add('drag-over');
}});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {{
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files);
}});
fileInput.addEventListener('change', () => {{
  if (fileInput.files.length) uploadFiles(fileInput.files);
}});

async function uploadFiles(files) {{
  const total = files.length;
  let ok = 0, fail = 0;

  for (let i = 0; i < total; i++) {{
    const f = files[i];
    if (f.size > MAX_BYTES) {{
      toast(`❌ "${{f.name}}" exceeds ${{MAX_MB}} MB limit`, 'error');
      fail++;
      continue;
    }}

    // Show progress
    progressBar.classList.add('active');
    progressFill.style.width = '0%';

    const formData = new FormData();
    formData.append('file', f);

    try {{
      const xhr = new XMLHttpRequest();
      await new Promise((resolve, reject) => {{
        xhr.upload.addEventListener('progress', e => {{
          if (e.lengthComputable) {{
            const pct = Math.round((e.loaded / e.total) * 100);
            progressFill.style.width = pct + '%';
          }}
        }});
        xhr.addEventListener('load', () => {{
          if (xhr.status === 200) resolve();
          else reject(new Error(xhr.responseText || 'Upload failed'));
        }});
        xhr.addEventListener('error', () => reject(new Error('Network error')));
        xhr.open('POST', '/upload');
        xhr.send(formData);
      }});
      ok++;
    }} catch(err) {{
      toast(`❌ "${{f.name}}": ${{err.message}}`, 'error');
      fail++;
    }}
  }}

  progressBar.classList.remove('active');
  fileInput.value = '';

  if (ok > 0) toast(`✅ ${{ok}} file(s) uploaded successfully`, 'success');
  if (fail > 0) toast(`⚠️ ${{fail}} file(s) failed`, 'error');

  // Refresh file list after a short delay
  setTimeout(() => location.reload(), 600);
}}

// === Delete ===
async function deleteFile(name) {{
  if (!confirm(`Delete "${{name}}" ?`)) return;
  try {{
    const r = await fetch('/' + encodeURIComponent(name), {{ method: 'DELETE' }});
    if (r.ok) {{
      toast(`🗑️ "${{name}}" deleted`, 'success');
      setTimeout(() => location.reload(), 400);
    }} else {{
      const msg = await r.text();
      toast(`❌ ${{msg}}`, 'error');
    }}
  }} catch(err) {{
    toast(`❌ Delete failed: ${{err.message}}`, 'error');
  }}
}}

// === Toast ===
function toast(msg, type) {{
  const container = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => {{
    el.classList.add('fade-out');
    setTimeout(() => el.remove(), 300);
  }}, 3000);
}}
</script>
</body>
</html>"""

ITEM_TMPL = """\
    <div class="file-item">
      <div class="file-info">
        <span class="file-icon">{icon}</span>
        <div>
          <div class="file-name">{name}</div>
          <div class="file-meta">{size} · {mtime}</div>
        </div>
      </div>
      <div class="btn-group">
        <a class="btn btn-dl" href="{url}" download>⬇</a>
        <button class="btn btn-del" onclick="deleteFile('{name_escaped}')">🗑️</button>
      </div>
    </div>"""


def get_icon(name: str) -> str:
    ext = Path(name).suffix.lower()
    return {
        ".zip": "📦", ".rar": "📦", ".7z": "📦", ".tar": "📦", ".gz": "📦",
        ".pdf": "📄", ".doc": "📝", ".docx": "📝", ".txt": "📝", ".md": "📝",
        ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️", ".gif": "🖼️", ".webp": "🖼️",
        ".mp4": "🎬", ".avi": "🎬", ".mkv": "🎬", ".mov": "🎬",
        ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵",
        ".py": "🐍", ".js": "📜", ".html": "🌐", ".css": "🎨",
        ".exe": "⚙️", ".msi": "⚙️", ".deb": "⚙️", ".rpm": "⚙️",
        ".iso": "💿", ".img": "💿",
    }.get(ext, "📁")


def fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} PB"


def fmt_time(t: int) -> str:
    return datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")


def collect_files():
    """Return list of file dicts in ROOT, excluding server.py."""
    files = []
    total = 0
    for p in sorted(ROOT.iterdir()):
        if p.name == "server.py":
            continue
        if p.is_file():
            st = p.stat()
            total += st.st_size
            files.append({
                "name": p.name,
                "url": "/" + p.name,
                "size": fmt_size(st.st_size),
                "mtime": fmt_time(st.st_mtime),
                "icon": get_icon(p.name),
                "name_escaped": p.name.replace("'", "\\'").replace('"', '&quot;'),
            })
    return files, total


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/" or path == "/index.html":
            self.send_html()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/upload":
            self.handle_upload()
        else:
            self.send_error(404, "Not found")

    def do_DELETE(self):
        """Delete a file."""
        path = self.path.split("?")[0]
        filename = path.lstrip("/")

        if not filename:
            self.send_error(400, "No filename specified")
            return

        # Security: prevent path traversal
        safe_name = Path(filename).name
        if safe_name != filename or safe_name == "server.py":
            self.send_error(403, "Forbidden")
            return

        filepath = ROOT / safe_name
        if not filepath.exists():
            self.send_error(404, "File not found")
            return
        if not filepath.is_file():
            self.send_error(400, "Not a file")
            return

        try:
            filepath.unlink()
            self.send_json({"ok": True, "deleted": safe_name})
            print(f"[{datetime.now().strftime('%H:%M:%S')}] DELETED: {safe_name}")
        except Exception as e:
            self.send_error(500, str(e))

    def handle_upload(self):
        """Handle multipart file upload."""
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_error(400, "Expected multipart/form-data")
            return

        # Parse multipart form data
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > MAX_UPLOAD_MB * 1024 * 1024:
                self.send_error(413, f"File too large (max {MAX_UPLOAD_MB} MB)")
                return

            # Read boundaries and parse
            body = self.rfile.read(content_length)

            # Extract boundary from Content-Type
            boundary = None
            for part in content_type.split(";"):
                part = part.strip()
                if part.startswith("boundary="):
                    boundary = part[9:].strip('"').encode()
                    break

            if not boundary:
                self.send_error(400, "No boundary found")
                return

            # Split by boundary
            parts = body.split(b"--" + boundary)
            saved_files = []

            for part in parts:
                if b"--" in part[:4] or not part.strip():
                    continue

                # Split headers from body
                if b"\r\n\r\n" in part:
                    header_section, file_data = part.split(b"\r\n\r\n", 1)
                else:
                    continue

                file_data = file_data.rstrip(b"\r\n").rstrip(b"--")

                # Parse headers for filename
                headers_text = header_section.decode("utf-8", errors="replace")
                filename = None
                for line in headers_text.split("\r\n"):
                    if "filename=" in line:
                        start = line.find('filename="')
                        if start >= 0:
                            start += 10
                            end = line.find('"', start)
                            if end >= 0:
                                filename = line[start:end]
                        break

                if not filename or not file_data:
                    continue

                # Security: strip path, keep only basename
                safe_name = Path(filename).name
                if not safe_name or safe_name == "server.py":
                    continue

                # Handle duplicate names
                dest = ROOT / safe_name
                counter = 1
                stem, ext = os.path.splitext(safe_name)
                while dest.exists():
                    dest = ROOT / f"{stem} ({counter}){ext}"
                    counter += 1

                dest.write_bytes(file_data)
                saved_files.append(dest.name)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] UPLOADED: {dest.name} ({fmt_size(len(file_data))})")

            if saved_files:
                self.send_json({"ok": True, "files": saved_files})
            else:
                self.send_error(400, "No valid files found in upload")

        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            self.send_error(500, f"Upload error: {e}")

    def send_html(self):
        files, total_size = collect_files()

        items = "\n".join(ITEM_TMPL.format(**f) for f in files)

        html = HTML.format(
            file_count=len(files),
            total_size=fmt_size(total_size),
            file_items=items if files else '<div class="empty">📭 No files yet — drop some here!</div>',
            lan_ip=LAN_IP,
            port=PORT,
            max_upload=MAX_UPLOAD_MB,
        )

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def main():
    os.chdir(ROOT)

    lan_url = f"http://{LAN_IP}:{PORT}"
    local_url = f"http://localhost:{PORT}"

    print(f"  📂 Serving: {ROOT}")
    print(f"  🖥️  Local:   {local_url}")
    print(f"  🌐 Network: {lan_url}")
    print(f"  📤 Upload max: {MAX_UPLOAD_MB} MB")
    print(f"  Press Ctrl+C to stop.\n")

    threading.Timer(1.0, lambda: webbrowser.open(lan_url)).start()

    with http.server.ThreadingHTTPServer((HOST, PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped.")


if __name__ == "__main__":
    main()
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | HTML file hub page |
| `GET` | `/<filename>` | Download file |
| `POST` | `/upload` | Upload file(s) via multipart form |
| `DELETE` | `/<filename>` | Delete a file |

### Upload (POST /upload)

- Content-Type: `multipart/form-data`
- Field name: `file` (can include multiple)
- Response: `{"ok": true, "files": ["uploaded_name.txt"]}`
- Max size: configurable via `MAX_UPLOAD_MB`

### Delete (DELETE /filename)

- Response: `{"ok": true, "deleted": "filename.txt"}`
- Protected: cannot delete `server.py`

---

## Configuration

### Port

```python
PORT = 9090  # Change from default 8080
```

### Max Upload Size

```python
MAX_UPLOAD_MB = 200  # Change from default 500 MB
```

### Exclude Extra Files

```python
if p.name in ("server.py", ".gitignore", "secret.txt"):
    continue
```

---

## How It Works

### LAN IP Detection

`get_lan_ip()` creates a UDP socket and "connects" to `8.8.8.8:80` — no data is sent, but the OS resolves the local interface for that route. The socket's `getsockname()` returns the LAN IP.

### Multipart Upload Parsing

Since Python 3.14 removed the `cgi` module, the server manually parses `multipart/form-data`:
1. Extract boundary from `Content-Type` header
2. Split body by boundary markers
3. Parse `Content-Disposition` header for filename
4. Extract binary payload between headers and next boundary
5. Handle duplicate names by appending `(1)`, `(2)`, etc.

### Security

- Binds to `0.0.0.0` — think before exposing to public networks
- Path traversal prevented: only basename is used from uploaded filenames
- `server.py` is protected from deletion and excluded from file listing
- Upload size limit enforced server-side

---

## Troubleshooting

### "Address already in use"

```bash
# Windows: find and kill the process
netstat -ano | findstr :8080
taskkill /f /pid <PID>
```

Or change `PORT` in the script.

### Other devices can't connect

1. Must be on same WiFi network
2. Windows Firewall may block:
   ```bash
   netsh advfirewall firewall add rule name="Python HTTP" dir=in action=allow program="C:\path\to\python.exe" enable=yes
   ```

### Upload fails silently

Check console for `[ERROR] Upload failed:` messages. Common causes:
- File exceeds `MAX_UPLOAD_MB` limit
- Multipart boundary parsing issue (check browser compatibility)

### Unicode errors on Windows console

The script includes a `sys.stdout.reconfigure` fix. Alternatively:
```bash
chcp 65001
python server.py
```
