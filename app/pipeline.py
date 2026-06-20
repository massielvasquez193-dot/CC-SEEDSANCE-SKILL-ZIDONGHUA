"""
TikTok UGC Video Factory — Phase 2 Pipeline
强制流程: 参考视频→UGC导演分析→GPT脚本→GPT口播→GPT Storyboard→GPT Image关键帧→Seedance视频→FFmpeg合成

优先级: 真人感 > 视频质量 > 特效
固定模型: GPT-5.5(脚本) + GPT Image(关键帧)
禁止: PIL绘图、占位图、纯Prompt视频生成、AI塑料感
目标: TikTok真人UGC广告标准
"""

import json
import logging
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.scanner import FileScanner
from app.product_extractor import ProductExtractor
from app.video_analyzer import VideoAnalyzer
from app.character_extractor import CharacterExtractor
from app.task_manager import TaskManager, Task
from app.ugc_director import UGCDirector

from agents.master_script_generator import MasterScriptGenerator
from agents.voiceover_generator import VoiceoverGenerator
from agents.character_consistency import CharacterConsistency
from agents.character_generator import CharacterGenerator
from agents.storyboard_generator import StoryboardGenerator
from agents.keyframe_generator import KeyframeGenerator
from agents.seedance_generator import SeedanceGenerator
from agents.continuity_engine import ContinuityEngine
from agents.ugc_score import UGCScore
from agents.export_manager import ExportManager

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)


