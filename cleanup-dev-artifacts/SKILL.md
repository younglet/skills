---
name: cleanup-dev-artifacts
description: Post-development cleanup phase — finds and removes requirement-change commentary (code comments, .md, .html, debug print() calls) that looks unprofessional or confusing to other developers reviewing the final code. Run this after feature completion, before code review or commit.
---

# Post-Dev Cleanup — Remove Requirement-Change Artifacts

After coding against shifting requirements, your codebase accumulates "dev commentary" — comments, notes, and debug prints that chronicle the journey of requirement changes. These artifacts are useful *during* development but look unprofessional and confusing to others reading the finished code. This skill guides you through detecting and removing them.

## What to Remove

### 1. Requirement-Change Comments in Code

Comments that explain **why** code was changed due to a requirement shift. These are not useful permanent documentation — they are development journal entries.

**Examples to REMOVE:**
```python
# Changed from POST to GET per client's new requirement on 6/5
response = requests.get(url)

// 需求变更：之前是硬编码的URL，现在从配置读取
const API_URL = config.get('api_url');

<!-- 应PM要求，临时改成两列布局 -->
<div class="grid-2col">

# TODO: revert this after demo — requirement said 3s timeout
timeout = 5

// previously was: return data.items.filter(...)
// updated per JIRA-4567: sort by date instead
return data.items.sort_by_date()
```

**Examples to KEEP** (permanent documentation):
```python
# RFC 7231 Section 6.3.1: 200 OK for successful GET
status = 200

# This lock prevents a race condition when two ISRs fire simultaneously
_lock = threading.Lock()

// Chrome 87+ requires passive event listeners for scroll performance
{ passive: true }
```

**Key distinction:** Keep comments that explain *why the code is the way it is* (architecture, constraints, standards). Remove comments that explain *why it changed from something else* (requirement history).

### 2. Change-Log Markdown Files

`CHANGELOG_*.md`, `notes.md`, `changes.md`, `todo.md`, `REQUIREMENT_CHANGES.md`, and any `.md` file whose primary purpose is tracking requirement shifts during development.

Remove them entirely — git history is the real changelog.

### 3. Change-Log HTML Files

Same as markdown — any `.html` files created as dev journals, change summaries, or requirement tracking. These are internal development artifacts, not deliverable documentation.

### 4. Debug/Explanatory `print()` Calls

`print()` statements added to verify or explain requirement changes during development. These pollute the output and look sloppy in production.

```python
print("TODO: changed endpoint to v2")
print(f"DEBUG: now using {new_url} instead of {old_url}")
print("临时修改：超时设为10s")
```

## Detection Patterns (grep-ready)

Use these patterns to find suspect artifacts. The script `cleanup-scan.py` automates this.

### Suspect Comment Patterns
```
changed from|changed per|需求变更|需求变动|需求变化|临时修改|临时方案
previously was|previously:|was:.*now
更新于|updated per|updated to|switched from|switched to
new requirement|requirement change|requirement shift
TODO: revert|TODO: change back|TODO: undo|TODO: remove
应PM|应产品|应需求|per PM|per client|per stakeholder
临时改成|临时换成|先这样|暂时
HACK:|WORKAROUND:|FIXME:.*requirement
```

### Suspect Filename Patterns
```
CHANGELOG*.md, notes*.md, changes*.md, todo*.md
REQUIREMENT*.md, *_changes.md, UPDATE*.md
*.html (when in unexpected directories for an HTML-free project)
DEBUG*.md, scratch*.md, temp*.md, draft*.md
```

### Debug Print Patterns
```python
# Python
print("TODO|
print("DEBUG|
print("TEMP|
print("临时|
print("CHANGED|
print(f"DEBUG|
print(f"TODO|

# JavaScript
console.log('TODO|
console.log('DEBUG|
console.log('TEMP|
console.log('临时|
console.log('CHANGED|

# C/C++
printf("TODO|
printf("DEBUG|
printf("TEMP|
NSLog(@"TODO|
NSLog(@"DEBUG|
```

## How to Use This Skill

### Phase 1: Scan

Run `cleanup-scan.py <project-root>` to get a report of all suspect artifacts. The script:
- Greps for suspect comment patterns in source files
- Finds suspect `.md` and `.html` files
- Detects debug/explanation `print()` calls
- Outputs a categorized report with file paths and line numbers

### Phase 2: Review

For each flagged item, decide:
- **Remove entirely** — requirement-change comments, changelog files, debug prints
- **Rewrite** — if the comment contains useful permanent info, rewrite it as architectural documentation
- **Keep** — if it's legitimate documentation (rare; be skeptical)

### Phase 3: Clean

Delete/rewrite the flagged items. Use `cleanup-scan.py --apply` for batch removal of obvious cases (debug prints only — comments and files require human review).

## Important: What NOT to Remove

Do NOT remove:
- `README.md`, `CONTRIBUTING.md`, `LICENSE.md`, `ARCHITECTURE.md` — project documentation
- `CHANGELOG.md` (the official release changelog, if you maintain one) — but `CHANGELOG_draft.md` or `changes_temp.md` should go
- Comments documenting WHY a non-obvious algorithm or data structure was chosen
- Comments linking to issues, RFCs, or specs
- Structured docstrings (`"""..."""`, `/** ... */`) unless they contain requirement-change narrative
- Error handling comments that explain edge cases
- Performance notes that justify a particular approach

## Manual Review: A Smell Test

If a comment reads like a diary entry to your future self, remove it. If it reads like an explanation to a colleague joining the project next month, keep it.

| Diary (REMOVE) | Documentation (KEEP) |
|---|---|
| "Changed to POST because client said..." | "POST required; GET would expose API key in URL" |
| "需求变了，现在要三个按钮" | "Three buttons: submit, save-draft, cancel — covers all form exit paths" |
| "// previously: sort by name" | (nothing — git blame shows what changed) |
| "TODO: revert the 10s timeout after demo" | "10s timeout matches the upstream service SLA (see ops-docs/timeout.md)" |
