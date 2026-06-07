---
name: awesome-micropython-skill
description: Complete MicroPython v1.28.0 ESP32 development toolkit — API reference (53 verified JSONs), hardware driver recipes, firmware flashing, device verification, bootstrapping. Use for all ESP32 MicroPython coding, debugging, and project setup.
requires: mp-device
---

# awesome-micropython-skill — ESP32 MicroPython Development Toolkit

End-to-end ESP32 MicroPython development: from firmware flashing to API reference to hardware drivers to production cleanup.

## Architecture

```
awesome-micropython-skill/
│
├── SKILL.md                     ← You are here (architecture + self-correction + warnings)
│
├── api/                         ← [STABLE] 53 device-verified API JSONs
│   ├── README.md                    JSON structure, verification status, usage guide
│   ├── index.json                   Full module index
│   ├── import-guide.json            Critical import rules (u-prefix, lib/, epoch)
│   ├── builtin-types.json           CPython missing methods (91 gaps)
│   └── <module>.json (×49)         Per-module: functions, classes, constants, pitfalls
│
├── hardware/                    ← [GROWING] Electronic component drivers + pinout
│   ├── index.json                   5 categories, 20+ components
│   ├── esp32-pinout.json             ESP32 / C3 / S3 — every GPIO, ADC, touch, restrictions
│   ├── led.json                     GPIO/PWM LED + built-in LED
│   ├── servo.json                   50Hz PWM servo + external power warning
│   └── motor.json                   L298N DC motor + class wrapper
│
├── patterns/                    ← [STABLE] Reusable code architecture patterns
│   ├── index.json                   6 patterns cataloged
│   ├── wifi-reconnect.json          Non-blocking WiFi + auto-reconnect + WDT safe
│   ├── nonblocking-loop.json        Replace sleep() with ticks_ms() scheduler
│   └── sensor-read.json             Timeout + retry + graceful degradation
│
├── pitfalls.json                ← [SELF-HEALING] Error → ranked fixes with upvote/downvote
├── performance.json             ← [STABLE] Time and memory cost reference
│
├── firmware/                    ← [PLANNED] Firmware management
│   ├── cache/                       Downloaded .bin files keyed by board + version
│   └── flash.py                     Erase + flash with esptool, validate checksum
│
├── drivers/                     ← [GROWING] Community driver index (awesome-micropython.com)
│   ├── index.json                   Category index with git-clone + analyze workflow
│   ├── display.json                 OLED/TFT/e-Paper/LCD drivers (7 chips)
│   ├── sensor.json                  Temp/IMU/distance/gas/light/current (20+ chips)
│   ├── actuator.json                Motors, servos, relays
│   ├── storage.json                 SD, EEPROM, FRAM, databases
│   ├── communication.json           GPS, RFID, NFC, CAN, radio
│   ├── audio.json                   I2S DAC/ADC, MP3, speech
│   ├── power.json                   Battery, PMIC, energy monitoring
│   ├── utility.json                 Logging, scheduling, config
│   └── cache/                       Git-cloned driver repos (offline analysis)
│
└── mp-device/                   ← [STABLE] Sub-skill: device interaction
    ├── SKILL.md                     REPL, file transfer, diagnosis protocol
    └── scripts/
        ├── device-info.py           Full report + --json + --cache to device.json
        ├── mem-monitor.py           Snapshot / --watch / --run impact
        ├── wifi-setup.py            Interactive / --ssid --password --json (agent)
        ├── project-init.py          Scaffold standard MP project from template
        ├── verify-api.py            Full dir() verification of all api/ JSONs + --fix
        └── template/                src/{boot.py,main.py,lib/} + README + .gitignore
```

## Capability Map

