"""
TikTok AI Video Factory - VEO3 Prompt生成Agent
完整视频Prompt，支持8秒/15秒/30秒/60秒
"""

import logging
from datetime import datetime

from prompts.system_prompts import VEO3_PROMPT

logger = logging.getLogger(__name__)


class VEO3Generator:
    """Google VEO3视频Prompt生成器"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def generate(
        self,
        storyboard: str,
        product_info: dict,
        character_consistency: str,
        duration: int = 15,
    ) -> str:
        """生成VEO3 Prompt"""
        logger.info(f"生成VEO3视频Prompt ({duration}秒)...")
        product_name = product_info.get("product_name", "产品")
        brand = product_info.get("brand", "品牌")
        features = product_info.get("key_features", ["效果显著"])

        if self.ai_client:
            return self._ai_generate(storyboard, product_info, character_consistency, duration)
        else:
            return self._template_generate(product_name, brand, features, character_consistency, duration)

    def _ai_generate(self, storyboard, product_info, char_consistency, duration) -> str:
        """AI驱动生成VEO3 Prompt"""
        try:
            prompt = VEO3_PROMPT.format(
                storyboard=storyboard,
                product_info=str(product_info),
                character_consistency=char_consistency,
                duration=duration,
            )
            return prompt
        except Exception as e:
            logger.error(f"AI VEO3生成失败: {e}")
            return self._template_generate("产品", "品牌", [], char_consistency, duration)

    def _template_generate(self, product_name, brand, features, char_consistency, duration) -> str:
        """模板驱动生成VEO3 Prompt"""
        features_str = ", ".join(features) if features else "amazing results"

        # 根据时长调整场景密度
        if duration <= 8:
            scenes = 3
            detail = "compact"
        elif duration <= 15:
            scenes = 5
            detail = "moderate"
        elif duration <= 30:
            scenes = 8
            detail = "detailed"
        else:
            scenes = 12
            detail = "comprehensive"

        return f"""# VEO3 Video Generation Prompt

## Video Overview
- Duration: {duration} seconds
- Format: Vertical 9:16 (1080x1920)
- Style: Hyper-realistic cinematic social media video
- FPS: 30
- Language: Chinese voiceover with Chinese subtitles

## Full Video Description ({detail} detail level, {scenes} key scenes)

A {duration}-second TikTok-style product showcase video for **{brand} {product_name}**.

### Opening Hook (0-3s)
EXTREME CLOSE-UP of the {product_name} product. Fast push-in camera movement. The product's packaging gleams under soft studio lighting. Vibrant colors pop against a clean, minimal background. Text overlay appears with energetic motion graphics: "🔥 宝藏{product_name}". The shot establishes premium quality instantly.

### Problem Introduction (3-8s)
MEDIUM SHOT of a person (consistent character throughout) speaking directly to camera. Warm, natural lighting from a window. The person expresses a relatable pain point with genuine emotion. Hand gestures emphasize the frustration. Quick cut to a brief B-roll showing the problem scenario. Text overlay: "❌ 试过N种方法？"

### Product Reveal (8-15s)
CLOSE-UP of the person holding {product_name}. Smooth handheld camera movement follows the product as it's presented. The person demonstrates key features: **{features_str}**. Product remains sharp in focus while background is softly blurred. Lighting shifts to brighter, more polished look. Text overlay: "✨ {features_str}".

### Effect Demonstration ({15}-{duration - 5}s)
Split-screen or rapid sequence showing before/after transformation. High saturation, crisp details. The {product_name} visibly transforms the scene. Quick cuts between different angles maintain energy. The person's expression shifts from problem-state to delighted satisfaction. B-roll of product texture, application, and result.

### CTA Finale ({duration - 5}-{duration}s)
The person smiles warmly at camera, holding {product_name} prominently in frame. Clean white/light background. Product logo clearly visible. Animated text slides in: "🛒 限时优惠". The person gestures toward the screen/camera. Final freeze-frame on product + person with all key information displayed. Call to action: "主页链接".

## Visual Style Guidelines
- Color palette: Warm tones with teal/orange color grading
- Lighting: Soft key light + rim light for depth
- Depth of field: Shallow for product shots, moderate for person shots
- Motion: Energetic but smooth, no shaky footage
- Transitions: Mostly hard cuts with occasional whip pans for energy
- Text overlays: Bold, modern sans-serif font, pop-in animations

## Audio Direction
- Background music: Upbeat, trending TikTok electronic/pop
- Voiceover: Enthusiastic, confident female/male voice in Chinese
- Sound effects: Subtle whoosh for transitions, click for text pop-ins
- Audio mixing: Voiceover prominent, music at 30% during speech, 80% during B-roll

## Character Consistency
{char_consistency}

## Product Consistency
Product: {brand} {product_name}
Features: {features_str}
All shots must show the same product with consistent packaging, color, and branding.

---
Generated: {datetime.now().isoformat()}
Duration variant: {duration}s ({detail} detail)
"""
