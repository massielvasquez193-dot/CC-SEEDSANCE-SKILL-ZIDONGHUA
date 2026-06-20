"""
TikTok AI Video Factory - 即梦/云镜 Prompt生成Agent
支持中文描述，适合即梦和云镜平台
"""

import logging
from datetime import datetime

from prompts.system_prompts import JIMENG_PROMPT, YUNJING_PROMPT

logger = logging.getLogger(__name__)


class JimengGenerator:
    """即梦(Jimeng)视频Prompt生成器"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def generate(
        self,
        storyboard: str,
        product_info: dict,
        character_consistency: str,
    ) -> str:
        """生成即梦Prompt"""
        logger.info("生成即梦视频Prompt...")
        product_name = product_info.get("product_name", "产品")
        brand = product_info.get("brand", "品牌")
        color = product_info.get("color", "")
        packaging = product_info.get("packaging", "")
        features = product_info.get("key_features", [])

        shot_count = storyboard.count("### 镜头")
        if shot_count == 0:
            shot_count = 8

        if self.ai_client:
            return self._ai_generate(storyboard, product_info, character_consistency)
        else:
            return self._template_generate(product_name, brand, color, packaging, features, shot_count, character_consistency)

    def generate_yunjing(
        self,
        storyboard: str,
        product_info: dict,
        character_consistency: str,
    ) -> str:
        """生成云镜Prompt"""
        logger.info("生成云镜视频Prompt...")
        product_name = product_info.get("product_name", "产品")
        brand = product_info.get("brand", "品牌")
        features = product_info.get("key_features", [])

        if self.ai_client:
            return self._ai_generate_yunjing(storyboard, product_info, character_consistency)
        else:
            return self._template_yunjing(product_name, brand, features, character_consistency)

    def _ai_generate(self, storyboard, product_info, char_consistency) -> str:
        """AI驱动生成即梦Prompt"""
        try:
            prompt = JIMENG_PROMPT.format(
                storyboard=storyboard,
                product_info=str(product_info),
                character_consistency=char_consistency,
            )
            return prompt
        except Exception as e:
            logger.error(f"AI即梦生成失败: {e}")
            return self._template_generate("产品", "品牌", "", "", [], 8, char_consistency)

    def _ai_generate_yunjing(self, storyboard, product_info, char_consistency) -> str:
        """AI驱动生成云镜Prompt"""
        try:
            prompt = YUNJING_PROMPT.format(
                storyboard=storyboard,
                product_info=str(product_info),
                character_consistency=char_consistency,
            )
            return prompt
        except Exception as e:
            logger.error(f"AI云镜生成失败: {e}")
            return self._template_yunjing("产品", "品牌", [], char_consistency)

    def _template_generate(self, product_name, brand, color, packaging, features, shot_count, char_consistency) -> str:
        """模板驱动生成即梦中文Prompt"""
        features_str = "、".join(features) if features else "效果显著"

        shots = []
        shot_templates = [
            f"特写镜头：{color}色{packaging}包装的{product_name}产品，光线从侧面打在产品上，背景虚化，产品质感强烈，高端产品摄影风格",
            f"中景镜头：人物自然站立，手持{product_name}，面对镜头微笑，柔和的自然光，温馨的室内环境，9:16竖屏构图",
            f"近景镜头：人物展示{product_name}的使用方法，动作自然流畅，浅景深突出主体，温暖的色调",
            f"特写镜头：{product_name}核心卖点{features_str}的细节展示，微距拍摄，侧逆光勾勒产品轮廓",
            f"全景镜头：人物使用{product_name}的整体场景，自然光线，生活化的环境，真实不做作",
            f"近景镜头：Before/After对比效果，左侧使用前右侧使用后，高饱和度突出变化，视觉冲击力强",
            f"中景镜头：人物面对镜头分享使用感受，表情自然真诚，柔光美化，亲和力强",
            f"特写镜头：{product_name}和人物同框，产品logo清晰，明亮的正面光，干净的背景，适合添加CTA文字",
        ]

        for i in range(shot_count):
            template = shot_templates[i % len(shot_templates)]
            shots.append(f"""### 镜头{i+1}
{template}

负面提示词: 模糊, 变形, 多余的手指, 畸形的手, 糟糕的画质, 水印, 文字, 杂乱的背景, 过曝, 欠曝, 不自然的颜色, 扭曲的脸
""")

        return f"""# 即梦 (Jimeng) 视频生成 Prompt

## 项目信息
- 产品: {brand} {product_name}
- 卖点: {features_str}
- 风格: 超写实电影感 / TikTok竖屏视频
- 分辨率: 1080x1920 (9:16)
- 时长: 约15秒

## 人物一致性要求
{char_consistency}

## 镜头拆解 (共{shot_count}个镜头)

{"".join(shots)}

## 全局参数
- 视频风格: 写实
- 运镜: 平滑稳定
- 色彩: 暖色调，高饱和，电影级调色
- 光线: 柔和的摄影棚灯光，自然光辅助
- 转场: 快切为主
- BGM: 快节奏电子/TikTok热门

---
生成时间: {datetime.now().isoformat()}
"""

    def _template_yunjing(self, product_name, brand, features, char_consistency) -> str:
        """模板驱动生成云镜Prompt"""
        features_str = "、".join(features) if features else "效果显著"

        return f"""# 云镜 (Yunjing) 视频生成 Prompt

## 视频整体描述

这是一段{brand}{product_name}的TikTok产品展示视频，时长约15秒，9:16竖屏格式。

### 视觉风格
超写实电影感画面，暖色调调色，柔和的摄影棚灯光配合自然光，浅景深突出主体，画面干净高级。

### 人物
{char_consistency}

### 产品
{brand} {product_name}，核心卖点：{features_str}。所有镜头中产品包装、颜色、品牌元素保持一致。

### 镜头序列

**镜头1 (0-2秒) — Hook开场**
产品特写，快速推镜，{product_name}在柔光下闪耀，深色背景突出产品质感，字幕弹出"🔥 发现宝藏"。

**镜头2 (2-5秒) — 问题引入**
人物中景，手持{product_name}，面对镜头分享痛点，自然光线，真实场景。

**镜头3 (5-8秒) — 产品展示**
产品近景特写，展示核心卖点{features_str}，侧逆光勾勒轮廓，微距细节。

**镜头4 (8-11秒) — 效果对比**
分屏Before/After，高饱和度，视觉冲击力强，快速切换。

**镜头5 (11-15秒) — CTA引导**
人物微笑面对镜头，产品居中，白色干净背景，字幕"🛒 限时优惠"。

### 全局参数
- 风格: 写实
- 色调: 暖色
- 节奏: 快节奏卡点
- 转场: 硬切

---
生成时间: {datetime.now().isoformat()}
"""
