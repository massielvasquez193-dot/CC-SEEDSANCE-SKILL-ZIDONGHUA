"""
TikTok AI Factory Pro — Cost Tracker
======================================
Scans output directories, aggregates video stats, estimates costs.
Generates cost_dashboard.json for the Customer Portal.

Data sources:
  - output/ → scan video_final.mp4 files
  - output/*/summary.json → per-task cost info
  - output/*/oneclick_summary.json → one-click records
  - output/batch_log.json → batch records
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Per-video cost estimate (matching cost_report.py)
PER_VIDEO_COST = {
    "openai_text": 0.013,
    "openai_image": 0.240,
    "elevenlabs_tts": 0.004,
    "seedance_video": 0.075,
    "total": 0.332,
}


class CostTracker:
    """Aggregates video production stats and costs from output directories."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.output_dir = self.project_root / "output"

    # ================================================================
    # Video counting
    # ================================================================

    def count_videos(self, since: datetime = None) -> Dict[str, int]:
        """
        Count total videos in output directories, optionally filtered by date.

        Returns:
            {"today": N, "this_week": N, "this_month": N, "total": N}
        """
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        counts = {"today": 0, "this_week": 0, "this_month": 0, "total": 0}

        for video_file in self.output_dir.rglob("video_final*.mp4"):
            mtime = datetime.fromtimestamp(video_file.stat().st_mtime)
            counts["total"] += 1
            if mtime >= today_start:
                counts["today"] += 1
            if mtime >= week_start:
                counts["this_week"] += 1
            if mtime >= month_start:
                counts["this_month"] += 1

        return counts

    # ================================================================
    # Cost aggregation
    # ================================================================

    def calculate_costs(self) -> Dict[str, Any]:
        """
        Calculate estimated costs from video count.

        Returns breakdown by provider + totals.
        """
        counts = self.count_videos()
        total = counts["total"]

        return {
            "video_counts": counts,
            "per_video_breakdown": PER_VIDEO_COST,
            "openai_cost": round(total * PER_VIDEO_COST["openai_text"], 2),
            "openai_image_cost": round(total * PER_VIDEO_COST["openai_image"], 2),
            "elevenlabs_cost": round(total * PER_VIDEO_COST["elevenlabs_tts"], 2),
            "seedance_cost": round(total * PER_VIDEO_COST["seedance_video"], 2),
            "total_cost": round(total * PER_VIDEO_COST["total"], 2),
            "avg_cost_per_video": round(PER_VIDEO_COST["total"], 3),
            "this_month_cost": round(counts["this_month"] * PER_VIDEO_COST["total"], 2),
            "today_cost": round(counts["today"] * PER_VIDEO_COST["total"], 2),
        }

    # ================================================================
    # Task history from logs
    # ================================================================

    def get_task_stats(self) -> Dict[str, Any]:
        """
        Read batch_log.json or scan output dirs for task success/failure stats.

        Returns:
            {"success": N, "failed": N, "total": N, "success_rate": float}
        """
        success = 0
        failed = 0

        # Try batch log first
        batch_log = self.output_dir / "batch_log.json"
        if batch_log.exists():
            try:
                data = json.loads(batch_log.read_text(encoding="utf-8"))
                for task in data.get("tasks", []):
                    if task.get("status") == "completed":
                        success += 1
                    elif task.get("status") == "failed":
                        failed += 1
            except (json.JSONDecodeError, KeyError):
                pass

        # Also scan summary files
        for summary_file in self.output_dir.rglob("summary.json"):
            try:
                data = json.loads(summary_file.read_text(encoding="utf-8"))
                if data.get("status") == "completed":
                    success += 1
                else:
                    failed += 1
            except (json.JSONDecodeError, KeyError):
                pass

        # Also scan oneclick summaries
        for summary_file in self.output_dir.rglob("oneclick_summary.json"):
            try:
                data = json.loads(summary_file.read_text(encoding="utf-8"))
                if data.get("status") == "completed":
                    success += 1
                else:
                    failed += 1
            except (json.JSONDecodeError, KeyError):
                pass

        total = success + failed
        rate = round(success / total * 100, 1) if total > 0 else 100.0

        return {
            "success": success,
            "failed": failed,
            "total": total,
            "success_rate": rate,
        }

    # ================================================================
    # Dashboard JSON
    # ================================================================

    def generate_dashboard(self) -> Dict[str, Any]:
        """Generate a complete cost_dashboard.json."""
        return {
            "generated_at": datetime.now().isoformat(),
            "video_stats": self.count_videos(),
            "costs": self.calculate_costs(),
            "task_stats": self.get_task_stats(),
        }

    def save_dashboard(self, path: Path = None):
        """Save cost_dashboard.json to output directory."""
        if path is None:
            path = self.output_dir / "cost_dashboard.json"
        dashboard = self.generate_dashboard()
        path.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False), encoding="utf-8")
        return dashboard

    # ================================================================
    # Chart data
    # ================================================================

    def get_monthly_trend(self) -> List[Dict]:
        """
        Get monthly video generation trend (last 12 months).
        Returns list of {"month": "2026-06", "count": N, "cost": $N}.
        """
        now = datetime.now()
        monthly = {}
        for i in range(12):
            key = (now.replace(day=1) - timedelta(days=i * 31)).strftime("%Y-%m")
            monthly[key] = 0

        for video_file in self.output_dir.rglob("video_final*.mp4"):
            mtime = datetime.fromtimestamp(video_file.stat().st_mtime)
            key = mtime.strftime("%Y-%m")
            if key in monthly:
                monthly[key] += 1

        per_video = PER_VIDEO_COST["total"]
        result = []
        for month in sorted(monthly.keys()):
            count = monthly[month]
            result.append({
                "month": month,
                "count": count,
                "cost": round(count * per_video, 2),
            })
        return result
