# 通用题库 JSON 格式规范 v3.0

## 完整 Schema

```json
{
  "meta": {
    "title": "题库名称",
    "description": "简短描述（1句话）",
    "version": "3.0",
    "tags": ["标签1", "标签2"],
    "question_count": 10
  },
  "questions": [
    {
      "type": "single",
      "stem": "题干文本（支持 Markdown）",
      "options": [
        {"text": "正确选项", "is_correct": true},
        {"text": "错误选项", "is_correct": false},
        {"text": "错误选项", "is_correct": false},
        {"text": "错误选项", "is_correct": false}
      ],
      "explanation": "详细解析（支持 Markdown）",
      "tags": ["子标签"]
    },
    {
      "type": "multiple",
      "stem": "多选题题干",
      "options": [
        {"text": "正确选项 A", "is_correct": true},
        {"text": "错误选项", "is_correct": false},
        {"text": "正确选项 B", "is_correct": true},
        {"text": "错误选项", "is_correct": false}
      ],
      "explanation": "解析说明为什么这些选项正确",
      "tags": ["子标签"]
    }
  ]
}
```

## 字段说明

### meta

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 题库名称，显示在应用标题栏 |
| `description` | string | 是 | 简短描述，显示在快速加载列表 |
| `version` | string | 否 | 固定 `"3.0"` |
| `tags` | string[] | 否 | 全局标签 |
| `question_count` | number | 否 | 题目总数（可自动计算） |

### questions[]

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 否 | `"single"` 单选题，`"multiple"` 多选题。不填则自动检测（多个 is_correct 视为多选） |
| `stem` | string | 是 | 题干，支持 Markdown / LaTeX |
| `options` | array | 是 | 选项数组，建议 4 个 |
| `options[].text` | string | 是 | 选项文本，**不要**加 A. B. C. 等前缀，应用动态分配字母 |
| `options[].is_correct` | boolean | 是 | 是否为正确答案。单选 1 个 true，多选 2+ 个 true |
| `explanation` | string | 是 | 解析，解释为什么对/错 |
| `tags` | string[] | 否 | 题目标签，显示在题目标签栏 |

## Markdown 语法支持

| 语法 | 效果 |
|------|------|
| `**粗体**` | **粗体** |
| `` `code` `` | 行内代码 |
| ` ``` ` 代码块 | 多行代码（支持语言高亮） |
| `$E=mc^2$` | 行内 LaTeX 公式 |
| `$$\sum x$$` | 块级 LaTeX 公式 |
| `- 列表` | 无序列表 |
| `1. 列表` | 有序列表 |

**注意**: 不要在选项 text 中加 `A. ` `B. ` 等前缀。

## 单选题示例

```json
{
  "type": "single",
  "stem": "Python 中，以下哪个是**不可变**（immutable）数据类型？",
  "options": [
    {"text": "`list`", "is_correct": false},
    {"text": "`dict`", "is_correct": false},
    {"text": "`tuple`", "is_correct": true},
    {"text": "`set`", "is_correct": false}
  ],
  "explanation": "`tuple` 是不可变类型，创建后不能增删改元素。`list`、`dict`、`set` 都是可变类型。",
  "tags": ["Python", "基础"]
}
```

## 多选题示例

```json
{
  "type": "multiple",
  "stem": "以下哪些属于**关系型数据库**？",
  "options": [
    {"text": "MySQL", "is_correct": true},
    {"text": "MongoDB", "is_correct": false},
    {"text": "PostgreSQL", "is_correct": true},
    {"text": "SQLite", "is_correct": true}
  ],
  "explanation": "MySQL、PostgreSQL、SQLite 都是关系型数据库。MongoDB 是文档型 NoSQL 数据库。",
  "tags": ["数据库"]
}
```

## 完整题库示例

参见 `C:\Users\young\Documents\projects\model-quiz\quizzes\demo.json`
