"""
TikTok AI Video Factory - Provider Registry
统一Provider注册和工厂方法
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Provider注册表
_PROVIDER_REGISTRY = {}


def register_provider(name: str, provider_class):
    """注册Provider"""
    _PROVIDER_REGISTRY[name.lower()] = provider_class


def get_provider(name: str):
    """获取Provider类"""
    return _PROVIDER_REGISTRY.get(name.lower())


def list_providers() -> list[str]:
    """列出所有已注册的Provider"""
    return list(_PROVIDER_REGISTRY.keys())


def create_provider(provider_name: str, api_key: str = None, **kwargs):
    """
    工厂方法: 根据名称创建Provider实例

    Args:
        provider_name: openai | claude | gemini | deepseek | seedance | veo3 | jimeng | runway | kling
        api_key: API密钥 (可选，优先使用环境变量)
        **kwargs: 传递给Provider构造函数的额外参数

    Returns:
        BaseProvider 实例，或 None (如果Provider不可用)
    """
    from config.api_keys import APIKeys

    provider_cls = get_provider(provider_name)
    if provider_cls is None:
        logger.error(f"未知的Provider: {provider_name}. 可用: {list_providers()}")
        return None

    # 获取API密钥 (优先级: 参数 > 专用环境变量 > 通用 ARK_API_KEY)
    if api_key is None:
        api_key = APIKeys.get_key(provider_name)
    if api_key is None and provider_name in ("seedance", "jimeng"):
        import os
        api_key = os.getenv("ARK_API_KEY")

    if api_key is None and provider_cls.requires_api_key:
        logger.warning(
            f"Provider '{provider_name}' 需要API密钥，"
            f"请设置环境变量或传入 api_key 参数"
        )

    try:
        instance = provider_cls(api_key=api_key, **kwargs)
        if instance.is_available():
            logger.info(f"Provider '{provider_name}' 已就绪")
            return instance
        else:
            logger.warning(f"Provider '{provider_name}' 不可用")
            return None
    except Exception as e:
        logger.error(f"创建Provider '{provider_name}' 失败: {e}")
        return None


def create_all_available() -> dict[str, object]:
    """创建所有可用的Provider实例"""
    available = {}
    for name in list_providers():
        provider = create_provider(name)
        if provider is not None:
            available[name] = provider
    return available


# 延迟导入，避免循环依赖
def _auto_register():
    """自动注册所有Provider"""
    try:
        from providers.base_provider import BaseProvider
    except ImportError:
        pass

    try:
        from providers.openai_provider import OpenAIProvider
        register_provider("openai", OpenAIProvider)
    except ImportError:
        pass

    try:
        from providers.claude_provider import ClaudeProvider
        register_provider("claude", ClaudeProvider)
    except ImportError:
        pass

    try:
        from providers.gemini_provider import GeminiProvider
        register_provider("gemini", GeminiProvider)
    except ImportError:
        pass

    try:
        from providers.deepseek_provider import DeepSeekProvider
        register_provider("deepseek", DeepSeekProvider)
    except ImportError:
        pass

    try:
        from providers.seedance_provider import SeedanceProvider
        register_provider("seedance", SeedanceProvider)
    except ImportError:
        pass

    try:
        from providers.veo3_provider import VEO3Provider
        register_provider("veo3", VEO3Provider)
    except ImportError:
        pass

    try:
        from providers.jimeng_provider import JimengProvider
        register_provider("jimeng", JimengProvider)
    except ImportError:
        pass

    try:
        from providers.runway_provider import RunwayProvider
        register_provider("runway", RunwayProvider)
    except ImportError:
        pass

    try:
        from providers.kling_provider import KlingProvider
        register_provider("kling", KlingProvider)
    except ImportError:
        pass


# 模块加载时自动注册
_auto_register()
