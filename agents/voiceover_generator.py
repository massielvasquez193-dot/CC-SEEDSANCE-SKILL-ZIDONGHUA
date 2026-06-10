"""
TikTok AI Video Factory - Voiceover Generator (GPT + ElevenLabs)
GPT生成口播文本 → ElevenLabs TTS → voice.mp3
FFmpeg 合成: video + voice.mp3 + subtitle.srt → final video

目标: 真实人声、自然呼吸、口播节奏 — 非AI配音
"""

import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class VoiceoverGenerator:
    """GPT口播 + ElevenLabs TTS 生成器"""

    def __init__(self, provider=None):
        self.provider = provider

    def generate(self, master_script: str, output_dir: Path, character_info: dict = None) -> dict:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: 提取口播段
        segments = self._extract_segments(master_script)
        total_duration = self._extract_duration(master_script)

        # Step 2: GPT优化口播 (增加自然感)
        if self.provider and hasattr(self.provider, 'supports_text') and self.provider.supports_text:
            segments = self._gpt_refine_voiceover(segments, character_info)

        # Step 3: voiceover.txt
        txt_path = output_dir / "voiceover.txt"
        txt_path.write_text(self._build_timeline(segments, total_duration), encoding="utf-8")

        # Step 4: subtitle.srt
        srt_path = output_dir / "subtitle.srt"
        srt_path.write_text(self._build_srt(segments, total_duration), encoding="utf-8")

        # Step 5: ElevenLabs TTS
        mp3_path = None
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if api_key:
            try:
                mp3_path = self._tts_elevenlabs(segments, output_dir, character_info)
            except Exception as e:
                logger.warning(f"ElevenLabs TTS失败: {e}")
        else:
            logger.info("ELEVENLABS_API_KEY not set — skipping TTS, voiceover.txt + subtitle.srt ready")

        result = {
            "voiceover_txt": str(txt_path),
            "subtitle_srt": str(srt_path),
            "voice_mp3": str(mp3_path) if mp3_path else None,
            "segments": segments,
        }

        result_path = output_dir / "voiceover_result.json"
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

        logger.info(f"口播: {len(segments)} segments, TTS={'ElevenLabs' if mp3_path else 'none'}")
        return result

    def _extract_segments(self, script: str) -> list[dict]:
        pattern = re.findall(r'###\s*(HOOK|PROBLEM|SOLUTION|SOCIAL PROOF|CTA)[^`]*```\s*\n(.*?)```', script, re.DOTALL)
        if pattern:
            return [{"section": s[0], "text": s[1].strip().strip('"').strip("'")} for s in pattern]

        pattern = re.findall(r'口播[：:]\s*"([^"]*)"', script)
        if pattern:
            sections = ["HOOK", "PROBLEM", "SOLUTION", "SOCIAL_PROOF", "CTA"]
            return [{"section": sections[i] if i < len(sections) else f"PART_{i+1}", "text": t} for i, t in enumerate(pattern[:5])]

        return [{"section": "FULL", "text": "请参考主脚本中的口播内容。"}]

    def _extract_duration(self, script: str) -> float:
        m = re.search(r'时长[：:]\s*(\d+)', script)
        return float(m.group(1)) if m else 15.0

    def _gpt_refine_voiceover(self, segments: list[dict], character_info: dict) -> list[dict]:
        """GPT优化口播 — 增加口语化、呼吸感、停顿"""
        try:
            original = "\n".join([f"{s['section']}: {s['text']}" for s in segments])
            vibe = character_info.get("vibe", "自然亲切") if character_info else "自然亲切"

            refined = self.provider.generate_text(
                prompt=f"把以下口播改得更口语化、更像真人说话。增加停顿(用...表示)、呼吸感、口语词(天呐/你看/说真的/绝了)。保持原意。\n\n{original}",
                system_prompt=f"你是TikTok真人UGC口播写手。你写的口播像{vibe}的朋友在分享。禁止AI配音腔。直接返回优化后的口播，每段用SECTION:标记。",
                temperature=0.9,
                max_tokens=1000,
            )

            # 解析GPT返回
            refined_segments = []
            for line in refined.split("\n"):
                for section in ["HOOK", "PROBLEM", "SOLUTION", "SOCIAL", "CTA"]:
                    if line.upper().startswith(section):
                        text = line.split(":", 1)[-1].strip().strip('"').strip("'")
                        if text:
                            refined_segments.append({"section": section, "text": text})

            if len(refined_segments) >= 3:
                return refined_segments
        except Exception as e:
            logger.warning(f"GPT口播优化失败: {e}")

        return segments

    def _build_timeline(self, segments: list[dict], total: float) -> str:
        seg_dur = total / max(len(segments), 1)
        lines = [f"# Voiceover Timeline ({total:.0f}s)", ""]
        for i, s in enumerate(segments):
            start = i * seg_dur
            end = min((i+1) * seg_dur, total)
            lines.append(f"## {s['section']} ({start:.1f}s-{end:.1f}s)")
            lines.append(s["text"])
            lines.append("")
        return "\n".join(lines)

    def _build_srt(self, segments: list[dict], total: float) -> str:
        seg_dur = total / max(len(segments), 1)
        entries = []
        for i, s in enumerate(segments):
            start, end = i * seg_dur, min((i+1) * seg_dur, total)
            text = s["text"].strip()
            if len(text) > 20:
                for j in range(len(text)//2, min(len(text)//2+5, len(text))):
                    if text[j] in "，。！？、；：":
                        text = text[:j+1] + "\n" + text[j+1:]
                        break
            entries.append(f"{i+1}\n{self._ts(start)} --> {self._ts(end)}\n{text}\n")
        return "\n".join(entries)

    def _ts(self, sec: float) -> str:
        h, m = int(sec//3600), int((sec%3600)//60)
        s, ms = int(sec%60), int((sec%1)*1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _tts_elevenlabs(self, segments: list[dict], output_dir: Path, character_info: dict) -> Path:
        import requests
        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        full_text = " ".join(s["text"] for s in segments)

        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={
                "text": full_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.35, "similarity_boost": 0.75, "style": 0.3},
            },
            timeout=120,
        )
        resp.raise_for_status()

        mp3_path = output_dir / "voice.mp3"
        mp3_path.write_bytes(resp.content)
        logger.info(f"ElevenLabs TTS: voice.mp3 ({len(resp.content)} bytes)")
        return mp3_path

    # ================================================================
    # FFmpeg 合成: video + voice.mp3 + subtitle.srt → final_video.mp4
    # ================================================================
    def composite(self, video_path: Path, voice_path: Path, srt_path: Path, output_path: Path):
        """FFmpeg合成最终视频: 视频+音频+字幕"""
        import subprocess

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        if not voice_path.exists():
            raise FileNotFoundError(f"Voice not found: {voice_path}")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(voice_path),
            "-vf", f"subtitles={srt_path}:force_style='FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Alignment=2,MarginV=80'",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg合成失败: {result.stderr[:500]}")

        logger.info(f"FFmpeg合成完成: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path
