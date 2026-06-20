"""
TikTok AI Video Factory - Base Provider
所有Provider的统一抽象基类
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """
    AI Provider 统一基类

    所有Provider必须实现:
      - generate_text()   → 文本生成
      - generate_image()  → 图片生成 (可选)
      - generate_video()  → 视频生成 (可选)

    子类按能力覆盖:
      - TEXT providers:    OpenAI, Claude, Gemini, DeepSeek
      - IMAGE providers:   OpenAI(DALL-E), Jimeng
      - VIDEO providers:   Seedance, VEO3, Runway, Kling, Jimeng
    """

    # 子类覆盖
    provider_name: str = "base"
    requires_api_key: bool = True

    # 能力标记
    supports_text: bool = False
    supports_image: bool = False
    supports_video: bool = False
    supports_vision: bool = False

    def __init__(self, api_key: str = None, model: str = None, **kwargs):
        self.api_key = api_key
        self.model = model or self._default_model()
        self.kwargs = kwargs
        self._client = None

    # ================================================================
    # 抽象接口
    # ================================================================

    @abstractmethod
    def _default_model(self) -> str:
        """返回默认模型名"""
        ...

    @abstractmethod
    def _create_client(self):
        """创建底层API客户端"""
        ...

    def is_available(self) -> bool:
        """检查Provider是否可用"""
        if self.requires_api_key and not self.api_key:
            return False
        try:
            self._create_client()
            return True
        except Exception as e:
            logger.debug(f"Provider '{self.provider_name}' 不可用: {e}")
            return False

    @property
    def client(self):
        """懒加载客户端"""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    # ================================================================
    # 文本生成 (TEXT providers 必须实现)
    # ================================================================

    def generate_text(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> str:
        """
        生成文本

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度
            max_tokens: 最大token数
            **kwargs: 平台特定参数

        Returns:
            生成的文本

        Raises:
            NotImplementedError: 如果Provider不支持文本生成
        """
        if not self.supports_text:
            raise NotImplementedError(
                f"Provider '{self.provider_name}' 不支持文本生成"
            )
        return self._generate_text_impl(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def _generate_text_impl(self, prompt, system_prompt, temperature, max_tokens, **kwargs) -> str:
        """文本生成的实际实现 (子类覆盖)"""
        raise NotImplementedError

    # ================================================================
    # 图片生成 (IMAGE providers 必须实现)
    # ================================================================

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = None,
        width: int = 1080,
        height: int = 1920,
        num_images: int = 1,
        **kwargs,
    ) -> list[dict]:
        """
        生成图片

        Args:
            prompt: 图片描述提示词
            negative_prompt: 负面提示词
            width: 宽度
            height: 高度
            num_images: 生成数量
            **kwargs: 平台特定参数

        Returns:
            [{"url": "...", "width": 1080, "height": 1920, "format": "png"}, ...]

        Raises:
            NotImplementedError: 如果Provider不支持图片生成
        """
        if not self.supports_image:
            raise NotImplementedError(
                f"Provider '{self.provider_name}' 不支持图片生成"
            )
        return self._generate_image_impl(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_images=num_images,
            **kwargs,
        )

    def _generate_image_impl(self, prompt, negative_prompt, width, height, num_images, **kwargs) -> list[dict]:
        """图片生成的实际实现 (子类覆盖)"""
        raise NotImplementedError

    # ================================================================
    # 视频生成 (VIDEO providers 必须实现)
    # ================================================================

    def generate_video(
        self,
        prompt: str,
        negative_prompt: str = None,
        duration: float = 5.0,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
        reference_image: str = None,
        **kwargs,
    ) -> dict:
        """
        生成视频

        Args:
            prompt: 视频描述提示词
            negative_prompt: 负面提示词
            duration: 时长(秒)
            width: 宽度
            height: 高度
            fps: 帧率
            reference_image: 参考图片路径/URL (图生视频)
            **kwargs: 平台特定参数

        Returns:
            {
                "url": "视频URL",
                "duration": 5.0,
                "width": 1080,
                "height": 1920,
                "format": "mp4",
                "task_id": "平台任务ID",
                "status": "completed|processing|failed"
            }

        Raises:
            NotImplementedError: 如果Provider不支持视频生成
        """
        if not self.supports_video:
            raise NotImplementedError(
                f"Provider '{self.provider_name}' 不支持视频生成"
            )
        return self._generate_video_impl(
            prompt=prompt,
            negative_prompt=negative_prompt,
            duration=duration,
            width=width,
            height=height,
            fps=fps,
            reference_image=reference_image,
            **kwargs,
        )

    def _generate_video_impl(self, prompt, negative_prompt, duration, width, height, fps, reference_image, **kwargs) -> dict:
        """视频生成的实际实现 (子类覆盖)"""
        raise NotImplementedError

    # ================================================================
    # 视觉分析 (VISION providers 必须实现)
    # ================================================================

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        **kwargs,
    ) -> str:
        """
        分析图片内容

        Args:
            image_path: 图片路径或URL
            prompt: 分析提示词

        Returns:
            分析结果文本

        Raises:
            NotImplementedError: 如果Provider不支持视觉分析
        """
        if not self.supports_vision:
            raise NotImplementedError(
                f"Provider '{self.provider_name}' 不支持视觉分析"
            )
        return self._analyze_image_impl(image_path=image_path, prompt=prompt, **kwargs)

    def _analyze_image_impl(self, image_path, prompt, **kwargs) -> str:
        """视觉分析的实际实现 (子类覆盖)"""
        raise NotImplementedError

    # ================================================================
    # 任务查询 (异步视频生成平台)
    # ================================================================

    def query_task(self, task_id: str) -> dict:
        """
        查询异步任务状态

        Returns:
            {"task_id": "...", "status": "completed|processing|failed", "result_url": "..."}
        """
        return {
            "task_id": task_id,
            "status": "unknown",
            "message": f"Provider '{self.provider_name}' 不支持任务查询",
        }

    # ================================================================
    # 工具方法
    # ================================================================

    def get_capabilities(self) -> dict:
        """获取Provider能力清单"""
        return {
            "provider": self.provider_name,
            "model": self.model,
            "supports_text": self.supports_text,
            "supports_image": self.supports_image,
            "supports_video": self.supports_video,
            "supports_vision": self.supports_vision,
            "available": self.is_available(),
        }

    def __repr__(self) -> str:
        caps = self.get_capabilities()
        status = "OK" if caps["available"] else "NA"
        return (
            f"<{self.provider_name.upper()}Provider model={self.model} "
            f"text={caps['supports_text']} image={caps['supports_image']} "
            f"video={caps['supports_video']} [{status}]>"
        )
