---
name: novamp1.0
description: NovaMP v1.0 — Stemstar's customized MicroPython firmware with 16 pre-installed hardware drivers. Wi-Fi, NTP time sync, LED/Button/Motor/Servo/Buzzer/OLED/Ultrasonic/RGB-matrix/Sound/Light/Knob/RGB-LED. Every module supports `.help()` and `.test()`. Standalone peer of awesome-micropython-skill.
version: "1.0.0"
released: "2026-06-21"
upstream_firmware: "MicroPython v1.28.0"
publisher: "Stemstar Education"
---

# NovaMP v1.0 — Stemstar Custom MicroPython Firmware

> 深度定制的 MicroPython 教育固件 — 16 个预装驱动，开箱即跑

NovaMP v1.0 是由 **Stemstar Education** 为创客教育场景定制的 MicroPython 固件，在标准 MicroPython 基础上预装了 16 个常用硬件驱动，所有驱动均统一支持 `.help()`（查看文档）和 `.test()`（交互测试）。

This is a **standalone** skill that documents NovaMP's pre-installed drivers. It is a peer of `awesome-micropython-skill` (both live at `~/.skills/`), not a sub-skill. For underlying MicroPython modules (machine, network, time, etc.) use `awesome-micropython-skill`.

## Quick Reference

| Capability | Entry Point |
|-----------|-------------|
| View API for a module | Read `api/<module>.json` |
| List all 16 modules | `index.json` |
| Common usage patterns | `patterns/boot-with-wifi.json`, `patterns/interactive-test.json` |
| NovaMP-specific pitfalls | `pitfalls.json` |
| Standard MP API (machine, network, etc.) | Parent skill: `../api/` |

## Two-Line Onboarding

```python
from wifi import WiFi
from time_sync import TimeSyncer

WiFi(ssid='your_ssid', password='your_pwd').connect()
TimeSyncer(timezone=8).sync()
print(TimeSyncer(timezone=8).now())   # '2026-06-21 14:32:18'
```

## Architecture

```
novamp/
│
├── SKILL.md                     ← You are here
├── index.json                   ← 16-module index for v1.0
│
├── api/                         ← Per-module API reference (16 JSONs)
│   ├── README.md                    JSON schema + verification status
│   ├── button.json                  Button class — debounce + click
│   ├── buzzer.json                  Buzzer class — passive/active buzzer
│   ├── colors.json                  Color constants + gradient functions
│   ├── diff_drive_car.json          DiffDriveCar class — two-wheel robot
│   ├── hcsr04.json                  HCSR04 class — ultrasonic sensor
│   ├── knob.json                    Knob class — potentiometer
│   ├── ldr.json                     LDR class — light sensor
│   ├── led.json                     LED class — PWM LED control
│   ├── mic.json                     Microphone class — sound sensor
│   ├── motor.json                   Motor class — DC motor H-bridge
│   ├── rgb_matrix.json              RGBMatrix class — 8x8 NeoPixel
│   ├── sg90.json                    SG90 class — servo motor
│   ├── ssd1306.json                 SSD1306 class — OLED display
│   ├── time_sync.json               TimeSyncer class — NTP sync
│   ├── trilight.json                TriLight class — RGB LED
│   └── wifi.json                    WiFi class — STA connection
│
├── patterns/                    ← Reusable code architecture
│   ├── README.md
│   ├── boot-with-wifi.json          boot.py: WiFi + NTP on every boot
│   ├── interactive-test.json        .test() workflow for hardware validation
│   └── help-docs.json               .help() workflow for in-IDE learning
│
└── pitfalls.json                ← NovaMP-specific errors + fixes
```

## The 16 v1.0 Modules

| Module | Class | Function | Docs |
|--------|-------|----------|------|
| `button` | `Button` | Debounced button with click detection | [api/button.json](api/button.json) |
| `buzzer` | `Buzzer` | Passive/active buzzer, melody playback | [api/buzzer.json](api/buzzer.json) |
| `colors` | (functions) | RGB constants + gradient/rainbow | [api/colors.json](api/colors.json) |
| `diff_drive_car` | `DiffDriveCar` | Two-wheel differential drive | [api/diff_drive_car.json](api/diff_drive_car.json) |
| `hcsr04` | `HCSR04` | Ultrasonic distance sensor (2-400cm) | [api/hcsr04.json](api/hcsr04.json) |
| `knob` | `Knob` | Potentiometer with range mapping | [api/knob.json](api/knob.json) |
| `ldr` | `LDR` | Light sensor via ADC | [api/ldr.json](api/ldr.json) |
| `led` | `LED` | PWM LED with fade/breathe/blink | [api/led.json](api/led.json) |
| `mic` | `Microphone` | Sound sensor with peak detection + calibration | [api/mic.json](api/mic.json) |
| `motor` | `Motor` | DC motor H-bridge control | [api/motor.json](api/motor.json) |
| `rgb_matrix` | `RGBMatrix` | 8x8 WS2812B/NeoPixel matrix | [api/rgb_matrix.json](api/rgb_matrix.json) |
| `sg90` | `SG90` | Servo motor 0°-180° | [api/sg90.json](api/sg90.json) |
| `ssd1306` | `SSD1306` | I²C OLED display | [api/ssd1306.json](api/ssd1306.json) |
| `time_sync` | `TimeSyncer` | NTP time sync + RTC | [api/time_sync.json](api/time_sync.json) |
| `trilight` | `TriLight` | 3-channel RGB LED | [api/trilight.json](api/trilight.json) |
| `wifi` | `WiFi` | Wi-Fi STA connection with retry | [api/wifi.json](api/wifi.json) |

