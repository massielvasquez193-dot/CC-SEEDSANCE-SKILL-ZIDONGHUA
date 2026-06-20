"""
TikTok AI Factory Pro — Video History
=======================================
Scans output directories to build video generation history.
Reads summary.json, oneclick_summary.json, and batch_log.json.

Returns list of VideoRecord dicts for display in Customer Portal.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class VideoRecord:
    """A single video generation record."""
    __slots__ = ("timestamp", "task_id", "product", "character",
                 "reference", "duration", "status", "output_dir",
                 "video_path", "cost", "style", "country")

    def __init__(self, **kwargs):
        self.timestamp = kwargs.get("timestamp", "")
        self.task_id = kwargs.get("task_id", "")
        self.product = kwargs.get("product", "")
        self.character = kwargs.get("character", "")
        self.reference = kwargs.get("reference", "")
        self.duration = kwargs.get("duration", 0)
        self.status = kwargs.get("status", "unknown")
        self.output_dir = kwargs.get("output_dir", "")
        self.video_path = kwargs.get("video_path", "")
        self.cost = kwargs.get("cost", 0.0)
        self.style = kwargs.get("style", "")
        self.country = kwargs.get("country", "")

    def to_dict(self) -> dict:
        return {k: getattr(self, k, "") for k in self.__slots__}


class VideoHistory:
    """Builds video generation history from project output."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.output_dir = self.project_root / "output"

    def get_recent(self, limit: int = 100) -> List[Dict]:
        """
        Get the most recent video records, newest first.
        Scans output directories for summary files.
        """
        records = []

        # 1) Scan oneclick_summary.json files
        for summary_path in sorted(
            self.output_dir.rglob("oneclick_summary.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit]:
            try:
                data = json.loads(summary_path.read_text(encoding="utf-8"))
                task_dir = summary_path.parent

                # Find video file
                videos = list(task_dir.glob("video_final*.mp4"))

                product_file = task_dir / "product.jpg" if (task_dir / "product.jpg").exists() else task_dir / "product.png"
                char_file = task_dir / "character.jpg" if (task_dir / "character.jpg").exists() else task_dir / "character.png"

                record = VideoRecord(
                    timestamp=data.get("started_at", "") or str(datetime.fromtimestamp(summary_path.stat().st_mtime)),
                    task_id=task_dir.name,
                    product=product_file.stem if product_file.exists() else "",
                    character=char_file.stem if char_file.exists() else "",
                    reference="",
                    duration=int(data.get("elapsed_seconds", 0)),
                    status=data.get("status", "completed"),
                    output_dir=str(task_dir),
                    video_path=str(videos[0]) if videos else "",
                    cost=0.332,
                    style=data.get("style", ""),
                    country=data.get("country", ""),
                )
                records.append(record.to_dict())
            except (json.JSONDecodeError, OSError) as e:
                logger.debug(f"Skipping {summary_path}: {e}")

        # 2) Scan summary.json files (manual mode)
        for summary_path in sorted(
            self.output_dir.rglob("summary.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit]:
            try:
                data = json.loads(summary_path.read_text(encoding="utf-8"))
                task_dir = summary_path.parent

                videos = list(task_dir.glob("video_final*.mp4"))

                record = VideoRecord(
                    timestamp=data.get("exported_at", str(datetime.fromtimestamp(summary_path.stat().st_mtime))),
                    task_id=task_dir.name,
                    product=data.get("task", {}).get("product", task_dir.name),
                    character=data.get("task", {}).get("character", ""),
                    reference=data.get("task", {}).get("reference", ""),
                    duration=0,
                    status="completed",
                    output_dir=str(task_dir),
                    video_path=str(videos[0]) if videos else "",
                    cost=0.332,
                )
                records.append(record.to_dict())
            except (json.JSONDecodeError, OSError) as e:
                logger.debug(f"Skipping {summary_path}: {e}")

        # 3) Scan batch_log.json
        batch_log = self.output_dir / "batch_log.json"
        if batch_log.exists():
            try:
                data = json.loads(batch_log.read_text(encoding="utf-8"))
                for task in data.get("tasks", [])[:limit]:
                    record = VideoRecord(
                        timestamp=task.get("completed_at", task.get("started_at", "")),
                        task_id=task.get("task_id", ""),
                        product=Path(task.get("product_path", "")).stem,
                        character=Path(task.get("character_path", "")).stem,
                        reference=Path(task.get("reference_video_path", "")).stem,
                        duration=0,
                        status=task.get("status", "unknown"),
                        output_dir=task.get("output_dir", ""),
                        video_path=task.get("video_path", ""),
                        cost=0.332 if task.get("status") == "completed" else 0,
                        style=task.get("style", ""),
                        country=task.get("country", ""),
                    )
                    records.append(record.to_dict())
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"Skipping batch_log: {e}")

        # Sort by timestamp descending, deduplicate by task_id
        seen = set()
        deduped = []
        for r in sorted(records, key=lambda x: x["timestamp"], reverse=True):
            if r["task_id"] not in seen:
                seen.add(r["task_id"])
                deduped.append(r)

        return deduped[:limit]

    def get_stats(self) -> Dict:
        """Quick stats from history."""
        records = self.get_recent(limit=1000)
        completed = [r for r in records if r["status"] == "completed"]
        failed = [r for r in records if r["status"] == "failed"]

        return {
            "total_records": len(records),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": round(len(completed) / max(len(records), 1) * 100, 1),
            "total_cost": round(len(completed) * 0.332, 2),
        }
