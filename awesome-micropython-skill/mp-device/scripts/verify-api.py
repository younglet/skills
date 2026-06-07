#!/usr/bin/env python3
"""
verify-api.py — Compare on-device dir() against awesome-micropython-skill JSONs.
One-shot mpremote call collects everything, then diffs locally.

Usage:
  python verify-api.py COM3                # Windows
  python verify-api.py /dev/cu.usbmodem01  # macOS
  python verify-api.py COM3 --fix          # scan + auto-fix JSON files
  python verify-api.py COM3 --builtins     # only scan and create builtins.json
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import time

API_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "api")

# ── mpremote helpers ──────────────────────────────────────────────────

def mpremote(port: str, code: str, timeout: int = 30) -> str:
    """Run code on device via mpremote, return stdout."""
    # Wrap in a try/except so errors on device are captured
    wrapped = f"try:\n"
    for line in code.strip().split("\n"):
        wrapped += f"    {line}\n"
    wrapped += "except Exception as e:\n    print('__MPREMOTE_ERROR__:', e)"

    for attempt in range(3):
        try:
            r = subprocess.run(
                ["mpremote", "connect", port, "exec", wrapped],
                capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace",
            )
            if "__MPREMOTE_ERROR__" in r.stdout:
                print(f"  [device error] {r.stdout.strip()}", file=sys.stderr)
            if "failed to access" in r.stderr:
                time.sleep(1)
                continue
            return r.stdout
        except subprocess.TimeoutExpired:
            time.sleep(2)
    return ""


def parse_dir_output(output: str) -> list:
    """Parse the Python list output from dir(). Returns list of names."""
    # Output looks like: ['__class__', '__name__', 'dump', ...]
    # May have garbage before/after
    match = re.search(r"\[.*\]", output, re.DOTALL)
    if not match:
        return []
    try:
        return ast.literal_eval(match.group(0))
    except (ValueError, SyntaxError):
        return []


# ── build the device-side collection script ───────────────────────────

def build_collection_script() -> str:
    """Generate a MicroPython script that collects dir() for all modules."""
    lines = ['import sys', 'd = {}']

    # Module-level: import X; dir(X)
    modules = [
        "json", "time", "sys", "os", "gc", "re", "struct", "random", "math",
        "collections", "socket", "select", "_thread", "asyncio", "micropython",
        "neopixel", "framebuf", "dht", "onewire", "ntptime", "hashlib",
        "binascii", "io", "ssl", "cryptolib", "esp", "esp32", "network",
    ]

    # Optional modules (may not be installed)
    optional_modules = ["requests", "bluetooth", "espnow"]

    for mod in modules:
        lines.append(f"try:\n    import {mod}\n    d['{mod}']=dir({mod})\nexcept: d['{mod}']=None")

    for mod in optional_modules:
        lines.append(f"try:\n    import {mod}\n    d['{mod}']=dir({mod})\nexcept: d['{mod}']=None")

    # Class-level: from machine import X; dir(X)
    machine_classes = [
        "Pin", "ADC", "DAC", "PWM", "I2C", "SoftI2C", "SPI", "SoftSPI",
        "UART", "Timer", "RTC", "WDT", "SDCard", "TouchPad", "Signal",
        "I2S", "Counter", "Encoder", "ADCBlock",
    ]

    # machine module-level
    lines.append("try:\n    import machine\n    d['machine']=dir(machine)")
    for cls in machine_classes:
        safe = cls.replace(".", "_")
        lines.append(f"    try:\n        d['machine.{cls}']=dir(machine.{cls})\n    except: d['machine.{cls}']=None")
    lines.append("except: pass")

    # network classes
    lines.append("try:\n    import network\n    d['network.WLAN']=dir(network.WLAN)\n    d['network.LAN']=dir(network.LAN)\nexcept: pass")

    # esp32 classes
    esp32_classes = ["NVS", "RMT", "PCNT", "Partition", "ULP"]
    lines.append("try:\n    import esp32")
    for cls in esp32_classes:
        lines.append(f"    try:\n        d['esp32.{cls}']=dir(esp32.{cls})\n    except: d['esp32.{cls}']=None")
    lines.append("except: pass")

    # builtins
    lines.append("try:\n    import builtins\n    d['builtins']=dir(builtins)\nexcept: d['builtins']=None")

    # Print as JSON — also dive into any CamelCase names (potential classes)
    lines.append('import json')
    lines.append('d2 = {}')
    lines.append('for k, v in d.items():')
    lines.append('    if v is not None:')
    lines.append('        d2[k] = v')
    lines.append('        # For each module, also check CamelCase names (classes)')
    lines.append('        for name in v:')
    lines.append('            if name and name[0].isupper() and not name.startswith("__"):')
    lines.append('                try:')
    lines.append('                    full = k + "." + name')
    lines.append('                    exec("import " + k.split(".")[0])')
    lines.append('                    cls = eval(full)')
    lines.append('                    d2[full] = dir(cls)')
    lines.append('                except:')
    lines.append('                    pass')
    lines.append('print(json.dumps({k:v for k,v in d2.items() if v is not None}))')

    return "\n".join(lines)


# ── extract expected names from JSON ──────────────────────────────────

def extract_json_names(json_path: str) -> dict:
    """Extract all public API names from a JSON module file.
    Returns {name_type: set} where name_type is:
      'module_funcs' - module-level function names
      'module_consts' - module-level constant names
      'class_methods' - class method names (from all classes)
      'class_consts' - class constant names (from all classes)
      'class_methods_by_name' - {ClassName: set(method_names)}
      'class_consts_by_name' - {ClassName: set(const_names)}
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = {
        "module_funcs": set(),
        "module_consts": set(),
        "class_methods": set(),
        "class_consts": set(),
        "class_methods_by_name": {},
        "class_consts_by_name": {},
    }

    def short(name: str) -> str:
        if "." in name:
            return name.split(".", 1)[1]
        return name

    # Module-level functions
    for key in ("functions", "module_functions"):
        val = data.get(key, [])
        if isinstance(val, list):
            for func in val:
                if isinstance(func, dict):
                    name = func.get("name", "")
                    if name:
                        result["module_funcs"].add(short(name))

    # Module-level attributes (sys.json style)
    attrs = data.get("attributes", [])
    if isinstance(attrs, list):
        for a in attrs:
            if isinstance(a, dict):
                name = a.get("name", "")
                if name:
                    result["module_funcs"].add(short(name))

    # Module-level constants
    consts = data.get("constants")
    if isinstance(consts, dict):
        for name in consts.keys():
            if name:
                result["module_consts"].add(name)
    elif isinstance(consts, list):
        for c in consts:
            if isinstance(c, dict):
                name = c.get("name", "")
                if name:
                    result["module_consts"].add(short(name))

    # Class-level methods and constants
    for cls in data.get("classes", []):
        cname = cls.get("name", "")
        if not cname:
            continue

        methods = cls.get("methods", [])
        if isinstance(methods, list):
            mset = set()
            for method in methods:
                if isinstance(method, dict):
                    name = method.get("name", "")
                    if name:
                        s = short(name)
                        mset.add(s)
                        result["class_methods"].add(s)
            result["class_methods_by_name"][cname] = mset

        cconsts = cls.get("constants", {})
        if isinstance(cconsts, dict):
            cset = set()
            for const_name in cconsts.keys():
                if const_name:
                    cset.add(const_name)
                    result["class_consts"].add(const_name)
            result["class_consts_by_name"][cname] = cset

    return result


