# patterns/ — NovaMP v1.0 Reusable Code Patterns

Copy-paste recipes for common NovaMP v1.0 workflows.

| File | Use Case |
|------|----------|
| `boot-with-wifi.json` | boot.py that connects Wi-Fi and syncs NTP on every boot |
| `interactive-test.json` | The `.test()` workflow — interactive hardware validation |
| `help-docs.json` | The `.help()` workflow — in-IDE documentation lookup |

## Pattern Categories

- **Bootstrap** — code that runs automatically at boot (`boot.py`)
- **Test** — interactive REPL workflows for hardware validation
- **Documentation** — in-IDE help patterns for self-service learning

These complement the parent skill's `../patterns/` (which covers non-blocking WiFi, scheduling, sensor reads in standard MicroPython).