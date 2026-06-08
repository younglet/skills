#!/usr/bin/env python3
"""
Xiaomi MiMo TTS — 小米米墨语音合成
OpenAI-compatible chat completions API for text-to-speech.

Usage:
  Interactive mode (default):  python tts.py
  Single text:                 python tts.py --text "Hello"
  From file:                   python tts.py --file speaking_bank.txt
  From mimo-script JSON:       python tts.py --json script.json
"""

import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
from openai import OpenAI

# ─── Voice registry ───
VOICES = {
    "冰糖": {"lang": "zh", "gender": "F"},
    "茉莉": {"lang": "zh", "gender": "F"},
    "苏打": {"lang": "zh", "gender": "M"},
    "白桦": {"lang": "zh", "gender": "M"},
    "Mia":   {"lang": "en", "gender": "F"},
    "Chloe": {"lang": "en", "gender": "F"},
    "Milo":  {"lang": "en", "gender": "M"},
    "Dean":  {"lang": "en", "gender": "M"},
}

BASE_URL = "https://api.xiaomimimo.com/v1"
DEFAULT_MODEL = "mimo-v2.5-tts"


def clean_text(text: str) -> str:
    """Remove pronunciation annotations so TTS reads clean English."""
    text = re.sub(r"\*\*", "", text)           # bold markers
    text = re.sub(r"[₍₎]", "", text)            # unreleased stop markers
    text = re.sub(r"\s*‿\s*", " ", text)        # linking symbol → space
    text = re.sub(r"\s*[,]?\s*/\s*", ", ", text) # thought group / → comma
    text = re.sub(r"\s+", " ", text).strip()
    return text


def call_mimo_tts(
    api_key: str,
    text: str,
    voice: str = "Chloe",
    style: str = "",
    model: str = DEFAULT_MODEL,
    fmt: str = "wav",
) -> bytes:
    """Call MiMo TTS and return raw audio bytes."""
    client = OpenAI(api_key=api_key, base_url=BASE_URL)

    assistant_content = text
    if style:
        assistant_content = f"({style}){text}"

    user_content = ""
    if voice in ("Mia", "Chloe", "Milo", "Dean"):
        user_content = "Natural, expressive American English. Clear pronunciation."

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ],
        audio={"format": fmt, "voice": voice},
    )

    message = completion.choices[0].message
    audio_data = getattr(message, "audio", None)
    if audio_data is None:
        raise RuntimeError("No audio data in response")

    return base64.b64decode(audio_data.data)


def parse_coach_output(text: str) -> list[dict]:
    """Parse spoken-english-coach output, extract speaking bank sections.
    Only parses within the 口语 Bank / Speaking Bank section."""
    # Normalize line endings to \n
    text = text.replace("\r\n", "\n")

    # Isolate the speaking bank section (between "### 3️⃣" and the next "###")
    bank_match = re.search(
        r'###\s*3️⃣.*?口语\s*Bank.*?\n(.*?)(?=\n###\s*4️⃣|\n###\s*[45])',
        text, re.DOTALL
    )
    if not bank_match:
        # Fallback: try English "Speaking Bank"
        bank_match = re.search(
            r'###\s*3️⃣.*?Speaking\s*Bank.*?\n(.*?)(?=\n###\s*4️⃣|\n###\s*[45])',
            text, re.DOTALL
        )
    if not bank_match:
        return []

    bank_text = bank_match.group(1)

    sections = []
    pattern = r"#### ([A-D])\. (.+?)\n(.+?)(?=\n\n####|\n\n---|\Z)"

    for m in re.finditer(pattern, bank_text, re.DOTALL):
        label = m.group(1)
        name = m.group(2).strip()
        block = m.group(3).strip()

        if label in ("C", "D"):
            # Split short combinations by period + optional slash
            raw = re.split(r"\.\s*(?:/?\s*)", block)
            sentences = [s.strip() for s in raw if s.strip() and len(s.strip()) > 10]
            sentences = [s if s.endswith(".") else s + "." for s in sentences]
        else:
            sentences = [block]

        sections.append({
            "label": label,
            "name": name,
            "type": "short" if label in ("C", "D") else "long",
            "sentences": sentences,
        })

    return sections


# ═══════════════════════════════════════════════════════════
# Interactive Shell
# ═══════════════════════════════════════════════════════════

