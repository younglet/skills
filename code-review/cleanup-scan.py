#!/usr/bin/env python3
"""
cleanup-scan.py — Scan a project for development artifacts that should be
removed before code review / commit.

Scans for:
  1. Requirement-change comments (code comments explaining why something changed)
  2. Suspect .md / .html files (dev journals, change logs)
  3. Debug/explanation print() calls

Usage:
  python cleanup-scan.py <project-root>            # scan and report
  python cleanup-scan.py <project-root> --apply    # auto-remove debug prints
"""

import argparse
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Comments that look like requirement-change diary entries
SUSPECT_COMMENT_PATTERNS = [
    # English
    r"changed\s+from\b",
    r"changed\s+per\b",
    r"previously\s+(was|:)",
    r"was:.*\bnow\b",
    r"switched\s+(from|to)\b",
    r"updated\s+(per|to)\b",
    r"new\s+requirement",
    r"requirement\s+(change|shift|update)",
    r"TODO:\s*(revert|change\s*back|undo|remove)",
    r"per\s+(PM|client|stakeholder|product|manager)",
    r"temporary\s+(fix|change|solution|hack)",
    r"HACK:.*requirement",
    r"WORKAROUND:.*requirement",
    r"FIXME:.*requirement",
    # Chinese
    r"需求变更",
    r"需求变动",
    r"需求变化",
    r"临时修改",
    r"临时方案",
    r"临时改成",
    r"临时换成",
    r"先这样",
    r"暂时",
    r"应PM",
    r"应产品",
    r"应需求",
    r"产品说",
    r"客户说",
    # Generic "this was changed" signals
    r"之前是",
    r"原来是",
    r"原来是.*现在",
    r"修改为",
    r"换成了",
]

# Source code extensions to scan for suspect comments
SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".c", ".cpp", ".h", ".hpp",
    ".java", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".cs", ".vb", ".m", ".mm", ".lua", ".r", ".sql", ".sh", ".bash",
    ".zsh", ".ps1", ".pl", ".pm", ".t", ".ex", ".exs", ".erl", ".hrl",
    ".hs", ".elm", ".clj", ".cljs", ".dart", ".groovy", ".scss", ".less",
    ".vue", ".svelte",
}

# Patterns for debug/explanation print statements
DEBUG_PRINT_PATTERNS = [
    # Python
    (r"\.py$", r"print\(\s*[\"'](TODO|DEBUG|TEMP|临时|CHANGED|FIXME|HACK|NOTE:)"),
    (r"\.py$", r"print\(\s*f[\"'](TODO|DEBUG|TEMP|临时|CHANGED)"),
    # JavaScript / TypeScript
    (r"\.(js|ts|jsx|tsx|mjs|cjs)$", r"console\.(log|warn|error)\(\s*[\"'](TODO|DEBUG|TEMP|临时|CHANGED)"),
    # C / C++
    (r"\.(c|cpp|h|hpp|m|mm)$", r'(printf|NSLog)\(\s*[\"@]?(TODO|DEBUG|TEMP|临时|CHANGED)'),
    # Go
    (r"\.go$", r'fmt\.(Println|Printf)\(\s*[\"](TODO|DEBUG|TEMP|临时|CHANGED)'),
    # Rust
    (r"\.rs$", r'(println!|eprintln!|dbg!)\(\s*[\"](TODO|DEBUG|TEMP)'),
    # Java
    (r"\.java$", r'System\.(out|err)\.(print|println)\(\s*[\"](TODO|DEBUG|TEMP|临时|CHANGED)'),
    # PHP
    (r"\.php$", r'(echo|print|var_dump)\s+[\"\'](TODO|DEBUG|TEMP)'),
    # Ruby
    (r"\.rb$", r'(puts|print|p)\s+[\"\'](TODO|DEBUG|TEMP)'),
    # Shell
    (r"\.(sh|bash|zsh)$", r'echo\s+[\"\'](TODO|DEBUG|TEMP)'),
    # Generic: print with f-string debug prefix
    (r"\.(py|js|ts|jsx|tsx)$", r"print\(.*\b(debug|temp|tmp)\b"),
]

