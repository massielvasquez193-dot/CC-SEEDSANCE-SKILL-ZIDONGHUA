"""
TikTok AI Video Factory - 主工作流
定义完整的自动化视频生产工作流

支持的工作流模式:
1. full_auto: 全自动模式 (默认)
2. script_only: 只生成脚本
3. storyboard_only: 只生成分镜
4. prompt_only: 只生成Prompt
5. single_task: 手动指定单个任务

Provider动态切换:
  provider=openai | claude | gemini | deepseek | seedance | veo3 | jimeng | runway | kling
"""

import logging
from pathlib import Path
from typing import Optional

from app.pipeline import FactoryPipeline
from app.scanner import FileScanner
from app.task_manager import TaskManager
from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)


class FactoryWorkflow:
    """工厂工作流管理器 — 支持动态Provider切换"""

    def __init__(self, ai_client=None, provider_name: str = None, provider_instance=None):
        """
        Args:
            ai_client: (兼容旧版)直接传入的AI客户端
            provider_name: Provider名称字符串，如 "openai", "claude"
            provider_instance: 已创建的Provider实例
        """
        self.provider_name = provider_name
        self.provider = provider_instance

        # 如果传入了provider_name但未传实例，自动创建
        if self.provider is None and provider_name:
            self.provider = self._create_provider(provider_name)

        # 兼容旧版ai_client参数
        self.ai_client = ai_client or self.provider
        self.pipeline = FactoryPipeline(
            ai_client=self.ai_client,
            provider=self.provider,
        )
        self.scanner = FileScanner()
        self.task_manager = TaskManager()

    def _create_provider(self, name: str):
        """根据名称创建Provider实例"""
        from providers import create_provider
        return create_provider(name)

    # ================================================================
    # Provider切换
    # ================================================================
    def switch_provider(self, provider_name: str) -> bool:
        """
        动态切换Provider

        Args:
            provider_name: openai|claude|gemini|deepseek

        Returns:
            True if successful
        """
        provider = self._create_provider(provider_name)
        if provider is None:
            logger.error(f"切换Provider失败: {provider_name}")
            return False

        self.provider_name = provider_name
        self.provider = provider
        self.ai_client = provider
        self.pipeline.provider = provider
        self.pipeline.ai_client = provider

        # 更新所有agent的provider引用
        self.pipeline.product_extractor.ai_client = provider
        self.pipeline.video_analyzer.ai_client = provider
        self.pipeline.character_extractor.ai_client = provider
        self.pipeline.viral_analyzer.ai_client = provider
        self.pipeline.script_generator.ai_client = provider
        self.pipeline.storyboard_generator.ai_client = provider
        self.pipeline.image_prompt_generator.ai_client = provider
        self.pipeline.seedance_generator.ai_client = provider
        self.pipeline.veo3_generator.ai_client = provider
        self.pipeline.jimeng_generator.ai_client = provider
        self.pipeline.subtitle_generator.ai_client = provider
        self.pipeline.export_manager.ai_client = provider

        logger.info(f"已切换Provider: {provider_name}")
        return True

    def get_available_providers(self) -> dict:
        """获取所有可用的Provider及其状态"""
        from providers import list_providers, create_provider

        result = {}
        for name in list_providers():
            p = create_provider(name)
            result[name] = {
                "available": p is not None,
                "capabilities": p.get_capabilities() if p else None,
            }
        return result

    # ================================================================
    # 工作流模式
    # ================================================================
    def run_full_auto(self, max_tasks: Optional[int] = None) -> dict:
        """全自动模式"""
        logger.info(f"启动全自动工作流 [Provider: {self.provider_name or 'none'}]...")
        return self.pipeline.run(max_tasks=max_tasks)

    def run_script_only(self, product_path: str, video_path: str, character_path: str) -> str:
        """仅生成脚本模式"""
        logger.info("启动脚本生成工作流...")
        from app.product_extractor import ProductExtractor
        from app.video_analyzer import VideoAnalyzer
        from app.character_extractor import CharacterExtractor
        from agents.script_generator import ScriptGenerator

        product_info = ProductExtractor(self.ai_client).extract(Path(product_path))
        video_analysis = VideoAnalyzer(self.ai_client).analyze_viral_elements(Path(video_path))
        character_info = CharacterExtractor(self.ai_client).extract(Path(character_path))

        return ScriptGenerator(self.ai_client).generate(
            viral_analysis=video_analysis,
            product_info=product_info,
            character_info=character_info,
        )

    def run_storyboard_only(self, script: str, product_path: str, character_path: str, video_path: str) -> str:
        """仅生成分镜模式"""
        logger.info("启动分镜生成工作流...")
        from app.product_extractor import ProductExtractor
        from app.video_analyzer import VideoAnalyzer
        from app.character_extractor import CharacterExtractor
        from agents.storyboard_generator import StoryboardGenerator

        product_info = ProductExtractor(self.ai_client).extract(Path(product_path))
        video_analysis = VideoAnalyzer(self.ai_client).analyze_viral_elements(Path(video_path))
        character_info = CharacterExtractor(self.ai_client).extract(Path(character_path))

        return StoryboardGenerator(self.ai_client).generate(
            script=script,
            product_info=product_info,
            character_info=character_info,
            viral_analysis=video_analysis,
        )

    def run_prompt_only(self, storyboard: str, product_path: str, character_path: str) -> dict:
        """仅生成Prompt模式"""
        logger.info("启动Prompt生成工作流...")
        from app.product_extractor import ProductExtractor
        from app.character_extractor import CharacterExtractor
        from agents.image_prompt_generator import ImagePromptGenerator
        from agents.seedance_generator import SeedanceGenerator
        from agents.veo3_generator import VEO3Generator
        from agents.jimeng_generator import JimengGenerator

        product_info = ProductExtractor(self.ai_client).extract(Path(product_path))
        character_info = CharacterExtractor(self.ai_client).extract(Path(character_path))

        char_consistency = CharacterExtractor(self.ai_client).generate_consistency_description(character_info)
        product_consistency = self.pipeline._generate_product_consistency(product_info)

        return {
            "image_prompt": ImagePromptGenerator(self.ai_client).generate(
                storyboard, char_consistency, product_consistency, 6
            ),
            "seedance": SeedanceGenerator(self.ai_client).generate(
                storyboard, product_info, char_consistency
            ),
            "veo3": VEO3Generator(self.ai_client).generate(
                storyboard, product_info, char_consistency, 15
            ),
            "jimeng": JimengGenerator(self.ai_client).generate(
                storyboard, product_info, char_consistency
            ),
        }

    def run_single_task(
        self,
        product_path: str,
        video_path: str,
        character_path: str,
        task_id: str = "custom_task",
    ) -> dict:
        """单任务模式"""
        logger.info(f"启动单任务工作流: {task_id}")

        from app.task_manager import Task

        output_dir = OUTPUT_DIR / task_id
        task = Task(
            task_id=task_id,
            product_image=Path(product_path),
            reference_video=Path(video_path),
            character_image=Path(character_path),
            output_dir=output_dir,
        )

        result = self.pipeline._process_task(task)
        task.mark_completed()
        return result

    def show_status(self) -> dict:
        """显示当前状态"""
        scan = self.scanner.scan_all()
        provider_info = {}
        if self.provider:
            provider_info = {
                "name": self.provider_name,
                "capabilities": self.provider.get_capabilities(),
            }

        return {
            "input_files": {
                "products": len(scan["products"]),
                "videos": len(scan["reference_videos"]),
                "characters": len(scan["characters"]),
            },
            "output_dir": str(OUTPUT_DIR),
            "ready": all([
                len(scan["products"]) > 0,
                len(scan["reference_videos"]) > 0,
                len(scan["characters"]) > 0,
            ]),
            "provider": provider_info,
        }
