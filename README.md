---
name: younglet-skills
description: Index of younglet's personal pi skill repository. Contains awesome-micropython-skill and cleanup-dev-artifacts skills.
disable-model-invocation: true
---

# younglet's PI Skill Repo

Personal skill repository for [pi coding agent](https://github.com/badlogic/pi).

## Skills

| Skill | Description |
|-------|-------------|
| [awesome-micropython-skill](./awesome-micropython-skill/) | MicroPython v1.28.0 ESP32 — 53 verified API/type JSONs, device validator, auto-fixer, 91 CPython-missing methods. Includes mp-device sub-skill. |
| [cleanup-dev-artifacts](./cleanup-dev-artifacts/) | Post-dev cleanup scanner — remove requirement-change commentary, debug prints, dev journals |

## Usage

Configure pi to load skills from this repo by adding to `~/.pi/agent/settings.json`:

```json
{
  "skills": ["C:/Users/younglet/pi-skills", "C:/Users/younglet/skills"]
}
```