# Filename patterns for suspect .md and .html files
SUSPECT_FILENAME_PATTERNS = [
    r"(?i)^CHANGELOG[_-]",
    r"(?i)^notes[_-]",          # notes_xxx, notes-xxx
    r"(?i)^notes$",             # notes.md, notes.html exactly
    r"(?i)^changes[_-]?",
    r"(?i)^todo[_-]?",
    r"(?i)^REQUIREMENT",
    r"(?i)_changes$",
    r"(?i)^UPDATE[_-]?",
    r"(?i)^DEBUG[_-]?",
    r"(?i)^scratch[_-]?",
    r"(?i)^temp[_-]?",
    r"(?i)^draft[_-]?",
    r"(?i)^tmp[_-]?",
    r"(?i)^临时",
    r"(?i)^备忘",
    r"(?i)^修改说明",
]

# Directories to skip
SKIP_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules",
    "venv", ".venv", "env", ".env", ".tox", "dist", "build",
    ".next", ".nuxt", "target", "vendor", "bower_components",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".turbo",
    "coverage", ".coverage", "htmlcov",
}

# Known-good files to never flag
KEEP_FILES = {
    "README.md", "CONTRIBUTING.md", "LICENSE.md", "ARCHITECTURE.md",
    "ARCHITECTURE.MD", "SECURITY.md", "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",  # official release changelog
}


# ---------------------------------------------------------------------------
# Scanning logic
# ---------------------------------------------------------------------------

def should_skip_dir(dirname: str) -> bool:
    return dirname in SKIP_DIRS or dirname.startswith(".")


def should_skip_file(filename: str) -> bool:
    return filename in KEEP_FILES


def is_source_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in SOURCE_EXTENSIONS


def is_suspect_md_or_html(filename: str) -> bool:
    """Check if a .md or .html file has a suspect name."""
    base = os.path.splitext(filename)[0]
    for pat in SUSPECT_FILENAME_PATTERNS:
        if re.search(pat, base):
            return True
    return False


def scan_file(filepath: str) -> dict:
    """Scan a single file for suspect artifacts.
    Returns a dict with lists of findings.
    """
    findings = {
        "suspect_comments": [],
        "debug_prints": [],
    }

    ext = os.path.splitext(filepath)[1].lower()

    # Compile comment patterns
    comment_patterns_compiled = [re.compile(p, re.IGNORECASE) for p in SUSPECT_COMMENT_PATTERNS]

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return findings

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Check for suspect comments
        # Looks like a comment?
        is_comment = False
        if stripped.startswith(("#", "//", "/*", "*", "<!--", "rem ", "REM ")):
            is_comment = True
        # Python inline comment
        elif "#" in stripped:
            comment_part = stripped.split("#", 1)[1] if "#" in stripped else ""
            if comment_part:
                # Check only the comment part
                for pat in comment_patterns_compiled:
                    if pat.search(comment_part):
                        findings["suspect_comments"].append((i, line.rstrip("\n")))
                        break
                continue  # already checked inline

        if is_comment:
            for pat in comment_patterns_compiled:
                if pat.search(stripped):
                    findings["suspect_comments"].append((i, line.rstrip("\n")))
                    break

        # Check for debug prints
        for ext_pat, print_pat in DEBUG_PRINT_PATTERNS:
            if re.search(ext_pat, filepath, re.IGNORECASE):
                if re.search(print_pat, stripped, re.IGNORECASE):
                    findings["debug_prints"].append((i, line.rstrip("\n")))
                    break  # one match per line is enough

    return findings


def walk_project(root: str) -> dict:
    """Walk the project tree and collect all findings."""
    all_findings = {
        "suspect_files": [],       # .md, .html with suspect names
        "suspect_comments": {},    # filepath -> [(line, text), ...]
        "debug_prints": {},        # filepath -> [(line, text), ...]
    }

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter directories
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        for fname in filenames:
            filepath = os.path.join(dirpath, fname)
            relpath = os.path.relpath(filepath, root)

            # Check for suspect filenames
            ext = os.path.splitext(fname)[1].lower()
            if ext in (".md", ".html") and not should_skip_file(fname):
                if is_suspect_md_or_html(fname):
                    all_findings["suspect_files"].append(relpath)

            # Scan source files
            if is_source_file(fname):
                findings = scan_file(filepath)
                if findings["suspect_comments"]:
                    all_findings["suspect_comments"][relpath] = findings["suspect_comments"]
                if findings["debug_prints"]:
                    all_findings["debug_prints"][relpath] = findings["debug_prints"]

    return all_findings


