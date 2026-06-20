"""
TikTok UGC Video Factory — Voice Style Analyzer
分析参考视频的语音风格 → voice_style.json

提取: 语速 / 情绪 / 停顿 / 强调词
映射: 情绪 → ElevenLabs settings (stability/style/similarity)
"""

import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class VoiceStyleAnalyzer:
    """语音风格分析器 — 从参考视频提取真人语音模式"""

    # 情绪 → ElevenLabs 参数映射
    EMOTION_TO_ELEVENLABS = {
        "surprised":  {"stability": 0.25, "similarity_boost": 0.70, "style": 0.55, "speed": 1.15},
        "excited":    {"stability": 0.20, "similarity_boost": 0.75, "style": 0.60, "speed": 1.20},
        "concerned":  {"stability": 0.40, "similarity_boost": 0.80, "style": 0.30, "speed": 0.95},
        "happy":      {"stability": 0.30, "similarity_boost": 0.75, "style": 0.50, "speed": 1.05},
        "confident":  {"stability": 0.35, "similarity_boost": 0.80, "style": 0.45, "speed": 1.00},
        "warm":       {"stability": 0.40, "similarity_boost": 0.78, "style": 0.35, "speed": 0.90},
        "urgent":     {"stability": 0.22, "similarity_boost": 0.72, "style": 0.55, "speed": 1.18},
        "natural":    {"stability": 0.35, "similarity_boost": 0.75, "style": 0.40, "speed": 1.00},
    }

    def __init__(self):
        pass

    def analyze(self, performance_script: dict, master_script: str, video_analysis: dict) -> dict:
        """
        分析参考视频 → 生成 voice_style.json
        """
        shots = performance_script.get("shots", {})
        speech = performance_script.get("speech_pattern", {})
        duration = performance_script.get("total_duration", 15)

        # 从 performance_script 提取每段情绪
        segment_styles = []
        for shot_id, shot in shots.items():
            emotion = shot.get("emotion", "natural")
            segment_styles.append({
                "shot": shot_id,
                "role": shot.get("role", ""),
                "emotion": emotion,
                "pace": shot.get("pace", "normal"),
                "elevenlabs_settings": self.EMOTION_TO_ELEVENLABS.get(emotion, self.EMOTION_TO_ELEVENLABS["natural"]),
            })

        voice_style = {
            "version": "phase3",
            "generated_at": datetime.now().isoformat(),
            "source": "performance_script.json analysis",

            # 全局语音参数
            "global_style": {
                "overall_pace": speech.get("overall_pace", "natural"),
                "words_per_second": speech.get("words_per_second", 3.2),
                "emphasis_rule": speech.get("emphasis_rule", "product slow+loud, benefits high pitch"),
                "naturalness": speech.get("naturalness", "include breath sounds, slight imperfections"),
            },

            # 停顿设计
            "pause_design": speech.get("pauses", [
                {"position": "after_hook", "duration": 0.5},
                {"position": "before_cta", "duration": 0.4},
            ]),

            # 逐段语音风格
            "segment_styles": segment_styles,

            # UGC语音铁律
            "ugc_voice_rules": {
                "forbidden": [
                    "AI robotic voice", "broadcast tone", "advertisement voice",
                    "perfect pronunciation", "monotone delivery", "no pauses",
                    "overly polished", "radio voice", "TTS default settings",
                ],
                "required": [
                    "natural breathing sounds", "slight voice cracks", "informal tone",
                    "varying pace within sentence", "emotional emphasis on key words",
                    "slight stumbles (real person feel)", "conversational rhythm",
                ],
            },

            # ElevenLabs 全局默认设置
            "elevenlabs_default": {
                "model": "eleven_multilingual_v2",
                "stability": 0.32,
                "similarity_boost": 0.75,
                "style": 0.45,
                "speaker_boost": True,
            },
        }

        return voice_style

    def get_elevenlabs_settings(self, emotion: str) -> dict:
        """根据情绪获取 ElevenLabs 设置"""
        return self.EMOTION_TO_ELEVENLABS.get(emotion, self.EMOTION_TO_ELEVENLABS["natural"])

    def save(self, voice_style: dict, output_dir: Path) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "voice_style.json"
        path.write_text(json.dumps(voice_style, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Voice style saved: {path}")
        return path
