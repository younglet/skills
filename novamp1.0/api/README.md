# api/ — NovaMP v1.0 Module Reference (16 JSONs)

NovaMP-specific driver API reference. Each JSON documents one of the 16 pre-installed modules in `NovaMP v1.0`.

## How to Use

When writing NovaMP code, check the relevant JSON **before** writing any import:

1. Find the module in `../index.json` → `modules[].file`
2. Open that file — exact constructor signature, parameters, methods
3. Pay attention to `esp32_notes` and `hardware_notes` — NovaMP-specific gotchas
4. Use `.help()` for in-IDE documentation; `.test()` for interactive validation

## JSON Structure

Each file follows this schema:

```jsonc
{
  "name": "module-name",           // Unique identifier
  "module": "module",              // Python import name
  "class": "ClassName",            // Primary exported class
  "import": "from module import ClassName",
  "version": "1.0.0",              // NovaMP v1.0
  "category": "input|output|sensor|network|utility",
  "description": "What it does",

  // Constructor parameters
  "constructor_params": [
    {"name": "pin", "type": "Pin|int", "default": null, "description": "..."}
  ],

  // Properties (readable attributes)
  "properties": [
    {"name": "brightness", "type": "int", "read": true, "write": true, "description": "..."}
  ],

  // Methods
  "methods": [
    {"name": "on", "signature": "on()", "returns": "None", "description": "..."}
  ],

  // Module-level functions (e.g. colors.py)
  "functions": [
    {"name": "generate_gradient_colors", "signature": "(start, end, steps)", "returns": "list", "description": "..."}
  ],

  // Module-level constants (e.g. colors.py color constants)
  "constants": {
    "RED": [255, 0, 0]
  },

  // Class-level constants
  "class_constants": {
    "NOTE_FREQUENCIES": {"C": 261.63, ...}
  },

  // Working example
  "example": "from machine import Pin\nfrom led import LED\nled = LED(Pin(4))",

  // Universal NovaMP methods
  "help_method": "LED.help()  # prints docs",
  "test_method": "LED.test()  # interactive test",

  // NovaMP-specific gotchas
  "esp32_notes": ["GPIO 34-39 are input-only"],
  "hardware_notes": ["Must use H-bridge (L298N/TB6612FNG)"]
}
```

## Verification Status

| Metric | Value |
|--------|-------|
| Source | NovaMP docs/*.md + lib/*.py (Stemstar Education) |
| Modules | 16/16 documented |
| Last sync | 2026-06-21 (matches firmware release date) |
| Parent firmware | MicroPython v1.28.0 (see parent skill `../SKILL.md`) |

## File Index

See `../index.json` for the full module list with descriptions and links.