def apply_remove_debug_prints(root: str, findings: dict) -> int:
    """Remove debug print lines from files. Returns count of removed lines."""
    removed = 0
    for relpath, entries in findings.get("debug_prints", {}).items():
        filepath = os.path.join(root, relpath)
        lines_to_remove = set(line_no for line_no, _ in entries)
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            continue

        new_lines = [l for i, l in enumerate(lines, 1) if i not in lines_to_remove]
        if len(new_lines) < len(lines):
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            removed += len(lines) - len(new_lines)

    return removed


def print_report(root: str, findings: dict):
    """Print a formatted report."""
    total = (
        len(findings["suspect_files"])
        + sum(len(v) for v in findings["suspect_comments"].values())
        + sum(len(v) for v in findings["debug_prints"].values())
    )

    print("=" * 72)
    print("  Post-Dev Cleanup Scan Report")
    print(f"  Project: {os.path.abspath(root)}")
    print(f"  Total artifacts found: {total}")
    print("=" * 72)

    # Suspect files
    if findings["suspect_files"]:
        print(f"\n[FILES] Suspect .md / .html files ({len(findings['suspect_files'])})")
        print("   These look like dev journals / change logs. Review and delete.")
        print("   " + "-" * 60)
        for f in sorted(findings["suspect_files"]):
            print(f"   {f}")
    else:
        print("\n[FILES] Suspect files: none found (ok)")

    # Suspect comments
    if findings["suspect_comments"]:
        count = sum(len(v) for v in findings["suspect_comments"].values())
        print(f"\n[COMMENTS] Suspect requirement-change comments ({count})")
        print("   These explain what changed, not why the code exists. Remove or rewrite.")
        print("   " + "-" * 60)
        for fpath in sorted(findings["suspect_comments"].keys()):
            entries = findings["suspect_comments"][fpath]
            print(f"\n   >> {fpath} ({len(entries)}):")
            for line_no, text in entries[:5]:  # limit to 5 per file
                print(f"      L{line_no}: {text[:100]}")
            if len(entries) > 5:
                print(f"      ... and {len(entries) - 5} more")
    else:
        print("\n[COMMENTS] Suspect comments: none found (ok)")

    # Debug prints
    if findings["debug_prints"]:
        count = sum(len(v) for v in findings["debug_prints"].values())
        print(f"\n[PRINTS] Debug/explanation print() calls ({count})")
        print("   These were added during dev to verify changes. Remove them.")
        print("   " + "-" * 60)
        for fpath in sorted(findings["debug_prints"].keys()):
            entries = findings["debug_prints"][fpath]
            print(f"\n   >> {fpath} ({len(entries)}):")
            for line_no, text in entries[:5]:
                print(f"      L{line_no}: {text[:100]}")
            if len(entries) > 5:
                print(f"      ... and {len(entries) - 5} more")
    else:
        print("\n[PRINTS] Debug prints: none found (ok)")

    print("\n" + "=" * 72)
    if total > 0:
        print("  Next: review each item above. Use --apply to auto-remove debug prints.")
    else:
        print("  [OK] Clean! No development artifacts detected.")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scan project for development artifacts to clean up"
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Automatically remove debug print lines (safe, only removes matched prints)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output findings as JSON (for piping to other tools)",
    )
    args = parser.parse_args()

    root = os.path.abspath(args.root)

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    findings = walk_project(root)

    if args.apply:
        removed = apply_remove_debug_prints(root, findings)
        # Re-scan to get updated report
        findings = walk_project(root)
        if args.json:
            import json
            # Clear debug prints since we removed them
            findings["_removed"] = removed
            print(json.dumps({k: v for k, v in findings.items()
                              if not k.startswith("_")}, indent=2, ensure_ascii=False))
        else:
            print(f"[OK] Removed {removed} debug print lines.\n")
            print_report(root, findings)
    elif args.json:
        import json
        print(json.dumps({k: v for k, v in findings.items()
                          if not k.startswith("_")}, indent=2, ensure_ascii=False))
    else:
        print_report(root, findings)

    # Exit with non-zero if findings exist (for CI)
    total = (
        len(findings["suspect_files"])
        + sum(len(v) for v in findings["suspect_comments"].values())
        + sum(len(v) for v in findings["debug_prints"].values())
    )
    sys.exit(1 if total > 0 else 0)


if __name__ == "__main__":
    main()
