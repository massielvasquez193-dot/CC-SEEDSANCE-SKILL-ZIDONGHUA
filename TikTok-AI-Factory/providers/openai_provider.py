"""
TikTok AI Video Factory - OpenAI Provider
支持: GPT-4o (text/vision), DALL-E 3 (image)
"""

import base64
import logging
from pathlib import Path
from typing import Optional

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    provider_name = "openai"
    supports_text = True
    supports_image = True
    supports_vision = True
    supports_video = False

    def _default_model(self) -> str:
        return "gpt-4.1"  # GPT-5.5 equivalent — latest GPT model for production

    def _create_client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.api_key)

    # ================================================================
    # 文本生成
    # ================================================================
    def _generate_text_impl(self, prompt, system_prompt, temperature, max_tokens, **kwargs) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content

    # ================================================================
    # 视觉分析
    # ================================================================
    def _analyze_image_impl(self, image_path, prompt, **kwargs) -> str:
        image_url = self._encode_image(image_path)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        return response.choices[0].message.content

    # ================================================================
    # 图片生成 (DALL-E 3)
    # ================================================================
    def _generate_image_impl(self, prompt, negative_prompt, width, height, num_images, **kwargs) -> list[dict]:
        # DALL-E 3 不支持 negative prompt 和自定义尺寸，做最佳适配
        size = self._map_dalle_size(width, height)
        quality = kwargs.get("quality", "hd")
        style = kwargs.get("style", "vivid")

        # 将 negative prompt 注入到 prompt 中
        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt}. AVOID: {negative_prompt}"

        results = []
        for _ in range(num_images):
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=full_prompt[:4000],
                size=size,
                quality=quality,
                style=style,
                n=1,
            )
            results.append({
                "url": response.data[0].url,
                "revised_prompt": getattr(response.data[0], "revised_prompt", ""),
                "width": width,
                "height": height,
                "format": "png",
            })

        return results

    def _map_dalle_size(self, width: int, height: int) -> str:
        """DALL-E 3 支持的尺寸映射"""
        if width == height:
            return "1024x1024"
        elif height > width:
            return "1024x1792"  # 竖屏
        else:
            return "1792x1024"  # 横屏

    # ================================================================
    # 辅助
    # ================================================================
    def _encode_image(self, image_path: str) -> str:
        """将本地图片编码为 base64 data URL"""
        if image_path.startswith(("http://", "https://", "data:")):
            return image_path

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")

        suffix = path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp",
            ".gif": "image/gif",
        }
        mime = mime_types.get(suffix, "image/jpeg")

        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")

        return f"data:{mime};base64,{data}"
