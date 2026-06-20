"""
TikTok AI Factory Pro — RC Stress Test
========================================
100-task batch stress test for Release Candidate validation.
Measures: success rate, failure rate, avg time, avg cost, API error rate.

Usage: python tools/rc_stress_test.py [--tasks 100] [--concurrent 3]
"""

import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class StressTestRunner:
    """Runs N batch tasks and collects comprehensive metrics."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None

    def run(self, task_count: int = 100, max_concurrent: int = 3) -> dict:
        """Execute the stress test."""
        print(f"\n{'='*60}")
        print(f"  TikTok AI Factory Pro — RC Stress Test")
        print(f"  Tasks: {task_count} | Concurrent: {max_concurrent}")
        print(f"  Started: {datetime.now().isoformat()}")
        print(f"{'='*60}\n")

        self.start_time = datetime.now()

        # Build test tasks using existing input files
        products = self._list_files("input/products", [".jpg", ".jpeg", ".png", ".webp"])
        characters = self._list_files("input/characters", [".jpg", ".jpeg", ".png"])
        refs = self._list_files("input/reference_videos", [".mp4", ".mov"])

        if not products or not characters or not refs:
            print("[ERROR] Missing input files — need at least 1 product, 1 character, 1 reference video")
            return {"status": "error", "reason": "missing_input_files"}

        print(f"  Input: {len(products)} products × {len(characters)} characters × {len(refs)} refs\n")

        # Generate task list
        tasks = []
        for i in range(task_count):
            tasks.append({
                "task_id": f"rc_{i+1:04d}",
                "product": products[i % len(products)],
                "character": characters[i % len(characters)],
                "reference": refs[i % len(refs)],
                "country": "美国",
                "style": ["TikTok UGC", "Beauty Review", "Problem Solution", "Before After", "Testimonial"][i % 5],
            })

        # Execute tasks
        completed = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {executor.submit(self._execute_one, t): t for t in tasks}

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result(timeout=300)
                    self.results.append(result)
                    if result.get("status") == "completed":
                        completed += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    self.errors.append({
                        "task_id": task["task_id"],
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    })

                # Progress
                done = completed + failed
                pct = int(done / task_count * 100)
                bar = "█" * (pct // 2) + "░" * (50 - pct // 2)
                print(f"\r  [{bar}] {done}/{task_count}  ✓{completed} ✗{failed}", end="", flush=True)

        self.end_time = datetime.now()
        print("\n")

        return self._analyze(task_count)

    def _execute_one(self, task: dict) -> dict:
        """Execute a single task and return metrics."""
        from app.gui.one_click_controller import OneClickController

        t_start = time.time()
        ctrl = OneClickController(self.project_root)

        result = ctrl.run(
            product_path=task["product"],
            character_path=task["character"],
            video_path=task["reference"],
            country=task["country"],
            video_count=1,
            style=task["style"],
        )

        elapsed = time.time() - t_start

        return {
            "task_id": task["task_id"],
            "status": result.get("status", "unknown"),
            "elapsed_seconds": round(elapsed, 1),
            "style": task["style"],
            "country": task["country"],
            "videos": result.get("videos", []),
            "output_dir": result.get("output_dir", ""),
            "steps_completed": self._count_steps(result),
            "error": result.get("error", ""),
        }

    def _count_steps(self, result: dict) -> int:
        """Count how many pipeline steps completed."""
        files = result.get("files", {})
        return len(files)

    def _analyze(self, task_count: int) -> dict:
        """Compute KPIs from collected results."""
        completed = [r for r in self.results if r["status"] == "completed"]
        failed = [r for r in self.results if r["status"] != "completed"]

        times = [r["elapsed_seconds"] for r in completed] if completed else [0]
        times_all = [r["elapsed_seconds"] for r in self.results] if self.results else [0]

        total_elapsed = (self.end_time - self.start_time).total_seconds()

        # Cost estimate ($0.332 per completed video)
        total_cost = len(completed) * 0.332

        # Step completion rates
        step_counts = {}
        for r in self.results:
            steps = r.get("steps_completed", 0)
            step_counts[steps] = step_counts.get(steps, 0) + 1

        metrics = {
            "test_config": {
                "task_count": task_count,
                "concurrent": 3,
                "mode": os.getenv("TIKTOK_FACTORY_DEV_MODE", "false"),
                "started_at": self.start_time.isoformat(),
                "finished_at": self.end_time.isoformat(),
            },
            "results": {
                "total": task_count,
                "completed": len(completed),
                "failed": len(failed),
                "success_rate": round(len(completed) / task_count * 100, 1) if task_count > 0 else 0,
                "failure_rate": round(len(failed) / task_count * 100, 1) if task_count > 0 else 0,
            },
            "timing": {
                "total_elapsed_seconds": round(total_elapsed, 1),
                "avg_per_task_seconds": round(sum(times_all) / len(times_all), 1),
                "min_seconds": round(min(times_all), 1),
                "max_seconds": round(max(times_all), 1),
                "median_seconds": round(sorted(times_all)[len(times_all)//2], 1),
                "throughput_tasks_per_minute": round(task_count / (total_elapsed / 60), 1),
            },
            "costs": {
                "per_video_estimate": 0.332,
                "total_completed_cost": round(total_cost, 2),
                "avg_cost_per_successful_task": 0.332,
            },
            "step_analysis": {
                "steps_distribution": step_counts,
                "max_steps_possible": 9,
                "steps_with_errors": len(self.errors),
            },
            "error_analysis": {
                "total_errors": len(self.errors),
                "error_rate": round(len(self.errors) / task_count * 100, 1) if task_count > 0 else 0,
                "error_types": {},
                "sample_errors": [e["error"][:120] for e in self.errors[:5]],
            },
            "api_status": {
                "text_ai_available": self._check_provider("claude") or self._check_provider("openai") or self._check_provider("deepseek"),
                "image_ai_available": self._check_provider("openai"),  # DALL-E
                "video_ai_available": self._check_provider("seedance"),
                "tts_ai_available": self._check_provider("elevenlabs"),
            },
            "verdict": {},
        }

        # Error type classification
        for e in self.errors:
            etype = "unknown"
            msg = e["error"]
            if "API" in msg or "api" in msg or "key" in msg.lower():
                etype = "api_key_missing"
            elif "timeout" in msg.lower():
                etype = "timeout"
            elif "ffmpeg" in msg.lower() or "ffprobe" in msg.lower():
                etype = "ffmpeg_missing"
            elif "provider" in msg.lower():
                etype = "provider_unavailable"
            elif "memory" in msg.lower() or "MemoryError" in msg:
                etype = "memory"
            metrics["error_analysis"]["error_types"][etype] = \
                metrics["error_analysis"]["error_types"].get(etype, 0) + 1

        # Verdict
        sr = metrics["results"]["success_rate"]
        api = metrics["api_status"]
        if sr >= 95 and not metrics["error_analysis"]["error_types"]:
            verdict = "READY"
            verdict_text = "达到商业发布标准 — 所有核心指标通过"
        elif sr >= 80:
            verdict = "CONDITIONAL"
            verdict_text = "条件通过 — 需配置 API Key 后重新测试"
        else:
            verdict = "NOT_READY"
            verdict_text = "未达到发布标准 — 存在关键问题需修复"

        if not api["text_ai_available"]:
            verdict = "CONDITIONAL"
            verdict_text += "（文本 AI 未配置，脚本质量受限于模板模式）"
        if not api["image_ai_available"]:
            verdict_text += "（图像 AI 未配置，关键帧使用占位图）"

        metrics["verdict"] = {
            "status": verdict,
            "text": verdict_text,
            "api_keys_needed": [
                name for name, available in api.items() if not available
            ],
        }

        return metrics

    def _list_files(self, dir_path: str, extensions: list) -> list:
        """List files in a directory with given extensions."""
        d = self.project_root / dir_path
        if not d.exists():
            return []
        files = []
        for ext in extensions:
            files.extend([str(p) for p in d.glob(f"*{ext}")])
        return sorted(files)

    def _check_provider(self, name: str) -> bool:
        """Check if a provider has a configured API key."""
        try:
            from providers import create_provider
            p = create_provider(name)
            return p is not None and p.is_available()
        except Exception:
            return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="RC Stress Test")
    parser.add_argument("--tasks", type=int, default=100, help="Number of tasks (default: 100)")
    parser.add_argument("--concurrent", type=int, default=3, help="Max concurrent workers (default: 3)")
    args = parser.parse_args()

    runner = StressTestRunner()
    metrics = runner.run(task_count=args.tasks, max_concurrent=args.concurrent)

    # Save results
    out_path = Path(__file__).resolve().parent.parent / "output" / "rc_stress_test_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\n  Results saved to: {out_path}")

    # Print summary
    r = metrics["results"]
    t = metrics["timing"]
    c = metrics["costs"]
    v = metrics["verdict"]

    print(f"\n{'='*60}")
    print(f"  STRESS TEST SUMMARY")
    print(f"{'='*60}")
    print(f"  Tasks:      {r['total']}")
    print(f"  Completed:  {r['completed']} ({r['success_rate']}%)")
    print(f"  Failed:     {r['failed']} ({r['failure_rate']}%)")
    print(f"  Total time: {t['total_elapsed_seconds']:.1f}s")
    print(f"  Avg/task:   {t['avg_per_task_seconds']:.1f}s")
    print(f"  Throughput: {t['throughput_tasks_per_minute']:.1f} tasks/min")
    print(f"  Est. cost:  ${c['total_completed_cost']:.2f}")
    print(f"  Errors:     {metrics['error_analysis']['total_errors']}")
    print(f"{'='*60}")
    print(f"  VERDICT: {v['status']}")
    print(f"  {v['text']}")
    print(f"{'='*60}")

    return metrics


if __name__ == "__main__":
    main()
