"""
TikTok AI Video Factory - Gemini Provider
支持: Gemini 2.0 Flash (text/vision), Imagen (image)
"""

import logging
from pathlib import Path
from typing import Optional

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    provider_name = "gemini"
    supports_text = True
    supports_image = True
    supports_vision = True
    supports_video = False

    def _default_model(self) -> str:
        return "gemini-2.0-flash"

    def _create_client(self):
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        return genai

    # ================================================================
    # 文本生成
    # ================================================================
    def _generate_text_impl(self, prompt, system_prompt, temperature, max_tokens, **kwargs) -> str:
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Gemini 使用 system_instruction
        model_kwargs = {"model_name": self.model}
        if system_prompt:
            model_kwargs["system_instruction"] = system_prompt

        model = self.client.GenerativeModel(**model_kwargs)
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )
        return response.text

    # ================================================================
    # 视觉分析
    # ================================================================
    def _analyze_image_impl(self, image_path, prompt, **kwargs) -> str:
        from google.generativeai.types import Part

        image_part = self._load_image_gemini(image_path)
        model = self.client.GenerativeModel(self.model)
        response = model.generate_content([prompt, image_part])
        return response.text

    # ================================================================
    # 图片生成 (Imagen)
    # ================================================================
    def _generate_image_impl(self, prompt, negative_prompt, width, height, num_images, **kwargs) -> list[dict]:
        # Gemini Imagen 通过专门的模型
        imagen_model = self.client.GenerativeModel("imagen-3.0-generate-001")

        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt}. Avoid: {negative_prompt}"

        results = []
        for _ in range(num_images):
            response = imagen_model.generate_content(
                full_prompt,
                generation_config={
                    "response_modalities": ["image"],
                    "image_config": {
                        "aspect_ratio": "9:16" if height > width else "1:1" if height == width else "16:9",
                    },
                },
            )
            # 提取图片数据
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    results.append({
                        "url": None,
                        "base64_data": part.inline_data.data,
                        "mime_type": part.inline_data.mime_type,
                        "width": width,
                        "height": height,
                        "format": part.inline_data.mime_type.split("/")[-1],
                    })

        return results

    # ================================================================
    # 辅助
    # ================================================================
    def _load_image_gemini(self, image_path: str):
        """加载图片为Gemini Part"""
        from google.generativeai.types import Part

        if image_path.startswith(("http://", "https://")):
            import requests
            resp = requests.get(image_path, timeout=30)
            return Part.from_data(data=resp.content, mime_type=resp.headers.get("content-type", "image/jpeg"))

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")

        suffix = path.suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp",
        }
        mime_type = mime_map.get(suffix, "image/jpeg")

        with open(path, "rb") as f:
            return Part.from_data(data=f.read(), mime_type=mime_type)