HELP_TEXT = """
╔══════════════════════════════════════════════╗
║      MiMo TTS Shell — 命令参考              ║
╠══════════════════════════════════════════════╣
║  直接输入文字  → 朗读                         ║
║                                               ║
║  :voice <name>  → 切换音色                    ║
║  :style <tag>   → 设置情感/风格               ║
║  :speed <n>     → 语速 (slow/normal/fast)     ║
║  :format <fmt>  → 格式 (wav/mp3)              ║
║  :voices        → 列出所有音色                ║
║  :status        → 查看当前设置                ║
║  :play <file>   → 播放最近音频 (Windows)      ║
║  :dir           → 打开输出目录                 ║
║  :save <text>   → 合成并保存                   ║
║  :help / :h     → 显示帮助                    ║
║  :quit / :q     → 退出                         ║
╚══════════════════════════════════════════════╝
"""


def print_voices():
    """Print available voices in a nice table."""
    print()
    print("┌────────┬────────┬────────┐")
    print("│ Voice  │ Lang   │ Gender │")
    print("├────────┼────────┼────────┤")
    for name, info in VOICES.items():
        lang = "中文" if info["lang"] == "zh" else "English"
        gender = "女" if info["gender"] == "F" else "男"
        print(f"│ {name:<6} │ {lang:<6} │ {gender:<6} │")
    print("└────────┴────────┴────────┘")
    print()


def print_status(voice, style, fmt, out_dir, counter):
    """Print current shell settings."""
    print()
    print(f"  音色 : {voice}")
    print(f"  风格 : {style or '(无)'}")
    print(f"  格式 : {fmt}")
    print(f"  输出 : {out_dir}")
    print(f"  已生成: {counter} 个文件")
    print()