# ── comparison ────────────────────────────────────────────────────────

def compare_module(device_names: list, json_names: set) -> dict:
    """Compare device dir() against JSON expectations.
    Returns {missing_in_json, missing_on_device}
    """
    device_set = set(device_names)

    # Filter dunder names from comparison
    device_public = {n for n in device_set if not n.startswith("__")}
    json_public = {n for n in json_names if not n.startswith("__")}

    missing_in_json = device_public - json_public  # on device but not documented
    missing_on_device = json_public - device_public  # documented but not on device

    return {
        "missing_in_json": sorted(missing_in_json),
        "missing_on_device": sorted(missing_on_device),
    }


# ── map device keys to JSON files ─────────────────────────────────────

def build_device_to_json_map() -> dict:
    """Map device-side keys (e.g. 'json', 'machine.Pin', 'dht.DHT11') to
    (json_path, compare_type) tuples where compare_type is 'module' or 'class'.
    """
    index_path = os.path.join(API_DIR, "index.json")
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    mapping = {}

    for mod in index["modules"]:
        filepath = os.path.join(API_DIR, mod["file"])
        if not os.path.exists(filepath):
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        module_name = data.get("module", "")
        class_name = data.get("class_name", "")

        # Module-level: always map the bare module name
        if module_name and module_name not in mapping:
            mapping[module_name] = (filepath, "module")

        # Class-level: for JSONs with 'class_name' (like machine-pin.json)
        if class_name:
            full = f"{module_name}.{class_name}"
            mapping[full] = (filepath, "class")

        # Class-level: for JSONs with 'classes' array (multiple classes in one file)
        for cls in data.get("classes", []):
            cname = cls.get("name", "")
            if cname:
                full = f"{module_name}.{cname}"
                if full not in mapping:
                    mapping[full] = (filepath, "class")

    return mapping


