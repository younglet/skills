# api/ — MicroPython Module Reference (53 JSONs)

Device-verified API reference for MicroPython v1.28.0 on ESP32. Every function, method, and constant confirmed via `dir()` on real hardware.

## How to Use

When writing MicroPython code, check the relevant JSON file **before** writing any import or method call:

1. Find the module in `index.json` → `modules[].file`
2. Open that file — it contains exact `import` syntax, function signatures, and CPython differences
3. Pay attention to `differences_from_cpython` and `esp32_notes` — these prevent the most common AI mistakes

## JSON Structure

Each file follows this schema:

```jsonc
{
  "name": "module-name",          // Unique identifier
  "module": "module",             // Python import name
  "import": "import module",      // Exact import statement
  "version": "1.28.0",           // Target MicroPython version
  "category": "standard|esp32",  // standard = all ports, esp32 = ESP32-only
  "description": "What it does",

  // Module-level functions (module.json, time.json style)
  "functions": [
    {"name": "module.func", "signature": "func(arg, ...)", "returns": ..., "description": "..."}
  ],

  // Module-level attributes (sys.json style)
  "attributes": [
    {"name": "sys.platform", "type": "str", "description": "..."}
  ],

  // Module-level constants
  "constants": {"CONST_NAME": null, ...},

  // Classes (machine-pin.json, network.json style)
  "classes": [
    {
      "name": "ClassName",
      "methods": [
        {"name": "Class.method", "signature": "method(...)", "returns": ..., "description": "..."}
      ],
      "constants": {"CLASS_CONST": null}
    }
  ],

  // Critical differences from CPython
  "differences_from_cpython": ["..."],

  // ESP32-specific gotchas
  "esp32_notes": ["..."]
}
```

## Verification Status

| Metric | Value |
|--------|-------|
| Device verified | ✅ ESP32 MicroPython v1.28.0 |
| Verification method | `dir()` on every module + class |
| Stale entries (JSON has, device lacks) | **0** |
| Last verification | See `mp-device/scripts/verify-api.py` output |

Run `python mp-device/scripts/verify-api.py <PORT>` from the skill root to re-verify all 53 files against a connected ESP32.

## File Index

See `api/index.json` for the complete module list with descriptions. See `api/import-guide.json` for critical import rules (no `u` prefix, no `lib.` prefix, etc.). See `api/builtin-types.json` for str/list/dict/bytes methods missing vs CPython.
