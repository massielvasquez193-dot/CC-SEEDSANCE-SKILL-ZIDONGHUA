"""
TikTok UGC Video Factory — Voice Engine
voiceover.txt → voice.mp3

支持: ElevenLabs TTS, 情绪映射, 多段合成, UGC风格
输入: voiceover.txt (带 [HOOK] [PAUSE N] [Emotion] 标记)
输出: voice.mp3
"""

import json
import logging
import os
import re
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceEngine:
    """真人级口播引擎"""

    def __init__(self, provider=None):
        self.provider = provider
        self._elevenlabs = None

    @property
    def elevenlabs(self):
        if self._elevenlabs is None:
            from providers.elevenlabs_provider import ElevenLabsProvider
            api_key = os.getenv("ELEVENLABS_API_KEY")
            self._elevenlabs = ElevenLabsProvider(api_key=api_key)
        return self._elevenlabs

    def is_available(self) -> bool:
        return bool(os.getenv("ELEVENLABS_API_KEY"))

    # ================================================================
    # 主入口: voiceover.txt → voice.mp3
    # ================================================================
    def generate(
        self,
        voiceover_txt_path: Path,
        output_dir: Path,
        voice_config: dict = None,
        voice_style: dict = None,
    ) -> dict:
        """
        从voiceover.txt生成真人级口播

        Args:
            voiceover_txt_path: voiceover.txt 路径
            output_dir: 输出目录
            voice_config: config/voices.json 中的声音配置
            voice_style: voice_style.json (语速/情绪/停顿)

        Returns:
            {
                "voice_mp3": "path/to/voice.mp3",
                "segments": [...],
                "duration_seconds": 12.5,
                "voice_id": "...",
            }
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not self.is_available():
            logger.warning("ELEVENLABS_API_KEY not set — generating voiceover.txt only")
            return {"voice_mp3": None, "segments": [], "duration_seconds": 0}

        # Step 1: 解析 voiceover.txt
        segments = self._parse_voiceover_txt(voiceover_txt_path)
        if not segments:
            raise ValueError(f"Failed to parse voiceover.txt: {voiceover_txt_path}")

        # Step 2: 加载声音配置
        voice_id = self._resolve_voice_id(voice_config, voice_style)

        # Step 3: 逐段生成语音
        audio_segments = []
        for i, seg in enumerate(segments):
            emotion = seg.get("emotion", "natural")
            text = seg["text"]
            pause_before = seg.get("pause_before", 0)
            pause_after = seg.get("pause_after", 0)

            if not text.strip():
                continue

            logger.info(f"  TTS segment {i+1}/{len(segments)} [{emotion}]: {text[:60]}...")

            try:
                seg_audio = self.elevenlabs.text_to_speech(
                    text=text,
                    voice_id=voice_id,
                    emotion=emotion,
                )
                audio_segments.append({
                    "index": i,
                    "section": seg["section"],
                    "emotion": emotion,
                    "text": text,
                    "audio": seg_audio,
                    "pause_before": pause_before,
                    "pause_after": pause_after,
                })
            except Exception as e:
                logger.error(f"TTS segment {i} failed: {e}")
                # 继续处理其他段

        # Step 4: 合并语音段 + 停顿
        voice_path = output_dir / "voice.mp3"
        self._merge_audio_segments(audio_segments, voice_path)

        # Step 5: 计算总时长
        total_duration = sum(
            s.get("pause_before", 0) + self._audio_duration(s.get("audio"))
            + s.get("pause_after", 0)
            for s in audio_segments
        )

        result = {
            "voice_mp3": str(voice_path),
            "segments": [
                {"section": s["section"], "emotion": s["emotion"], "text": s["text"][:80]}
                for s in audio_segments
            ],
            "duration_seconds": round(total_duration, 1),
            "voice_id": voice_id,
            "generated_at": datetime.now().isoformat(),
        }

        # 保存结果
        result_path = output_dir / "voice_engine_result.json"
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(f"Voice Engine: voice.mp3 ({voice_path.stat().st_size} bytes, {total_duration:.1f}s)")
        return result

    # ================================================================
    # voiceover.txt 解析
    # ================================================================
    def _parse_voiceover_txt(self, txt_path: Path) -> list[dict]:
        """解析voiceover.txt — 提取段、情绪、停顿"""
        content = txt_path.read_text(encoding="utf-8")
        segments = []

        # 按 ## SECTION 分割
        section_blocks = re.split(r'##\s+([A-Z_ ]+)', content)
        for i in range(1, len(section_blocks), 2):
            section = section_blocks[i].strip()
            block = section_blocks[i + 1] if i + 1 < len(section_blocks) else ""

            # 提取情绪
            emotion_match = re.search(r'Emotion:\s*(\w+)', block)
            emotion = emotion_match.group(1).lower() if emotion_match else "natural"

            # 提取停顿
            pauses = re.findall(r'\[pause\s+([\d.]+)\]', block)
            pause_after = float(pauses[0]) if pauses else 0

            # 提取语音文本行 (在 [Emotion] 标记后的内容)
            # 清理标记行
            lines = []
            capture = False
            for line in block.split("\n"):
                line = line.strip()
                if line.startswith("[") and not line.startswith("[pause"):
                    capture = True
                    continue
                if capture and line and not line.startswith("Emotion:") and not line.startswith("Voice:") and not line.startswith("Pace:"):
                    if line.startswith("[pause"):
                        continue
                    lines.append(line)

            text = " ".join(lines).strip().strip('"').strip("'")

            if text:
                segments.append({
                    "section": section,
                    "emotion": emotion,
                    "text": text,
                    "pause_after": pause_after,
                    "pause_before": 0.3,
                })

        return segments

    # ================================================================
    # 声音选择
    # ================================================================
    def _resolve_voice_id(self, voice_config: dict = None, voice_style: dict = None) -> str:
        """从配置/风格解析voice_id"""
        # 1. 直接指定
        if voice_config and voice_config.get("voice_id"):
            return voice_config["voice_id"]

        # 2. 从 voices.json 加载
        try:
            config_path = Path(__file__).resolve().parent.parent / "config" / "voices.json"
            if config_path.exists():
                voices = json.loads(config_path.read_text(encoding="utf-8"))
                # 按风格匹配
                if voice_style:
                    for vid, vcfg in voices.items():
                        if vcfg.get("style") == voice_style.get("style", ""):
                            return vcfg["voice_id"]
                # 使用第一个
                first = list(voices.values())[0] if voices else {}
                if first.get("voice_id"):
                    return first["voice_id"]
        except Exception as e:
            logger.warning(f"Failed to load voices.json: {e}")

        # 3. 环境变量默认
        return os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    # ================================================================
    # 音频合并
    # ================================================================
    def _merge_audio_segments(self, segments: list[dict], output_path: Path):
        """合并多段音频 + 停顿"""
        import subprocess

        if not segments:
            return

        # 单段直接保存
        if len(segments) == 1 and not segments[0].get("pause_before"):
            output_path.write_bytes(segments[0]["audio"])
            return

        # 多段: 用ffmpeg concat
        # 1) 生成静音片段用于停顿
        tmp_dir = Path(tempfile.mkdtemp())
        concat_file = tmp_dir / "concat.txt"

        with open(concat_file, "w") as f:
            for seg in segments:
                # 停顿 → 静音
                pause = seg.get("pause_before", 0) + seg.get("pause_after", 0)
                if pause > 0:
                    silence_path = tmp_dir / f"silence_{seg['index']}.mp3"
                    subprocess.run([
                        "ffmpeg", "-y", "-f", "lavfi",
                        "-i", f"anullsrc=r=44100:cl=mono:d={pause}",
                        "-c:a", "libmp3lame", "-q:a", "2",
                        str(silence_path),
                    ], capture_output=True, timeout=10)
                    if silence_path.exists():
                        f.write(f"file '{silence_path.resolve()}'\n")

                # 语音段
                audio = seg.get("audio")
                if audio:
                    seg_path = tmp_dir / f"seg_{seg['index']}.mp3"
                    seg_path.write_bytes(audio)
                    f.write(f"file '{seg_path.resolve()}'\n")

        # ffmpeg concat
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
               "-c:a", "libmp3lame", "-q:a", "2", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            # 降级: 只用第一段
            logger.warning(f"ffmpeg concat failed, using first segment only")
            if segments and segments[0].get("audio"):
                output_path.write_bytes(segments[0]["audio"])
        else:
            logger.info(f"Audio merged: {output_path} ({output_path.stat().st_size} bytes)")

        # 清理
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def _audio_duration(self, audio_bytes) -> float:
        """估算音频时长 (MP3) — 粗略: 128kbps"""
        if not audio_bytes:
            return 0
        bits_per_second = 128000
        return len(audio_bytes) * 8 / bits_per_second
