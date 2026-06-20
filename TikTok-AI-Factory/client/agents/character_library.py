"""
TikTok AI Video Factory - Character Library
管理多个数字人素材，自动提取特征，生成 character_profile.json

支持 input/characters/ 多个数字人
每个数字人生成独立 profile
支持按国家/年龄/风格筛选匹配
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class CharacterLibrary:
    """数字人素材库"""

    # 国家识别 (从文件名/特征推断)
    COUNTRY_INDICATORS = {
        "cn": "中国", "us": "美国", "jp": "日本", "kr": "韩国",
        "br": "巴西", "id": "印尼", "th": "泰国", "vn": "越南",
        "ph": "菲律宾", "mx": "墨西哥", "sa": "沙特", "ae": "阿联酋",
        "chinese": "中国", "american": "美国", "japanese": "日本",
        "korean": "韩国", "brazilian": "巴西", "indonesian": "印尼",
    }

    def __init__(self, characters_dir: Path = None, ai_client=None):
        from config.settings import CHARACTERS_DIR
        self.characters_dir = characters_dir or CHARACTERS_DIR
        self.ai_client = ai_client
        self.library: dict[str, dict] = {}

    # ================================================================
    # 扫描与提取
    # ================================================================
    def scan_and_build(self) -> dict[str, dict]:
        """扫描 characters/ 目录，为每个数字人生成 profile"""
        self.library = {}

        if not self.characters_dir.exists():
            logger.warning(f"Characters directory not found: {self.characters_dir}")
            return self.library

        from app.character_extractor import CharacterExtractor
        extractor = CharacterExtractor(self.ai_client)

        supported = (".jpg", ".jpeg", ".png", ".webp")
        image_files = []
        for ext in supported:
            image_files.extend(self.characters_dir.glob(f"*{ext}"))
            image_files.extend(self.characters_dir.glob(f"*{ext.upper()}"))

        for img_path in sorted(set(image_files)):
            char_id = img_path.stem
            logger.info(f"注册数字人: {char_id}")

            # 基础特征提取
            features = extractor.extract(img_path)

            # 构建 profile
            profile = self._build_profile(char_id, img_path, features)
            self.library[char_id] = profile

        logger.info(f"数字人库: {len(self.library)} 个角色已注册")
        return self.library

    def _build_profile(self, char_id: str, img_path: Path, features: dict) -> dict:
        """构建单个数字人的完整 profile"""
        # 推断国家
        country = self._detect_country(char_id, features)

        profile = {
            "character_id": char_id,
            "file": str(img_path),
            "file_name": img_path.name,

            # 身份
            "identity": {
                "name": features.get("name", char_id),
                "age_range": features.get("age_range", "25-30岁"),
                "gender": features.get("gender", "female"),
                "country": country,
                "language": self._country_to_language(country),
            },

            # 外观
            "appearance": {
                "hair_style": features.get("hair_style", ""),
                "hair_color": features.get("hair_color", ""),
                "skin_tone": features.get("skin_tone", ""),
                "face_shape": features.get("face_shape", ""),
                "body_type": features.get("body_type", ""),
                "height": features.get("height_estimate", ""),
                "distinctive_features": features.get("distinctive_features", []),
            },

            # 妆容
            "makeup": {
                "style": features.get("makeup", ""),
                "detail": features.get("makeup_detail", ""),
            },

            # 服装
            "clothing": {
                "outfit": features.get("clothing", ""),
                "style": features.get("clothing_style", ""),
                "detail": features.get("clothing_detail", ""),
            },

            # 风格/气质
            "style": {
                "vibe": features.get("vibe", ""),
                "overall_style": features.get("overall_style", ""),
                "expression": features.get("expression", ""),
            },

            # 元数据
            "metadata": {
                "registered_at": datetime.now().isoformat(),
                "source_file": str(img_path),
                "file_size": img_path.stat().st_size if img_path.exists() else 0,
                "extraction_method": features.get("extraction_method", "heuristic"),
            },

            # 标签 (用于搜索匹配)
            "tags": self._generate_tags(features, country),
        }

        return profile

    # ================================================================
    # 国家/语言检测
    # ================================================================
    def _detect_country(self, char_id: str, features: dict) -> str:
        """从文件名和特征推断国家"""
        name_lower = char_id.lower()

        for indicator, country in self.COUNTRY_INDICATORS.items():
            if indicator in name_lower:
                return country

        # 从肤色推断
        skin = features.get("skin_tone", "").lower()
        if "白" in skin:
            return "中国"
        elif "小麦" in skin:
            return "巴西"

        return "中国"  # 默认

    def _country_to_language(self, country: str) -> str:
        lang_map = {
            "中国": "zh", "美国": "en", "英国": "en",
            "日本": "ja", "韩国": "ko", "巴西": "pt",
            "印尼": "id", "泰国": "th", "越南": "vi",
            "菲律宾": "en", "墨西哥": "es", "沙特": "ar", "阿联酋": "ar",
        }
        return lang_map.get(country, "en")

    def _generate_tags(self, features: dict, country: str) -> list[str]:
        tags = [country]
        vibe = features.get("vibe", "")
        if "亲切" in str(vibe):
            tags.append("warm")
        if "专业" in str(vibe):
            tags.append("professional")
        if "酷" in str(vibe):
            tags.append("cool")
        if "优雅" in str(vibe):
            tags.append("elegant")

        age = features.get("age_range", "")
        if "20" in str(age):
            tags.append("young")
        elif "30" in str(age):
            tags.append("mature")

        gender = features.get("gender", "")
        tags.append(gender)

        return tags

    # ================================================================
    # 查询匹配
    # ================================================================
    def get_character(self, character_id: str) -> Optional[dict]:
        """按ID获取数字人"""
        return self.library.get(character_id)

    def find_by_country(self, country: str) -> list[dict]:
        """按国家筛选"""
        return [
            p for p in self.library.values()
            if p["identity"]["country"] == country
        ]

    def find_by_tags(self, tags: list[str]) -> list[dict]:
        """按标签筛选"""
        result = []
        for p in self.library.values():
            p_tags = p.get("tags", [])
            if all(t in p_tags for t in tags):
                result.append(p)
        return result

    def match_for_product(self, product_info: dict, country: str = None) -> Optional[dict]:
        """为产品匹配最佳数字人"""
        if country:
            candidates = self.find_by_country(country)
        else:
            candidates = list(self.library.values())

        if not candidates:
            return None

        # 优先匹配目标用户年龄段
        audience = product_info.get("target_audience", "")
        if "年轻" in str(audience):
            candidates = [
                c for c in candidates
                if "young" in c.get("tags", [])
            ] or candidates

        return candidates[0] if candidates else None

    # ================================================================
    # 保存
    # ================================================================
    def save_library(self, output_dir: Path) -> Path:
        """保存整个数字人库"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        lib_data = {
            "library_version": "2.0",
            "updated_at": datetime.now().isoformat(),
            "total_characters": len(self.library),
            "characters": {
                cid: {
                    k: v for k, v in profile.items()
                    if k != "metadata"  # metadata可能过大
                }
                for cid, profile in self.library.items()
            },
        }

        path = output_dir / "character_library.json"
        path.write_text(
            json.dumps(lib_data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        logger.info(f"Character library saved: {path} ({len(self.library)} characters)")
        return path

    def save_character_profile(self, character_id: str, output_dir: Path) -> Path:
        """保存单个数字人 profile"""
        profile = self.library.get(character_id)
        if not profile:
            raise ValueError(f"Character not found: {character_id}")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "character_profile.json"
        path.write_text(
            json.dumps(profile, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        return path
