#!/usr/bin/env python3
"""
project-init.py — Scaffold a standard MicroPython project from template.
Usage: python project-init.py <project_name> [target_dir]
"""

import sys, os, shutil
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "template"

def init_project(name, target=None):
    target = Path(target or ".").resolve() / name
    if target.exists():
        print(f"Error: {target} already exists")
        return 1

    shutil.copytree(TEMPLATE, target)
    # Replace placeholder in README
    readme = target / "README.md"
    content = readme.read_text(encoding="utf-8").replace("{project_name}", name)
    readme.write_text(content, encoding="utf-8")

    print(f"Created {target}/")
    for f in sorted(target.rglob("*")):
        if f.is_file():
            rel = f.relative_to(target)
            print(f"  {rel}")

    print(f"\nNext:")
    print(f"  cd {name}")
    print(f"  mpremote devs")
    print(f"  # Edit src/main.py, then:")
    print(f"  mpremote connect PORT run src/main.py")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python project-init.py <project_name> [target_dir]")
        print("  Creates a standard MicroPython project scaffold.")
        sys.exit(1)
    name = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(init_project(name, target))
