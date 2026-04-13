"""
create_episode.py - 从 Markdown 演讲稿生成 episode JSON

使用方法：
  python create_episode.py --input speech.md --output ../content/episode-02.json

演讲稿格式（Markdown）：

    # 视频标题

    ## 段落小标题
    这一段的配音台词，可以写多行，
    会自动合并为一段 narration。

    ## 下一段标题
    下一段的台词...

规则：
  - `#` 一级标题 → 视频总标题
  - `##` 二级标题 → 每个 segment 的显示文字
  - 标题下方的正文 → 该段的 narration（配音台词）
  - 第一段和最后一段自动设为 title 类型（片头/片尾）
  - 中间段设为 animation 类型（通用文字动画）
  - 可在标题行末尾用 `{type=chart}` 或 `{animation=spectrum}` 覆盖默认值
"""

import re
import json
import argparse
from pathlib import Path


def parse_speech(text: str) -> dict:
    """
    解析 Markdown 演讲稿，返回 episode 字典。

    支持在 ## 标题行末尾添加属性标记：
      ## 波长与散射 {type=chart, chart_type=wavelength_scatter}
      ## 光谱分解 {animation=spectrum}
    """
    lines = text.strip().splitlines()

    title = ""
    segments = []
    current_heading = None
    current_attrs = {}
    current_body_lines = []

    def flush_segment():
        nonlocal current_heading, current_body_lines, current_attrs
        if current_heading is None:
            return
        narration = "\n".join(current_body_lines).strip()
        # 将多行合并为单行（去掉换行，保留句间空格）
        narration = re.sub(r"\s*\n\s*", "", narration)
        if narration:
            seg = {
                "heading": current_heading,
                "narration": narration,
                "attrs": current_attrs,
            }
            segments.append(seg)
        current_heading = None
        current_body_lines = []
        current_attrs = {}

    for line in lines:
        stripped = line.strip()

        # 一级标题 → 视频总标题
        m = re.match(r"^#\s+(.+)$", stripped)
        if m and not stripped.startswith("##"):
            title = m.group(1).strip()
            continue

        # 二级标题 → segment
        m = re.match(r"^##\s+(.+)$", stripped)
        if m:
            flush_segment()
            heading_raw = m.group(1).strip()
            # 提取 {key=value, ...} 属性
            attrs = {}
            attr_match = re.search(r"\{(.+?)\}\s*$", heading_raw)
            if attr_match:
                heading_raw = heading_raw[: attr_match.start()].strip()
                for pair in attr_match.group(1).split(","):
                    pair = pair.strip()
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        attrs[k.strip()] = v.strip()
            current_heading = heading_raw
            current_attrs = attrs
            continue

        # 跳过空行（但保留在 body 中用于段落分隔）
        # 普通正文 → narration
        if current_heading is not None:
            current_body_lines.append(stripped)

    flush_segment()

    if not title and segments:
        title = segments[0]["heading"]

    return build_episode(title, segments)


def build_episode(title: str, segments: list) -> dict:
    """将解析后的段落列表构建为 episode JSON 结构。"""
    episode_segments = []

    for i, seg in enumerate(segments):
        is_first = i == 0
        is_last = i == len(segments) - 1
        attrs = seg["attrs"]

        # 确定 segment type
        seg_type = attrs.get("type")
        if not seg_type:
            if is_first or is_last:
                seg_type = "title"
            else:
                seg_type = "animation"

        # 生成 id（从标题取拼音首字母太复杂，用序号+简化标题）
        seg_id = attrs.get("id", f"seg_{i:02d}_{_slugify(seg['heading'])}")

        entry = {
            "id": seg_id,
            "type": seg_type,
            "text": seg["heading"],
            "narration": seg["narration"],
            "duration_hint": _estimate_duration(seg["narration"]),
        }

        # animation 类型的附加字段
        if seg_type == "animation":
            entry["animation"] = attrs.get("animation", "default")
        elif seg_type == "chart":
            entry["chart_type"] = attrs.get("chart_type", "bar")

        episode_segments.append(entry)

    return {
        "title": title,
        "description": "",
        "voice": "Cherry",
        "language": "Chinese",
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "segments": episode_segments,
    }


def _slugify(text: str, max_len: int = 20) -> str:
    """将中文/英文标题转为简短的 ASCII slug，用于 segment id。"""
    # 保留字母数字和中文
    slug = re.sub(r"[^\w\u4e00-\u9fff]", "_", text)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug[:max_len].rstrip("_") or "untitled"


def _estimate_duration(narration: str) -> int:
    """根据文本长度估算时长（秒），中文约 4 字/秒。"""
    char_count = len(re.sub(r"\s+", "", narration))
    duration = max(3, round(char_count / 4))
    return duration


def main():
    parser = argparse.ArgumentParser(description="从 Markdown 演讲稿生成 episode JSON")
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Markdown 演讲稿文件路径",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出 JSON 路径（默认放到 content/ 目录下）",
    )
    parser.add_argument(
        "--voice",
        default="Cherry",
        help="TTS 音色 (Cherry, Bella, Ethan 等)",
    )
    parser.add_argument(
        "--language",
        default="Chinese",
        help="语言 (Chinese, English, Auto)",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"错误: 文件不存在: {input_path}")
        return

    text = input_path.read_text(encoding="utf-8")
    episode = parse_speech(text)

    # 应用命令行参数覆盖
    episode["voice"] = args.voice
    episode["language"] = args.language

    # 确定输出路径
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        content_dir = Path(__file__).parent.parent / "content"
        content_dir.mkdir(parents=True, exist_ok=True)
        output_path = content_dir / f"{input_path.stem}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(episode, f, ensure_ascii=False, indent=2)

    print(f"✓ Episode JSON 已生成: {output_path}")
    print(f"  标题: {episode['title']}")
    print(f"  段落数: {len(episode['segments'])}")
    for seg in episode["segments"]:
        print(f"    [{seg['type']:10s}] {seg['id']} - {seg['text']}")


if __name__ == "__main__":
    main()
