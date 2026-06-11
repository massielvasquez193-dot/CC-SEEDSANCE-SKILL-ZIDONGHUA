"""
TikTok UGC Video Factory — Character Generator (GPT Image)
使用 GPT Image 生成真实一致的人物参考图

输出:
  character_reference.png  — 人物主参考图 (所有keyframe必须引用)
  character_sheet.png      — 7姿态一致性参考表

姿态:
  正面 / 45度 / 侧面 / 微笑 / 口播 / 拿产品 / CTA动作

规则:
  同一人物贯穿全视频 — same woman, same hair, same outfit, same makeup, same room
  禁止: 随机人物、换脸、人物漂移、Seedance随机人

固定模型: GPT Image (DALL-E 3)
"""

import base64
import json
import logging
import time
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class CharacterGenerator:
    """GPT Image 人物生成器 — 真人级一致性"""

    # 7姿态prompt模板
    POSE_PROMPTS = {
        "front": (
            "front-facing portrait, looking directly at camera, neutral relaxed expression, "
            "natural standing pose, arms relaxed at sides, eye-level smartphone camera angle"
        ),
        "angle_45": (
            "45-degree angle view, slightly turned to the side, looking at camera with slight smile, "
            "natural casual stance, one hand visible, smartphone selfie perspective"
        ),
        "side": (
            "side profile view, looking slightly toward camera, natural profile silhouette, "
            "showing hair length and style from side angle, relaxed posture"
        ),
        "smile": (
            "front-facing warm genuine smile, showing teeth naturally, eyes slightly crinkled, "
            "happy authentic expression, natural laugh moment captured, smartphone quality"
        ),
        "speaking": (
            "front-facing speaking pose, mouth slightly open mid-word, one hand gesturing naturally, "
            "engaged expression as if talking to friend, slight head tilt, casual conversational"
        ),
        "hold_product": (
            "holding a product with both hands at chest level, looking at product then camera, "
            "demonstrating pose, product centered in frame, natural grip, slight lean forward"
        ),
        "cta": (
            "warm smile looking directly at camera, one hand pointing down toward bottom of frame, "
            "product visible in other hand, inviting trustworthy expression, slight lean in"
        ),
    }

    UGC_CHARACTER_SUFFIX = (
        "Real person (not AI, not model, not celebrity). "
        "Natural skin texture with visible pores and slight imperfections. "
        "NO beauty filter, NO plastic skin, NO airbrushing, NO CGI, "
        "NO 3D render, NO cartoon, NO illustration. "
        "Smartphone front camera selfie quality. "
        "Natural window lighting in a real American home. "
        "Casual unstaged candid feel. TikTok UGC authentic style."
    )

    def __init__(self, provider=None):
        self.provider = provider

    # ================================================================
    # 主入口: 生成人物参考图 + 7姿态一致性表
    # ================================================================
    def generate(
        self,
        character_info: dict,
        output_dir: Path,
        product_info: dict = None,
    ) -> dict:
        """
        使用GPT Image生成人物参考图和姿态表

        Returns:
            {
                "reference_image": "path/to/character_reference.png",
                "sheet_image": "path/to/character_sheet.png",
                "character_anchor": "same woman, same hair, same outfit...",
                "poses": [...],
            }
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not self.provider or not (hasattr(self.provider, 'supports_image') and self.provider.supports_image):
            raise RuntimeError(
                "GPT Image provider required for character generation. "
                "Set OPENAI_API_KEY and use --provider openai. "
                "NO random characters, NO placeholders."
            )

        char_desc = self._build_character_description(character_info)
        product_desc = self._build_product_description(product_info) if product_info else "a skincare product"

        # Step 1: 生成主参考图
        logger.info(f"[CharacterGen] Generating character_reference.png...")
        ref_path = output_dir / "character_reference.png"
        self._generate_with_gpt_image(
            prompt=(
                f"Vertical 9:16 portrait of {char_desc}. "
                f"Front-facing, natural relaxed expression, eye-level smartphone camera. "
                f"Clean uncluttered bedroom background. "
                f"{self.UGC_CHARACTER_SUFFIX}"
            ),
            output_path=ref_path,
        )
        logger.info(f"[CharacterGen] character_reference.png: {ref_path.stat().st_size} bytes")

        # Step 2: 生成7姿态一致性表
        logger.info(f"[CharacterGen] Generating character_sheet.png (7 poses)...")
        sheet_path = output_dir / "character_sheet.png"

        # 单图7姿态 — DALL-E 3一次生成
        poses_desc = ", ".join([
            f"top-left: {self.POSE_PROMPTS['front']}",
            f"top-center: {self.POSE_PROMPTS['angle_45']}",
            f"top-right: {self.POSE_PROMPTS['side']}",
            f"middle-left: {self.POSE_PROMPTS['smile']}",
            f"middle-center: {self.POSE_PROMPTS['speaking']}",
            f"bottom-left: {self.POSE_PROMPTS['hold_product'].replace('a product', product_desc)}",
            f"bottom-center: {self.POSE_PROMPTS['cta'].replace('product visible', f'{product_desc} visible')}",
        ])

        sheet_prompt = (
            f"A 3x3 grid photo sheet showing the SAME real woman ({char_desc}) "
            f"in 7 different poses arranged in a grid. "
            f"EVERY panel must show the EXACT same person — same face, same hair, same outfit, same room. "
            f"Poses: {poses_desc}. "
            f"Style: {self.UGC_CHARACTER_SUFFIX}. "
            f"Grid layout: 7 labeled panels on a clean white background. "
            f"Label each panel: 'FRONT', '45DEG', 'SIDE', 'SMILE', 'SPEAK', 'HOLD', 'CTA'."
        )

        self._generate_with_gpt_image(prompt=sheet_prompt, output_path=sheet_path)
        logger.info(f"[CharacterGen] character_sheet.png: {sheet_path.stat().st_size} bytes")

        # Step 3: 构建一致性锚点
        anchor = self._build_character_anchor(character_info)

        result = {
            "reference_image": str(ref_path),
            "sheet_image": str(sheet_path),
            "character_anchor": anchor,
            "poses": list(self.POSE_PROMPTS.keys()),
            "generated_by": "GPT Image (DALL-E 3)",
            "generated_at": datetime.now().isoformat(),
        }

        # 保存元数据
        meta_path = output_dir / "character_generation.json"
        meta_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(f"[CharacterGen] Complete: reference + 7-pose sheet → {output_dir}")
        return result

    # ================================================================
    # 辅助
    # ================================================================
    def _build_character_description(self, info: dict) -> str:
        """构建人物视觉描述"""
        name = info.get("name", "a woman")
        age = info.get("age_range", "25-30")
        hair_style = info.get("hair_style", "long straight hair")
        hair_color = info.get("hair_color", "brown")
        skin_tone = info.get("skin_tone", "natural fair")
        makeup = info.get("makeup", "minimal natural makeup")
        clothing = info.get("clothing", "casual cream top")

        # 从详细字段提取
        if isinstance(clothing, dict):
            clothing = clothing.get("outfit", clothing.get("style", "casual top"))

        return (
            f"a real American woman, {age} years old, "
            f"{hair_style} {hair_color} hair, "
            f"{skin_tone} skin with natural texture, "
            f"{makeup}, wearing {clothing}"
        )

    def _build_product_description(self, info: dict) -> str:
        return f"{info.get('brand', '')} {info.get('product_name', 'product')} ({info.get('color', '')})"

    def _build_character_anchor(self, info: dict) -> str:
        """构建全视频人物一致性锚点"""
        name = info.get("name", "主角")
        hair = f"{info.get('hair_style', 'long straight hair')} {info.get('hair_color', 'brown')}"
        makeup = info.get("makeup", "minimal natural makeup")
        clothing = info.get("clothing", "casual cream top")
        if isinstance(clothing, dict):
            clothing = clothing.get("outfit", "casual top")
        skin = info.get("skin_tone", "natural skin")

        return (
            f"CHARACTER CONSISTENCY ANCHOR — SAME WOMAN across ALL shots:\n"
            f"- Same person: {name}\n"
            f"- Same hair: {hair}\n"
            f"- Same outfit: {clothing}\n"
            f"- Same makeup: {makeup}\n"
            f"- Same skin: {skin}\n"
            f"- Same room: natural bedroom/living room background\n\n"
            f"FORBIDDEN: hair change, outfit change, makeup change, "
            f"face morphing, different person, random character, Seedance random person, "
            f"character drift, face swapping, beauty filter, plastic skin."
        )

    def _generate_with_gpt_image(self, prompt: str, output_path: Path):
        """调用 GPT Image (DALL-E 3) 生成真实图片"""
        import requests

        result = self.provider.generate_image(
            prompt=prompt,
            negative_prompt=(
                "CGI, 3D render, cartoon, illustration, plastic skin, beauty filter, "
                "studio lighting, cinematic, different person in each panel, "
                "hair change, outfit change, inconsistent face, random character"
            ),
            width=1024,
            height=1792,
            num_images=1,
            quality="hd",
            style="vivid",
        )

        if not result or not result[0].get("url"):
            raise RuntimeError(f"GPT Image returned no URL for character generation")

        resp = requests.get(result[0]["url"], timeout=60)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