## Two Universal Conventions

Every NovaMP v1.0 class supports two methods:

### 1. `.help()` — In-IDE Documentation

```python
from led import LED
LED.help()
```

Prints the class's full signature, parameter list, method list, and a working example. **Always call this first** before writing code for an unfamiliar module.

### 2. `.test()` — Interactive Hardware Validation

```python
from hcsr04 import HCSR04
HCSR04.test()
```

Launches an interactive REPL wizard that prompts for pin numbers, runs the module through its paces, and reports results. **Always run this first** when wiring a new module to confirm pinout and basic operation.

## Import Ordering Convention

Imports are ordered by category — **base modules first, hardware drivers last**. All imports stay in one contiguous block (no blank lines between groups); one blank line before the code that follows.

### The 4 Categories (top → bottom)

| # | Category | Typical modules |
|---|----------|-----------------|
| 1 | Python standard library | `time`, `json`, `struct`, `re`, `math` |
| 2 | MicroPython built-ins | `machine`, `network`, `esp`, `uos` |
| 3 | Framework / third-party | `nova_server`, custom libs |
| 4 | NovaMP hardware drivers | `led`, `hcsr04`, `ssd1306`, `wifi` |

### ✅ Correct

```python
import time
import json
from machine import Pin, ADC
from nova_server import NovaServer
from led import LED
from hcsr04 import HCSR04

_hcsr04 = HCSR04(...)
```

### ❌ Wrong — drivers before `machine`

```python
from led import LED                    # group 4 — too early
from nova_server import NovaServer      # group 3
from machine import Pin                 # group 2 — too late
```

### Rationale

- Reading top-to-bottom mirrors **dependency direction**: drivers depend on `machine.Pin`, which depends on firmware.
- Teachers can scan the top of any script and instantly see what hardware is attached (last lines of the import block).
- Visually compact — a single import block is easier to read than a wall of blank lines.

## Pin-Based Design

All NovaMP drivers accept either an integer GPIO number OR a `machine.Pin` instance:

```python
from machine import Pin
from led import LED

# Integer form (driver creates Pin internally)
led = LED(4)

# Pin instance form (recommended — matches MicroPython official style)
led = LED(Pin(4))
```

Both forms are equivalent. Use the `Pin()` form when you need fine control over pull-ups, mode, or alternate functions.

## Wiring Convention (S-V-G)

All NovaMP sensors use the **S-V-G** 3-wire convention unless otherwise noted:

| Wire | Meaning | Color (typical) | Function |
|------|---------|-----------------|----------|
| **S** | Signal | Yellow | Data (ADC / GPIO / PWM / I²C) |
| **V** | Voltage | Red | Power input (3.3V or 5V) |
| **G** | Ground | Black | Common ground |

Some sensors use different conventions:
- **HCSR04**: Trig (yellow) + Echo (green) + VCC (red) + GND (black) — 4-wire
- **SSD1306**: SCL (yellow) + SDA (green) + VCC (red) + GND (black) — I²C
- **RGBMatrix**: DI/DIN (yellow/green) + VCC (red) + GND (black) — single-wire data

## Core MP Support: Wi-Fi + NTP Time Sync

The user-requested focus. See full API in:
- [`api/wifi.json`](api/wifi.json) — `WiFi` class
- [`api/time_sync.json`](api/time_sync.json) — `TimeSyncer` class

### Standard Pattern

```python
from wifi import WiFi
from time_sync import TimeSyncer

# 1. Connect Wi-Fi
wifi = WiFi(ssid='your_ssid', password='your_pwd', hostname='my-esp32')
if wifi.connect():
    print('IP:', wifi.ip)
    print('DNS:', wifi.dns)

    # 2. Sync time via NTP
    ts = TimeSyncer(timezone=8)   # Beijing UTC+8
    if ts.sync(force=True):
        print('Local:', ts.now())           # '2026-06-21 14:32:18'
        print('HTTP:', ts.http_time())      # 'Sun, 21 Jun 2026 06:32:18 GMT'
```

