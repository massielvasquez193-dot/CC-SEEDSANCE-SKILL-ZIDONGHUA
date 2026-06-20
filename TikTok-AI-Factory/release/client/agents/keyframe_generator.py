"""
TikTok UGC Video Factory — Keyframe Generator (GPT Image Phase 2)
每个镜头生成真实关键帧PNG

固定模型: GPT Image (DALL-E 3)
禁止: PIL绘图、占位图、Dummy Image

UGC Prompt规则:
  真实美国TikTok达人 / 真实手机自拍 / 自然肤质
  轻微瑕疵 / 自然光 / 真实家庭场景 / 手持镜头
禁止:
  CGI / Plastic Skin / Beauty Filter / Commercial Studio / 3D Render
"""

import base64
import logging
import time
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class KeyframeGenerator:
    """Phase 2 GPT Image 关键帧生成器"""

    # UGC风格强制prompt后缀
    UGC_STYLE_SUFFIX = (
        "TikTok UGC authentic style. Real person (not model, not AI), "
        "natural skin texture with slight imperfections and visible pores, "
        "NO beauty filter, NO plastic skin, NO airbrushing. "
        "Smartphone front camera selfie quality, natural window lighting, "
        "real American bedroom or living room background, slightly messy lived-in feel. "
        "Handheld phone shot with slight natural camera shake. "
        "Casual unstaged candid moment. "
        "ABSOLUTELY NO: CGI, 3D render, cartoon, illustration, studio lighting, "
        "commercial photography, perfect composition, beauty filter, plastic skin, "
        "over-smoothed face, cinematic look, advertising aesthetic."
    )

    def __init__(self, provider=None):
        self.provider = provider

    def generate(self, master_script: str, storyboard_text: str, character_consistency: dict, product_info: dict, output_dir: Path, keyframe_count: int = 6, character_canon: dict = None) -> dict:
        output_dir = Path(output_dir)
        kf_dir = output_dir / "keyframes"
        kf_dir.mkdir(parents=True, exist_ok=True)

        import re
        shot_matches = re.findall(r'###\s*镜头\s*(\d+)', storyboard_text)
        shot_count = len(shot_matches) if shot_matches else keyframe_count

        keyframes = []
        for i in range(shot_count):
            shot_id = i + 1
            role = ["hook", "problem", "agitate", "solution", "result", "cta"][i % 6]

            prompt = self._build_ugc_prompt(shot_id, role, character_consistency, product_info, master_script, character_canon)
            kf_path = kf_dir / f"keyframe_{shot_id:02d}.png"

            if self.provider and hasattr(self.provider, 'supports_image') and self.provider.supports_image:
                self._generate_with_gpt_image(prompt, kf_path)
            elif self._is_dev_mode():
                logger.warning(f"DEV MODE: Using PIL placeholder for keyframe {shot_id}")
                self._generate_dev_placeholder(prompt, kf_path, shot_id)
            else:
                raise RuntimeError(
                    f"GPT Image provider not available for keyframe {shot_id}. "
                    f"Set OPENAI_API_KEY and use --provider openai. NO placeholders allowed."
                )

            keyframes.append({"shot_id": shot_id, "path": str(kf_path), "file": kf_path.name, "role": role, "prompt": prompt, "generator": "GPT Image (DALL-E 3)"})
            logger.info(f"GPT Image Keyframe {shot_id}/{shot_count}: {kf_path.name} [{role}]")
            time.sleep(0.5)

        import json
        index = {"generated_at": datetime.now().isoformat(), "generator": "GPT Image (DALL-E 3)",
                 "total_keyframes": shot_count, "style": "TikTok UGC — real person, real skin, real home, handheld",
                 "keyframes": [{"shot_id": k["shot_id"], "file": k["file"], "role": k["role"]} for k in keyframes]}
        (kf_dir / "keyframe_index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(f"Phase 2 Keyframes: {shot_count} real GPT Image PNGs → {kf_dir}")
        return {"keyframes": keyframes, "index_file": str(kf_dir / "keyframe_index.json")}

    def _build_ugc_prompt(self, shot_id: int, role: str, consistency: dict, product: dict, script: str, character_canon: dict = None) -> str:
        """UGC风格GPT Image prompt — 强制引用 character.json"""
        # 优先使用 character_canon (人物圣经)
        if character_canon:
            c = character_canon
            identity = c.get("identity", {})
            appearance = c.get("appearance", {})
            hair = appearance.get("hair", {})
            face = appearance.get("face", {})
            body = appearance.get("body", {})
            clothing = c.get("clothing", {})
            makeup = c.get("makeup", {})
            vibe = c.get("vibe", {})

            char_desc = (
                f"a real {identity.get('race','')} {identity.get('gender','female')}, "
                f"{identity.get('age_range','25-30')} years old, "
                f"{hair.get('style','long straight')} {hair.get('color','brown')} hair, "
                f"{face.get('skin_tone','natural')} skin with real texture and visible pores, "
                f"{makeup.get('style','natural minimal')} makeup, "
                f"wearing {clothing.get('outfit','casual top')}, "
                f"{body.get('type','slim')} build, "
                f"{vibe.get('overall','friendly natural')} vibe. "
                f"SAME EXACT PERSON as character.json — NO variation."
            )
        else:
            rules = consistency.get("consistency_rules", {})
            a = rules.get("appearance", {})
            char_desc = (
                f"a real American TikTok creator, {a.get('age_range','25-30')} female, "
                f"{a.get('hair_style','long natural hair')} {a.get('hair_color','brown')}, "
                f"{a.get('skin_tone','natural')} skin with real texture, "
                f"natural minimal makeup, wearing {a.get('clothing',{}).get('outfit','casual top') if isinstance(a.get('clothing'), dict) else 'casual top'}"
            )
        prod_desc = f"{product.get('brand','')} {product.get('product_name','')} ({product.get('color','')})"

        role_prompts = {
            "hook": f"Vertical 9:16 smartphone selfie. {char_desc} holds {prod_desc} VERY close to camera lens, surprised excited expression, product rushes toward camera, motion blur from quick movement, natural room light, candid moment.",
            "problem": f"Vertical 9:16 selfie. {char_desc} looking at camera with concerned relatable expression, slight frown, holding {prod_desc} casually, one hand gesturing, real bedroom behind, window light.",
            "agitate": f"Vertical 9:16 selfie. {char_desc} with frustrated expression, open hands shrugging gesture, head slightly shaking, {prod_desc} on desk nearby, real home background, natural light, imperfect framing.",
            "solution": f"Vertical 9:16 handheld shot. {char_desc} excited discovery expression, holding {prod_desc} with both hands demonstrating use, bright genuine smile, natural light, product-focused frame.",
            "result": f"Vertical 9:16 selfie. {char_desc} proud confident expression, pointing at visible results, holding {prod_desc} next to face showing comparison, warm natural light, genuine smile.",
            "cta": f"Vertical 9:16 selfie. {char_desc} warm genuine smile looking directly at camera, {prod_desc} centered in frame with logo visible, one hand gesturing toward bottom of frame, clean warm home background.",
        }

        base = role_prompts.get(role, role_prompts["solution"])
        return f"{base} {self.UGC_STYLE_SUFFIX}"

    @staticmethod
    def _is_dev_mode() -> bool:
        import os
        return os.getenv("TIKTOK_FACTORY_DEV_MODE", "").lower() in ("true", "1", "yes")

    def _generate_dev_placeholder(self, prompt: str, output_path: Path, shot_id: int):
        """Dev mode: generate a labeled placeholder image via PIL"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (1024, 1792), "#2a1a3e")
            draw = ImageDraw.Draw(img)
            try:
                font_large = ImageFont.truetype("arial.ttf", 36)
                font_small = ImageFont.truetype("arial.ttf", 20)
            except Exception:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            draw.text((40, 800), f"KEYFRAME {shot_id:02d}", fill="#e94560", font=font_large)
            draw.text((40, 860), "[DEV PLACEHOLDER]", fill="#ffcc00", font=font_small)
            # Truncate prompt for display
            lines = [prompt[i:i+50] for i in range(0, min(len(prompt), 300), 50)]
            y = 920
            for line in lines[:6]:
                draw.text((40, y), line.strip(), fill="#888888", font=font_small)
                y += 28
            img.save(output_path)
            logger.info(f"  Dev placeholder: {output_path}")
        except Exception as e:
            logger.warning(f"Dev placeholder failed: {e}")
            output_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    def _generate_with_gpt_image(self, prompt: str, output_path: Path):
        import requests
        result = self.provider.generate_image(
            prompt=prompt,
            negative_prompt="CGI, 3D render, cartoon, illustration, plastic skin, beauty filter, studio lighting, cinematic, commercial photography, perfect composition, over-smoothed",
            width=1024, height=1792, num_images=1, quality="hd", style="vivid",
        )
        if not result or not result[0].get("url"):
            raise RuntimeError(f"GPT Image returned no URL")
        resp = requests.get(result[0]["url"], timeout=60)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        logger.info(f"  GPT Image: {output_path} ({len(resp.content)} bytes)")
