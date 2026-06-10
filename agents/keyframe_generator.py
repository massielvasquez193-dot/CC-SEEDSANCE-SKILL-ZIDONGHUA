"""
TikTok AI Video Factory - Keyframe Generator (GPT Image)
每个镜头生成真实关键帧PNG — 使用GPT Image (DALL-E 3)

禁止: PIL绘图、占位图、随机图片模型
固定模型: GPT Image (via OpenAI DALL-E 3 API)

UGC风格要求:
  自然皮肤质感 (非塑料美颜)
  真实手机自拍角度
  真实生活场景 (卧室/客厅/浴室)
  轻微镜头抖动感
  自然光线 (窗光/环形灯)
"""

import base64
import logging
import time
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class KeyframeGenerator:
    """GPT Image 关键帧生成器 — 真实图片，不是占位图"""

    def __init__(self, provider=None):
        self.provider = provider

    def generate(
        self,
        master_script: str,
        storyboard_text: str,
        character_consistency: dict,
        product_info: dict,
        output_dir: Path,
        keyframe_count: int = 9,
    ) -> dict:
        output_dir = Path(output_dir)
        kf_dir = output_dir / "keyframes"
        kf_dir.mkdir(parents=True, exist_ok=True)

        import re
        shot_matches = re.findall(r'###\s*镜头\s*(\d+)', storyboard_text)
        shot_count = len(shot_matches) if shot_matches else keyframe_count

        char_name = character_consistency.get("consistency_rules", {}).get("identity", {}).get("name", "主角")
        char_desc = self._char_desc(character_consistency)
        prod_desc = self._prod_desc(product_info)

        keyframes = []
        descriptions = self._get_shot_descriptions(master_script, shot_count)

        for i in range(shot_count):
            shot_id = i + 1
            desc = descriptions[i % len(descriptions)]

            # 构建 GPT Image prompt — UGC真实感
            prompt = (
                f"Vertical 9:16 smartphone selfie photo, TikTok UGC style. "
                f"A real person ({char_desc}) "
                f"{'holding and showing a product (' + prod_desc + ') to the camera' if i > 0 else 'quickly bringing a product (' + prod_desc + ') close to the camera lens'}. "
                f"{desc}. "
                f"Natural window lighting, real bedroom or living room background, "
                f"slight motion blur from hand movement, casual unstaged feel, "
                f"natural skin texture with no plastic smoothing, "
                f"smartphone front camera quality, slightly imperfect framing. "
                f"NO cinematic lighting, NO studio setup, NO 3D render, "
                f"NO plastic skin, NO perfect composition, NO advertising look."
            )

            kf_path = kf_dir / f"keyframe_{shot_id:02d}.png"

            if self.provider and hasattr(self.provider, 'supports_image') and self.provider.supports_image:
                self._generate_with_gpt_image(prompt, kf_path)
            else:
                raise RuntimeError(
                    f"GPT Image provider not available. "
                    f"Keyframe {shot_id} requires real image generation. "
                    f"Set OPENAI_API_KEY and ensure provider=openai."
                )

            keyframes.append({
                "shot_id": shot_id,
                "path": str(kf_path),
                "file": kf_path.name,
                "prompt": prompt,
                "description": desc,
                "generator": "GPT Image (DALL-E 3)",
            })

            logger.info(f"GPT Image Keyframe {shot_id}/{shot_count}: {kf_path.name}")
            time.sleep(0.5)

        # 保存索引
        import json
        index = {
            "generated_at": datetime.now().isoformat(),
            "generator": "GPT Image (DALL-E 3)",
            "total_keyframes": shot_count,
            "ugc_style": "natural skin, phone selfie, real scene, slight shake",
            "keyframes": [{"shot_id": kf["shot_id"], "file": kf["file"]} for kf in keyframes],
        }
        index_path = kf_dir / "keyframe_index.json"
        index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(f"GPT Image 关键帧生成完成: {shot_count} real PNGs → {kf_dir}")
        return {"keyframes": keyframes, "index_file": str(index_path)}

    def _generate_with_gpt_image(self, prompt: str, output_path: Path):
        """调用 GPT Image (DALL-E 3) 生成真实图片"""
        import requests

        result = self.provider.generate_image(
            prompt=prompt,
            negative_prompt="3D render, cartoon, illustration, plastic skin, studio lighting, cinematic, perfect composition, advertising",
            width=1024,
            height=1792,
            num_images=1,
            quality="hd",
            style="vivid",
        )

        if not result or not result[0].get("url"):
            raise RuntimeError(f"GPT Image returned no URL for prompt: {prompt[:100]}...")

        image_url = result[0]["url"]
        resp = requests.get(image_url, timeout=60)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        logger.info(f"  GPT Image saved: {output_path} ({len(resp.content)} bytes)")

    def _char_desc(self, consistency: dict) -> str:
        rules = consistency.get("consistency_rules", {})
        a = rules.get("appearance", {})
        c = rules.get("clothing", {})
        return (
            f"{a.get('hair_style','long hair')} {a.get('hair_color','black')} hair, "
            f"{a.get('skin_tone','natural')} skin, natural makeup, "
            f"wearing {c.get('outfit','casual top')}, "
            f"real person, not AI, not model, not celebrity"
        )

    def _prod_desc(self, product: dict) -> str:
        return (
            f"{product.get('brand','')} {product.get('product_name','')}, "
            f"{product.get('color','')} color, {product.get('packaging','')} packaging"
        )

    def _get_shot_descriptions(self, script: str, count: int) -> list[str]:
        import re
        descs = re.findall(r'\*\*画面\*\*[：:]\s*(.+?)(?:\n|$)', script)
        if descs and len(descs) >= count:
            return descs[:count]
        return [
            "Product close to camera lens, quick reveal, natural light",
            "Person talking to phone camera naturally, real bedroom background",
            "Person demonstrating product, hand-held, real lighting",
            "Product detail close-up, natural texture visible, no studio",
            "Person + product together, slight camera movement, candid",
            "Before/after or usage result, real unedited look",
            "Person sharing experience genuinely, phone selfie angle",
            "Product centered + person smiling, warm home feel",
            "Final CTA shot, person + product + natural smile",
        ]
