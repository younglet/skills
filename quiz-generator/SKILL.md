---
name: quiz-generator
description: Generate quiz JSON files for the Open Quiz app. Creates single/multiple choice questions with Markdown/LaTeX support. Use when user asks to create quiz questions, generate a quiz, build a question bank, or make practice tests on any topic.
---

# 题库生成器 (Quiz Generator)

Generate structured quiz JSON files for the [Open Quiz](https://github.com) application.

## Quick Start

Copy this file to your agent's skill directory:

| Agent | Path |
|-------|------|
| Pi | `~/.pi/agent/skills/quiz-generator/SKILL.md` |
| Claude Code | `~/.claude/skills/quiz-generator/SKILL.md` |
| Codex | `~/.codex/skills/quiz-generator/SKILL.md` |
| 项目级 | `.agents/skills/quiz-generator/SKILL.md` |

Then ask your agent:
```
生成一个关于 XXX 的题库，50 题，中等难度
```

## What the Agent Should Do

1. Ask user: topic, question count, difficulty, single/mixed types
2. Generate questions following [the format spec](references/format-spec.md)
3. Save to `quizzes/<name>.json` in the project root

## Format Rules

- Options MUST NOT contain A/B/C/D prefixes — app assigns labels dynamically
- Each question: exactly one `is_correct: true` (single) or 2+ (multiple)
- Stem, options, explanation all support Markdown and `$LaTeX$`
- Write informative explanations (WHY, not just WHAT)

## Example Output

```json
{
  "meta": {
    "title": "Python 基础题库",
    "description": "Python 语法、数据结构、常用库",
    "version": "3.0",
    "tags": ["Python", "编程"]
  },
  "questions": [
    {
      "type": "single",
      "stem": "Python 中以下哪个是**不可变**类型？",
      "options": [
        {"text": "`list`", "is_correct": false},
        {"text": "`tuple`", "is_correct": true},
        {"text": "`dict`", "is_correct": false},
        {"text": "`set`", "is_correct": false}
      ],
      "explanation": "`tuple` 创建后不可修改。`list`/`dict`/`set` 都是可变类型。",
      "tags": ["基础"]
    }
  ]
}
```

See [references/format-spec.md](references/format-spec.md) for complete schema.