def interactive_shell(api_key, initial_voice, initial_style, initial_model, initial_fmt, out_dir):
    """Run the TTS interactive command-line shell."""
    voice = initial_voice
    style = initial_style
    model = initial_model
    fmt = initial_fmt
    counter = 0

    print()
    print("╔══════════════════════════════════════╗")
    print("║   MiMo TTS Shell — 小米米墨语音合成  ║")
    print("╠══════════════════════════════════════╣")
    print(f"║   音色: {voice:<28}║")
    print(f"║   风格: {style or '(无)':<28}║")
    print(f"║   格式: {fmt:<28}║")
    print("╠══════════════════════════════════════╣")
    print("║   输入文字直接朗读 | :help 查看命令   ║")
    print("╚══════════════════════════════════════╝")
    print()

    out_dir.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            raw = input("tts> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not raw:
            continue

        # ── Commands ──
        if raw.startswith(":") or raw.startswith("："):  # support Chinese colon
            cmd_line = raw.lstrip(":：")
            parts = cmd_line.split(maxsplit=1)
            cmd = parts[0].lower() if parts else ""
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("q", "quit", "exit"):
                print("再见!")
                break

            elif cmd in ("h", "help", "?"):
                print(HELP_TEXT)

            elif cmd == "voice":
                if not arg:
                    print("用法: :voice <名称>")
                    print(f"可选: {', '.join(VOICES.keys())}")
                    continue
                if arg in VOICES:
                    voice = arg
                    print(f"✓ 音色已切换为: {voice}")
                else:
                    print(f"✗ 未知音色: {arg}")
                    print(f"  可选: {', '.join(VOICES.keys())}")

            elif cmd == "style":
                style = arg
                print(f"✓ 风格已设置为: {style or '(清除)'}")

            elif cmd == "format":
                if arg in ("wav", "mp3"):
                    fmt = arg
                    print(f"✓ 格式已切换为: {fmt}")
                else:
                    print("格式只能是 wav 或 mp3")

            elif cmd == "voices":
                print_voices()

            elif cmd == "status":
                print_status(voice, style, fmt, out_dir, counter)

            elif cmd == "dir":
                os.startfile(str(out_dir))
                print(f"已打开: {out_dir}")

            elif cmd == "save":
                # :save <text> — explicitly save with given text
                text = arg
                if not text:
                    print("用法: :save <要合成的文字>")
                    continue
                counter += 1
                filename = f"tts_{counter:03d}.{fmt}"
                fpath = out_dir / filename
                print(f"[合成] {filename}")
                print(f"       {text[:70]}{'...' if len(text) > 70 else ''}")
                try:
                    audio = call_mimo_tts(api_key, text, voice=voice, style=style,
                                          model=model, fmt=fmt)
                    fpath.write_bytes(audio)
                    print(f"       ✓ 已保存 ({len(audio) // 1024} KB)")
                except Exception as e:
                    print(f"       ✗ 失败: {e}")
                    counter -= 1

            elif cmd == "play":
                # Play the most recent file
                import glob as _glob
                files = sorted(out_dir.glob(f"*.{fmt}"), key=lambda p: p.stat().st_mtime, reverse=True)
                if files:
                    os.startfile(str(files[0]))
                    print(f"▶ 播放: {files[0].name}")
                else:
                    print("没有已生成的音频文件")

            else:
                print(f"未知命令: {cmd}  (输入 :help 查看帮助)")

            continue

        # ── Plain text → speak it ──
        text = clean_text(raw)
        if len(text) < 2:
            print("文字太短，请输入更多内容")
            continue

        counter += 1
        filename = f"tts_{counter:03d}.{fmt}"
        fpath = out_dir / filename

        print(f"[合成] {filename}  ({voice}{' · ' + style if style else ''})")
        print(f"       {text[:70]}{'...' if len(text) > 70 else ''}")

        try:
            audio = call_mimo_tts(api_key, text, voice=voice, style=style,
                                  model=model, fmt=fmt)
            fpath.write_bytes(audio)
            print(f"       ✓ 已保存 ({len(audio) // 1024} KB)")

            # Auto-play on Windows
            if sys.platform == "win32":
                os.startfile(str(fpath))
                print(f"       ▶ 正在播放...")
        except Exception as e:
            print(f"       ✗ 失败: {e}")
            counter -= 1


# ═══════════════════════════════════════════════════════════
# Batch mode (--text / --file)
# ═══════════════════════════════════════════════════════════

def batch_generate(api_key, args, out_dir):
    """Original batch generation from --text or --file."""
    results = []

    if args.file:
        raw = Path(args.file).read_text(encoding="utf-8")
        sections = parse_coach_output(raw)

        if not sections:
            print("WARN: No speaking-bank sections found.")
            sys.exit(1)

        for sec in sections:
            label = sec["label"]
            for i, sentence in enumerate(sec["sentences"]):
                clean = clean_text(sentence)
                if not clean or len(clean) < 3:
                    continue

                if sec["type"] == "long":
                    filename = f"{'长句'}{'1' if label == 'A' else '2'}.wav"
                else:
                    combo = "1" if label == "C" else "2"
                    filename = f"短句组合{combo}_{i+1}.wav"

                print(f"[GEN] {filename}")
                print(f"      {clean[:90]}{'...' if len(clean) > 90 else ''}")

                try:
                    audio = call_mimo_tts(api_key, clean, voice=args.voice, style=args.style,
                                          model=args.model, fmt=args.format)
                    fpath = out_dir / filename
                    fpath.write_bytes(audio)
                    print(f"      OK  ({len(audio) // 1024} KB)")
                    results.append({"filename": filename, "text": clean, "path": str(fpath)})
                except Exception as e:
                    print(f"      FAIL: {e}", file=sys.stderr)

    elif args.text:
        clean = clean_text(args.text)
        sentences = re.split(r"(?<=[a-z)])[.!?]\s+", clean)
        sentences = [s.strip().rstrip(".") + "." for s in sentences if s.strip()]

        for i, s in enumerate(sentences):
            if len(s) < 3:
                continue
            filename = f"sentence_{i+1:02d}.{args.format}"
            print(f"[GEN] {filename}")
            print(f"      {s[:90]}{'...' if len(s) > 90 else ''}")

            try:
                audio = call_mimo_tts(api_key, s, voice=args.voice, style=args.style,
                                      model=args.model, fmt=args.format)
                fpath = out_dir / filename
                fpath.write_bytes(audio)
                print(f"      OK  ({len(audio) // 1024} KB)")
                results.append({"filename": filename, "text": s, "path": str(fpath)})
            except Exception as e:
                print(f"      FAIL: {e}", file=sys.stderr)

    # Metadata
    meta_path = out_dir / "sentences.json"
    meta = {
        "topic": args.topic,
        "voice": args.voice,
        "style": args.style,
        "model": args.model,
        "generated": datetime.now().isoformat(),
        "sentences": results,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDone: {len(results)} files -> {out_dir}")
    print(f"Meta: {meta_path}")


# ═══════════════════════════════════════════════════════════
# JSON mode (mimo-script output)
# ═══════════════════════════════════════════════════════════

def _safe_dirname(heading: str) -> str:
    """Sanitize heading for use as directory/file name."""
    # Replace Windows-illegal chars with underscore
    safe = re.sub(r'[<>:"/\\|?*]', '_', heading)
    safe = safe.strip().rstrip('.')
    return safe if safe else "section"


# Reverse mapping: TTS spelled-out → original form for SRT display
_TTS_TO_SUB = {
    "S S H": "ssh",
    "N M C L I": "nmcli",
    "W LAN 零": "wlan0",
    "Power Shell": "PowerShell",
    "VS Code": "VSCode",
    "Git Graph": "GitGraph",
    "Git Lens": "GitLens",
    "read me": "README",
    "wheel": "whl",
    "arm": "ARM",
    "Control Shift P": "Ctrl+Shift+P",
    "Remote SSH": "Remote - SSH",
    "git version": "git --version",
}


def _strip_mimo_tags(text: str, for_subtitle: bool = False) -> str:
    """Remove MiMo annotations and restore original forms.
    
    If for_subtitle, also strip all punctuation except commas and question marks,
    as defined in mimo-tags.json subtitle.keepPunctuation.
    """
    # Remove emotion/dialect tags: (开心), (东北话), etc.
    text = re.sub(r'\([^)]*\)', '', text)
    # Remove effect tags: [停顿], [深吸一口气], etc.
    text = re.sub(r'\[[^\]]*\]', '', text)
    # Restore IP addresses: 192 点 168 点 55 点 1 → 192.168.55.1
    text = re.sub(r'(\d+)\s*点\s*(\d+)\s*点\s*(\d+)\s*点\s*(\d+)', r'\1.\2.\3.\4', text)
    # Restore spelled-out forms first
    for tts_form, orig_form in _TTS_TO_SUB.items():
        text = text.replace(tts_form, orig_form)
    # Restore ssh user at host → ssh user@host (after S S H → ssh)
    text = re.sub(r'(ssh\s+\S+)\s+at\s+', r'\1@', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s*。', '。', text)
    text = re.sub(r'\s*，', '，', text)

    if for_subtitle:
        # Strip all punctuation except commas and question marks
        # Remove Chinese punctuation (except ， and ？)
        text = re.sub(r'[。！；：、…～]', '', text)
        # Remove ASCII punctuation (except , and ?)
        text = re.sub(r'[!.;:\'\"@#|\\/\-\–—]', '', text)
        # Clean up any double spaces caused by punctuation removal
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove stray leading/trailing punctuation marks like commas
        text = text.strip('，, ')

    return text


def _split_for_subtitle(text: str, max_chars: int = 24, min_chars: int = 4) -> list[str]:
    """Split a long line into subtitle-friendly chunks.
    
    Splits at [停顿], then at 。！？, then at ，. Won't split if the
    resulting chunk would be too short (min_chars) to avoid fragments.
    """
    if len(text) <= max_chars:
        return [text]

    # Split at [停顿] boundaries first
    parts = re.split(r'(\[停顿\])', text)
    chunks = []
    buffer = ""
    for part in parts:
        if not part:
            continue
        if part == "[停顿]":
            if buffer.strip():
                chunks.append(buffer.strip())
            buffer = ""
        else:
            buffer += part
    if buffer.strip():
        chunks.append(buffer.strip())

    if not chunks:
        return [text]

    # Split at sentence-level punctuation, but keep adjacent short pieces
    final = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            final.append(chunk)
        else:
            sub = re.split(r'(?<=[。！？，,])', chunk)
            merged = []
            for sp in sub:
                sp = sp.strip().rstrip('。！？，,')
                if not sp:
                    continue
                if len(sp) <= max_chars:
                    if merged and len(merged[-1]) + len(sp) + 1 <= max_chars:
                        merged[-1] = merged[-1] + '，' + sp
                    elif len(sp) >= min_chars:
                        merged.append(sp)
                else:
                    merged.append(sp)
            final.extend(merged)

    return final if final else [text]


def _format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_from_json(api_key, json_path, model=DEFAULT_MODEL, output_dir=None):
    """Read a mimo-script JSON and generate audio per line + SRT subtitles.

    Input JSON uses flat 'lines' array (no sections/headings).
    Each line already contains MiMo annotations.

    Output:
      <topic>/
        ├── 0001.wav
        ├── 0002.wav
        ├── ...
        ├── subtitles.srt   ← millisecond precision, commas & question marks only
        ├── full.wav
        └── sentences.json
    """
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))

    voice = data.get("voice", "Chloe")
    fmt = data.get("format", "wav")
    topic = data.get("topic", "general")

    if output_dir:
        base_dir = Path(output_dir) / topic
    else:
        base_dir = Path.home() / "Documents" / "spoken-english" / topic
    base_dir.mkdir(parents=True, exist_ok=True)

    results = []
    srt_entries = []
    elapsed = 0.0
    lines = data.get("lines", [])
    total_lines = len(lines)

    for li, line in enumerate(lines):
        text = line.strip()
        if not text or len(text) < 2:
            continue

        # Split long lines at [停顿] for better subtitle pacing
        is_last_line = (li == total_lines - 1)
        sub_chunks = _split_for_subtitle(text)

        for ci, chunk in enumerate(sub_chunks):
            is_last_chunk = is_last_line and (ci == len(sub_chunks) - 1)
            tts_text = chunk + (" [停顿]" if is_last_chunk else "")

            chunk_suffix = f"_{ci+1}" if len(sub_chunks) > 1 else ""
            filename = f"{li+1:04d}{chunk_suffix}.{fmt}"
            fpath = base_dir / filename

            if len(sub_chunks) > 1:
                print(f"[合成] {filename}  (拆分 {ci+1}/{len(sub_chunks)})")
            else:
                print(f"[合成] {filename}")
            print(f"       {chunk[:80]}{'...' if len(chunk) > 80 else ''}")

            try:
                audio = call_mimo_tts(api_key, tts_text, voice=voice, style="",
                                      model=model, fmt=fmt)
                fpath.write_bytes(audio)

                import soundfile as sf
                info = sf.info(str(fpath))
                duration = info.duration

                start = elapsed
                elapsed += duration

                print(f"       ✓ 已保存 ({len(audio) // 1024} KB, {duration:.3f}s)")

                results.append({
                    "index": li + 1,
                    "text": chunk,
                })

                # Subtitle: strip MiMo tags, keep only commas & question marks
                sub_text = _strip_mimo_tags(chunk, for_subtitle=True)
                srt_entries.append({
                    "index": len(srt_entries) + 1,
                    "start": start,
                    "end": elapsed,
                    "text": sub_text,
                })

            except Exception as e:
                print(f"       ✗ 失败: {e}")

    # Write SRT with millisecond precision
    srt_path = base_dir / "subtitles.srt"
    srt_lines = []
    for entry in srt_entries:
        srt_lines.append(str(entry["index"]))
        srt_lines.append(f"{_format_srt_time(entry['start'])} --> {_format_srt_time(entry['end'])}")
        srt_lines.append(entry["text"])
        srt_lines.append("")
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
    print(f"\nSRT: {srt_path} ({len(srt_entries)} 条字幕)")

    # Merge all audio into full track
    if fmt == "wav":
        import soundfile as sf
        wav_files = sorted(base_dir.glob(f"*.{fmt}"))
        if wav_files:
            merged = []
            sr = None
            for f in wav_files:
                audio_chunk, sr = sf.read(str(f))
                merged.append(audio_chunk)
            if merged and sr:
                full_audio = np.concatenate(merged)
                full_path = base_dir / f"full.{fmt}"
                sf.write(str(full_path), full_audio, sr)
                print(f"合并: {full_path} ({len(full_audio)/sr:.1f}s)")

    # Metadata
    meta_path = base_dir / "sentences.json"
    meta = {
        "title": data.get("title", ""),
        "role": data.get("role", ""),
        "voice": voice,
        "topic": topic,
        "model": model,
        "generated": datetime.now().isoformat(),
        "total": len(results),
        "sentences": results,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done: {len(results)} files -> {base_dir}")


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="MiMo TTS — Xiaomi Speech Synthesis")
    parser.add_argument("--text", help="Text to speak")
    parser.add_argument("--file", help="Path to spoken-english-coach output")
    parser.add_argument("--json", help="Path to mimo-script JSON file")
    parser.add_argument("--voice", default="Chloe", help="Voice ID (default: Chloe)")
    parser.add_argument("--style", default="", help='Style tag e.g. "Happy", "Whisper", "叹气"')
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model ID")
    parser.add_argument("--format", default="wav", choices=["wav", "mp3"], help="Output format")
    parser.add_argument("--topic", default="general", help="Topic subfolder name")
    parser.add_argument("--output-dir", help="Custom output directory")
    parser.add_argument("--api-key", help="MiMo API key (or set MIMO_API_KEY)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Force interactive mode")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("MIMO_API_KEY")
    if not api_key:
        print("ERROR: Missing API key. Set MIMO_API_KEY or use --api-key", file=sys.stderr)
        sys.exit(1)

    # ── Mode selection ──
    if args.json:
        generate_from_json(api_key, args.json, model=args.model, output_dir=args.output_dir)
    elif args.interactive or (not args.text and not args.file):
        if args.output_dir:
            out_dir = Path(args.output_dir)
        else:
            out_dir = Path.home() / "Documents" / "spoken-english" / args.topic
        interactive_shell(api_key, args.voice, args.style, args.model, args.format, out_dir)
    else:
        if args.output_dir:
            out_dir = Path(args.output_dir)
        else:
            out_dir = Path.home() / "Documents" / "spoken-english" / args.topic
        out_dir.mkdir(parents=True, exist_ok=True)
        batch_generate(api_key, args, out_dir)


if __name__ == "__main__":
    main()
