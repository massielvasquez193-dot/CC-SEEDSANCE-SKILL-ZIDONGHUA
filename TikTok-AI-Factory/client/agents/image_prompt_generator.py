"""
TikTok AI Video Factory - 图片Prompt生成Agent
生成人物/产品一致的Keyframe图片Prompt
"""

import logging
from datetime import datetime

from prompts.system_prompts import IMAGE_PROMPT_PROMPT

logger = logging.getLogger(__name__)


class ImagePromptGenerator:
    """图片生成Prompt生成器"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def generate(
        self,
        storyboard: str,
        character_consistency: str,
        product_consistency: str,
        keyframe_count: int = 6,
    ) -> str:
        """生成图片Prompt"""
        logger.info(f"生成{keyframe_count}个Keyframe图片Prompt...")

        if self.ai_client:
            return self._ai_generate(
                storyboard, character_consistency, product_consistency, keyframe_count,
            )
        else:
            return self._template_generate(
                storyboard, character_consistency, product_consistency, keyframe_count,
            )

    def _ai_generate(self, storyboard, char_consistency, prod_consistency, kf_count) -> str:
        """AI驱动生成图片Prompt"""
        try:
            prompt = IMAGE_PROMPT_PROMPT.format(
                storyboard=storyboard,
                character_consistency=char_consistency,
                product_consistency=prod_consistency,
                keyframe_count=kf_count,
            )
            # response = self.ai_client.chat(prompt)
            # return response
            return self._template_generate(storyboard, char_consistency, prod_consistency, kf_count)
        except Exception as e:
            logger.error(f"AI图片Prompt生成失败: {e}")
            return self._template_generate(storyboard, char_consistency, prod_consistency, kf_count)

    def _template_generate(self, storyboard, char_consistency, prod_consistency, kf_count) -> str:
        """模板驱动生成图片Prompt"""
        prompts_md = []

        shot_descriptions = [
            ("产品特写", "产品置于画面中央，光线从左侧45度打来，深色背景突出产品质感，微距拍摄展现细节"),
            ("人物引入", "人物自然站立，手持产品，柔和的环形光打在面部，浅景深虚化背景，竖屏中景构图"),
            ("使用场景", "人物正在使用产品，自然光线从窗户照入，温馨的生活场景，动态抓拍感"),
            ("效果对比", "分屏展示使用前后对比，左侧Before右侧After，高饱和度突出变化效果"),
            ("产品细节", "产品关键部位微距特写，侧逆光勾勒轮廓，水滴/光斑点缀增加质感"),
            ("CTA结尾", "人物微笑举产品面对镜头，产品logo清晰可见，明亮的正面光，干净的白色背景"),
        ]

        for i in range(kf_count):
            desc = shot_descriptions[i % len(shot_descriptions)]
            title = desc[0]
            scene = desc[1]

            mj_prompt = (
                f"Hyper-realistic product photography, {title}, "
                f"vertical 9:16 aspect ratio for TikTok, cinematic lighting, "
                f"4K resolution, professional color grading, shallow depth of field --ar 9:16 --style raw --v 6.1"
            )

            dalle_prompt = (
                f"A hyper-realistic vertical 9:16 photo of {title}. {scene}. "
                f"Professional product photography, cinematic lighting, high detail, 4K quality. "
                f"TikTok style vertical video frame."
            )

            prompts_md.append(f"""### Keyframe {i+1:02d}
**对应镜头**: 镜头{i+1}
**场景**: {title}

**Midjourney Prompt**:
```
{mj_prompt}
```

**DALL-E Prompt**:
```
{dalle_prompt}
```

**Stable Diffusion Prompt**:
```
masterpiece, best quality, photorealistic, {title.lower()}, vertical composition, product showcase, cinematic lighting, sharp focus, 8k, highly detailed
Negative: blurry, low quality, distortion, bad anatomy, watermark, text, logo, deformed
```

---
""")

        return f"""# 图片生成Prompt

## 人物一致性描述 (全局Prefix)
{char_consistency}

## 产品一致性描述 (全局Prefix)
{prod_consistency}

## Keyframe Prompts (共{kf_count}个)

{"".join(prompts_md)}

---
生成时间: {datetime.now().isoformat()}
"""
