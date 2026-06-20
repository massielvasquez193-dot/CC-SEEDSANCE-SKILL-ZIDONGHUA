"""
TikTok UGC Video Factory — FFmpeg Voice Merge
video.mp4 + voice.mp3 + subtitle.srt → final_video.mp4

UGC规则: 字幕位置适合竖屏、字体自然、不遮挡产品
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class FFmpegVoiceMerge:
    """FFmpeg 视频+配音+字幕 合成器"""

    def merge(
        self,
        video_path: Path,
        voice_path: Path,
        subtitle_path: Path,
        output_path: Path,
        volume_voice: float = 1.0,
        volume_original: float = 0.0,
        **kwargs,
    ) -> Path:
        """
        合成最终视频

        Args:
            video_path: 视频文件
            voice_path: 配音文件 (voice.mp3)
            subtitle_path: 字幕文件 (subtitle.srt)
            output_path: 输出路径 (final_video.mp4)
            volume_voice: 配音音量 (1.0=100%)
            volume_original: 原视频音频音量 (0.0=静音)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        if not voice_path.exists():
            raise FileNotFoundError(f"Voice not found: {voice_path}")
        if not subtitle_path.exists():
            raise FileNotFoundError(f"Subtitle not found: {subtitle_path}")

        # UGC风格字幕: 白色字体+黑色半透明背景+底部居中+适合竖屏
        subtitle_style = (
            "FontSize=20,"
            "PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,"
            "BackColour=&H80000000,"
            "BorderStyle=3,"
            "Outline=1,"
            "Shadow=1,"
            "Alignment=2,"
            "MarginV=120,"
            "FontName=Arial"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(voice_path),
            "-vf", f"subtitles={subtitle_path}:force_style='{subtitle_style}'",
            "-c:v", "libx264",
            "-preset", kwargs.get("preset", "medium"),
            "-crf", kwargs.get("crf", "23"),
            "-c:a", "aac",
            "-b:a", "128k",
            "-filter:a", f"volume={volume_voice}",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(output_path),
        ]

        logger.info(f"FFmpeg merging: video + voice + subtitles → {output_path.name}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg merge failed (exit {result.returncode}):\n"
                f"STDERR: {result.stderr[:500]}"
            )

        logger.info(f"FFmpeg merge complete: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path

    def merge_with_bgm(
        self,
        video_path: Path,
        voice_path: Path,
        subtitle_path: Path,
        bgm_path: Path,
        output_path: Path,
        bgm_volume: float = 0.15,
        voice_volume: float = 1.0,
    ) -> Path:
        """
        合成: 视频 + 配音 + 背景音乐 + 字幕

        BGM音量保持在15% — 不压过口播
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        subtitle_style = (
            "FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            "BackColour=&H80000000,BorderStyle=3,Alignment=2,MarginV=120"
        )

        # 复杂滤镜: 混合配音+BGM + 字幕
        filter_complex = (
            f"[1:a]volume={voice_volume}[voice];"
            f"[2:a]volume={bgm_volume}[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=shortest[audio]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(voice_path),
            "-i", str(bgm_path),
            "-vf", f"subtitles={subtitle_path}:force_style='{subtitle_style}'",
            "-filter_complex", filter_complex,
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-map", "0:v:0", "-map", "[audio]",
            "-shortest",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg merge+BGM failed: {result.stderr[:500]}")

        logger.info(f"FFmpeg merge+BGM: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path.postcoder

    def strip_original_audio(self, video_path: Path, output_path: Path) -> Path:
        """移除原视频音频轨道"""
        cmd = ["ffmpeg", "-y", "-i", str(video_path), "-c:v", "copy", "-an", str(output_path)]
        subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
        return output_path