| Capability | Status | Entry Point |
|-----------|--------|------------|
| API lookup (module functions, classes, methods) | ✅ Stable | `api/<module>.json` |
| Import validation (no `u` prefix, no `lib.` prefix) | ✅ Stable | `api/import-guide.json` |
| Type method validation (str/bytes/int/float gaps) | ✅ Stable | `api/builtin-types.json` |
| Device verification (dir() diff) | ✅ Stable | `python mp-device/scripts/verify-api.py <PORT>` |
| Auto-fix stale JSON entries | ✅ Stable | `python mp-device/scripts/verify-api.py <PORT> --fix` |
| Device diagnosis (info, memory, WiFi) | ✅ Stable | `mp-device/scripts/` |
| Project scaffolding | ✅ Stable | `python mp-device/scripts/project-init.py <name>` |
| Hardware driver lookup | ✅ Growing | `hardware/index.json` + `hardware/<component>.json` |
| Hardware driver authoring | ✅ Growing | Follow `led.json`/`servo.json`/`motor.json` format |
| Code patterns (WiFi, loop, sensor) | ✅ Stable | `patterns/` — copy-paste recipes |
| Error diagnosis + ranked fixes | ✅ Self-healing | `pitfalls.json` — upvote/downvote fixes |
| Performance reference (time + memory) | ✅ Stable | `performance.json` — ISR safety, costs |
| Community driver lookup (display, sensor, storage...) | ✅ Growing | `drivers/<category>.json` — 30+ drivers from awesome-micropython.com |
| ESP32 pinout reference (C3/S3) | ✅ Stable | `hardware/esp32-pinout.json` — every GPIO, ADC, touch |
| Firmware flashing | 📋 Planned | `firmware/flash.py` + `firmware/cache/` |

## Platform Compatibility

All scripts and mpremote commands work on **Windows, macOS, and Linux**. The only platform-specific detail is the serial port:

| Platform | Port Example | Detection |
|----------|-------------|-----------|
| Windows | `COM3`, `COM4` | `mpremote devs` |
| macOS | `/dev/cu.usbmodem01` | `ls /dev/cu.*` |
| Linux | `/dev/ttyACM0`, `/dev/ttyUSB0` | `ls /dev/tty*` |

## CRITICAL Import Rules

### 1. NEVER use `u` prefix modules — use standard Python names

The `u` prefix (`ujson`, `urequests`, `utime`, `urandom`, etc.) is **DEPRECATED and FORBIDDEN** in all code you generate.

```python
# FORBIDDEN — NEVER write these:
import urequests, ujson, ure, ustruct, ucollections, urandom
import usocket, uhashlib, uio, ubinascii, utime, uselect, uasyncio
import ubluetooth, ucryptolib
from urequests import get, post
from ujson import dumps, loads
from utime import sleep, ticks_ms

# REQUIRED — always use standard names:
import requests, json, re, struct, collections, random
import socket, hashlib, io, binascii, time, select, asyncio
import bluetooth, cryptolib
from requests import get, post
from json import dumps, loads
from time import sleep, ticks_ms
```

### 2. lib/ directory files do NOT use `lib.` prefix

```python
# WRONG:
import lib.mymodule
import lib.requests

# CORRECT:
import mymodule
import requests
```

Files in `/lib/` are on `sys.path` directly. The directory name `lib` is NOT a Python package namespace.

## Self-Healing: pitfalls.json Voting

`pitfalls.json` is a **self-improving error database**. Each error has ranked fixes with upvote/downvote counts:

```json
"OSError: [Errno 110] ETIMEDOUT": {
  "fixes": [
    {"action": "Re-initialize I2C", "upvotes": 5, "downvotes": 0},
    {"action": "Check pull-up resistors", "upvotes": 2, "downvotes": 1}
  ]
}
```

**When you apply a fix:**
- It works → **upvote it** (increment `upvotes`)
- It fails → **downvote it** (increment `downvotes`)

Over time, the most reliable fixes per error/device/version rise to the top. Fixes with (upvotes - downvotes) < -3 should be deprecated.

## Performance Reference

`performance.json` contains timing and memory costs for common operations — use it to decide: can this run in an ISR? will it fit in memory?

## Self-Correction Protocol

When you encounter an error in MicroPython code (import fails, AttributeError, TypeError, etc.), follow this procedure:

### Step 1: Check the relevant JSON file

Read `api/<module>.json` and verify: function/method/class name, parameter names/order/types, import syntax, ESP32-specific notes.

### Step 2: If the JSON is wrong — FIX IT

If the JSON file contains incorrect information (wrong function name, missing method, wrong type, wrong default value), **immediately edit the JSON file to correct it**. Never leave wrong API data.

### Step 3: If the issue is complex or edge-case — ADD notes

Add a new note under `esp32_notes` or `edge_cases` for complex interactions, timing issues, memory quirks, or hardware-specific behavior.

### Step 4: Verify with the ESP32 if possible

