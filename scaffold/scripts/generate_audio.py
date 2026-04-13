"""
generate_audio.py - 使用 Qwen3-TTS (DashScope API) 生成语音

使用方法：
  python generate_audio.py --input ../content/episode-01.json --output ../remotion/public/

前置条件：
  1. pip install dashscope
  2. 设置环境变量 DASHSCOPE_API_KEY="sk-xxx"
     (新加坡地域的 API Key，在阿里云百炼平台获取)

说明：
  - 读取 episode JSON 文件中所有 segments 的 narration 文本
  - 将所有文本拼接后调用 Qwen3-TTS 生成完整音频
  - 也支持逐段生成后拼接（更精确的时间控制）
"""

import os
import sys
import json
import base64
import argparse
import threading
import tempfile
import subprocess
import requests
from pathlib import Path


class AuthError(RuntimeError):
    """API 鉴权失败（如 InvalidApiKey）"""


def get_api_config():
    """获取 API 配置，自动检测地域"""
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        print("错误: 请设置环境变量 DASHSCOPE_API_KEY")
        print("获取方式: https://help.aliyun.com/zh/model-studio/get-api-key")
        sys.exit(1)

    # 默认使用 DashScope 正式 API 路径
    base_url = os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com/api/v1"
    ).rstrip("/")

    # 兼容错误配置：compatible-mode/v1 不能直接拼接 services 路径
    if base_url.endswith("/compatible-mode/v1"):
        base_url = base_url.replace("/compatible-mode/v1", "/api/v1")
        print("提示: 检测到 compatible-mode 端点，已自动切换到 /api/v1")

    return api_key, base_url


def get_realtime_ws_url(base_url: str) -> str:
    """根据配置推断 Realtime WebSocket URL"""
    ws_url = os.getenv("DASHSCOPE_REALTIME_URL", "").strip()
    if ws_url:
        return ws_url

    if "dashscope-intl.aliyuncs.com" in base_url:
        return "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"
    return "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"


def pcm_to_mp3_bytes(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1) -> bytes:
    """将 16bit PCM 音频转为 MP3"""
    in_file = None
    out_file = None
    try:
        in_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pcm")
        out_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        in_file.write(pcm_data)
        in_file.close()
        out_file.close()

        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "s16le",
                "-ar",
                str(sample_rate),
                "-ac",
                str(channels),
                "-i",
                in_file.name,
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "128k",
                out_file.name,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"PCM 转 MP3 失败: {result.stderr[-300:]}")

        with open(out_file.name, "rb") as f:
            return f.read()
    finally:
        if in_file and os.path.exists(in_file.name):
            os.remove(in_file.name)
        if out_file and os.path.exists(out_file.name):
            os.remove(out_file.name)


