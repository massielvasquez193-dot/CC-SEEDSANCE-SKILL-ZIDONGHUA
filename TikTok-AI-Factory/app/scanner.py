"""
TikTok AI Video Factory - 文件扫描模块
扫描input目录，发现产品图片、参考视频、人物图片
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from config.settings import (
    PRODUCTS_DIR,
    REFERENCE_VIDEOS_DIR,
    CHARACTERS_DIR,
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_VIDEO_FORMATS,
)

logger = logging.getLogger(__name__)


class FileScanner:
    """扫描input目录中的文件"""

    def __init__(self):
        self.scan_time = datetime.now().isoformat()

    def scan_products(self) -> list[Path]:
        """扫描产品图片"""
        products = []
        if PRODUCTS_DIR.exists():
            for ext in SUPPORTED_IMAGE_FORMATS:
                products.extend(PRODUCTS_DIR.glob(f"*{ext}"))
                products.extend(PRODUCTS_DIR.glob(f"*{ext.upper()}"))
        logger.info(f"扫描到 {len(products)} 个产品图片")
        return sorted(set(products))

    def scan_reference_videos(self) -> list[Path]:
        """扫描参考视频"""
        videos = []
        if REFERENCE_VIDEOS_DIR.exists():
            for ext in SUPPORTED_VIDEO_FORMATS:
                videos.extend(REFERENCE_VIDEOS_DIR.glob(f"*{ext}"))
                videos.extend(REFERENCE_VIDEOS_DIR.glob(f"*{ext.upper()}"))
        logger.info(f"扫描到 {len(videos)} 个参考视频")
        return sorted(set(videos))

    def scan_characters(self) -> list[Path]:
        """扫描人物图片"""
        characters = []
        if CHARACTERS_DIR.exists():
            for ext in SUPPORTED_IMAGE_FORMATS:
                characters.extend(CHARACTERS_DIR.glob(f"*{ext}"))
                characters.extend(CHARACTERS_DIR.glob(f"*{ext.upper()}"))
        logger.info(f"扫描到 {len(characters)} 个人物图片")
        return sorted(set(characters))

    def scan_all(self) -> dict:
        """扫描所有输入文件"""
        return {
            "scan_time": self.scan_time,
            "products": [str(p) for p in self.scan_products()],
            "reference_videos": [str(v) for v in self.scan_reference_videos()],
            "characters": [str(c) for c in self.scan_characters()],
        }

    def get_scan_summary(self) -> str:
        """获取扫描摘要"""
        data = self.scan_all()
        return (
            f"扫描完成 ({data['scan_time']})\n"
            f"  产品图片: {len(data['products'])} 个\n"
            f"  参考视频: {len(data['reference_videos'])} 个\n"
            f"  人物图片: {len(data['characters'])} 个"
        )