```bash
mpremote devs                                              # detect port
mpremote connect <PORT> exec "import module; print(dir(module))"
mpremote connect <PORT> exec "from machine import Pin; print(dir(Pin))"
python mp-device/scripts/verify-api.py <PORT>                                # full re-verify
```

## Hardware Components

`hardware/esp32-pinout.json` is the **mandatory pin reference** — ESP32 / ESP32-C3 / ESP32-S3 every GPIO with functions, ADC channels, touch pins, forbidden pins, and strapping constraints. Always check before assigning pins.

`hardware/index.json` catalogs electronic components with wiring diagrams, code recipes, and pitfalls. When writing code involving hardware:

1. Check `hardware/index.json` for the component
2. If documented → read the JSON for pin requirements, wiring, code
3. If NOT documented → **create a new JSON** following `led.json`/`servo.json`/`motor.json` format, then update `hardware/index.json`

## ESP32 Hardware Warnings (MANDATORY)

These constraints are MANDATORY for all generated code. Violating them causes hardware damage or crash.

### GPIO Safety

| Rule | Detail |
|------|--------|
| GPIO 6-11 are FORBIDDEN | Connected to internal SPI flash. Using them crashes ESP32 or corrupts firmware. |
| GPIO 34-39 are INPUT ONLY | No pull-up/pull-down, no output. Use for buttons, sensors, ADC only. |
| GPIO 1, 3 are UART0 (USB) | Used for REPL/serial. Avoid unless you know what you're doing. |
| 12mA max per GPIO | Total across all GPIOs should stay under ~100mA. Use transistors/MOSFETs for higher loads. |
| 3.3V logic levels | GPIO outputs 3.3V. 5V sensors may need level shifters. |

### Power

| Rule | Detail |
|------|--------|
| NEVER power motors/servos from ESP32 pins | Use external supply with common GND. ESP32 pins are logic-only. |
| Brownout at <3.0V | ESP32 resets if voltage sags. Add capacitors (100µF+) near power pins. |
| USB power is ~500mA | For WiFi + motors + LEDs, use external 5V 2A+ supply. |
| Deep sleep: ~5µA | Use `machine.deepsleep(ms)` for battery projects. |

### Memory

| Rule | Detail |
|------|--------|
| ~160KB free heap after boot | Typical. WiFi + TLS can consume 50-80KB. Monitor with `gc.mem_free()`. |
| Large strings crash | Single string >~50KB may cause MemoryError. Stream data. |
| gc.collect() before allocations | Call before creating large buffers or after deleting objects. |
| Recursion limit: ~20 | MicroPython has a shallow call stack. Avoid deep recursion. |

### Common Crashes

| Symptom | Likely Cause |
|---------|-------------|
| `MemoryError` | Heap exhausted. `gc.collect()`, reduce buffers, stream. |
| `OSError: [Errno 12] ENOMEM` | Socket/memory. Close sockets, `gc.collect()`. |
| `RuntimeError: schedule queue full` | Too many `micropython.schedule()` calls. Max queue: 4. |
| WDT reset | Code blocked >5s. Add `time.sleep_ms(10)` in long loops. |
| Device won't boot after upload | `boot.py` has infinite loop. Reflash or soft-reset. |
| `ValueError: pin is input-only` | GPIO 34-39 used as output. |

### Wi-Fi Constraints

| Rule | Detail |
|------|--------|
| `wlan.connect()` is blocking | Blocks up to 15s. For responsive apps, poll `wlan.isconnected()`. |
| Wi-Fi + BLE share radio | Simultaneous use reduces throughput on both. |
| `wlan.active(True)` before `espnow` | ESP-NOW requires active Wi-Fi (even without connection). |
| Credentials persist across soft-reset | Call `wlan.active(False)` to clear stored credentials. |

## Built-in Type Methods (CRITICAL)

`api/builtin-types.json` documents 91 CPython methods missing from MicroPython. AI frequently generates these:

```python
# CRASHES on MicroPython:
"hello".removeprefix("he")     # AttributeError
(3.14).is_integer()             # AttributeError (float has NO methods!)
(42).bit_count()                # AttributeError (use bin(x).count('1'))
memoryview(b"x").tobytes()     # AttributeError (use bytes(mv))
bytearray(b"x").copy()         # AttributeError (use bytearray(ba))
```

Always check `api/builtin-types.json` before using string/bytes/int/float methods.
