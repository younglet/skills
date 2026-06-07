#!/usr/bin/env python3
"""
wifi-setup.py — ESP32 WiFi configuration. Interactive mode or agent-driven via args.
Usage:
  # Interactive (prompts user):
  python wifi-setup.py COM3

  # Agent-driven (no prompts):
  python wifi-setup.py COM3 --ssid MyWiFi --password pass123
  python wifi-setup.py COM3 --ssid MyWiFi --password pass123 --hostname esp32-livingroom
  python wifi-setup.py COM3 --ssid MyWiFi --password pass123 --persist  # save to boot.py
"""

import subprocess, sys, json

def mpremote(port, code, timeout=15):
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

def scan(port):
    """Scan Wi-Fi networks. Returns list of {ssid, rssi, channel, security}."""
    out = mpremote(port,
        "import network; w=network.WLAN(network.STA_IF); w.active(True); "
        "nets=w.scan(); "
        "for n in sorted(nets, key=lambda x: -x[3])[:20]: "
        "    print(f'{n[3]}|{n[2]}|{n[4]}|{n[0].decode()}')",
        timeout=15
    )
    results = []
    for line in out.split("\n"):
        parts = line.strip().split("|", 3)
        if len(parts) == 4:
            results.append({"rssi": int(parts[0]), "channel": int(parts[1]),
                          "security": int(parts[2]), "ssid": parts[3]})
    return results

def connect(port, ssid, password, hostname=None):
    """Connect to Wi-Fi. Returns dict with success/ip or error."""
    code = (
        "import network, time; "
        "w=network.WLAN(network.STA_IF); "
        "w.active(True); "
    )
    if hostname:
        code += f"network.hostname('{hostname}'); "
    code += (
        f"w.connect('{ssid}', '{password}'); "
        "for i in range(30): "
        "    if w.isconnected(): break; "
        "    time.sleep(0.5); "
        "if w.isconnected(): "
        "    print(w.ifconfig()[0]); "
        "    print(w.ifconfig()[2]); "
        "    print(w.ifconfig()[3]); "
        "else: "
        "    print('FAILED')"
    )
    out = mpremote(port, code, timeout=20)
    lines = out.strip().split("\n")
    if lines and lines[-1] == "FAILED":
        return {"connected": False, "error": "Connection timed out"}
    if len(lines) >= 3:
        return {"connected": True, "ip": lines[0], "gateway": lines[1], "dns": lines[2]}
    return {"connected": False, "error": out}

def persist_to_boot(port, ssid, password, hostname=None):
    """Write WiFi config to device boot.py."""
    snippet = (
        "# Auto-generated WiFi config\n"
        "import network, time\n"
        "wlan = network.WLAN(network.STA_IF)\n"
        "wlan.active(True)\n"
    )
    if hostname:
        snippet += f"network.hostname('{hostname}')\n"
    snippet += (
        f"wlan.connect('{ssid}', '{password}')\n"
        "for _ in range(30):\n"
        "    if wlan.isconnected(): break\n"
        "    time.sleep(0.5)\n"
        "if wlan.isconnected():\n"
        "    print(f'WiFi OK: {wlan.ifconfig()[0]}')\n"
        "else:\n"
        "    print('WiFi FAILED')\n"
    )
    import tempfile, os
    tmp = tempfile.mktemp(suffix=".py")
    with open(tmp, "w") as f:
        f.write(snippet)
    subprocess.run(["mpremote", "connect", port, "fs", "cp", tmp, ":boot.py"],
                   capture_output=True)
    os.remove(tmp)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ESP32 WiFi setup")
    parser.add_argument("port", help="Serial port")
    parser.add_argument("--ssid", help="WiFi SSID")
    parser.add_argument("--password", help="WiFi password")
    parser.add_argument("--hostname", help="Device hostname (optional)")
    parser.add_argument("--persist", action="store_true", help="Save to boot.py")
    parser.add_argument("--json", action="store_true", help="JSON output for agent consumption")
    args = parser.parse_args()

    ssid = args.ssid
    password = args.password

    if not ssid:
        # Interactive mode
        print("Scanning Wi-Fi networks...")
        nets = scan(args.port)
        for n in nets:
            print(f"  {n['rssi']:>4}dBm  CH:{n['channel']:>2}  {n['ssid']}")

        ssid = input("\nSSID: ").strip()
        if not ssid:
            print("Cancelled.")
            return
        password = input("Password: ").strip()
        hostname = input("Hostname (optional): ").strip() or None
        persist = input("Save to boot.py? [y/N]: ").strip().lower() == 'y'
    else:
        if not password:
            print("Error: --password required when using --ssid", file=sys.stderr)
            sys.exit(1)
        hostname = args.hostname
        persist = args.persist

    print(f"\nConnecting to '{ssid}'...")
    result = connect(args.port, ssid, password, hostname)

    if args.json:
        print(json.dumps(result))
    elif result["connected"]:
        print(f"Connected!")
        print(f"  IP:      {result['ip']}")
        print(f"  Gateway: {result['gateway']}")
        print(f"  DNS:     {result['dns']}")
    else:
        print(f"Failed: {result.get('error', 'unknown')}")
        sys.exit(1)

    if persist:
        persist_to_boot(args.port, ssid, password, hostname)
        print("WiFi config saved to boot.py")

if __name__ == "__main__":
    main()