# ── main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Verify awesome-micropython-skill JSONs against real ESP32")
    parser.add_argument("port", help="Serial port (e.g., COM3 on Windows, /dev/cu.usbmodem01 on macOS, /dev/ttyACM0 on Linux)")
    parser.add_argument("--fix", action="store_true", help="Auto-fix JSON files")
    parser.add_argument("--builtins-only", action="store_true", help="Only generate builtins.json")
    parser.add_argument("--module", help="Verify only a specific module (e.g., 'machine.Pin')")
    args = parser.parse_args()

    # ── Generate builtins.json ────────────────────────────────────────
    print("=== Collecting builtins ===")
    builtins_out = mpremote(args.port, "import builtins; print(dir(builtins))")
    builtins_names = parse_dir_output(builtins_out)

    if builtins_names:
        # Categorize builtins
        exceptions = []
        functions = []
        types_ = []
        constants = []
        others = []

        for name in sorted(builtins_names):
            if name.startswith("_"):
                continue
            if name.endswith("Error") or name.endswith("Exception") or name.endswith("Exit") or name in ("GeneratorExit", "StopIteration", "StopAsyncIteration", "KeyboardInterrupt", "SystemExit", "BaseException", "Exception", "ArithmeticError", "AssertionError", "AttributeError", "EOFError", "ImportError", "IndentationError", "IndexError", "KeyError", "LookupError", "MemoryError", "NameError", "NotImplementedError", "OSError", "OverflowError", "RuntimeError", "SyntaxError", "TypeError", "ValueError", "ZeroDivisionError", "UnicodeError", "ViperTypeError"):
                exceptions.append(name)
            elif name in ("bool", "bytearray", "bytes", "complex", "dict", "float", "frozenset", "int", "list", "memoryview", "object", "set", "slice", "str", "tuple", "type"):
                types_.append(name)
            elif name in ("Ellipsis", "NotImplemented", "True", "False", "None"):
                constants.append(name)
            elif callable(eval(name, {"__builtins__": {}})) if False else True:
                # Simple heuristic: known callables
                if name in ("abs", "all", "any", "bin", "callable", "chr", "classmethod", "compile", "delattr", "dir", "divmod", "enumerate", "eval", "exec", "execfile", "filter", "getattr", "globals", "hasattr", "hash", "help", "hex", "id", "input", "isinstance", "issubclass", "iter", "len", "locals", "map", "max", "min", "next", "oct", "open", "ord", "pow", "print", "property", "range", "repr", "reversed", "round", "setattr", "sorted", "staticmethod", "sum", "super", "vars", "zip", "__build_class__", "__import__"):
                    functions.append(name)
                else:
                    functions.append(name)
            else:
                others.append(name)

        builtins_json = {
            "name": "builtins",
            "module": "builtins",
            "import": "(always available, no import needed)",
            "version": "1.28.0",
            "category": "standard",
            "description": "Python built-in functions, types, exceptions, and constants. Always available in every MicroPython script.",
            "exceptions": sorted(exceptions),
            "functions": sorted(functions),
            "types": sorted(types_),
            "constants": sorted(constants),
            "differences_from_cpython": [
                "No __builtins__ global (use import builtins instead).",
                "MicroPython-specific additions: execfile(), ViperTypeError.",
                "No frozenset literal syntax, but frozenset type exists.",
                "MemoryError is common on ESP32 with ~160KB free heap.",
                "No WindowsError, BlockingIOError, etc. Only OS-level exceptions."
            ]
        }

        builtins_path = os.path.join(API_DIR, "builtins.json")
        with open(builtins_path, "w", encoding="utf-8") as f:
            json.dump(builtins_json, f, indent=2, ensure_ascii=False)
        print(f"  Created builtins.json: {len(functions)} functions, {len(types_)} types, {len(exceptions)} exceptions")

        # Update index.json
        index_path = os.path.join(API_DIR, "index.json")
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        existing = [m["file"] for m in index["modules"]]
        if "builtins.json" not in existing:
            index["modules"].insert(0, {
                "file": "builtins.json",
                "module": "builtins",
                "category": "standard",
                "description": "Built-in functions, types, and exceptions — always available"
            })
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            print("  Updated index.json with builtins entry")
    else:
        print("  FAILED to get builtins")

    if args.builtins_only:
        return

    # ── Collect all module dir() data from device ──────────────────────
    print("\n=== Collecting module data from device ===")
    script = build_collection_script()
    print(f"  Script size: {len(script)} bytes")
    out = mpremote(args.port, script, timeout=60)
    if not out.strip():
        print("  FAILED: No output from device")
        sys.exit(1)

    try:
        device_data = json.loads(out.strip().split("\n")[-1])
    except json.JSONDecodeError:
        print(f"  FAILED to parse device output as JSON:")
        print(f"  Raw: {out[:500]}")
        sys.exit(1)

    print(f"  Collected {len(device_data)} module/class entries")

    # ── Build mapping ─────────────────────────────────────────────────
    mapping = build_device_to_json_map()
    print(f"  Local JSON mapping: {len(mapping)} entries")

    # ── Compare each module ───────────────────────────────────────────
    print("\n=== Comparing ===")
    total_missing_json = 0
    total_missing_device = 0
    fixes_applied = 0

    for dev_key, (json_path, compare_type) in sorted(mapping.items()):
        if args.module and args.module != dev_key:
            continue

        if dev_key not in device_data:
            print(f"  {dev_key}: NOT FOUND on device (skipping)")
            continue

        device_names = device_data[dev_key]
        all_json_names = extract_json_names(json_path)

        # Choose which JSON names to compare based on type
        if compare_type == "module":
            # Module-level: compare against module_funcs + module_consts
            json_names = all_json_names["module_funcs"] | all_json_names["module_consts"]
        else:
            # Class-level: extract class name from dev_key (e.g., "bluetooth.BLE" -> "BLE")
            class_name = dev_key.split(".")[-1] if "." in dev_key else dev_key
            # Compare against this specific class's methods + constants
            json_names = (all_json_names["class_methods_by_name"].get(class_name, set()) |
                         all_json_names["class_consts_by_name"].get(class_name, set()))

        diff = compare_module(device_names, json_names)

        if not diff["missing_in_json"] and not diff["missing_on_device"]:
            print(f"  {dev_key}: OK")
            continue

        has_issues = False
        if diff["missing_in_json"]:
            n = len(diff["missing_in_json"])
            total_missing_json += n
            names = ", ".join(diff["missing_in_json"][:10])
            suffix = f" +{n-10} more" if n > 10 else ""
            print(f"  {dev_key}: +{n} UNDOCUMENTED (on device, not in JSON): {names}{suffix}")
            has_issues = True

        if diff["missing_on_device"]:
            n = len(diff["missing_on_device"])
            total_missing_device += n
            names = ", ".join(diff["missing_on_device"][:10])
            suffix = f" +{n-10} more" if n > 10 else ""
            print(f"  {dev_key}: -{n} STALE (in JSON, not on device): {names}{suffix}")
            has_issues = True

        # ── Auto-fix JSON ─────────────────────────────────────────────
        if args.fix and has_issues:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Add missing names to JSON
            for name in diff["missing_in_json"]:
                # Find the right place to add it
                # Prefer adding to constants for ALL_CAPS names
                if name.isupper() or name[0].isupper() and "_" in name:
                    for cls in data.get("classes", []):
                        if "constants" not in cls:
                            cls["constants"] = {}
                        if name not in cls["constants"]:
                            cls["constants"][name] = None  # value unknown
                    if not data.get("classes"):
                        # module-level constant
                        if "constants" not in data:
                            data["constants"] = {}
                        data["constants"][name] = None
                else:
                    # Add as undocumented function/method
                    pass  # Don't auto-add functions — needs manual docs

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            fixes_applied += 1

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n=== Summary ===")
    print(f"  Undocumented names (on device, not in JSON): {total_missing_json}")
    print(f"  Stale names (in JSON, not on device):       {total_missing_device}")
    if args.fix:
        print(f"  JSON files auto-fixed: {fixes_applied}")
    elif total_missing_json + total_missing_device > 0:
        print(f"  Run with --fix to auto-fix JSON files")


if __name__ == "__main__":
    main()
