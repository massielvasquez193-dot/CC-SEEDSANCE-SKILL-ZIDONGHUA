"""
TikTok AI Video Factory - 爆款视频分析Agent
实现Video Replication Skill：视频摘要、拆解、镜头分析、替换逻辑、节奏分析
"""

import json
import logging
from pathlib import Path

from prompts.system_prompts import VIRAL_ANALYZER_PROMPT

logger = logging.getLogger(__name__)


class ViralAnalyzer:
    """爆款视频复制分析器"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def replicate(
        self,
        reference_video: Path,
        product_info: dict,
        character_info: dict,
    ) -> dict:
        """
        视频复制分析
        输出: 视频摘要、拆解、镜头分析、替换逻辑、节奏分析
        """
        logger.info(f"分析视频复制策略: {reference_video.name}")

        result = {
            "reference_video": str(reference_video),
            "video_summary": "",
            "shot_breakdown": [],
            "replacement_logic": {},
            "pacing_analysis": {},
        }

        if self.ai_client:
            result = self._ai_replicate(reference_video, product_info, character_info)
        else:
            result = self._template_replicate(reference_video, product_info, character_info)

        return result

    def _ai_replicate(self, video: Path, product: dict, character: dict) -> dict:
        """AI驱动的视频复制分析"""
        try:
            prompt = f"""分析这个爆款视频并生成复制策略：

产品: {json.dumps(product, ensure_ascii=False)}
人物: {json.dumps(character, ensure_ascii=False)}

返回JSON:
{{
    "video_summary": "视频内容摘要",
    "shot_breakdown": [
        {{"shot_id": 1, "duration": 2.5, "scene_type": "特写", "content": "内容描述", "purpose": "目的"}}
    ],
    "replacement_logic": {{
        "product_replacement": "产品替换策略",
        "brand_replacement": "品牌替换策略",
        "character_replacement": "人物替换策略",
        "script_adaptation": "脚本适配策略"
    }},
    "pacing_analysis": {{
        "hook_pattern": "Hook模式",
        "climax_points": [1, 3, 5],
        "rhythm_type": "节奏类型",
        "retention_strategy": "留存策略"
    }}
}}"""
            # response = self.ai_client.chat(prompt)
            # return json.loads(response)
            return self._template_replicate(video, product, character)
        except Exception as e:
            logger.error(f"AI复制分析失败: {e}")
            return self._template_replicate(video, product, character)

    def _template_replicate(self, video: Path, product: dict, character: dict) -> dict:
        """模板驱动的复制分析"""
        product_name = product.get("product_name", "产品")
        brand = product.get("brand", "品牌")

        return {
            "reference_video": str(video),
            "video_summary": f"这是一个{product_name}的展示视频，通过展示产品使用效果吸引用户。",
            "shot_breakdown": [
                {"shot_id": 1, "duration": 2.0, "scene_type": "特写", "content": f"{product_name}产品特写", "purpose": "Hook吸引注意"},
                {"shot_id": 2, "duration": 3.0, "scene_type": "中景", "content": "人物使用产品", "purpose": "展示使用场景"},
                {"shot_id": 3, "duration": 3.0, "scene_type": "近景", "content": "产品效果展示", "purpose": "建立信任"},
                {"shot_id": 4, "duration": 4.0, "scene_type": "特写", "content": "产品核心卖点", "purpose": "强化记忆"},
                {"shot_id": 5, "duration": 3.0, "scene_type": "中景", "content": "CTA引导", "purpose": "转化"},
            ],
            "replacement_logic": {
                "product_replacement": f"将原产品替换为{product_name}，保持产品展示角度和光线一致",
                "brand_replacement": f"所有品牌元素替换为{brand}",
                "character_replacement": "保持原视频人物动作和表情，替换为新人物的外观特征",
                "script_adaptation": f"口播文案中的产品名和品牌名替换为{product_name}和{brand}",
            },
            "pacing_analysis": {
                "hook_pattern": "前3秒产品特写+问题引导",
                "climax_points": [0, 5, 12],
                "rhythm_type": "快-慢-快",
                "retention_strategy": "每3秒切换画面保持新鲜感",
            },
        }