class FactoryPipeline:
    """Phase 2 UGC工厂流水线"""

    def __init__(self, ai_client=None, provider=None, pairing_mode: str = "one_to_one"):
        self.provider = provider or ai_client
        self.ai_client = self.provider
        self.pairing_mode = pairing_mode

        self.scanner = FileScanner()
        self.product_extractor = ProductExtractor(self.provider)
        self.video_analyzer = VideoAnalyzer(self.provider)
        self.character_extractor = CharacterExtractor(self.provider)
        self.task_manager = TaskManager()

        self.ugc_director = UGCDirector(self.provider)
        self.master_script = MasterScriptGenerator(self.provider)
        self.voiceover = VoiceoverGenerator(self.provider)
        self.character_consistency = CharacterConsistency(self.provider)
        self.character_generator = CharacterGenerator(self.provider)
        self.storyboard = StoryboardGenerator(self.provider)
        self.keyframe = KeyframeGenerator(self.provider)
        self.seedance = SeedanceGenerator(self.provider)
        self.continuity = ContinuityEngine()
        self.ugc_scorer = UGCScore()
        self.export_manager = ExportManager(self.provider)

    def run(self, max_tasks: int = None) -> dict:
        logger.info("=" * 60)
        logger.info("TikTok UGC Video Factory — Phase 2 — 启动")
        logger.info(f"Provider: {self.provider.provider_name if self.provider else 'none'}")
        logger.info("=" * 60)

        results = {"started_at": datetime.now().isoformat(), "steps": {}, "tasks": []}
        scan = self.scanner.scan_all()
        if not all([scan["products"], scan["reference_videos"], scan["characters"]]):
            logger.warning("Missing input files")
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
                logger.error(f"Task {task.task_id} failed: {e}")
                task.mark_failed(str(e))
                results["tasks"].append({"task_id": task.task_id, "status": "failed", "error": str(e)})
            self.task_manager.save_dashboard()

        results["completed_at"] = datetime.now().isoformat()
        results["summary"] = self.task_manager.get_summary()
        return results

    def _process_task(self, task: Task) -> dict:
        logger.info(f"\n{'='*40}\n[{task.task_id}] Phase 2 Pipeline\n{'='*40}")
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

        # STEP 1: UGC Director — 分析参考视频表演模式
        logger.info(f"  [{task.task_id}] STEP 1: UGC Director")
        self.continuity.lock_character(character_info)
        self.continuity.lock_product(product_info)
        self.continuity.lock_scene()

        # 先生成主脚本框架以便director引用
        script = self.master_script.generate(product_info, character_info, video_analysis, duration)
        self._save(out / "master_script.md", script)

        perf = self.ugc_director.analyze(task.reference_video, video_analysis, script, character_info, product_info)
        self.ugc_director.save(perf, out)

        # STEP 2: GPT Image Character Generation → 保存 character.json (人物圣经)
        logger.info(f"  [{task.task_id}] STEP 2: GPT Image Character → character.json canon")
        try:
            char_result = self.character_generator.generate(character_info, out, product_info)
            char_anchor = char_result["character_anchor"]
            # 保存人物圣经 — 以后所有镜头必须引用此文件
            self.character_generator.save_character_canon(character_info, out)
        except RuntimeError as e:
            logger.warning(f"GPT Image unavailable, using PIL fallback: {e}")
            char_consistency = self.character_consistency.generate(character_info, out)
            char_anchor = self.continuity.get_character_anchor()
            char_result = {"reference_image": str(out / "character_reference.png"), "sheet_image": None}
            self.character_generator.save_character_canon(character_info, out)

        # 加载人物圣经供后续步骤使用
        character_canon = self.character_generator.load_character_canon(out)
        logger.info(f"  Character locked: {character_canon['identity']['gender']}, {character_canon['identity']['age_range']}, {character_canon['identity']['race']}")

        # STEP 3: Voiceover — performance_script驱动
        logger.info(f"  [{task.task_id}] STEP 3: Voiceover (performance-driven)")
        vo_result = self.voiceover.generate(script, out, perf, character_info)

        # STEP 4: Storyboard — 基于 script + voiceover + performance
        logger.info(f"  [{task.task_id}] STEP 4: Storyboard")
        storyboard_text = self.storyboard.generate(script, product_info, character_info, video_analysis)
        self._save(out / "storyboard.md", storyboard_text)
        self.storyboard.visualize(storyboard_text, out / "storyboard.png")

        # STEP 5: GPT Image Keyframes — 每帧引用 character_reference.png
        logger.info(f"  [{task.task_id}] STEP 5: GPT Image Keyframes (character-referenced)")
        shot_count = max(len(re.findall(r'###\s*镜头\s*(\d+)', storyboard_text)), 6)
        # 传入 character_anchor 确保每帧人物一致
        kf_consistency = {"consistency_rules": {
            "identity": {"name": character_info.get("name", "主角")},
            "appearance": {
                "hair_style": character_info.get("hair_style", ""),
                "hair_color": character_info.get("hair_color", ""),
                "skin_tone": character_info.get("skin_tone", ""),
                "clothing": character_info.get("clothing", ""),
            },
        }}
        kf_result = self.keyframe.generate(script, storyboard_text, kf_consistency, product_info, out, shot_count, character_canon)

        # STEP 6: Seedance — Reference Image + Prompt + Character Anchor
        logger.info(f"  [{task.task_id}] STEP 6: Seedance (Keyframe + Character Anchor)")
        seedance_result = self.seedance.generate(script, storyboard_text, kf_result, kf_consistency, product_info, out)

        # STEP 7: Video Generation + FFmpeg Composite
        logger.info(f"  [{task.task_id}] STEP 7: Video + FFmpeg Composite")
        video_result = self._step_generate_video(task, seedance_result, vo_result)
        self._save_json(out / "video_result.json", video_result)

        # Continuity Report
        self.continuity.generate_report(out)

        # UGC Score
        ugc = self.ugc_scorer.score(master_script=script, performance_script=perf, continuity_report={"character_locked": True})
        self.ugc_scorer.save_report(ugc, out)
        logger.info(f"  [{task.task_id}] UGC Score: {ugc['total_score']}/100 [{ugc['grade']}]")

        summary = self.export_manager.export_summary(task, product_info, character_info, video_analysis, script, storyboard_text)
        self.export_manager.save_summary(summary, out)

        logger.info(f"  [{task.task_id}] COMPLETE → {out}")
        return {"task_id": task.task_id, "status": "completed", "output_dir": str(out), "ugc_score": ugc["total_score"]}

    def _step_generate_video(self, task, seedance_result, vo_result):
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
                kf_path = kf_dir / seg["keyframe"]
                shot_data = {
                    "shot_id": seg["shot_id"], "duration": seg.get("duration", 5.0),
                    "positive_prompt": Path(seg["file"]).read_text(encoding="utf-8") if Path(seg["file"]).exists() else "",
                    "negative_prompt": "plastic skin, CGI, 3D, cartoon, cinematic, studio lighting, beauty filter, perfect composition",
                    "reference_image": str(kf_path) if kf_path.exists() else None,
                }
                r = sp._call_ark_api(shot_data, cfg.get("width", 1080), cfg.get("height", 1920), 24)
                r["shot_id"] = seg["shot_id"]
                seg_out = out / f"segment_{seg['shot_id']:02d}.mp4"
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

            if raw_video.exists() and vo_result.get("voice_mp3"):
                final_video = out / "video.mp4"
                self.voiceover.composite(raw_video, Path(vo_result["voice_mp3"]), Path(vo_result["subtitle_srt"]), final_video)
                return {"video_path": str(final_video), "segments": len(completed), "composited": True}

            if raw_video.exists():
                shutil.copy(raw_video, out / "video.mp4")
                return {"video_path": str(out / "video.mp4"), "segments": len(completed)}

        return {"video_path": None, "segments": 0, "reason": "Seedance unavailable"}

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
