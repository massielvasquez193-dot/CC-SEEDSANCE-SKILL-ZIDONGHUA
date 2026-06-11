"""
TikTok AI Video Factory - Seedance Segment Generator (GPT-driven v3)
每个镜头: Reference Image(对应Keyframe) + Prompt + Continuity Anchor
禁止纯Prompt视频生成

格式:
  [REFERENCE IMAGE]  ← 必须引用keyframe_NN.png (GPT Image生成的真实图片)
  [POSITIVE PROMPT]  ← GPT生成的镜头描述
  [NEGATIVE PROMPT]  ← 一致性保护负面词
  [CONTINUITY ANCHOR] ← 人物+产品+场景一致性锚点
  [CAMERA]           ← 运镜 (模拟手机手持)
  [SEGMENT DURATION]  ← 时长

UGC风格: 轻微镜头抖动、真实手持感、非电影运镜
"""

import json
import logging
import re
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class SeedanceGenerator:
    """Seedance分段生成器 — Reference Image + Prompt + Anchor"""

    def __init__(self, provider=None):
        self.provider = provider

    def generate(
        self,
        master_script: str,
        storyboard_text: str,
        keyframe_index: dict,
        character_consistency: dict,
        product_info: dict,
        output_dir: Path,
    ) -> dict:
        output_dir = Path(output_dir)
        seg_dir = output_dir / "seedance_segments"
        seg_dir.mkdir(parents=True, exist_ok=True)

        keyframes = keyframe_index.get("keyframes", [])
        shot_count = len(keyframes)

        char_anchor = self._build_continuity_anchor(character_consistency)
        prod_anchor = self._build_product_continuity(product_info)
        total_duration = self._extract_duration(master_script)
        shot_duration = round(total_duration / max(shot_count, 1), 1)

        # UGC风格运镜 — 模拟手机手持拍摄
        camera_moves = [
            "Handheld phone, slight natural shake, quick push toward product",
            "Steady phone selfie hold, subtle breathing movement",
            "Gentle wrist rotation around product, natural handheld",
            "Phone in one hand, quick angle switch, casual motion",
            "Slow arm extension toward product, slight unsteadiness",
            "Phone on tripod but with subtle environmental vibration",
            "Handheld walk toward mirror/reflection, natural bounce",
            "Phone lowered then raised, casual reveal motion",
            "Stable selfie hold with warm smile, minimal movement",
        ]

        segments = []
        for i in range(shot_count):
            shot_id = i + 1
            kf = keyframes[i]
            cm = camera_moves[i % len(camera_moves)]
            is_first = (i == 0)
            is_last = (i == shot_count - 1)

            if is_first:
                action = "Product quick reveal, person surprised expression, natural phone selfie"
            elif is_last:
                action = "Person warm smile, product centered, natural CTA, slight head tilt"
            else:
                action = f"Person naturally demonstrating product, genuine interaction, real home setting"

            positive = (
                f"UGC-style smartphone video segment, {shot_duration}s. "
                f"Camera: {cm}. "
                f"Action: {action}. "
                f"Lighting: Natural window light + ring light, real home lighting, NOT studio. "
                f"Scene: Real bedroom or living room, slightly messy natural background. "
                f"Style: TikTok UGC authentic — natural skin texture, slight imperfections, "
                f"real person feel, unstaged, candid. "
                f"Vertical 9:16, 30fps, smartphone camera quality."
            )

            negative = (
                "cinematic lighting, studio setup, perfect composition, "
                "plastic skin, over-smoothed face, AI airbrushed look, "
                "3D render, CG animation, cartoon, illustration, "
                "film look, movie aesthetic, professional camera, "
                "original person face, original logo, original brand, "
                "deformed hands, extra fingers, bad anatomy, "
                "watermark, text overlay, low quality, "
                "hair change, outfit change, makeup change, different person, "
                "product morphing, color change, packaging change, "
                "over-stylized, advertising look, commercial aesthetic"
            )

            segment_content = f"""# Seedance Segment {shot_id:02d}/{shot_count}

[REFERENCE IMAGE]
{Path('keyframes') / kf['file']}

[POSITIVE PROMPT]
{positive}

[NEGATIVE PROMPT]
{negative}

[CONTINUITY ANCHOR]
{char_anchor}
{prod_anchor}

[CAMERA]
{cm}

[SEGMENT DURATION]
{shot_duration}s
"""

            seg_file = seg_dir / f"seedance_segment_{shot_id:02d}.txt"
            seg_file.write_text(segment_content, encoding="utf-8")

            segments.append({
                "shot_id": shot_id,
                "file": str(seg_file),
                "filename": seg_file.name,
                "keyframe": kf["file"],
                "keyframe_path": kf.get("path", ""),
                "duration": shot_duration,
                "camera": cm,
            })

        overview = {
            "generated_at": datetime.now().isoformat(),
            "total_segments": shot_count,
            "total_duration": total_duration,
            "style": "UGC authentic — natural skin, phone selfie, real scene, slight shake",
            "rule": "EVERY segment MUST use its reference keyframe image — NO text-only generation",
            "character_anchor": char_anchor,
            "product_anchor": prod_anchor,
            "segments": [{"shot_id": s["shot_id"], "file": s["filename"], "keyframe": s["keyframe"]} for s in segments],
        }
        overview_path = seg_dir / "seedance_overview.json"
        overview_path.write_text(json.dumps(overview, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(f"Seedance生成: {shot_count} segments (Keyframe-driven) → {seg_dir}")
        return {"segments": segments, "segment_dir": str(seg_dir), "overview_file": str(overview_path)}

    def _build_continuity_anchor(self, consistency: dict) -> str:
        rules = consistency.get("consistency_rules", {})
        a = rules.get("appearance", {})
        i = rules.get("identity", {})
        c = rules.get("clothing", {})
        return (
            f"SAME REAL PERSON: {i.get('name','主角')}, {i.get('age_range','25-30')} {i.get('gender','female')}, "
            f"{a.get('hair_style','long hair')} {a.get('hair_color','black')} hair, "
            f"{a.get('skin_tone','natural')} skin with natural texture, "
            f"wearing {c.get('outfit','casual top')}. "
            f"Natural real-person look, NOT model, NOT AI generated face. "
            f"NO hair change, NO outfit change, NO face morphing, NO plastic skin."
        )

    def _build_product_continuity(self, product: dict) -> str:
        return (
            f"SAME PRODUCT: {product.get('brand','')} {product.get('product_name','')}, "
            f"{product.get('color','')} color, {product.get('packaging','')}. "
            f"NO color change, NO packaging change, NO product morphing."
        )

    def _extract_duration(self, script: str) -> float:
        match = re.search(r'时长[：:]\s*(\d+)', script)
        if match:
            return float(match.group(1))
        match = re.search(r'(\d+)秒', script[:500])
        return float(match.group(1)) if match else 15.0
