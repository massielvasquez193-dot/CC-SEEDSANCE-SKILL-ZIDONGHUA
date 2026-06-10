"""
TikTok AI Video Factory - 人物分析模块 (P3)
功能: 读取人物图片，输出年龄段/性别/肤色/发型/服装/妆容，保存character.json
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class CharacterExtractor:
    """人物特征提取器 — 从人物图片中提取结构化人物数据"""

    # 年龄段划分
    AGE_RANGES = {
        "teen": "13-19岁 / 青少年",
        "young_adult": "20-25岁 / 年轻成人",
        "adult": "25-30岁 / 成人",
        "mature": "30-40岁 / 成熟",
        "middle_age": "40-50岁 / 中年",
        "senior": "50岁以上 / 老年",
    }

    # 肤色描述
    SKIN_TONES = {
        "fair": "白皙 / 冷白皮",
        "light": "自然偏白 / 暖白皮",
        "medium": "自然肤色 / 中性皮",
        "olive": "橄榄皮 / 小麦色偏暖",
        "tan": "小麦色 / 健康肤色",
        "dark": "深肤色 / 偏黑",
        "deep": "深色 / 黑皮",
    }

    # 发型分类
    HAIR_STYLES = {
        "long_straight": "长直发",
        "long_wavy": "长卷发",
        "medium_straight": "中长直发 / 锁骨发",
        "medium_wavy": "中长卷发 / 波浪",
        "short_bob": "短发 / 波波头",
        "short_pixie": "超短发 / 精灵短发",
        "ponytail": "马尾",
        "bun": "丸子头 / 发髻",
        "braid": "编发 / 辫子",
        "half_up": "半扎发",
        "messy": "慵懒随意",
        "styled_updo": "精致盘发",
    }

    # 发色
    HAIR_COLORS = {
        "black": "黑色",
        "dark_brown": "深棕色",
        "light_brown": "浅棕色 / 栗色",
        "blonde": "金色",
        "red": "红色 / 红棕色",
        "gray": "灰色 / 银发",
        "colorful": "彩色 / 染发",
        "ombre": "渐变染",
        "highlight": "挑染",
    }

    # 妆容风格
    MAKEUP_STYLES = {
        "natural": "自然裸妆 / 伪素颜",
        "korean": "韩系水光妆",
        "japanese": "日系元气妆",
        "western": "欧美妆 / 浓妆",
        "clean": "清纯淡妆",
        "matte": "哑光雾面妆",
        "dewy": "水光肌 / 光泽妆",
        "retro": "复古妆",
        "no_makeup": "素颜 / 无妆",
        "light": "淡妆",
        "full_glam": "全妆 / 精致妆容",
    }

    # 服装风格
    CLOTHING_STYLES = {
        "casual": "休闲日常",
        "streetwear": "街头潮流",
        "minimal": "极简风",
        "elegant": "优雅知性",
        "sporty": "运动休闲",
        "vintage": "复古风",
        "korean_fashion": "韩系穿搭",
        "japanese_fashion": "日系穿搭",
        "office": "通勤 / 职场",
        "sexy": "性感风",
        "cute": "甜美可爱",
        "home": "居家舒适",
        "luxury": "轻奢 / 高级感",
        "athleisure": "运动时尚",
    }

    # 体型
    BODY_TYPES = {
        "slim": "纤细 / 苗条",
        "athletic": "运动型 / 紧致",
        "average": "标准 / 匀称",
        "curvy": "丰满 / 曲线型",
        "petite": "娇小",
        "tall": "高挑",
    }

    # 气质描述
    VIBES = {
        "friendly": "亲切 / 邻家",
        "professional": "专业 / 干练",
        "cool": "酷帅 / 高冷",
        "cute": "可爱 / 甜美",
        "elegant": "优雅 / 知性",
        "energetic": "活力 / 元气",
        "minimalist": "极简 / 高级",
        "trendy": "时尚 / 潮流",
        "natural": "自然 / 清新",
        "confident": "自信 / 气场强",
    }

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    # ================================================================
    # 主提取方法
    # ================================================================
    def extract(self, image_path: Path) -> dict:
        """
        从人物图片提取完整特征
        Returns: 姓名代号/年龄段/性别/肤色/发型/发色/脸型/妆容/服装/体型/气质
        """
        logger.info(f"提取人物特征: {image_path.name}")

        character = {
            "file_name": image_path.name,
            "file_path": str(image_path),
            "file_size_bytes": image_path.stat().st_size if image_path.exists() else 0,
            "format": image_path.suffix.lower(),
            "name": "",
            "age_range": "",
            "age_range_en": "",
            "gender": "",
            "skin_tone": "",
            "skin_tone_en": "",
            "hair_style": "",
            "hair_style_en": "",
            "hair_color": "",
            "hair_color_en": "",
            "face_shape": "",
            "eye_shape": "",
            "makeup": "",
            "makeup_en": "",
            "makeup_detail": "",
            "clothing": "",
            "clothing_style": "",
            "clothing_detail": "",
            "body_type": "",
            "height_estimate": "",
            "distinctive_features": [],
            "overall_style": "",
            "vibe": "",
            "vibe_en": "",
            "expression": "",
            "pose": "",
            "extraction_method": "heuristic",
        }

        # 从文件名推断
        filename_info = self._parse_filename(image_path.stem)
        character.update(filename_info)

        # AI视觉分析
        if self.ai_client:
            try:
                ai_info = self._ai_analyze(image_path)
                if ai_info:
                    character.update(ai_info)
                    character["extraction_method"] = "ai"
            except Exception as e:
                logger.error(f"AI人物分析失败: {e}")

        # 补充默认值
        character = self._fill_defaults(character)

        return character

    # ================================================================
    # 文件名解析
    # ================================================================
    def _parse_filename(self, filename: str) -> dict:
        """从文件名推断人物信息"""
        clean = filename.replace("-", "_").replace(" ", "_")
        parts = [p for p in clean.split("_") if p]

        info = {}
        if parts:
            info["name"] = parts[0]

        # 尝试匹配已知属性
        for part in parts:
            part_lower = part.lower()
            # 性别
            if part_lower in ("female", "male", "woman", "man", "girl", "boy"):
                info["gender"] = "female" if part_lower in ("female", "woman", "girl") else "male"
            # 年龄段
            for key, val in self.AGE_RANGES.items():
                if key in part_lower:
                    info["age_range_en"] = key
                    info["age_range"] = val
                    break

        return info

    # ================================================================
    # 默认值填充
    # ================================================================
    def _fill_defaults(self, character: dict) -> dict:
        """填充未识别字段的默认值"""
        defaults = {
            "name": "character_01",
            "age_range": self.AGE_RANGES["adult"],
            "age_range_en": "adult",
            "gender": "female",
            "skin_tone": self.SKIN_TONES["light"],
            "skin_tone_en": "light",
            "hair_style": self.HAIR_STYLES["long_straight"],
            "hair_style_en": "long_straight",
            "hair_color": self.HAIR_COLORS["black"],
            "hair_color_en": "black",
            "face_shape": "鹅蛋脸 / oval",
            "eye_shape": "杏仁眼 / almond",
            "makeup": self.MAKEUP_STYLES["natural"],
            "makeup_en": "natural",
            "makeup_detail": "清透底妆、自然眉形、淡色唇釉",
            "clothing": "简约白色上衣",
            "clothing_style": self.CLOTHING_STYLES["casual"],
            "clothing_detail": "日常休闲风格，干净利落",
            "body_type": self.BODY_TYPES["slim"],
            "height_estimate": "160-170cm",
            "distinctive_features": [],
            "overall_style": "自然清新",
            "vibe": self.VIBES["friendly"],
            "vibe_en": "friendly",
            "expression": "自然微笑 / natural smile",
            "pose": "正面站立 / front facing",
        }

        for key, val in defaults.items():
            if not character.get(key):
                character[key] = val

        return character

    # ================================================================
    # AI分析
    # ================================================================
    def _ai_analyze(self, image_path: Path) -> dict:
        """使用AI视觉分析人物图片"""
        if not self.ai_client:
            return {}

        try:
            prompt = """分析这个人物图片，以JSON返回所有特征：
{
    "name": "人物代号",
    "age_range": "年龄段(中文)",
    "age_range_en": "teen/young_adult/adult/mature/middle_age/senior",
    "gender": "female/male",
    "skin_tone": "肤色描述(中文)",
    "skin_tone_en": "fair/light/medium/olive/tan/dark/deep",
    "hair_style": "发型中文描述",
    "hair_style_en": "long_straight/long_wavy/medium_straight/medium_wavy/short_bob/short_pixie/ponytail/bun/braid/half_up/messy/styled_updo",
    "hair_color": "发色中文描述",
    "hair_color_en": "black/dark_brown/light_brown/blonde/red/gray/colorful/ombre/highlight",
    "face_shape": "脸型",
    "eye_shape": "眼型",
    "makeup": "妆容风格中文",
    "makeup_en": "natural/korean/japanese/western/clean/matte/dewy/retro/no_makeup/light/full_glam",
    "makeup_detail": "妆容细节描述",
    "clothing": "服装描述",
    "clothing_style": "服装风格中文",
    "clothing_detail": "服装细节",
    "body_type": "体型中文",
    "height_estimate": "身高估算",
    "distinctive_features": ["显著特征"],
    "overall_style": "整体风格",
    "vibe": "气质中文",
    "vibe_en": "friendly/professional/cool/cute/elegant/energetic/minimalist/trendy/natural/confident",
    "expression": "表情描述",
    "pose": "姿势描述"
}"""
            # response = self.ai_client.analyze_image(image_path, prompt)
            # return json.loads(response)
            return {}
        except Exception:
            return {}

    # ================================================================
    # 一致性描述
    # ================================================================
    def generate_consistency_description(self, character: dict) -> str:
        """
        生成人物一致性描述
        用于所有镜头的Prompt前缀，确保人物不变
        """
        c = character
        lines = [
            "=== 人物一致性要求 (全部镜头必须遵守) ===",
            "",
            f"同一人物: {c.get('name', '')}",
            f"  - 年龄: {c.get('age_range', '')}",
            f"  - 性别: {c.get('gender', '')}",
            f"  - 肤色: {c.get('skin_tone', '')}",
            f"  - 发型: {c.get('hair_style', '')}，{c.get('hair_color', '')}",
            f"  - 妆容: {c.get('makeup', '')}（{c.get('makeup_detail', '')}）",
            f"  - 服装: {c.get('clothing', '')}（{c.get('clothing_style', '')}）",
            f"  - 脸型: {c.get('face_shape', '')}",
            f"  - 体型: {c.get('body_type', '')}",
            f"  - 气质: {c.get('vibe', '')}",
            f"  - 整体风格: {c.get('overall_style', '')}",
            "",
            "禁止事项:",
            "  - 禁止改变人物发型、发色、长度",
            "  - 禁止改变妆容风格",
            "  - 禁止改变服装",
            "  - 禁止改变肤色",
            "  - 禁止改变年龄感",
            "  - 禁止替换为不同人物",
            "  - 禁止出现原视频人物的脸/身份/特征",
        ]
        return "\n".join(lines)

    # ================================================================
    # 默认角色
    # ================================================================
    @classmethod
    def default_character(cls) -> dict:
        """
        默认人物设定 (来自SKILL.md)
        一位年轻成年女性美妆达人，干净自然妆容，长发，居家上衣，粉色美甲
        """
        return {
            "name": "default_beauty_creator",
            "age_range": cls.AGE_RANGES["young_adult"],
            "age_range_en": "young_adult",
            "gender": "female",
            "skin_tone": cls.SKIN_TONES["light"],
            "skin_tone_en": "light",
            "hair_style": cls.HAIR_STYLES["long_straight"],
            "hair_style_en": "long_straight",
            "hair_color": cls.HAIR_COLORS["dark_brown"],
            "hair_color_en": "dark_brown",
            "face_shape": "鹅蛋脸 / oval",
            "eye_shape": "杏仁眼 / almond",
            "makeup": cls.MAKEUP_STYLES["natural"],
            "makeup_en": "natural",
            "makeup_detail": "干净自然底妆、野生眉、裸色唇釉、轻微腮红",
            "clothing": "居家上衣 (浅色系)",
            "clothing_style": cls.CLOTHING_STYLES["home"],
            "clothing_detail": "舒适的居家上衣、粉色美甲",
            "body_type": cls.BODY_TYPES["slim"],
            "height_estimate": "160-168cm",
            "distinctive_features": ["粉色美甲", "自然微笑", "干净妆容"],
            "overall_style": "自然清新美妆达人",
            "vibe": cls.VIBES["friendly"],
            "vibe_en": "friendly",
            "expression": "自然微笑、有种草感、真实亲切",
            "pose": "面对手机前置镜头自然口播",
        }

    # ================================================================
    # 保存
    # ================================================================
    def save_character_json(self, character: dict, output_dir: Path) -> Path:
        """保存 character.json"""
        output_dir.mkdir(parents=True, exist_ok=True)
        character["extracted_at"] = datetime.now().isoformat()

        json_path = output_dir / "character.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(character, f, ensure_ascii=False, indent=2)
        logger.info(f"character.json 已保存: {json_path}")
        return json_path

    def batch_extract(self, image_paths: list[Path]) -> list[dict]:
        """批量提取人物特征"""
        return [self.extract(p) for p in image_paths]
