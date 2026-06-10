"""
TikTok AI Video Factory - 脚本生成Agent
保留爆款结构，替换产品/品牌/人物，提高转化率
"""

import logging
from pathlib import Path

from prompts.system_prompts import SCRIPT_GENERATOR_PROMPT

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """视频脚本生成器"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def generate(
        self,
        viral_analysis: dict,
        product_info: dict,
        character_info: dict,
        replication: dict = None,
    ) -> str:
        """生成视频脚本"""
        logger.info("生成视频脚本...")

        product_name = product_info.get("product_name", "产品")
        product_brand = product_info.get("brand", "品牌")
        character_name = character_info.get("name", "人物")

        duration = viral_analysis.get("metadata", {}).get("duration", 15)
        pacing = viral_analysis.get("pacing_estimate", "medium")

        cta_start = max(3, duration - 5)

        if self.ai_client:
            return self._ai_generate(
                viral_analysis, product_info, character_info,
                product_name, product_brand, character_name,
                duration, pacing, cta_start,
            )
        else:
            return self._template_generate(
                viral_analysis, product_info, character_info,
                product_name, product_brand, character_name,
                duration, pacing, cta_start,
            )

    def _ai_generate(self, viral_analysis, product_info, character_info,
                     product_name, product_brand, character_name,
                     duration, pacing, cta_start) -> str:
        """AI驱动生成脚本"""
        try:
            prompt = SCRIPT_GENERATOR_PROMPT.format(
                viral_analysis=str(viral_analysis),
                product_info=str(product_info),
                character_info=str(character_info),
                product_name=product_name,
                product_brand=product_brand,
                character_name=character_name,
                duration=int(duration),
                cta_start=int(cta_start),
                pacing=pacing,
                peak_moments="3秒, 8秒, 12秒",
                bgm_suggestion="快节奏电子音乐/TikTok热门BGM",
            )
            # response = self.ai_client.chat(prompt)
            # return response
            return self._template_generate(
                viral_analysis, product_info, character_info,
                product_name, product_brand, character_name,
                duration, pacing, cta_start,
            )
        except Exception as e:
            logger.error(f"AI脚本生成失败: {e}")
            return self._template_generate(
                viral_analysis, product_info, character_info,
                product_name, product_brand, character_name,
                duration, pacing, cta_start,
            )

    def _template_generate(self, viral_analysis, product_info, character_info,
                           product_name, product_brand, character_name,
                           duration, pacing, cta_start) -> str:
        """模板驱动生成脚本"""
        features = product_info.get("key_features", ["高品质", "性价比高", "效果显著"])
        features_str = "、".join(features) if features else "超值好物"
        color = product_info.get("color", "")
        packaging = product_info.get("packaging", "")
        age = character_info.get("age_range", "")
        vibe = character_info.get("vibe", "")

        return f"""# 视频脚本

## 基本信息
- 产品：{product_name}
- 品牌：{product_brand}
- 人物：{character_name} ({age}, {vibe})
- 时长：{int(duration)}秒

## Hook (0-3秒)
[口播文案]
"天呐！这个{product_name}也太好用了吧！"

[画面描述]
产品特写镜头，快速展示{product_name}的{color}外观和{packaging}包装

[字幕]
🔥 发现了一个宝藏{product_name}！

## 问题展示 (3-8秒)
[口播文案]
"你是不是也遇到过...（痛点描述）？之前试过好多产品都没用，直到我发现了{product_brand}的这个{product_name}！"

[画面描述]
人物({character_name})面对镜头展示问题场景，表情自然真实

[字幕]
❌ 试过N种方法？都不管用？
✅ 终于找到解决方案！

## 产品引入 (8-15秒)
[口播文案]
"你看这个{features_str}，而且是{color}色的{packaging}包装，颜值也太高了吧！"

[画面描述]
人物手持{product_name}，展示产品细节和使用方法，镜头缓缓推近

[字幕]
✨ {features_str}
💎 {product_brand} {product_name}

## 效果展示 (15-{int(cta_start)}秒)
[口播文案]
"用了之后效果真的太惊艳了！你看这个...（展示效果）"

[画面描述]
产品使用前后对比/B&A效果展示，快速切换突出变化

[字幕]
📸 使用效果惊艳！
💯 真实测评

## CTA ({int(cta_start)}-{int(duration)}秒)
[口播文案]
"赶紧去试试吧！链接我放在主页了，现在下单还有限时优惠！"

[画面描述]
人物微笑举着产品+产品在画面中央+价格/优惠信息弹出

[字幕]
🛒 限时优惠·错过等一年
👇 主页链接

## 节奏说明
- 整体节奏: {pacing}
- 高潮点: 3秒(Hook), 8秒(解决方案), 12秒(效果炸裂)
- BGM建议: TikTok热榜电子音乐 / 节奏感强的卡点BGM

## 转化优化
- 卖点强化: 在Hook阶段直接用惊人效果抓住注意力，中间用具体数字和对比强化说服力
- 信任背书: 真实使用场景展示，Before/After对比，产品细节实拍
- 紧迫感: 限时优惠+限量感，引导用户立即行动
"""
