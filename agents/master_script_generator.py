"""
TikTok AI Video Factory - Master Script Generator (GPT-5.5)
全视频唯一主脚本 — GPT生成，真人UGC口播风格

目标: TikTok真人UGC广告标准
禁止: AI播音腔、完美文案、广告感
"""

import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MasterScriptGenerator:
    """GPT-5.5 主脚本生成器"""

    def __init__(self, provider=None):
        self.provider = provider

    def generate(self, product_info: dict, character_info: dict, video_analysis: dict, duration: float = 15.0) -> str:
        product_name = product_info.get("product_name", "产品")
        brand = product_info.get("brand", "品牌")
        category = product_info.get("category", "好物")
        color = product_info.get("color", "")
        features = product_info.get("key_features", [])
        features_str = "、".join(features) if features else "效果好"

        char_name = character_info.get("name", "我")
        char_vibe = character_info.get("vibe", "自然亲切")
        char_age = character_info.get("age_range", "25-30")

        if self.provider and hasattr(self.provider, 'supports_text') and self.provider.supports_text:
            return self._gpt_generate(product_info, character_info, video_analysis, duration)
        else:
            return self._template_generate(product_name, brand, category, color, features_str, char_name, char_vibe, char_age, duration)

    def _gpt_generate(self, product, character, video_analysis, duration):
        system_prompt = """你是TikTok爆款视频脚本写手。你写的是真人UGC口播脚本，不是AI文案。

硬性要求:
- 口播必须是真人说话的方式: 有停顿、有呼吸、有口语词(天呐/你看/说真的/绝了)
- 禁止播音腔、禁止完美句子、禁止书面语
- Hook前3秒必须用感叹词开头(天呐!/姐妹们!/救命!/你看这个!)
- 产品必须在第1秒就出现
- CTA必须由人物自然说出，不是推销
- 每一句都要像朋友在跟你分享，不像广告

输出格式:
# MASTER SCRIPT
## HOOK (0-3s)
口播: ...
画面: ...
情绪: ...

## PROBLEM (3-6s)
口播: ...
画面: ...
情绪: ...

## SOLUTION (6-10s)
口播: ...
画面: ...
情绪: ...

## SOCIAL PROOF (10-13s)
口播: ...
画面: ...
情绪: ...

## CTA (13-15s)
口播: ...
画面: ...
情绪: ..."""

        user_prompt = f"""为以下产品写一个{duration:.0f}秒TikTok真人UGC口播脚本:

产品: {product.get('brand','')} {product.get('product_name','')}
品类: {product.get('category','')}
颜色: {product.get('color','')}
卖点: {product.get('key_features',[])}
人物: {character.get('name','')}, {character.get('age_range','')}, {character.get('vibe','')}
目标: TikTok真人UGC广告标准 — 自然皮肤、真实场景、轻微镜头抖动、真实口播节奏

直接输出完整脚本，不做解释。"""

        try:
            return self.provider.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.9,
                max_tokens=2000,
            )
        except Exception as e:
            logger.error(f"GPT脚本生成失败: {e}")
            return self._template_generate(
                product.get('product_name','产品'), product.get('brand','品牌'),
                product.get('category','好物'), product.get('color',''),
                "、".join(product.get('key_features',['效果好'])),
                character.get('name','我'), character.get('vibe','自然'),
                character.get('age_range','25-30'), duration
            )

    def _template_generate(self, product_name, brand, category, color, features_str, char_name, char_vibe, char_age, duration):
        return f"""# MASTER SCRIPT — {brand} {product_name}

## HOOK (0-3s)
口播: "天呐！这个{brand}的{product_name}也太好用了吧！"
画面: {char_name}手机自拍视角，{product_name}快速靠近镜头，{color}色外观在自然光下展示
情绪: 惊喜、真实 — 强度 8/10

## PROBLEM (3-6s)
口播: "你是不是也遇到过...之前试了好多{category}产品都不行，说真的我都快放弃了"
画面: {char_name}面对镜头自然说话，轻微手势，真实室内背景
情绪: 共鸣、真实 — 强度 5/10

## SOLUTION (6-10s)
口播: "直到我发现这个！你看{features_str}，而且它这个设计真的很贴心，用起来完全不一样"
画面: {char_name}手持{product_name}展示使用，产品细节，自然光线
情绪: 真诚推荐 — 强度 7/10

## SOCIAL PROOF (10-13s)
口播: "我已经用了好几天了，效果真的明显，我朋友都在问我在用什么"
画面: Before/After效果对比或使用过程展示
情绪: 自信分享 — 强度 6/10

## CTA (13-{duration:.0f}s)
口播: "赶紧去试试吧！链接在我主页，现在还有限时优惠，错过真的要等！"
画面: {char_name}微笑+{product_name}居中+链接指向
情绪: 温暖紧迫 — 强度 9/10

---
CHARACTER: {char_name} ({char_age}, {char_vibe}) — 全视频一致
PRODUCT: {brand} {product_name} ({color}色) — 全视频一致
TARGET: TikTok真人UGC广告标准
"""
