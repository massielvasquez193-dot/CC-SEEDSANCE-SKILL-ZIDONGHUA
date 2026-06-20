"""
TikTok AI Video Factory - API密钥管理
从环境变量读取，不硬编码密钥
"""

import os
from typing import Optional


class APIKeys:
    """API密钥管理器"""

    @staticmethod
    def get_openai_key() -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")

    @staticmethod
    def get_claude_key() -> Optional[str]:
        return os.getenv("ANTHROPIC_API_KEY")

    @staticmethod
    def get_deepseek_key() -> Optional[str]:
        return os.getenv("DEEPSEEK_API_KEY")

    @staticmethod
    def get_gemini_key() -> Optional[str]:
        return os.getenv("GEMINI_API_KEY")

    @staticmethod
    def get_seedance_key() -> Optional[str]:
        return os.getenv("SEEDANCE_API_KEY")

    @staticmethod
    def get_veo3_key() -> Optional[str]:
        return os.getenv("VEO3_API_KEY")

    @staticmethod
    def get_jimeng_key() -> Optional[str]:
        return os.getenv("JIMENG_API_KEY")

    @staticmethod
    def get_runway_key() -> Optional[str]:
        return os.getenv("RUNWAY_API_KEY")

    @staticmethod
    def get_kling_key() -> Optional[str]:
        return os.getenv("KLING_API_KEY")

    @classmethod
    def get_key(cls, provider: str) -> Optional[str]:
        """根据提供商名称获取API密钥"""
        method_map = {
            "openai": cls.get_openai_key,
            "claude": cls.get_claude_key,
            "deepseek": cls.get_deepseek_key,
            "gemini": cls.get_gemini_key,
            "seedance": cls.get_seedance_key,
            "veo3": cls.get_veo3_key,
            "jimeng": cls.get_jimeng_key,
            "runway": cls.get_runway_key,
            "kling": cls.get_kling_key,
        }
        method = method_map.get(provider.lower())
        return method() if method else None

    @classmethod
    def check_all(cls) -> dict:
        """检查所有API密钥状态"""
        providers = ["openai", "claude", "deepseek", "gemini", "seedance", "veo3", "jimeng", "runway", "kling"]
        return {p: bool(cls.get_key(p)) for p in providers}
