"""
pipeline.py - 一键生成科普视频的全流程脚本

使用方法：
  cd scripts/
  python pipeline.py --episode ../content/episode-01.json

完整流程：
  1. 读取 episode JSON 文案
  2. 调用 Qwen3-TTS 生成语音 -> audio.mp3
    3. 生成字幕（默认基于脚本，也可选 Whisper） -> subtitles.srt
  4. 生成 Remotion 配置 -> script.json
  5. （可选）调用 Remotion 渲染视频 -> output.mp4

环境变量：
  DASHSCOPE_API_KEY  - 阿里云百炼 API Key（必须）
  DASHSCOPE_BASE_URL - API 端点（可选）
"""

import os
import sys
import json
import argparse
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional


def find_executable(name: str) -> Optional[str]:
    """跨平台查找可执行文件（Windows 优先 .cmd/.exe/.bat）。"""
    candidates = [name]
    if os.name == "nt":
        candidates = [f"{name}.cmd", f"{name}.exe", f"{name}.bat", name]

    for candidate in candidates:
        exe = shutil.which(candidate)
        if exe:
            return exe
    return None


def get_remotion_cli(remotion_dir: Path) -> List[str]:
    """返回可用的 Remotion 命令前缀。"""
    local_bin = remotion_dir / "node_modules" / ".bin" / (
        "remotion.cmd" if os.name == "nt" else "remotion"
    )
    if local_bin.exists():
        return [str(local_bin)]

    npm_exe = find_executable("npm")
    if npm_exe:
        return [npm_exe, "exec", "--", "remotion"]

    npx_exe = find_executable("npx")
    if npx_exe:
        return [npx_exe, "remotion"]

    raise FileNotFoundError(
        "未找到 Remotion 可执行命令。请安装 Node.js/npm，或先在 remotion 目录执行 npm install。"
    )

def run_pipeline(
    episode_path: str,
    render: bool = False,
    whisper_model: str = "base",
    subtitle_source: str = "script",
) -> None:
    """执行完整的视频生成流程。"""

    episode_path = str(Path(episode_path).resolve())

    # 如果传入的是 Markdown 演讲稿，先转换为 episode JSON
    if episode_path.endswith(".md"):
        from create_episode import parse_speech

        md_text = Path(episode_path).read_text(encoding="utf-8")
        episode_data = parse_speech(md_text)

        content_dir = Path(__file__).parent.parent / "content"
        content_dir.mkdir(parents=True, exist_ok=True)
        json_path = content_dir / f"{Path(episode_path).stem}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(episode_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 演讲稿已转换为 episode JSON: {json_path}")
        episode_path = str(json_path.resolve())
    project_root = Path(__file__).parent.parent
    remotion_dir = project_root / "remotion"
    public_dir = remotion_dir / "public"
    scripts_dir = Path(__file__).parent

    public_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  科普视频生成流水线")
    print("=" * 60)

    with open(episode_path, "r", encoding="utf-8") as f:
        episode = json.load(f)
    print(f"\n主题: {episode['title']}")
    print(f"片段数: {len(episode['segments'])}")

    # Step 1: 生成语音
    print("\n" + "-" * 40)
    print("步骤 1/4: 生成语音 (Qwen3-TTS)")
    print("-" * 40)

    subprocess.run(
        [
            sys.executable,
            str(scripts_dir / "generate_audio.py"),
            "--input",
            episode_path,
            "--output",
            str(public_dir),
        ],
        check=True,
    )

    audio_file = public_dir / "audio.mp3"
    if not audio_file.exists():
        raise RuntimeError("音频文件未生成")

    # Step 2: 生成字幕
    print("\n" + "-" * 40)
    if subtitle_source == "script":
        print("步骤 2/4: 生成字幕 (Script 文案)")
    else:
        print("步骤 2/4: 生成字幕 (Whisper)")
    print("-" * 40)

    srt_file = public_dir / "subtitles.srt"
    script_json = remotion_dir / "src" / "data" / "script.json"

    if subtitle_source == "script":
        if not script_json.exists():
            raise RuntimeError(f"未找到 script.json: {script_json}")
        subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "generate_srt.py"),
                "--from-script",
                str(script_json),
                "--output",
                str(srt_file),
            ],
            check=True,
        )
    elif subtitle_source == "whisper":
        subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "generate_srt.py"),
                "--audio",
                str(audio_file),
                "--output",
                str(srt_file),
                "--model",
                whisper_model,
            ],
            check=True,
        )
    else:
        raise ValueError("subtitle_source 必须是 'script' 或 'whisper'")

    # Step 3: 安装 Remotion 依赖
    print("\n" + "-" * 40)
    print("步骤 3/4: 安装 Remotion 依赖")
    print("-" * 40)

    if not (remotion_dir / "node_modules").exists():
        npm_exe = find_executable("npm")
        if not npm_exe:
            raise FileNotFoundError("未找到 npm 可执行文件，请安装 Node.js 并重开终端后重试。")
        subprocess.run([npm_exe, "install"], cwd=str(remotion_dir), check=True)
        print("✓ npm 依赖已安装")
    else:
        print("✓ npm 依赖已就绪")

    # Step 4: 渲染/预览
    print("\n" + "-" * 40)
    print("步骤 4/4: 视频渲染")
    print("-" * 40)

    remotion_cli = get_remotion_cli(remotion_dir)

    if render:
        print("正在渲染完整视频（这可能需要几分钟）...")
        output_dir = project_root / "output"
        output_dir.mkdir(exist_ok=True)

        subprocess.run(
            remotion_cli + ["render", "ScienceVideo", str(output_dir / "video.mp4")],
            cwd=str(remotion_dir),
            check=True,
        )
        print(f"\n✓ 视频已保存到: {output_dir / 'video.mp4'}")
    else:
        preview_cmd = " ".join(remotion_cli + ["studio"])
        print("跳过渲染。启动预览：")
        print(f"  cd {remotion_dir}")
        print(f"  {preview_cmd}")
        print("\n或者渲染完整视频：")
        print(f"  python pipeline.py --episode {episode_path} --render")

    print("\n" + "=" * 60)
    print("  流水线执行完成！")
    print("=" * 60)
    print("\n生成的文件：")
    print(f"  音频: {audio_file}")
    print(f"  字幕: {srt_file}")
    print(f"  配置: {remotion_dir / 'src' / 'data' / 'script.json'}")
    if render:
        print(f"  视频: {project_root / 'output' / 'video.mp4'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="科普视频一键生成流水线")
    parser.add_argument(
        "--episode",
        default="../content/episode-01.json",
        help="Episode JSON 或 Markdown 演讲稿路径（.md 会自动转换）",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="是否渲染完整视频（否则仅生成素材）",
    )
    parser.add_argument(
        "--whisper-model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper 模型大小",
    )
    parser.add_argument(
        "--subtitle-source",
        default="script",
        choices=["script", "whisper"],
        help="字幕来源：script=使用文案与时间轴，whisper=从音频识别",
    )
    args = parser.parse_args()

    try:
        run_pipeline(
            episode_path=args.episode,
            render=args.render,
            whisper_model=args.whisper_model,
            subtitle_source=args.subtitle_source,
        )
    except subprocess.CalledProcessError as e:
        print(f"错误: 子进程执行失败，退出码 {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
