"""
TikTok UGC Video Factory — Voiceover Generator (Phase 3)
根据 performance_script.json 生成UGC风格口播

输出:
  voiceover.txt   — [HOOK]...[PAUSE 0.6]...[RESULT] 格式
  subtitle.srt    — 时间轴精确SRT字幕
  voice.mp3       — ElevenLabs真人级TTS

格式:
  [HOOK]
  Guys... I honestly didn't expect this.
  [PAUSE 0.6]
  After only seven days...
  [RESULT]
  Look at my skin now.

目标: 听起来像真人TikTok达人自拍视频，而不是AI配音
禁止: 广告腔、播音腔、AI机器人语音
"""

import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class VoiceoverGenerator:
    """Phase 2 口播生成器 — performance_script驱动"""

    def __init__(self, provider=None):
        self.provider = provider

    def generate(self, master_script: str, output_dir: Path, performance_script: dict = None, character_info: dict = None) -> dict:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: 从主脚本提取口播段
        segments = self._extract_segments(master_script)
        duration = self._extract_duration(master_script)

        # Step 2: 应用 performance_script 的情绪/停顿/重音
        if performance_script:
            segments = self._apply_performance(segments, performance_script)

        # Step 3: voiceover.txt — 带表演标记
        txt_path = output_dir / "voiceover.txt"
        txt_path.write_text(self._build_voiceover_text(segments, duration), encoding="utf-8")

        # Step 4: subtitle.srt
        srt_path = output_dir / "subtitle.srt"
        srt_path.write_text(self._build_srt(segments, duration), encoding="utf-8")

        # Step 5: ElevenLabs TTS
        mp3_path = None
        if os.getenv("ELEVENLABS_API_KEY"):
            try:
                mp3_path = self._tts_elevenlabs(segments, output_dir)
            except Exception as e:
                logger.warning(f"ElevenLabs TTS failed: {e}")

        result = {
            "voiceover_txt": str(txt_path),
            "subtitle_srt": str(srt_path),
            "voice_mp3": str(mp3_path) if mp3_path else None,
            "segments": segments,
        }

        result_path = output_dir / "voiceover_result.json"
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

        logger.info(f"[Phase2 Voiceover] {len(segments)} segments, TTS={'ElevenLabs' if mp3_path else 'none'}")
        return result

    def _extract_segments(self, script: str) -> list[dict]:
        """提取口播段，保留情绪和停顿标记"""
        pattern = re.findall(
            r'##\s*(HOOK|PROBLEM|AGITATE|SOLUTION|RESULT|CTA)[^#]*?口播[：:]\s*"([^"]*)"',
            script, re.DOTALL | re.IGNORECASE,
        )
        if pattern:
            return [{"section": s[0].upper(), "text": s[1].strip()} for s in pattern]

        # 备用: 匹配所有口播行
        pattern2 = re.findall(r'口播[：:]\s*"([^"]*)"', script)
        if pattern2:
            sections = ["HOOK", "PROBLEM", "AGITATE", "SOLUTION", "RESULT", "CTA"]
            return [{"section": sections[i] if i < len(sections) else f"PART{i+1}", "text": t} for i, t in enumerate(pattern2[:6])]

        return [{"section": "FULL", "text": "Please check master_script.md for voiceover content."}]

    def _extract_duration(self, script: str) -> float:
        m = re.search(r'(\d+)[秒s]', script[:500])
        return float(m.group(1)) if m else 15.0

    def _apply_performance(self, segments: list[dict], performance: dict) -> list[dict]:
        """将 performance_script 的情绪/停顿/重音应用到口播段"""
        shots = performance.get("shots", {})
        shot_list = list(shots.values())
        speech = performance.get("speech_pattern", {})
        pauses = speech.get("pauses", [])

        for i, seg in enumerate(segments):
            if i < len(shot_list):
                shot = shot_list[i]
                seg["emotion"] = shot.get("emotion", "natural")
                seg["pace"] = shot.get("pace", "normal")
                seg["gesture"] = shot.get("gesture", "")
                seg["voice_tone"] = shot.get("voice_tone", "")

            # 插入停顿
            for pause in pauses:
                pos = pause.get("position", "")
                if i == 0 and "hook" in pos:
                    seg.setdefault("pauses", []).append(pause)
                elif i == 1 and "problem" in pos and "agitate" not in pos:
                    seg.setdefault("pauses", []).append(pause)
                elif i == 2 and "agitate" in pos:
                    seg.setdefault("pauses", []).append(pause)
                elif i == 3 and "solution" in pos:
                    seg.setdefault("pauses", []).append(pause)
                elif i == 5 and "cta" in pos:
                    seg.setdefault("pauses", []).append(pause)

        return segments

    def _build_voiceover_text(self, segments: list[dict], duration: float) -> str:
        """Phase 3格式: [SECTION] 文本 [PAUSE N] — 纯UGC口播脚本"""
        lines = ["# TikTok UGC Voiceover Script", f"# Duration: {duration:.0f}s", f"# Style: Real person, not AI", ""]

        for i, seg in enumerate(segments):
            section = seg["section"].upper().replace(" ", "_")
            text = seg["text"].strip().strip('"').strip("'")
            # 清理旧标记
            text = __import__('re').sub(r'\[.*?\]', '', text).strip()
            pause_after = seg.get("pause_after", 0)

            lines.append(f"[{section}]")
            lines.append(text)
            lines.append("")
            if pause_after > 0:
                lines.append(f"[PAUSE {pause_after}]")
                lines.append("")

        return "\n".join(lines)

    def _build_srt(self, segments: list[dict], duration: float) -> str:
        seg_dur = duration / max(len(segments), 1)
        entries = []
        for i, seg in enumerate(segments):
            start, end = i * seg_dur, min((i+1) * seg_dur, duration)
            # 清理表演标记
            text = re.sub(r'\[pause\s+[\d.]+\]', '', seg["text"])
            text = text.strip().strip('"').strip("'")
            if len(text) > 20:
                for j in range(len(text)//2, min(len(text)//2+5, len(text))):
                    if text[j] in "，。！？、；：,":
                        text = text[:j+1] + "\n" + text[j+1:]
                        break
            entries.append(f"{i+1}\n{self._ts(start)} --> {self._ts(end)}\n{text}\n")
        return "\n".join(entries)

    def _ts(self, sec: float) -> str:
        h, m = int(sec//3600), int((sec%3600)//60)
        s, ms = int(sec%60), int((sec%1)*1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _tts_elevenlabs(self, segments: list[dict], output_dir: Path) -> Path:
        import requests
        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        # 清理标记后合并
        full_text = " ".join(re.sub(r'\[.*?\]', '', s["text"]).strip() for s in segments)

        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={"text": full_text, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.3, "similarity_boost": 0.8, "style": 0.4}},
            timeout=120,
        )
        resp.raise_for_status()
        mp3_path = output_dir / "voice.mp3"
        mp3_path.write_bytes(resp.content)
        logger.info(f"ElevenLabs TTS: voice.mp3 ({len(resp.content)} bytes)")
        return mp3_path

    # FFmpeg合成
    def composite(self, video_path: Path, voice_path: Path, srt_path: Path, output_path: Path):
        import subprocess
        if not video_path.exists():
            raise FileNotFoundError(f"Video: {video_path}")
        if not voice_path.exists():
            raise FileNotFoundError(f"Voice: {voice_path}")
        cmd = ["ffmpeg", "-y", "-i", str(video_path), "-i", str(voice_path),
               "-vf", f"subtitles={srt_path}:force_style='FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Alignment=2,MarginV=80'",
               "-c:v", "libx264", "-preset", "medium", "-crf", "23",
               "-c:a", "aac", "-b:a", "128k", "-map", "0:v:0", "-map", "1:a:0", "-shortest", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg composite failed: {result.stderr[:500]}")
        logger.info(f"FFmpeg composite: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path
