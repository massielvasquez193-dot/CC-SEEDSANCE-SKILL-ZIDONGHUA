"""
TikTok AI Video Factory - Claude Provider
支持: Claude Opus/Sonnet (text/vision), 不支持图像/视频生成
"""

import base64
import logging
from pathlib import Path
from typing import Optional

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseProvider):
    provider_name = "claude"
    supports_text = True
    supports_image = False
    supports_vision = True
    supports_video = False

    def _default_model(self) -> str:
        return "claude-sonnet-4-6"

    def _create_client(self):
        if not self.api_key:
            raise ValueError("API key is required for Claude provider")
        from anthropic import Anthropic
        return Anthropic(api_key=self.api_key)

    # ================================================================
    # 文本生成
    # ================================================================
    def _generate_text_impl(self, prompt, system_prompt, temperature, max_tokens, **kwargs) -> str:
        kwargs.pop("system_prompt", None)  # Claude用system参数

        messages = []
        if system_prompt:
            # Claude system prompt 通过顶层参数传递
            pass
        messages.append({"role": "user", "content": prompt})

        create_kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            create_kwargs["system"] = system_prompt

        response = self.client.messages.create(**create_kwargs)
        return response.content[0].text

    # ================================================================
    # 视觉分析
    # ================================================================
    def _analyze_image_impl(self, image_path, prompt, **kwargs) -> str:
        image_data = self._load_image(image_path)

        content = [
            {"type": "image", "source": image_data},
            {"type": "text", "text": prompt},
        ]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=[{"role": "user", "content": content}],
        )
        return response.content[0].text

    def generate_text_with_image(
        self,
        prompt: str,
        image_path: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> str:
        """
        Claude特有: 文本+图片混合输入
        """
        image_data = self._load_image(image_path)
        content = [
            {"type": "image", "source": image_data},
            {"type": "text", "text": prompt},
        ]

        create_kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": content}],
        }
        if system_prompt:
            create_kwargs["system"] = system_prompt

        response = self.client.messages.create(**create_kwargs)
        return response.content[0].text

    # ================================================================
    # 辅助
    # ================================================================
    def _load_image(self, image_path: str) -> dict:
        """加载图片为Claude格式"""
        if image_path.startswith(("http://", "https://")):
            import requests
            resp = requests.get(image_path, timeout=30)
            data = base64.b64encode(resp.content).decode("utf-8")
            media_type = resp.headers.get("content-type", "image/jpeg")
        else:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"图片不存在: {image_path}")
            suffix = path.suffix.lower()
            mime_map = {
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".webp": "image/webp",
                ".gif": "image/gif",
            }
            media_type = mime_map.get(suffix, "image/jpeg")
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")

        return {
            "type": "base64",
            "media_type": media_type,
            "data": data,
        }
