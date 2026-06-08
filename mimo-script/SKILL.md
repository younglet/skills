---
name: mimo-script
description: Add MiMo TTS annotations to an existing script and output as JSON for direct TTS consumption. Supports configurable roles (tutorial, storytelling, productIntro, casual) via mimo-tags.json.
---

# MiMo 逐字稿标注

把已经写好的脚本，标注上 MiMo TTS 官方语法，输出 JSON 文件。`mimo-tts --json` 可直接合成音频 + 导出 SRT 字幕。

## 配置文件

- [mimo-tags.json](mimo-tags.json) — 全部标签定义 + 角色预设 + 字幕规则

## 角色系统

| 角色 | 音色 | 语气 | 场景 |
|------|------|------|------|
| `tutorial` | 冰糖 | 严肃 | 教程讲解 |
| `storytelling` | 茉莉 | 温柔 | 讲故事 |
| `productIntro` | 苏打 | 磁性 | 产品介绍 |
| `casual` | 冰糖 | 活泼 | 闲聊 vlog |

## 核心规则

### 行长度严格控制

**每行 ≤ 24 字**（不含 MiMo 标注符）。这是最硬性的约束。

```
✅ "首先确认设备已连接。[停顿]"        （11 字）
✅ "然后输入以下命令。[停顿]"           （10 字）
❌ "首先确认设备已连接，然后输入以下命令来启动服务。[停顿]"  （24+ 字）
```

> 长句必须在 `[停顿]` 处拆分成多行。宁可多拆，不可越界。

### 字幕规则

字幕从标注行自动提取，处理规则：
- **保留**：逗号（，,）、问号（？?）
- **移除**：句号（。）、感叹号（！）、分号（；）、冒号（：）、顿号（、）、省略号（…）等一切其他标点
- 字幕不含 MiMo 标签，纯文字

### 标注密度

每 3-5 句一个标注，宁少勿多。最后一句末尾必须加 `[停顿]` 防止音频截断。

### 命令/代码处理

命令和代码不能直接扔给 TTS 读，要分情况处理：

**保持原样**（TTS 能读对）：
- 由常见英文单词组成的命令：`git clone`、`sudo apt install`、`python`
- 完整英文短语：`password`、`connect`

**替换为可读写法**（嵌入原文，不额外标注）：

| 原文 | TTS 写法 | 原因 |
|------|----------|------|
| `ssh` | S S H | 缩写，逐字母 |
| `ip addr` | IP addr | IP 大写，addr 可读 |
| `wlan0` | W LAN 零 | 混合缩写 |
| `nmcli` | N M C L I | 无对应单词 |
| `WiFi` | WiFi | 常见词，不用拆 |
| `pip install` | pip install | 可读 |
| `192.168.55.1` | 一 九 二 点 一 六 八 点 五 五 点 一 | IP 地址，逐位数字朗读 |
| `git --version` | git version | 去掉 `--` |
| `Ctrl+Shift+P` | Control Shift P | 展开修饰键 |

**规则**：命令前后各加 `[停顿]`；缩写逐字母写开（G P U、S S H、A P I）；IP 用中文"点"连接、逐位数字朗读

## 输出 JSON 格式

```json
{
  "title": "脚本标题",
  "role": "tutorial",
  "voice": "冰糖",
  "format": "wav",
  "topic": "topic-name",
  "lines": [
    "(严肃)首先确认设备已连接。[停顿]",
    "随后打开终端输入以下命令。[停顿]",
    "S S H username at 一 九 二 点 一 六 八 点 五 五 点 一。[停顿]"
  ]
}
```

> 无章节/段落标题。`lines` 是扁平数组，每行对应的字幕行在合成时由脚本自动提取。

## 工作流程

用户给一段定稿文字 + 指定角色（默认 `tutorial`），你：

1. 加载 [mimo-tags.json](mimo-tags.json)
2. 按角色规则插入 MiMo 标注
3. **严格按 24 字/行拆分**
4. 命令/代码按替换表处理
5. 输出 JSON 文件

## 合成输出

```bash
python tts.py --json script.json
```

自动生成：
```
Documents/spoken-english/<topic>/
├── 0001.wav        ← 每行一个音频
├── 0002.wav
├── ...
├── subtitles.srt   ← SRT 字幕（毫秒精度，纯文字）
├── full.wav         ← 合并音频
└── sentences.json   ← 元数据
```