The complete boot.py pattern with error handling is in [`patterns/boot-with-wifi.json`](patterns/boot-with-wifi.json).

## Critical NovaMP Differences from Standard MicroPython

| Area | NovaMP v1.0 | Standard MicroPython |
|------|--------------|----------------------|
| Default Wi-Fi | `stemstaroffice` / `ilovestem` | None — must configure manually |
| Time sync | Built-in `TimeSyncer` class with 4h cache | `ntptime.settime()` only |
| Hardware drivers | 16 pre-installed in `/lib/` | None — must upload manually |
| Pin creation | `LED(Pin(4))` or `LED(4)` | `Pin(4, Pin.OUT)` manual |
| `.help()` / `.test()` | Universal on all classes | Not present |

## Quick-Start Examples

### LED with breathing effect

```python
from machine import Pin
from led import LED

led = LED(Pin(4))
while True:
    led.breathe()        # fade-in + fade-out
```

### Distance sensor

```python
from machine import Pin
from hcsr04 import HCSR04

sensor = HCSR04(trig_pin=Pin(14), echo_pin=Pin(12))
while True:
    print(f'{sensor.distance:.1f} cm')
```

### Servo sweep

```python
from machine import Pin
from sg90 import SG90

servo = SG90(Pin(4))
for angle in (0, 45, 90, 135, 180):
    servo.move_to(angle)
```

### Wi-Fi + HTTP weather

```python
from wifi import WiFi
import requests

wifi = WiFi()
if wifi.connect():
    r = requests.get('https://api.example.com/weather?city=shanghai')
    print(r.json())
```

## Common Pitfalls

See [`pitfalls.json`](pitfalls.json) for the full ranked-fixes database. Most common:

1. **Forgetting to call `deinit()`** — PWM resources leak. Always call `led.deinit()` / `motor.deinit()` before re-init.
2. **GPIO 34-39 used as outputs** — they are input-only on ESP32. NovaMP drivers raise `ValueError` for misuse.
3. **Motors without H-bridge** — never connect DC motors directly to GPIO. Use L298N/TB6612FNG.
4. **Time sync before Wi-Fi** — `ntptime.settime()` raises `OSError: ETIMEDOUT` if WLAN is inactive.
5. **Servo jitter** — `SG90` rounds to 0.01° to prevent PWM jitter, but avoid rapid `move_to()` calls <50ms apart.

## Firmware Flashing

```bash
# 擦除
python -m esptool --chip esp32 --port COM3 erase_flash

# 烧录（波特率 1258000 可大幅提速）
python -m esptool --chip esp32 --port COM3 --baud 1258000 write_flash -z 0x1000 firmwares/novamp_v1.0_esp32_generic.bin

# 烧录完成后，用 mpremote 上传项目文件
mpremote connect COM3
mpremote fs cp server.py :server.py
mpremote fs cp lib/tomato_clock.py :lib/tomato_clock.py
mpremote fs cp index.html :index.html
# 等等
```

注意：第一次烧录后 flash 是空的，需要把 nova_server.mpy、项目文件等重新上传。

## Relationship to Peer Skill

`awesome-micropython-skill` documents **standard MicroPython v1.28.0** modules (`machine`, `network`, `time`, etc.).
This skill documents **NovaMP v1.0** wrappers built on top of those standards.

When writing code for a NovaMP device:
- Use this skill (`novamp1.0/api/<nova-module>.json`) for NovaMP classes
- Reference the peer skill (`awesome-micropython-skill/api/<standard>.json`) for underlying MicroPython behavior

## Versioning

This skill follows **per-version standalone skills** pattern. Each NovaMP firmware major/minor version gets its own skill folder under `~/.skills/`:

| Skill folder | Firmware version | Status | Entry Point |
|--------------|-----------------|--------|-------------|
| **`novamp1.0/`** | NovaMP v1.0 (2026-06-21) | ✅ Stable | This file |
| `novamp1.1/` | NovaMP v1.1 | 📋 Planned | (future) |
| `novamp2.0/` | NovaMP v2.0 | 📋 Planned | (future) |

The version suffix in the folder name (`novamp1.0`) matches the upstream firmware version. The version manifest `../awesome-micropython.md` lists which version is the current recommended target.

## See also

- `../awesome-micropython.md` — version manifest noting novamp1.0 as the tracked NovaMP version
- `../awesome-micropython-skill/` — peer skill for standard MicroPython modules