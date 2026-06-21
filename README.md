---
name: young-skills
description: Personal pi skill repository for multi-device sync. Contains 10 skills spanning MicroPython, TTS, quizzes, English coaching, file serving, and dev tooling.
disable-model-invocation: true
---

# PI Skill Repo (multi-device sync)

Personal skill repository for [pi coding agent](https://github.com/badlogic/pi).

## Skills

| Skill | Description |
|-------|-------------|
| [awesome-micropython-skill](./awesome-micropython-skill/) | MicroPython v1.28.0 ESP32 — 53 verified API/type JSONs, device validator, auto-fixer, 91 CPython-missing methods. Includes mp-device sub-skill. |
| [novamp1.0](./novamp1.0/) | NovaMP v1.0 firmware wrapper — 16 hardware drivers (WiFi, NTP, LED, motor, servo, OLED...) on Stemstar's customized MicroPython. Peer skill of awesome-micropython-skill. |
| [cleanup-dev-artifacts](./cleanup-dev-artifacts/) | Post-dev cleanup scanner — remove requirement-change commentary, debug prints, dev journals. |
| [design-roast](./design-roast/) | Technical problem diagnosis in savage Tieba-bro style — skill issue or design disaster? |
| [lan-file-server](./lan-file-server/) | Local HTTP file server with upload/download/delete over WiFi LAN. Drag-and-drop, dark UI. |
| [mimo-script](./mimo-script/) | Add MiMo TTS annotations to scripts, output JSON for direct TTS consumption. |
| [mimo-tts](./mimo-tts/) | Convert English/Chinese text to speech via Xiaomi MiMo TTS API (OpenAI-compatible). |
| [quiz-generator](./quiz-generator/) | Generate quiz JSON files for Open Quiz app. Single/multiple choice with Markdown/LaTeX. |
| [spoken-english-coach](./spoken-english-coach/) | American English pronunciation practice materials with stress patterns, linking, thought groups. |
| [yazi-setup](./yazi-setup/) | Setup and configure Yazi terminal file manager with plugins. Covers Windows & Unix. |

## Version manifest

See [awesome-micropython.md](./awesome-micropython.md) for the version manifest tracking compatible NovaMP companion skills.

## Usage

Configure pi to load skills from this repo by adding to `~/.pi/agent/settings.json`:

```json
{
  "skills": ["C:/Users/young/skills"]
}
```

Or for other devices, use the appropriate path (e.g., `/home/user/skills` on Linux/macOS).