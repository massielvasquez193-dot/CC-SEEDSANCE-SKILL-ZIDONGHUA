"""
TikTok UGC Video Factory — Master Script Generator (Phase 2)
全视频唯一主脚本 — GPT生成，真人UGC口播风格

结构固定: HOOK → PROBLEM → AGITATE → SOLUTION → RESULT → CTA
禁止: 镜头独立编故事、AI播音腔、完美文案
"""

import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MasterScriptGenerator:
    """Phase 2 主脚本生成器 — 固定6段式UGC结构"""

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

        if self.provider and hasattr(self.provider, 'supports_text') and self.provider.supports_text:
            return self._gpt_generate(product_info, character_info, video_analysis, duration)
        else:
            return self._template_generate(product_name, brand, category, color, features_str, char_name, char_vibe, duration)

    def _gpt_generate(self, product, character, video_analysis, duration):
        system = """你是TikTok真人UGC口播写手。不是AI。你写的每个字都像真人朋友在说话。

结构固定6段:
HOOK(0-3s) → PROBLEM(3-6s) → AGITATE(6-9s) → SOLUTION(9-12s) → RESULT(12-14s) → CTA(14-15s)

每段必须包含: 口播文案 + 画面描述 + 情绪标注

硬性要求:
- 口语化: "Guys..." "天呐" "你看" "说真的" "绝了"
- 有停顿: 用 [pause 0.5] 标记
- 有情绪: [Excited] [Concerned] [Amazed]
- Hook立即展示产品
- CTA自然不推销
- 禁止完美句子
- 禁止播音腔"""

        user = f"""为这个产品写{duration:.0f}秒TikTok真人UGC脚本:

产品: {product.get('brand','')} {product.get('product_name','')} ({product.get('color','')})
品类: {product.get('category','')}
卖点: {product.get('key_features',[])}
人物: {character.get('name','')}, {character.get('vibe','')}

结构: HOOK → PROBLEM → AGITATE → SOLUTION → RESULT → CTA

直接输出完整脚本，不要解释。"""

        try:
            return self.provider.generate_text(prompt=user, system_prompt=system, temperature=0.9, max_tokens=2000)
        except Exception as e:
            logger.error(f"GPT脚本失败: {e}")
            return self._template_generate(
                product.get('product_name','产品'), product.get('brand','品牌'),
                product.get('category','好物'), product.get('color',''),
                "、".join(product.get('key_features',['效果好'])),
                character.get('name','我'), character.get('vibe','自然'), duration
            )

    def _template_generate(self, name, brand, category, color, features, char_name, vibe, duration):
        return f"""# MASTER SCRIPT — {brand} {name}
# Structure: HOOK → PROBLEM → AGITATE → SOLUTION → RESULT → CTA
# Target: TikTok真人UGC广告标准

## HOOK (0-3s)
[Excited] 口播: "天呐！{brand}这个{name}也太好用了吧！"
画面: {char_name}手机自拍，{name}快速推近镜头，{color}色外观在自然光下亮相
情绪: surprised_excited | 手势: hold_product_close | 运镜: selfie_handheld_shaky

## PROBLEM (3-6s)
[Concerned] 口播: "你是不是也遇到过...之前试了好多{category}都不行。[pause 0.3] 说真的，我都快放弃了。"
画面: {char_name}面对镜头，自然室内背景，轻微手势，真实表情
情绪: concerned_relatable | 手势: point_at_face | 运镜: selfie_closeup_stable

## AGITATE (6-9s)
[Frustrated] 口播: "每次都是效果不明显，钱花了一大堆。[pause 0.4] 真的太让人崩溃了。"
画面: {char_name}摊手、摇头，表达挫败感，真实不做作
情绪: frustrated_empathetic | 手势: open_hands_shrug | 运镜: selfie_slight_shake

## SOLUTION (9-12s)
[Excited Discovery] 口播: "直到我发现这个！[pause 0.3] 你看{features}。[pause 0.2] 而且它的设计真的很贴心。"
画面: {char_name}手持{name}展示使用，自然光线，产品细节
情绪: excited_discovery | 手势: hold_product_demonstrate | 运镜: handheld_product_focus

## RESULT (12-14s)
[Amazed] 口播: "我已经用了好几天了。[pause 0.3] Look! 效果真的明显！朋友都在问。"
画面: Before/After效果对比，{char_name}自信展示
情绪: amazed_satisfied | 手势: point_at_result | 运镜: selfie_stable_proud

## CTA (14-{duration:.0f}s)
[Warm Urgent] 口播: "赶紧去试试吧！[pause 0.4] 链接在我主页，现在还有限时优惠。[pause 0.3] 错过真的要等！"
画面: {char_name}温暖微笑，{name}居中，链接指向区域
情绪: warm_urgent | 手势: point_to_link | 运镜: selfie_smile_stable

---
CHARACTER: {char_name} ({vibe}) — 全视频同一人
PRODUCT: {brand} {name} ({color}色) — 全视频同一产品
CAMERA: 始终手机自拍 — 轻微自然晃动 — 禁止三脚架
SKIN: 自然肤质 — 禁止美颜滤镜
SCENE: 真实家庭场景 — 禁止影棚
"""
