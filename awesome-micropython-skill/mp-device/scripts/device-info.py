#!/usr/bin/env python3
"""
device-info.py — Full ESP32 health check with local caching.
Usage:
  python device-info.py <PORT>              # Full report (fresh from device)
  python device-info.py <PORT> --cache DIR  # Save to DIR/device.json, skip if recent
  python device-info.py <PORT> --json       # JSON output only (for scripts/agent)

Cache file format (device.json):
  {"port": "COM3", "timestamp": "2026-06-07T22:00:00",
   "firmware": "MicroPython v1.28.0", "platform": "esp32",
   "cpu_freq_hz": 160000000, "flash_bytes": 4194304,
   "heap_free": 165168, "heap_alloc": 1424, "heap_total": 166592,
   "mac": "24:0a:c4:...", "files": ["boot.py", "main.py", ...]}
"""

import subprocess, sys, json, os
from datetime import datetime, timezone

def run(port, code, timeout=10):
    wrapped = ""
    for line in code.strip().split("\n"):
        wrapped += f"    {line}\n"
    wrapped = f"try:\n{wrapped}except Exception as e:\n    print('ERROR:', e)"
    try:
        r = subprocess.run(
            ["mpremote", "connect", port, "exec", wrapped],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except Exception as e:
        return f"FAILED: {e}"

def collect(port):
    """Collect all device info, return dict."""
    info = {"port": port, "timestamp": datetime.now(timezone.utc).isoformat()}

    # Firmware
    out = run(port, "import sys; print(sys.version); print(sys.platform)")
    lines = out.split("\n")
    info["firmware"] = lines[0].strip() if lines else ""
    info["platform"] = lines[1].strip() if len(lines) > 1 else ""

    # Hardware
    out = run(port, "import machine, esp; print(machine.freq()); print(esp.flash_size())")
    parts = out.split()
    if len(parts) >= 2:
        try: info["cpu_freq_hz"] = int(parts[0])
        except: info["cpu_freq_hz"] = 0
        try: info["flash_bytes"] = int(parts[1])
        except: info["flash_bytes"] = 0

    # Memory
    out = run(port, "import gc; gc.collect(); print(gc.mem_free(), gc.mem_alloc())")
    parts = out.split()
    if len(parts) >= 2:
        try:
            info["heap_free"] = int(parts[0])
            info["heap_alloc"] = int(parts[1])
            info["heap_total"] = info["heap_free"] + info["heap_alloc"]
        except: pass

    # MAC
    out = run(port, "import network, binascii; w=network.WLAN(); m=w.config('mac'); print(binascii.hexlify(m,':').decode())")
    if out and "ERROR" not in out and "FAILED" not in out:
        info["mac"] = out.strip()

    # Files
    out = run(port, "import os; print(os.listdir('/'))")
    if out and "ERROR" not in out:
        try:
            info["files"] = eval(out) if out.startswith("[") else out.split(",")
        except:
            info["files"] = out

    return info

def print_report(info):
    """Human-readable report."""
    sep = "=" * 55
    print(sep)
    print(f"  DEVICE: {info.get('mac', 'N/A')}  ({info.get('port', '?')})")
    print(sep)
    print(f"  Firmware:  {info.get('firmware', '?')}")
    print(f"  Platform:  {info.get('platform', '?')}")
    print(f"  CPU freq:  {info.get('cpu_freq_hz', 0):,} Hz".replace(",", "_").replace("_", ","))
    print(f"  Flash:     {info.get('flash_bytes', 0) // 1024:,} KB".replace(",", "_").replace("_", ","))
    print(f"  Heap free: {info.get('heap_free', 0):,} bytes".replace(",", "_").replace("_", ","))
    print(f"  Heap used: {info.get('heap_alloc', 0):,} bytes".replace(",", "_").replace("_", ","))
    print(f"  MAC:       {info.get('mac', 'N/A')}")
    files = info.get("files", [])
    if isinstance(files, list):
        print(f"  Files (/): {', '.join(str(f) for f in files[:20])}")
    print(f"  Cached:    {info.get('timestamp', '?')}")

def load_cache(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ESP32 device info with caching")
    parser.add_argument("port", help="Serial port")
    parser.add_argument("--cache", metavar="DIR", help="Save/load from DIR/device.json")
    parser.add_argument("--json", action="store_true", help="JSON output only")
    parser.add_argument("--force", action="store_true", help="Skip cache, always query device")
    args = parser.parse_args()

    cache_path = os.path.join(args.cache, "device.json") if args.cache else None

    # Try cache
    if not args.force and cache_path:
        cached = load_cache(cache_path)
        if cached:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(cached["timestamp"])).total_seconds()
            if age < 300:  # 5-minute cache
                if args.json:
                    print(json.dumps(cached, indent=2))
                else:
                    print_report(cached)
                    print(f"\n  (cached {age:.0f}s ago, use --force to refresh)")
                return

    # Collect from device
    info = collect(args.port)

    # Save cache
    if cache_path:
        os.makedirs(args.cache, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(info, f, indent=2)

    if args.json:
        print(json.dumps(info, indent=2))
    else:
        print_report(info)

if __name__ == "__main__":
    main()
