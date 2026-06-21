---
name: awesome-micropython
description: Version manifest for the awesome-micropython skill family. Documents which NovaMP versions and companion sub-skills are tracked and compatible. Index file for the awesome-micropython-skill folder.
disable-model-invocation: true
version: "1.0.0"
last_updated: "2026-06-21"
---

# awesome-micropython — version manifest

This file is the **top-level version manifest** for the `awesome-micropython` skill family.

## Layout

```
~/.skills/
├── README.md                       personal skill repo index
├── awesome-micropython.md          ← this file (version manifest)
├── awesome-micropython-skill/      core skill — standard MicroPython v1.28.0 ESP32
│   ├── SKILL.md
│   ├── api/                        53 device-verified MicroPython JSONs
│   ├── hardware/                   pinout + component recipes
│   ├── patterns/                   code architecture patterns
│   ├── mp-device/                  device interaction sub-skill
│   └── ...
├── novamp1.0/                      🔵 NovaMP firmware v1.0 (Stemstar custom) — peer skill
│   ├── SKILL.md
│   ├── api/                        16 NovaMP driver JSONs (wifi, time_sync, led, ...)
│   ├── patterns/                   boot-with-wifi, .test(), .help()
│   └── pitfalls.json
└── (future) novamp1.1/ novamp2.0/  per-firmware-version standalone skills
```

## Tracked companion skills

Each NovaMP firmware version is tracked as a **standalone peer skill**, not a sub-skill.

| Companion skill | Firmware | Released | Publisher | Status |
|-----------------|----------|----------|-----------|--------|
| [`novamp1.0/`](novamp1.0/SKILL.md) | NovaMP v1.0 | 2026-06-21 | Stemstar Education | ✅ Stable |
| `novamp1.1/` | NovaMP v1.1 | (TBD) | Stemstar Education | 📋 Planned |
| `novamp2.0/` | NovaMP v2.0 | (TBD) | Stemstar Education | 📋 Planned |

## Skill name → folder mapping

The folder name **encodes the version** (`novamp1.0`). When loading the skill, use the exact folder name — do not strip the version suffix.

```python
# Loading via pi skill loader
"skills": [
  "C:/Users/younglet/skills/awesome-micropython-skill",   # core
  "C:/Users/younglet/skills/novamp1.0"                    # NovaMP v1.0 wrapper
]
```

## Compatibility matrix

| MicroPython version | awesome-micropython-skill | novamp1.0 | novamp1.1 | novamp2.0 |
|---------------------|---------------------------|-----------|-----------|-----------|
| v1.28.0             | ✅ current                | ✅ current| 📋        | 📋        |
| v1.27.0             | ⚠️ legacy                 | ⚠️ partial| 📋        | 📋        |
| v1.20.x and earlier | ❌ unsupported            | ❌        | ❌        | ❌        |

## Adding a new NovaMP version skill

When a new NovaMP firmware ships:

1. Create `~/.skills/novamp<MAJOR>.<MINOR>/` as a sibling folder
2. Copy the SKILL.md template and update `version`, `released`, `name` headers
3. Update each `api/<module>.json` if the upstream driver changed
4. Add a row to the **Tracked companion skills** table above
5. Update the **Compatibility matrix** if MicroPython baseline changed
6. Bump `last_updated` in this file's frontmatter
7. Commit to the skill repo

## See also

- `README.md` — top-level index
- `awesome-micropython-skill/SKILL.md` — core skill entry
- `novamp1.0/SKILL.md` — NovaMP v1.0 entry