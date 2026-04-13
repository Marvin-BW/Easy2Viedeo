"""
generate_srt.py - 使用 Whisper 从音频生成 SRT 字幕文件

使用方法：
  python generate_srt.py --audio ../remotion/public/audio.mp3 --output ../remotion/public/subtitles.srt

前置条件：
  pip install openai-whisper
  # 或使用 stable-whisper 获得更精确的时间轴：
  pip install stable-ts

说明：
  - 读取 TTS 生成的音频文件
  - 使用 Whisper 进行语音识别，提取逐词/逐句时间轴
  - 输出标准 SRT 格式字幕文件
  - 支持 stable-whisper（推荐，时间轴更精确）和标准 whisper 两种模式
"""

import os
import sys
import argparse
import re
from pathlib import Path


def generate_srt_stable_whisper(audio_path: str, output_path: str, model_size: str = "base"):
    """
    使用 stable-whisper 生成 SRT（推荐）

    stable-whisper 在标准 whisper 基础上优化了时间轴精度，
    特别适合 TTS 生成的清晰语音
    """
    try:
        import stable_whisper
    except ImportError:
        print("stable-whisper 未安装，将使用标准 whisper")
        return generate_srt_whisper(audio_path, output_path, model_size)

    print(f"加载 stable-whisper 模型: {model_size}")
    model = stable_whisper.load_model(model_size)

    print(f"正在转录: {audio_path}")
    result = model.transcribe(
        audio_path,
        language="zh",
        word_timestamps=True,
    )

    # 输出 SRT 文件（segment_level=False 表示逐词级别，True 表示逐句）
    result.to_srt_vtt(output_path, segment_level=True, word_level=False)

    print(f"✓ 字幕已保存到: {output_path}")
    print(f"  共 {len(result.segments)} 个字幕段")


def generate_srt_whisper(audio_path: str, output_path: str, model_size: str = "base"):
    """
    使用标准 whisper 生成 SRT

    如果 stable-whisper 不可用时的降级方案
    """
    try:
        import whisper
    except ImportError:
        print("错误: 请安装 whisper: pip install openai-whisper")
        sys.exit(1)

    print(f"加载 whisper 模型: {model_size}")
    model = whisper.load_model(model_size)

    print(f"正在转录: {audio_path}")
    result = model.transcribe(
        audio_path,
        language="zh",
        word_timestamps=True,
        verbose=False,
    )

    # 手动生成 SRT
    srt_content = segments_to_srt(result["segments"])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"✓ 字幕已保存到: {output_path}")
    print(f"  共 {len(result['segments'])} 个字幕段")


def segments_to_srt(segments: list) -> str:
    """将 whisper segments 转换为 SRT 格式"""
    lines = []

    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = seg["text"].strip()

        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")  # 空行分隔

    return "\n".join(lines)