def generate_audio_segment_http(
    text: str,
    api_key: str,
    base_url: str,
    voice: str = "Cherry",
    language: str = "Chinese",
    model: str = "qwen3-tts-flash",
) -> bytes:
    """
    调用 Qwen3-TTS API 生成单段语音

    Args:
        text: 要合成的文本
        api_key: DashScope API Key
        base_url: API 基础 URL
        voice: 音色名称 (Cherry, Bella, Ethan 等)
        language: 语言 (Chinese, English, Auto)
        model: 模型名称

    Returns:
        音频数据 (bytes)
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "input": {
            "text": text,
            "voice": voice,
            "language_type": language,
        },
        "parameters": {
            "sample_rate": 24000,
            "response_format": "mp3",
        },
    }

    if base_url.endswith("/services/aigc/multimodal-generation/generation"):
        url = base_url
    else:
        url = f"{base_url}/services/aigc/multimodal-generation/generation"

    print(f"  正在生成语音: {text[:40]}...")
    response = requests.post(url, headers=headers, json=payload, timeout=120)

    # 部分账号需使用国际域名，404 时自动重试一次
    if response.status_code == 404 and "dashscope.aliyuncs.com" in url:
        retry_url = url.replace("dashscope.aliyuncs.com", "dashscope-intl.aliyuncs.com")
        print(f"  提示: 404，尝试国际域名重试: {retry_url}")
        response = requests.post(retry_url, headers=headers, json=payload, timeout=120)
        url = retry_url
    elif response.status_code == 404 and "dashscope-intl.aliyuncs.com" in url:
        retry_url = url.replace("dashscope-intl.aliyuncs.com", "dashscope.aliyuncs.com")
        print(f"  提示: 404，尝试大陆域名重试: {retry_url}")
        response = requests.post(retry_url, headers=headers, json=payload, timeout=120)
        url = retry_url

    if response.status_code != 200:
        err = (response.text or "").strip()
        if response.status_code == 401 and ("InvalidApiKey" in err or "API-key" in err):
            raise AuthError(
                "DashScope 鉴权失败（InvalidApiKey）。"
                "请确认 DASHSCOPE_API_KEY 正确、未过期，且地域与端点匹配。"
            )
        print(f"  API 错误 ({response.status_code}) @ {url}: {err[:300]}")
        raise Exception(f"TTS API 调用失败: {response.status_code}")

    try:
        result = response.json()
    except ValueError as e:
        raise Exception(f"TTS API 返回非 JSON: {response.text[:200]}") from e

    # 提取音频数据（base64 编码）
    audio_url = None
    if "output" in result:
        audio_obj = result["output"].get("audio")
        if isinstance(audio_obj, str):
            audio_url = audio_obj
        elif isinstance(audio_obj, dict):
            # 某些版本返回 audio_url
            audio_url = audio_obj.get("url")
            if not audio_url:
                # 某些版本返回 base64
                audio_b64 = audio_obj.get("data")
                if audio_b64:
                    return base64.b64decode(audio_b64)

    if audio_url:
        # 下载音频文件
        audio_resp = requests.get(audio_url, timeout=60)
        if audio_resp.status_code != 200:
            raise Exception(f"下载音频失败: {audio_resp.status_code}")
        return audio_resp.content

    # 兜底：尝试从 response 中直接获取
    print(f"  API 返回结构: {json.dumps(result, ensure_ascii=False)[:200]}")
    raise Exception("无法从 API 响应中提取音频数据")


def generate_audio_segment_realtime(
    text: str,
    api_key: str,
    base_url: str,
    voice: str = "Cherry",
    model: str = "qwen3-tts-flash",
) -> bytes:
    """优先使用 DashScope Realtime SDK 生成语音（PCM -> MP3）"""
    try:
        import dashscope
        from dashscope.audio.qwen_tts_realtime import (
            AudioFormat,
            QwenTtsRealtime,
            QwenTtsRealtimeCallback,
        )
    except Exception as e:
        raise RuntimeError("未安装或无法导入 dashscope realtime SDK") from e

    dashscope.api_key = api_key
    ws_url = get_realtime_ws_url(base_url)
    realtime_model = model if model.endswith("-realtime") else f"{model}-realtime"

    complete_event = threading.Event()
    audio_chunks = []
    event_error = {"error": None}

    class Callback(QwenTtsRealtimeCallback):
        def on_open(self) -> None:
            return

        def on_close(self, close_status_code, close_msg) -> None:
            return

        def on_event(self, response: dict) -> None:
            try:
                event_type = response.get("type")
                if event_type == "response.audio.delta":
                    recv_audio_b64 = response.get("delta")
                    if recv_audio_b64:
                        audio_chunks.append(base64.b64decode(recv_audio_b64))
                elif event_type == "error":
                    event_error["error"] = response
                    complete_event.set()
                elif event_type == "session.finished":
                    complete_event.set()
            except Exception as e:
                event_error["error"] = str(e)
                complete_event.set()

    print(f"  正在生成语音(Realtime): {text[:40]}...")
    qwen_tts = QwenTtsRealtime(
        model=realtime_model,
        callback=Callback(),
        url=ws_url,
    )

    qwen_tts.connect()
    qwen_tts.update_session(
        voice=voice,
        response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
        mode="server_commit",
    )
    qwen_tts.append_text(text)
    qwen_tts.finish()

    if not complete_event.wait(timeout=180):
        raise RuntimeError("Realtime TTS 超时未完成")

    if event_error["error"] is not None:
        raise RuntimeError(f"Realtime TTS 返回错误: {event_error['error']}")

    pcm_data = b"".join(audio_chunks)
    if not pcm_data:
        raise RuntimeError("Realtime TTS 未返回音频数据")

    return pcm_to_mp3_bytes(pcm_data)


def generate_audio_segment(
    text: str,
    api_key: str,
    base_url: str,
    voice: str = "Cherry",
    language: str = "Chinese",
    model: str = "qwen3-tts-flash",
) -> bytes:
    """生成单段语音：优先 Realtime SDK，失败后降级 HTTP"""
    try:
        return generate_audio_segment_realtime(
            text=text,
            api_key=api_key,
            base_url=base_url,
            voice=voice,
            model=model,
        )
    except Exception as realtime_error:
        rt_msg = str(realtime_error)
        if "InvalidApiKey" in rt_msg or "401" in rt_msg or "Unauthorized" in rt_msg:
            raise AuthError(
                "Realtime 鉴权失败（InvalidApiKey）。"
                "请确认 DASHSCOPE_API_KEY 正确、未过期，且地域与端点匹配。"
            ) from realtime_error
        print(f"  提示: Realtime 失败，降级 HTTP。原因: {realtime_error}")
        return generate_audio_segment_http(
            text=text,
            api_key=api_key,
            base_url=base_url,
            voice=voice,
            language=language,
            model=model,
        )


def generate_full_audio(episode_path: str, output_dir: str):
    """
    读取 episode JSON，生成完整音频

    策略：逐段生成音频文件，最后用 ffmpeg 拼接
    这样可以精确知道每段的时长，用于计算 startFrame/endFrame
    """
    api_key, base_url = get_api_config()

    with open(episode_path, "r", encoding="utf-8") as f:
        episode = json.load(f)

    voice = episode.get("voice", "Cherry")
    language = episode.get("language", "Chinese")
    fps = episode.get("fps", 30)
    segments = episode["segments"]

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    segment_files = []
    segment_durations = []  # 每段时长（秒）

    print(f"\n开始生成语音 - 共 {len(segments)} 个片段")
    print(f"音色: {voice} | 语言: {language}")
    print("-" * 50)

    for i, segment in enumerate(segments):
        narration = segment["narration"]
        seg_file = output_path / f"segment_{i:03d}.mp3"

        try:
            audio_data = generate_audio_segment(
                text=narration,
                api_key=api_key,
                base_url=base_url,
                voice=voice,
                language=language,
            )

            with open(seg_file, "wb") as f:
                f.write(audio_data)

            # 获取音频时长（需要 ffprobe）
            duration = get_audio_duration(str(seg_file))
            segment_durations.append(duration)
            segment_files.append(str(seg_file))

            print(f"  ✓ 片段 {i+1}/{len(segments)}: {duration:.2f}s - {segment['id']}")

        except Exception as e:
            print(f"  ✗ 片段 {i+1} 失败: {e}")
            if isinstance(e, AuthError):
                raise
            # 使用预估时长
            estimated = segment.get("duration_hint", 5)
            segment_durations.append(estimated)
            print(f"    使用预估时长: {estimated}s")

    if not segment_files:
        raise RuntimeError(
            "所有片段都生成失败，未产生任何音频文件。"
            "请检查 DASHSCOPE_BASE_URL 是否为 https://dashscope.aliyuncs.com/api/v1"
        )

    # 拼接所有片段
    final_audio = output_path / "audio.mp3"
    concat_audio(segment_files, str(final_audio))
    if not final_audio.exists() or final_audio.stat().st_size == 0:
        raise RuntimeError("音频拼接失败，audio.mp3 未生成或为空")
    print(f"\n✓ 完整音频已保存到: {final_audio}")

    # 生成 script.json（含精确帧信息）
    generate_script_json(episode, segment_durations, fps, output_dir)

    # 清理临时片段文件
    for f in segment_files:
        os.remove(f)

    print("✓ 音频生成完成！")


def get_audio_duration(filepath: str) -> float:
    """使用 ffprobe 获取音频时长"""
    import subprocess

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                filepath,
            ],
            capture_output=True,
            text=True,
        )
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception:
        # 如果 ffprobe 不可用，用 mutagen
        try:
            from mutagen.mp3 import MP3  # type: ignore[import-not-found]
            audio = MP3(filepath)
            return audio.info.length
        except ImportError:
            print("  警告: 无法获取音频时长，使用预估值")
            return 5.0


def concat_audio(files: list, output: str):
    """使用 ffmpeg 拼接音频文件"""
    import subprocess

    # 创建 concat 列表文件
    list_file = output + ".list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for filepath in files:
            safe_path = Path(filepath).resolve().as_posix()
            f.write(f"file '{safe_path}'\n")

    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output,
        ],
        capture_output=True,
        text=True,
    )

    os.remove(list_file)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 拼接失败: {result.stderr[-300:]}")


def generate_script_json(
    episode: dict,
    durations: list,
    fps: int,
    output_dir: str,
):
    """根据实际音频时长生成 Remotion 用的 script.json"""
    segments_out = []
    current_frame = 0

    for i, segment in enumerate(episode["segments"]):
        if i < len(durations):
            duration_frames = int(durations[i] * fps)
        else:
            duration_frames = int(segment.get("duration_hint", 5) * fps)

        seg_data = {
            "id": segment["id"],
            "type": segment["type"],
            "text": segment["text"],
            "narration": segment["narration"],
            "startFrame": current_frame,
            "endFrame": current_frame + duration_frames,
        }

        if "animation" in segment:
            seg_data["animation"] = segment["animation"]
        if "chart_type" in segment:
            seg_data["chart_type"] = segment["chart_type"]

        segments_out.append(seg_data)
        current_frame += duration_frames

    script = {
        "title": episode["title"],
        "fps": fps,
        "totalDurationInFrames": current_frame,
        "segments": segments_out,
    }

    # 写入 Remotion 的 src/data/ 目录
    remotion_data_dir = Path(output_dir).parent / "src" / "data"
    remotion_data_dir.mkdir(parents=True, exist_ok=True)

    script_path = remotion_data_dir / "script.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    print(f"✓ script.json 已保存到: {script_path}")
    print(f"  总时长: {current_frame / fps:.1f}s ({current_frame} frames @ {fps}fps)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Qwen3-TTS 语音生成")
    parser.add_argument(
        "--input",
        default="../content/episode-01.json",
        help="Episode JSON 文件路径",
    )
    parser.add_argument(
        "--output",
        default="../remotion/public/",
        help="输出目录（Remotion public 目录）",
    )
    args = parser.parse_args()

    generate_full_audio(args.input, args.output)
