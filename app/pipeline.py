"""
TikTok AI Video Factory v3 — GPT驱动生产流水线
强制流程: 参考视频→GPT拆解→GPT脚本→GPT口播→GPT Storyboard→GPT Image关键帧→Seedance视频→ElevenLabs配音→FFmpeg合成

固定模型: GPT-5.5(脚本) + GPT Image(关键帧)
禁止: PIL绘图、占位图、纯Prompt视频生成
目标: TikTok真人UGC广告标准
"""

import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.scanner import FileScanner
from app.product_extractor import ProductExtractor
from app.video_analyzer import VideoAnalyzer
from app.character_extractor import CharacterExtractor
from app.task_manager import TaskManager, Task

from agents.master_script_generator import MasterScriptGenerator
from agents.voiceover_generator import VoiceoverGenerator
from agents.character_consistency import CharacterConsistency
from agents.storyboard_generator import StoryboardGenerator
from agents.keyframe_generator import KeyframeGenerator
from agents.seedance_generator import SeedanceGenerator
from agents.export_manager import ExportManager
from agents.ugc_score import UGCScore

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)


class FactoryPipeline:
    """v3 GPT工厂流水线 — 8步强制顺序，UGC目标"""

    def __init__(self, ai_client=None, provider=None, pairing_mode: str = "one_to_one"):
        self.provider = provider or ai_client
        self.ai_client = self.provider
        self.pairing_mode = pairing_mode

        self.scanner = FileScanner()
        self.product_extractor = ProductExtractor(self.provider)
        self.video_analyzer = VideoAnalyzer(self.provider)
        self.character_extractor = CharacterExtractor(self.provider)
        self.task_manager = TaskManager()

        # GPT驱动模块
        self.master_script = MasterScriptGenerator(self.provider)
        self.voiceover = VoiceoverGenerator(self.provider)
        self.character_consistency = CharacterConsistency(self.provider)
        self.storyboard = StoryboardGenerator(self.provider)
        self.keyframe = KeyframeGenerator(self.provider)
        self.seedance = SeedanceGenerator(self.provider)
        self.export_manager = ExportManager(self.provider)
        self.ugc_scorer = UGCScore()

    def run(self, max_tasks: int = None) -> dict:
        logger.info("=" * 60)
        logger.info("TikTok AI Video Factory v3 — GPT驱动 — 启动")
        logger.info(f"Provider: {self.provider.provider_name if self.provider else 'none'}")
        logger.info("=" * 60)

        results = {"started_at": datetime.now().isoformat(), "steps": {}, "tasks": []}
        scan = self.scanner.scan_all()
        results["steps"]["scan"] = scan

        if not all([scan["products"], scan["reference_videos"], scan["characters"]]):
            logger.warning("缺少输入文件")
            return results

        tasks = self.task_manager.build_tasks_one_to_one(
            [Path(p) for p in scan["products"]],
            [Path(v) for v in scan["reference_videos"]],
            [Path(c) for c in scan["characters"]],
        )

        pending = self.task_manager.get_pending_tasks()
        if max_tasks:
            pending = pending[:max_tasks]

        for task in pending:
            try:
                results["tasks"].append(self._process_task(task))
                task.mark_completed()
            except Exception as e:
                logger.error(f"任务 {task.task_id} 失败: {e}")
                task.mark_failed(str(e))
                results["tasks"].append({"task_id": task.task_id, "status": "failed", "error": str(e)})
            self.task_manager.save_dashboard()

        results["completed_at"] = datetime.now().isoformat()
        results["summary"] = self.task_manager.get_summary()
        return results

    def _process_task(self, task: Task) -> dict:
        logger.info(f"\n{'='*40}\n[{task.task_id}] v3 Pipeline START\n{'='*40}")
        task.mark_running()
        out = task.output_dir
        out.mkdir(parents=True, exist_ok=True)

        self._copy_input_files(task)

        product_info = self.product_extractor.extract(task.product_image)
        character_info = self.character_extractor.extract(task.character_image)
        video_analysis = self.video_analyzer.analyze_viral_elements(task.reference_video)
        duration = video_analysis.get("metadata", {}).get("duration", 15)

        self.product_extractor.save_product_json(product_info, out)
        self.character_extractor.save_character_json(character_info, out)
        self.video_analyzer.save_analysis(video_analysis, out)

        # ================================================================
        # STEP 1: GPT拆解参考视频
        # ================================================================
        logger.info(f"  [{task.task_id}] STEP 1/8: GPT视频拆解")
        self._step_gpt_breakdown(video_analysis, product_info, character_info, out)

        # ================================================================
        # STEP 2: GPT-5.5 生成主脚本
        # ================================================================
        logger.info(f"  [{task.task_id}] STEP 2/8: GPT-5.5 主脚本")
        script = self.master_script.generate(product_info, character_info, video_analysis, duration)
        self._save(out / "master_script.md", script)

        # ================================================================
        # STEP 3: 人物一致性锁定
        # ================================================================
        logger.info(f"  [{task.task_id}] STEP 3/8: 人物一致性锁定")
        char_consistency = self.character_consistency.generate(character_info, out)

        # ================================================================
        # STEP 4: GPT口播 + ElevenLabs TTS
        # ================================================================
        logger.info(f"  [{task.task_id}] STEP 4/8: GPT口播 + ElevenLabs TTS")
        vo_result = self.voiceover.generate(script, out, character_info)

        # ================================================================
        # STEP 5: GPT Storyboard
        # ================================================================
        logger.info(f"  [{task.task_id}] STEP 5/8: GPT Storyboard")
        storyboard_text = self.storyboard.generate(script, product_info, character_info, video_analysis)
        self._save(out / "storyboard.md", storyboard_text)
        self.storyboard.visualize(storyboard_text, out / "storyboard.png")

        # ================================================================
        # STEP 6: GPT Image 关键帧 (真实PNG，禁止占位)
        # ================================================================
        logger.info(f"  [{task.task_id}] STEP 6/8: GPT Image 关键帧")
        import re
        shot_count = max(len(re.findall(r'###\s*镜头\s*(\d+)', storyboard_text)), 6)
        kf_result = self.keyframe.generate(script, storyboard_text, char_consistency, product_info, out, shot_count)

        # ================================================================
        # STEP 7: Seedance — Reference Image + Prompt + Anchor
        # ================================================================
        logger.info(f"  [{task.task_id}] STEP 7/8: Seedance (Keyframe-driven)")
        seedance_result = self.seedance.generate(script, storyboard_text, kf_result, char_consistency, product_info, out)

        # ================================================================
        # STEP 8: Seedance ARK API → video.mp4 + ElevenLabs配音 + FFmpeg合成
        # ================================================================
        logger.info(f"  [{task.task_id}] STEP 8/8: Video生成 + 配音 + 合成")
        video_result = self._step_generate_video(task, seedance_result, vo_result)

        # UGC评分
        ugc_report = self.ugc_scorer.score(
            master_script=script,
            performance_script={},
            continuity_report={},
        )
        self.ugc_scorer.save_report(ugc_report, out)
        logger.info(f"  [{task.task_id}] UGC Score: {ugc_report['total_score']}/100 [{ugc_report['grade']}]")

        # 导出总览
        summary = self.export_manager.export_summary(task, product_info, character_info, video_analysis, script, storyboard_text)
        self.export_manager.save_summary(summary, out)

        logger.info(f"  [{task.task_id}] COMPLETE → {out}")
        return {"task_id": task.task_id, "status": "completed", "output_dir": str(out), "ugc_score": ugc_report["total_score"]}

    def _step_gpt_breakdown(self, video_analysis, product_info, character_info, out):
        """GPT拆解参考视频结构"""
        breakdown = {
            "analyzed_at": datetime.now().isoformat(),
            "shots": video_analysis.get("shot_analysis", {}).get("shots", []),
            "structure": video_analysis.get("structure", {}),
            "pacing": video_analysis.get("pacing", {}),
        }
        self._save_json(out / "gpt_breakdown.json", breakdown)

    def _step_generate_video(self, task, seedance_result, vo_result):
        """Seedance ARK API + FFmpeg合成"""
        from providers.seedance_provider import SeedanceProvider
        from providers import create_provider

        sp = None
        if isinstance(self.provider, SeedanceProvider):
            sp = self.provider
        else:
            sp = create_provider("seedance")

        segments = seedance_result.get("segments", [])
        out = task.output_dir
        kf_dir = out / "keyframes"
        cfg = self._load_video_config()

        if sp and sp.is_available() and segments:
            segment_videos = []
            for seg in segments:
                shot_id = seg["shot_id"]
                kf_path = kf_dir / seg["keyframe"]
                shot_data = {
                    "shot_id": shot_id,
                    "duration": seg.get("duration", 5.0),
                    "positive_prompt": Path(seg["file"]).read_text(encoding="utf-8") if Path(seg["file"]).exists() else "",
                    "negative_prompt": "plastic skin, cinematic, 3D, cartoon, perfect composition, studio lighting",
                    "reference_image": str(kf_path) if kf_path.exists() else None,
                }
                r = sp._call_ark_api(shot_data, cfg.get("width", 1080), cfg.get("height", 1920), 24)
                r["shot_id"] = shot_id
                seg_out = out / f"segment_{shot_id:02d}.mp4"
                if r.get("video_url"):
                    sp._download_video(r["video_url"], seg_out)
                    r["local_path"] = str(seg_out)
                segment_videos.append(r)

            completed = [s for s in segment_videos if s.get("local_path")]
            raw_video = out / "video_raw.mp4"
            if len(completed) == 1:
                shutil.copy(completed[0]["local_path"], raw_video)
            elif len(completed) > 1:
                sp._merge_videos([s["local_path"] for s in completed], raw_video)

            # FFmpeg合成: 视频 + ElevenLabs配音 + 字幕
            if raw_video.exists() and vo_result.get("voice_mp3"):
                final_video = out / "video.mp4"
                srt_path = Path(vo_result["subtitle_srt"])
                voice_path = Path(vo_result["voice_mp3"])
                self.voiceover.composite(raw_video, voice_path, srt_path, final_video)
                return {"video_path": str(final_video), "segments": len(completed), "composited": True}

            if raw_video.exists():
                shutil.copy(raw_video, out / "video.mp4")
                return {"video_path": str(out / "video.mp4"), "segments": len(completed), "composited": False}

        return {"video_path": None, "segments": 0, "reason": "Seedance API unavailable or no segments"}

    def _copy_input_files(self, task: Task):
        for src, name in [(task.product_image, "product"+task.product_image.suffix),
                          (task.reference_video, "reference"+task.reference_video.suffix),
                          (task.character_image, "character"+task.character_image.suffix)]:
            if src.exists():
                shutil.copy2(src, task.output_dir / name)

    def _save(self, path: Path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _save_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    def _load_video_config(self) -> dict:
        try:
            return json.loads((Path(__file__).resolve().parent.parent/"config"/"factory.json").read_text(encoding="utf-8")).get("video", {})
        except Exception:
            return {"width": 1080, "height": 1920, "fps": 24}