def format_timestamp(seconds: float) -> str:
    """秒数转 SRT 时间戳格式 HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt_from_script(script_path: str, output_path: str):
    """
    备选方案：直接从 script.json 生成字幕

    当 Whisper 不可用时，使用 TTS 的时间估算生成近似字幕。
    字幕文本直接取自 narration 字段，时间使用 startFrame/endFrame 换算。
    精度不如 Whisper，但无需额外依赖。
    """
    import json

    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    fps = script["fps"]
    lines = []
    subtitle_index = 1

    for seg in script["segments"]:
        start_sec = seg["startFrame"] / fps
        end_sec = seg["endFrame"] / fps
        text = seg["narration"]

        # 将长文本分割为多行字幕（优先断句，避免标点落单）
        chunks = split_text(text, max_chars=25)

        # 按文本长度分配时长，比平均切分更贴近实际语速。
        durations = allocate_chunk_durations(
            chunks=chunks,
            total_duration=max(0.05, end_sec - start_sec),
        )

        cursor = start_sec
        for i, chunk in enumerate(chunks):
            chunk_start = cursor
            chunk_end = cursor + durations[i]
            if i == len(chunks) - 1:
                chunk_end = end_sec

            lines.append(f"{subtitle_index}")
            lines.append(
                f"{format_timestamp(chunk_start)} --> {format_timestamp(chunk_end)}"
            )
            lines.append(chunk)
            lines.append("")
            subtitle_index += 1
            cursor = chunk_end

    srt_content = "\n".join(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"✓ 基于脚本的字幕已保存到: {output_path}")


def split_text(text: str, max_chars: int = 25) -> list:
    """
    将中文文本按标点和长度分割

    优先在标点处断句，其次按最大字符数分割
    """
    normalized = normalize_subtitle_text(text)
    if not normalized:
        return [""]

    # 先按强标点断成小句，标点保留在句末。
    units = [
        u.strip()
        for u in re.findall(r"[^。！？!?；;]+[。！？!?；;]?", normalized)
        if u.strip()
    ]

    if not units:
        units = [normalized]

    chunks = []
    current = ""

    for unit in units:
        candidate = f"{current}{unit}" if current else unit
        if visible_len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        # 超长句：优先按逗号切，再按长度硬切。
        sub_units = [
            s.strip()
            for s in re.findall(r"[^，,]+[，,]?", unit)
            if s.strip()
        ]

        sub_current = ""
        for sub in sub_units:
            sub_candidate = f"{sub_current}{sub}" if sub_current else sub
            if visible_len(sub_candidate) <= max_chars:
                sub_current = sub_candidate
                continue

            if sub_current:
                chunks.append(sub_current)
                sub_current = ""

            if visible_len(sub) <= max_chars:
                sub_current = sub
            else:
                hard = hard_split_by_length(sub, max_chars)
                chunks.extend(hard[:-1])
                sub_current = hard[-1]

        if sub_current:
            current = sub_current

    if current:
        chunks.append(current)

    # 清理：不让标点单独成行，也不让行首出现标点。
    cleaned = []
    punct_only = re.compile(r"^[，,。！？!?；;：:、]+$")
    leading_punct = re.compile(r"^[，,。！？!?；;：:、]+")

    for chunk in chunks:
        c = chunk.strip()
        if not c:
            continue

        if punct_only.match(c):
            if cleaned:
                cleaned[-1] = f"{cleaned[-1]}{c}"
            continue

        if cleaned and leading_punct.match(c):
            m = leading_punct.match(c)
            if m:
                prefix = m.group(0)
                cleaned[-1] = f"{cleaned[-1]}{prefix}"
                c = c[len(prefix):].strip()
            if not c:
                continue

        cleaned.append(c)

    return cleaned if cleaned else [normalized]


def normalize_subtitle_text(text: str) -> str:
    """清洗字幕文本，统一空白与中英文标点间距。"""
    t = re.sub(r"\s+", " ", text.strip())
    # 中文标点前不留空格
    t = re.sub(r"\s+([，。！？；：、])", r"\1", t)
    # 中文标点后不强制加空格，避免视觉断裂
    t = re.sub(r"([，。！？；：、])\s+", r"\1", t)
    return t


def visible_len(text: str) -> int:
    """估算字幕可视长度（去掉空白）。"""
    return len(re.sub(r"\s+", "", text))


def hard_split_by_length(text: str, max_chars: int) -> list:
    """按可视长度硬切分，作为最后兜底。"""
    out = []
    current = ""
    for ch in text:
        candidate = f"{current}{ch}"
        if visible_len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                out.append(current)
            current = ch
    if current:
        out.append(current)
    return out if out else [text]


def allocate_chunk_durations(chunks: list, total_duration: float) -> list:
    """按文本长度加权分配每条字幕时长，并保证时长总和一致。"""
    if not chunks:
        return [total_duration]

    # 以字符数为主，给短句一个基础权重，避免太快闪过。
    weights = [max(6, visible_len(c)) for c in chunks]
    weight_sum = sum(weights)
    raw = [total_duration * (w / weight_sum) for w in weights]

    # 最短时长保护，避免阅读来不及。
    min_per_chunk = min(1.05, total_duration / len(chunks) * 0.85)
    adjusted = [max(min_per_chunk, d) for d in raw]

    # 归一化，确保总时长回到片段时长。
    scale = total_duration / sum(adjusted) if sum(adjusted) > 0 else 1.0
    normalized = [d * scale for d in adjusted]

    return normalized


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Whisper 字幕生成")
    parser.add_argument(
        "--audio",
        default="../remotion/public/audio.mp3",
        help="音频文件路径",
    )
    parser.add_argument(
        "--output",
        default="../remotion/public/subtitles.srt",
        help="SRT 输出路径",
    )
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper 模型大小",
    )
    parser.add_argument(
        "--from-script",
        default=None,
        help="从 script.json 生成字幕（不使用 Whisper）",
    )
    args = parser.parse_args()

    if args.from_script:
        generate_srt_from_script(args.from_script, args.output)
    else:
        generate_srt_stable_whisper(args.audio, args.output, args.model)
