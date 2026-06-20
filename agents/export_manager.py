"""
TikTok AI Video Factory - 导出管理Agent
生成summary.json汇总所有产出
"""

import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ExportManager:
    """导出管理器"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def export_summary(
        self,
        task,
        product_info: dict,
        character_info: dict,
        video_analysis: dict,
        script: str,
        storyboard: str,
    ) -> dict:
        """生成任务总结"""
        logger.info(f"导出任务总结: {task.task_id}")

        summary = {
            "task_id": task.task_id,
            "created_at": task.created_at,
            "completed_at": datetime.now().isoformat(),
            "status": task.status,
            "product": {
                "name": product_info.get("product_name", ""),
                "brand": product_info.get("brand", ""),
                "category": product_info.get("category", ""),
                "color": product_info.get("color", ""),
                "packaging": product_info.get("packaging", ""),
                "material": product_info.get("material", ""),
                "key_features": product_info.get("key_features", []),
                "source_image": str(task.product_image),
            },
            "video": {
                "source_video": str(task.reference_video),
                "duration": video_analysis.get("metadata", {}).get("duration", 0),
                "resolution": f"{video_analysis.get('metadata', {}).get('width', 0)}x{video_analysis.get('metadata', {}).get('height', 0)}",
                "fps": video_analysis.get("metadata", {}).get("fps", 0),
                "viral_elements": video_analysis.get("viral_elements", []),
                "structure": video_analysis.get("structure", ""),
            },
            "character": {
                "name": character_info.get("name", ""),
                "age_range": character_info.get("age_range", ""),
                "gender": character_info.get("gender", ""),
                "skin_tone": character_info.get("skin_tone", ""),
                "hair_style": character_info.get("hair_style", ""),
                "clothing": character_info.get("clothing", ""),
                "vibe": character_info.get("vibe", ""),
                "source_image": str(task.character_image),
            },
            "output_files": [],
            "generation_time": "",
        }

        # 检查输出目录中的文件
        output_dir = task.output_dir
        if output_dir.exists():
            for f in sorted(output_dir.iterdir()):
                if f.is_file():
                    summary["output_files"].append({
                        "name": f.name,
                        "size": f.stat().st_size,
                        "type": f.suffix,
                    })

        # 计算生成时间
        if task.created_at and task.completed_at:
            created = datetime.fromisoformat(task.created_at)
            completed = datetime.fromisoformat(task.completed_at)
            delta = completed - created
            summary["generation_time"] = f"{delta.total_seconds():.1f}秒"

        return summary

    def save_summary(self, summary: dict, output_dir: Path) -> Path:
        """保存总结JSON"""
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "summary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"总结已保存: {json_path}")
        return json_path

    def export_all_tasks_summary(self, tasks_results: list[dict], output_dir: Path) -> Path:
        """导出所有任务汇总"""
        output_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "exported_at": datetime.now().isoformat(),
            "total_tasks": len(tasks_results),
            "completed": sum(1 for t in tasks_results if t.get("status") == "completed"),
            "failed": sum(1 for t in tasks_results if t.get("status") == "failed"),
            "tasks": tasks_results,
        }
        json_path = output_dir / "all_tasks_summary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"全部任务总结已保存: {json_path}")
        return json_path

    def generate_report(self, summary: dict) -> str:
        """生成可读报告"""
        p = summary.get("product", {})
        c = summary.get("character", {})
        v = summary.get("video", {})

        return f"""
╔══════════════════════════════════════════╗
║     TikTok AI Video Factory Report       ║
╠══════════════════════════════════════════╣
║ Task ID: {summary.get('task_id', 'N/A'):<32} ║
║ Status:  {summary.get('status', 'N/A'):<32} ║
╠══════════════════════════════════════════╣
║ Product:  {p.get('brand', '')} {p.get('name', ''):<25} ║
║ Category: {p.get('category', 'N/A'):<28} ║
║ Color:    {p.get('color', 'N/A'):<28} ║
╠══════════════════════════════════════════╣
║ Character: {c.get('name', 'N/A'):<27} ║
║ Age:       {c.get('age_range', 'N/A'):<28} ║
║ Style:     {c.get('vibe', 'N/A'):<28} ║
╠══════════════════════════════════════════╣
║ Duration:  {v.get('duration', 0):>5.1f}s{'':<25} ║
║ Resolution:{v.get('resolution', 'N/A'):<28} ║
╠══════════════════════════════════════════╣
║ Generation Time: {summary.get('generation_time', 'N/A'):<22} ║
╚══════════════════════════════════════════╝
"""
