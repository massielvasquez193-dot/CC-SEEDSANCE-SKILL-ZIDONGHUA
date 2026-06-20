"""
TikTok AI Video Factory - DeepSeek Provider
支持: DeepSeek-Chat/V3 (text only, OpenAI兼容接口)
"""

import logging
from typing import Optional

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseProvider):
    provider_name = "deepseek"
    supports_text = True
    supports_image = False
    supports_vision = False
    supports_video = False

    def _default_model(self) -> str:
        return "deepseek-chat"

    def _create_client(self):
        from openai import OpenAI
        return OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1",
        )

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
    # DeepSeek特长: 推理模式
    # ================================================================
    def generate_with_reasoning(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 4096,
        **kwargs,
    ) -> dict:
        """
        DeepSeek-R1 推理模式
        返回思考过程 + 最终答案
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages,
            max_tokens=max_tokens,
            **kwargs,
        )

        choice = response.choices[0].message
        return {
            "reasoning": getattr(choice, "reasoning_content", ""),
            "answer": choice.content,
        }

    # ================================================================
    # JSON结构化输出
    # ================================================================
    def generate_json(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs,
    ) -> dict:
        """
        生成JSON结构化输出
        DeepSeek在JSON格式输出上表现优秀
        """
        import json

        full_system = "请严格以JSON格式返回结果，不要包含markdown代码块标记。"
        if system_prompt:
            full_system = system_prompt + "\n" + full_system

        text = self.generate_text(
            prompt=prompt,
            system_prompt=full_system,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # 清理可能的markdown标记
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("DeepSeek返回的不是有效JSON，返回原始文本")
            return {"raw_text": text}
