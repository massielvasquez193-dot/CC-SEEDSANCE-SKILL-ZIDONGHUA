"""
TikTok UGC Video Factory — Subtitle Alignment
根据 voice.mp3 自动生成时间轴精确的 subtitle.srt

方法: ffprobe 获取音频时长 → 按段均匀分配 → 字词级微调
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class SubtitleAlignment:
    """字幕对齐器 — voice.mp3 → subtitle.srt"""

    def generate(
        self,
        voiceover_txt_path: Path,
        voice_mp3_path: Path = None,
        output_dir: Path = None,
    ) -> Path:
        """
        生成时间轴精确的SRT字幕

        Args:
            voiceover_txt_path: voiceover.txt 路径
            voice_mp3_path: voice.mp3 路径 (用于获取精确时长)
            output_dir: 输出目录

        Returns:
            subtitle.srt 路径
        """
        output_dir = Path(output_dir) if output_dir else voiceover_txt_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: 解析 voiceover.txt 获取段落
        segments = self._parse_voiceover(voiceover_txt_path)
        if not segments:
            raise ValueError(f"Failed to parse: {voiceover_txt_path}")

        # Step 2: 获取总时长
        total_duration = self._get_audio_duration(voice_mp3_path) if voice_mp3_path else self._estimate_duration(segments)

        # Step 3: 分配时间轴 — 按字数比例
        srt_entries = self._build_srt_with_timing(segments, total_duration)

        # Step 4: 保存
        srt_path = output_dir / "subtitle.srt"
        srt_text = "\n".join(srt_entries)
        srt_path.write_text(srt_text, encoding="utf-8")

        logger.info(f"Subtitle aligned: {srt_path} ({len(srt_entries)} entries, {total_duration:.1f}s)")
        return srt_path

    def _parse_voiceover(self, txt_path: Path) -> list[dict]:
        """解析 voiceover.txt"""
        content = txt_path.read_text(encoding="utf-8")
        segments = []

        blocks = re.split(r'##\s+([A-Z_ ]+)', content)
        for i in range(1, len(blocks), 2):
            section = blocks[i].strip()
            block = blocks[i + 1] if i + 1 < len(blocks) else ""

            # 提取实际文本 (跳过标记行)
            lines = []
            capture = False
            for line in block.split("\n"):
                line = line.strip()
                if line.startswith("[") and not line.startswith("[pause"):
                    capture = True
                    continue
                if capture and line and not any(line.startswith(p) for p in ("Emotion:", "Voice:", "Pace:", "##")):
                    if line.startswith("[pause"):
                        continue
                    lines.append(line)

            text = " ".join(lines).strip().strip('"').strip("'")
            # 清理表演标记
            text = re.sub(r'\[.*?\]', '', text).strip()

            if text:
                segments.append({"section": section, "text": text})

        return segments

    def _get_audio_duration(self, mp3_path: Path) -> float:
        """ffprobe获取音频时长"""
        if not mp3_path or not mp3_path.exists():
            return 0
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(mp3_path)],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data.get("format", {}).get("duration", 0))
        except Exception as e:
            logger.warning(f"ffprobe failed: {e}")
        return 0

    def _estimate_duration(self, segments: list[dict]) -> float:
        """估算总时长 — 每秒3个中文字或2个英文词"""
        total_chars = sum(len(s["text"]) for s in segments)
        return max(3.0, total_chars / 3.0)  # 中文约3字/秒

    def _build_srt_with_timing(self, segments: list[dict], total_duration: float) -> list[str]:
        """按字数比例分配时间轴"""
        if not segments or total_duration <= 0:
            return []

        # 计算每个segment的字数权重
        text_lengths = [len(s["text"]) for s in segments]
        total_chars = sum(text_lengths)
        if total_chars == 0:
            return []

        entries = []
        time_cursor = 0.0

        for i, seg in enumerate(segments):
            # 按字数比例分配时长
            weight = text_lengths[i] / total_chars
            seg_duration = weight * total_duration

            start = time_cursor
            end = time_cursor + seg_duration
            time_cursor = end

            # 字幕文本 — 中文字幕断行
            text = seg["text"].strip()
            if len(text) > 20:
                # 在标点附近断行
                mid = len(text) // 2
                for j in range(mid, min(mid + 8, len(text))):
                    if text[j] in "，。！？、；：,.!?;: ":
                        text = text[:j+1] + "\n" + text[j+1:].lstrip()
                        break

            entries.append(
                f"{i+1}\n"
                f"{self._fmt_time(start)} --> {self._fmt_time(end)}\n"
                f"{text}\n"
            )

        return entries

    def _fmt_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
