---
name: mimo-tts
description: Convert English/Chinese text to natural speech audio using Xiaomi MiMo TTS API (OpenAI-compatible). Supports emotion, style tags, and voice selection. Saves organized MP3/WAV files to Documents/spoken-english/.
---

# Xiaomi MiMo TTS — 小米米墨语音合成

## Setup

```bash
cd ~/.pi/agent/skills/mimo-tts && pip install -r requirements.txt
```

设置环境变量：

```bash
setx MIMO_API_KEY "your-api-key"
```

## 用法

### 🎮 交互模式（默认）
直接运行进入 TTS Shell，输入文字即可朗读：
```bash
python tts.py
```

```
tts> Hello world!                    # 输入文字直接合成+播放
tts> :voice 冰糖                      # 切换音色
tts> :style Happy                     # 设置风格
tts> :voices                         # 列出所有音色
tts> :status                         # 查看当前设置
tts> :help                           # 命令帮助
```

### 单句朗读
```bash
python tts.py --text "The first step is to connect the Jetson Nano to the network." --voice Chloe
```

### 带情感/风格
```bash
python tts.py --text "Tomorrow is Friday, so happy!" --voice Chloe --style "Happy"
python tts.py --text "我真的太累了..." --voice 茉莉 --style "疲惫 叹气"
```

### 朗读口语 Bank 文件
```bash
python tts.py --file speaking_bank.txt --voice Chloe --topic "backronyms"
```

### Shell 命令速查

| 命令 | 说明 |
|------|------|
| 直接输入文字 | 合成并播放 |
| `:voice <名称>` | 切换音色 |
| `:style <标签>` | 设置情感/风格 |
| `:format wav\|mp3` | 设置输出格式 |
| `:voices` | 列出所有音色 |
| `:status` | 当前设置 |
| `:save <文字>` | 合成并保存（不播放） |
| `:play` | 播放最近生成的音频 |
| `:dir` | 打开输出目录 |
| `:help` / `:h` | 帮助 |
| `:quit` / `:q` | 退出 |

## 声音列表

| 中文 | 英文 | Voice ID |
|------|------|----------|
| 冰糖 (女) | — | `冰糖` |
| 茉莉 (女) | — | `茉莉` |
| 苏打 (男) | — | `苏打` |
| 白桦 (男) | — | `白桦` |
| — | Mia (F) | `Mia` |
| — | Chloe (F) | `Chloe` |
| — | Milo (M) | `Milo` |
| — | Dean (M) | `Dean` |

## 输出

```
~/Documents/spoken-english/<topic>/
├── sentence_01.mp3
├── sentence_02.mp3
└── sentences.json
```

> 💡 目前免费
