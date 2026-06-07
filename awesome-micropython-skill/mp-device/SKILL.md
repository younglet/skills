---
name: mp-device
description: MicroPython device interaction toolkit via mpremote. Device info, memory monitoring, WiFi setup, project scaffolding, REPL, file transfer, and diagnosis. Sub-skill of awesome-micropython-skill — not shown in skill list.
disable-model-invocation: true
---

# mp-device — MicroPython Device Toolkit

Interactive debugging and development tool for MicroPython devices via [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html).

## Quick Reference

| Command | Description |
|---------|-------------|
| `mpremote devs` | List connected devices |
| `mpremote connect COM1` | Connect to device on COM1 |
| `mpremote repl` | Open interactive REPL |
| `mpremote run script.py` | Run a local script on device |
| `mpremote fs ls` | List files on device |
| `mpremote fs cp local.py :remote.py` | Copy file to device |
| `mpremote fs cp :remote.py local.py` | Copy file from device |
| `mpremote fs rm :file.py` | Delete file on device |
| `mpremote exec "print(42)"` | Execute a one-liner |
| `mpremote soft-reset` | Soft reset the device |

## Convenience Scripts

Ready-to-run Python scripts that wrap common mpremote workflows. All take `<PORT>` as first argument.

| Script | Usage | Description |
|--------|-------|-------------|
| `scripts/device-info.py` | `python scripts/device-info.py COM3` | Full system report + cache to `device.json` |
| `scripts/device-info.py` | `python scripts/device-info.py COM3 --json` | JSON output for agent/script consumption |
| `scripts/device-info.py` | `python scripts/device-info.py COM3 --cache .` | Cache to `./device.json`, skip if <5min old |
| `scripts/mem-monitor.py` | `python scripts/mem-monitor.py COM3` | One-shot memory snapshot (free/alloc/used%) |
| `scripts/mem-monitor.py` | `python scripts/mem-monitor.py COM3 --watch 5` | Live memory monitor every 5s |
| `scripts/mem-monitor.py` | `python scripts/mem-monitor.py COM3 --run main.py` | Measure memory impact of running a script |
| `scripts/wifi-setup.py` | `python scripts/wifi-setup.py COM3` | Interactive scan → connect → optional persist |
| `scripts/wifi-setup.py` | `python scripts/wifi-setup.py COM3 --ssid X --password Y --persist --json` | Agent-driven, JSON output |
| `scripts/project-init.py` | `python scripts/project-init.py my-esp32-project` | Scaffold standard MP project from template |
| `scripts/verify-api.py` | `python scripts/verify-api.py COM3` | Full dir() verification of all api/ JSONs |
| `scripts/verify-api.py` | `python scripts/verify-api.py COM3 --fix` | Auto-fix stale JSON entries from device diff |

## Standard Project Template

Scaffolded by `project-init.py`. Structure:

```
my-project/
├── README.md
├── device.json          # Cached device info (device-info.py --cache)
├── .gitignore
└── src/
    ├── boot.py          # Runs on every boot (WiFi, imports, one-time setup)
    ├── main.py          # Application entry point
    └── lib/             # Third-party modules (import directly, no 'lib.' prefix)
```

## Setup

mpremote is bundled with MicroPython and available after `pip install mpremote`.

## First-Time Detection

Always start by identifying the device port:

```bash
mpremote devs
```

| Platform | Typical Port |
|----------|-------------|
| Windows | `COM3`, `COM4` |
| macOS | `/dev/cu.usbmodem*`, `/dev/cu.wchusbserial*` |
| Linux | `/dev/ttyACM0`, `/dev/ttyUSB0` |

## Debug Workflows

### 1. Interactive REPL Debugging

Open a REPL session to inspect variables, test code snippets, and explore the system:

```bash
mpremote connect COM3 repl
```

Inside REPL, use `Ctrl+C` to interrupt running code, `Ctrl+D` for soft reset.

### 2. Run a Script

Execute a local Python file on the device without copying it permanently:

```bash
mpremote connect COM3 run ./main.py
```

### 3. Inspect Device Filesystem

```bash
# List all files
mpremote connect COM3 fs ls

# Recursive listing
mpremote connect COM3 fs ls -r /
```

### 4. Transfer Files

```bash
# Upload to device
mpremote connect COM3 fs cp ./main.py :main.py

# Download from device
mpremote connect COM3 fs cp :boot.py ./backup/boot.py

# Bulk upload (mount workflow)
mpremote connect COM3 mount . exec "import your_module"
```

### 5. Execute Commands Without REPL

```bash
# Print system info
mpremote connect COM3 exec "import sys; print(sys.implementation)"

# Check free memory
mpremote connect COM3 exec "import gc; print(gc.mem_free())"

# List built-in modules
mpremote connect COM3 exec "help('modules')"
```

### 6. Soft Reset

```bash
mpremote connect COM3 soft-reset
```

## Common Issues

- **Permission denied (Linux)**: Add user to `dialout` group: `sudo usermod -a -G dialout $USER`
- **Port busy**: Close other serial terminal programs (PuTTY, Arduino IDE Serial Monitor, screen, etc.)
- **Device not responding**: Press the RST/EN button on the board, or try `mpremote bootloader`
- **Import errors**: Ensure the module is on the device; use `mpremote mip install <package>` to install micropython-lib packages

## Error Diagnosis Protocol

When MicroPython code fails on the ESP32, use these commands to diagnose:

### Check what's on the device
```bash
mpremote connect COM3 fs ls /
mpremote connect COM3 fs ls /lib/
```

### Test an import directly
```bash
mpremote connect COM3 exec "import mymodule; print(dir(mymodule))"
mpremote connect COM3 exec "import nonexistent" 2>&1
```

### Inspect a class API at runtime
```bash
mpremote connect COM3 exec "from machine import Pin; print(dir(Pin))"
mpremote connect COM3 exec "import network; print(dir(network.WLAN))"
```

### Check memory
```bash
mpremote connect COM3 exec "import gc; gc.collect(); print('Free:', gc.mem_free())"
```

### Check sys.path (where imports search)
```bash
mpremote connect COM3 exec "import sys; print(sys.path)"
```

### Self-Correction for awesome-micropython-skill skill

If an API call fails (AttributeError, ImportError, TypeError), verify the API by:
1. Run `mpremote connect COM3 exec "<test expression>"` to check the actual API on the device
2. Read the corresponding `awesome-micropython-skill/api/<module>.json` file
3. If the JSON is wrong, edit it to match the actual device behavior
4. If this is a new edge case, add a `notes` or `edge_cases` entry to the JSON
5. Run `mpremote connect COM3 exec "help('modules')"` to see what's actually built in
