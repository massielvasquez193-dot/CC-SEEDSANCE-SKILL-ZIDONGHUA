"""
TikTok AI Video Factory - 全局配置
"""

import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent

# 输入目录
INPUT_DIR = ROOT_DIR / "input"
PRODUCTS_DIR = INPUT_DIR / "products"
REFERENCE_VIDEOS_DIR = INPUT_DIR / "reference_videos"
CHARACTERS_DIR = INPUT_DIR / "characters"

# 输出目录
OUTPUT_DIR = ROOT_DIR / "output"

# 日志目录
LOGS_DIR = ROOT_DIR / "logs"

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = (".jpg", ".jpeg", ".png", ".webp")

# 支持的视频格式
SUPPORTED_VIDEO_FORMATS = (".mp4", ".mov")

# AI模型配置
AI_PROVIDERS = {
    "openai": {
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "claude": {
        "model": "claude-sonnet-4-6",
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "deepseek": {
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "gemini": {
        "model": "gemini-2.0-flash",
        "temperature": 0.7,
        "max_tokens": 4096,
    },
}

# 默认AI提供商
DEFAULT_AI_PROVIDER = os.getenv("TIKTOK_FACTORY_AI_PROVIDER", "claude")

# 视频生成平台
VIDEO_GEN_PLATFORMS = ["seedance", "veo3", "jimeng", "yunjing", "runway", "kling"]

# 视频时长选项 (秒)
VIDEO_DURATION_OPTIONS = [8, 15, 30, 60]

# 默认视频时长
DEFAULT_VIDEO_DURATION = 15

# Keyframe 数量
KEYFRAME_COUNT = 6

# 日志级别
LOG_LEVEL = os.getenv("TIKTOK_FACTORY_LOG_LEVEL", "INFO")

# 最大并发任务数
MAX_CONCURRENT_TASKS = int(os.getenv("TIKTOK_FACTORY_MAX_CONCURRENT", "3"))

# 确保必要目录存在
for d in [INPUT_DIR, PRODUCTS_DIR, REFERENCE_VIDEOS_DIR, CHARACTERS_DIR, OUTPUT_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
