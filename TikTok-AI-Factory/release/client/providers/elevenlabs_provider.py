"""
TikTok UGC Video Factory — ElevenLabs Provider
真人级TTS: Text-to-Speech / Voice Cloning / Multi-Language

API: https://api.elevenlabs.io/v1
Env:  ELEVENLABS_API_KEY

UGC要求: 禁止广告腔、播音腔、AI机器人语音
目标: 听起来像真人TikTok达人自拍视频
"""

import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class ElevenLabsProvider(BaseProvider):
    provider_name = "elevenlabs"
    requires_api_key = True
    supports_text = False
    supports_image = False
    supports_vision = False
    supports_video = False
    supports_audio = True

    API_BASE = "https://api.elevenlabs.io/v1"

    # 情绪→ElevenLabs参数映射
    EMOTION_SETTINGS = {
        "surprised":  {"stability": 0.25, "similarity_boost": 0.70, "style": 0.55, "speed": 1.15},
        "excited":    {"stability": 0.20, "similarity_boost": 0.75, "style": 0.60, "speed": 1.20},
        "concerned":  {"stability": 0.40, "similarity_boost": 0.80, "style": 0.30, "speed": 0.95},
        "happy":      {"stability": 0.30, "similarity_boost": 0.75, "style": 0.50, "speed": 1.05},
        "confident":  {"stability": 0.35, "similarity_boost": 0.80, "style": 0.45, "speed": 1.00},
        "warm":       {"stability": 0.40, "similarity_boost": 0.78, "style": 0.35, "speed": 0.90},
        "urgent":     {"stability": 0.22, "similarity_boost": 0.72, "style": 0.55, "speed": 1.18},
        "natural":    {"stability": 0.35, "similarity_boost": 0.75, "style": 0.40, "speed": 1.00},
    }

    def _default_model(self) -> str:
        return "eleven_multilingual_v2"

    def _create_client(self):
        import requests
        session = requests.Session()
        session.headers.update({
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        })
        return session

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            resp = self.client.get(f"{self.API_BASE}/voices", timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    # ================================================================
    # TTS — 文本转语音
    # ================================================================
    def text_to_speech(
        self,
        text: str,
        voice_id: str = None,
        emotion: str = "natural",
        output_path: Path = None,
        **kwargs,
    ) -> Path:
        """
        文本转语音 — UGC真人风格

        Args:
            text: 要转换的文本
            voice_id: ElevenLabs voice ID (默认从 config/voices.json 读取)
            emotion: surprised/excited/concerned/happy/confident/warm/urgent/natural
            output_path: 输出路径
        """
        voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        settings = self.EMOTION_SETTINGS.get(emotion, self.EMOTION_SETTINGS["natural"])

        url = f"{self.API_BASE}/text-to-speech/{voice_id}"
        payload = {
            "text": text,
            "model_id": kwargs.get("model_id", "eleven_multilingual_v2"),
            "voice_settings": {
                "stability": settings["stability"],
                "similarity_boost": settings["similarity_boost"],
                "style": settings["style"],
                "use_speaker_boost": kwargs.get("speaker_boost", True),
            },
        }

        resp = self.client.post(url, json=payload, timeout=120)
        resp.raise_for_status()

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(resp.content)
            logger.info(f"ElevenLabs TTS [{emotion}]: {output_path} ({len(resp.content)} bytes)")
            return output_path

        return resp.content

    # ================================================================
    # TTS with timestamps — 带时间戳的语音生成 (字幕对齐)
    # ================================================================
    def text_to_speech_with_timestamps(
        self,
        text: str,
        voice_id: str = None,
        emotion: str = "natural",
        output_path: Path = None,
    ) -> dict:
        """
        生成语音 + 单词级时间戳
        """
        voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        settings = self.EMOTION_SETTINGS.get(emotion, self.EMOTION_SETTINGS["natural"])

        url = f"{self.API_BASE}/text-to-speech/{voice_id}/with-timestamps"
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": settings["stability"],
                "similarity_boost": settings["similarity_boost"],
                "style": settings["style"],
            },
        }

        resp = self.client.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        # 保存音频
        if output_path and data.get("audio_base64"):
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(base64.b64decode(data["audio_base64"]))
            logger.info(f"ElevenLabs TTS+timestamps: {output_path}")

        return data

    # ================================================================
    # Voice Cloning — 声音克隆
    # ================================================================
    def clone_voice(
        self,
        name: str,
        audio_samples: list[Path],
        description: str = "",
        labels: dict = None,
    ) -> str:
        """
        克隆声音 → 返回 voice_id
        """
        url = f"{self.API_BASE}/voices/add"

        files = []
        for i, sample in enumerate(audio_samples):
            files.append(("files", (f"sample_{i}.mp3", sample.read_bytes(), "audio/mpeg")))

        data = {
            "name": name,
            "description": description or f"Cloned voice: {name}",
            "labels": json.dumps(labels or {}),
        }

        resp = self.client.post(url, data=data, files=files, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        voice_id = result.get("voice_id", "")
        logger.info(f"Voice cloned: {name} → {voice_id}")
        return voice_id

    # ================================================================
    # Multi-Language TTS
    # ================================================================
    def text_to_speech_multilingual(
        self,
        text: str,
        language: str = "en",
        voice_id: str = None,
        emotion: str = "natural",
        output_path: Path = None,
    ) -> Path:
        """
        多语言TTS — en/zh/ja/ko/es/pt/ar...
        """
        voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        # ElevenLabs multilingual v2 supports 29 languages
        supported = {"en", "zh", "ja", "ko", "es", "pt", "ar", "fr", "de", "id", "th", "vi", "hi"}
        if language not in supported:
            logger.warning(f"Language '{language}' may not be supported, falling back to auto-detect")

        return self.text_to_speech(
            text=text,
            voice_id=voice_id,
            emotion=emotion,
            output_path=output_path,
            model_id="eleven_multilingual_v2",
        )

    # ================================================================
    # Voice Library — 获取可用声音
    # ================================================================
    def list_voices(self) -> list[dict]:
        """获取所有可用声音"""
        resp = self.client.get(f"{self.API_BASE}/voices", timeout=15)
        resp.raise_for_status()
        return resp.json().get("voices", [])

    def get_voice(self, voice_id: str) -> dict:
        """获取单个声音信息"""
        resp = self.client.get(f"{self.API_BASE}/voices/{voice_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()

    # ================================================================
    # 语音历史
    # ================================================================
    def get_history(self, page_size: int = 10) -> dict:
        resp = self.client.get(f"{self.API_BASE}/history", params={"page_size": page_size}, timeout=15)
        resp.raise_for_status()
        return resp.json()

    # ================================================================
    # BaseProvider compatibility
    # ================================================================
    def _generate_text_impl(self, *args, **kwargs):
        raise NotImplementedError("ElevenLabs is audio-only")
    def _generate_image_impl(self, *args, **kwargs):
        raise NotImplementedError("ElevenLabs is audio-only")
    def _generate_video_impl(self, *args, **kwargs):
        raise NotImplementedError("ElevenLabs is audio-only")
