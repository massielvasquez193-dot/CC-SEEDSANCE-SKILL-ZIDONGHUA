"""
TikTok AI Factory Pro — Batch Scheduler
=========================================
Task queue, worker pool, retry logic, and real-time stats.

Supports:
  - Configurable concurrency (1-10 parallel tasks)
  - Auto-retry on failure (3 attempts per task)
  - Crash recovery (batch_log.json)
  - Real-time dashboard stats
  - ETA calculation
"""

import json
import logging
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchTask:
    """A single video generation task in the batch."""
    task_id: str
    product_path: str
    character_path: str
    reference_video_path: str
    country: str = "美国"
    style: str = "TikTok UGC"
    status: TaskStatus = TaskStatus.QUEUED
    attempts: int = 0
    max_attempts: int = 3
    output_dir: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    video_path: Optional[str] = None
    cost_estimate: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class BatchStats:
    """Real-time batch statistics."""
    total: int = 0
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    retried: int = 0
    started_at: Optional[str] = None
    estimated_seconds: float = 0
    elapsed_seconds: float = 0

    @property
    def remaining(self) -> int:
        return self.queued + self.running

    @property
    def progress_pct(self) -> int:
        if self.total == 0:
            return 0
        done = self.completed + self.failed + self.skipped
        return int(done / self.total * 100)

    @property
    def eta_seconds(self) -> float:
        if self.completed == 0:
            return self.estimated_seconds
        avg_time = self.elapsed_seconds / self.completed
        return avg_time * self.remaining

    def to_dict(self) -> dict:
        return {
            "total": self.total, "queued": self.queued, "running": self.running,
            "completed": self.completed, "failed": self.failed, "skipped": self.skipped,
            "retried": self.retried, "remaining": self.remaining,
            "progress_pct": self.progress_pct,
            "started_at": self.started_at,
            "elapsed_seconds": self.elapsed_seconds,
            "eta_seconds": self.eta_seconds,
            "eta_str": str(timedelta(seconds=int(self.eta_seconds))),
        }


class BatchScheduler:
    """
    Task scheduler with worker pool for batch video generation.

    Not a real QThread to avoid PySide6 dependency — caller wraps in QThread.
    """

    MAX_CONCURRENT = 3
    RETRY_DELAY = 5  # seconds between retries
    LOG_PATH = None   # set by controller

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.tasks: List[BatchTask] = []
        self.task_queue = deque()
        self.stats = BatchStats()
        self._lock = threading.Lock()
        self._running = False
        self._cancelled = False
        self._active_workers = 0

        # Callbacks
        self.on_task_start: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None
        self.on_task_fail: Optional[Callable] = None
        self.on_stats_update: Optional[Callable] = None
        self.on_all_complete: Optional[Callable] = None
        self.on_log: Optional[Callable] = None

        # Per-task worker function (set by controller)
        self._worker_fn: Optional[Callable] = None

    def build_tasks(
        self,
        products: List[str],
        characters: List[str],
        reference_videos: List[str],
        country: str,
        style: str,
        videos_per_product: int,
        mode: str = "random",
    ) -> List[BatchTask]:
        """
        Build the task matrix from input file lists.

        Modes:
          - "random": Shuffle and randomly pair product + character + ref video
          - "fixed": Direct 1:1:1 pairing (requires equal counts)
          - "viral_clone": Each product gets ALL reference videos
        """
        import random

        tasks = []
        task_idx = 0

        if mode == "fixed":
            count = min(len(products), len(characters), len(reference_videos))
            for i in range(count):
                for v in range(videos_per_product):
                    task_idx += 1
                    tasks.append(BatchTask(
                        task_id=f"batch_{task_idx:04d}",
                        product_path=products[i],
                        character_path=characters[i],
                        reference_video_path=reference_videos[i],
                        country=country, style=style,
                    ))

        elif mode == "viral_clone":
            for p_idx, product in enumerate(products):
                for v_idx, ref_video in enumerate(reference_videos):
                    char = characters[v_idx % len(characters)]
                    for vid in range(videos_per_product):
                        task_idx += 1
                        tasks.append(BatchTask(
                            task_id=f"batch_{task_idx:04d}",
                            product_path=product,
                            character_path=char,
                            reference_video_path=ref_video,
                            country=country, style=style,
                        ))

        else:  # "random"
            rng = random.Random(42)  # seeded for reproducibility
            for p_idx, product in enumerate(products):
                # Pick random character and reference for each product
                char_pool = rng.sample(characters, min(3, len(characters)))
                ref_pool = rng.sample(reference_videos, min(videos_per_product, len(reference_videos)))
                for vid in range(videos_per_product):
                    task_idx += 1
                    char = char_pool[vid % len(char_pool)]
                    ref = ref_pool[vid % len(ref_pool)]
                    tasks.append(BatchTask(
                        task_id=f"batch_{task_idx:04d}",
                        product_path=product,
                        character_path=char,
                        reference_video_path=ref,
                        country=country, style=style,
                    ))

        # Deduplicate: avoid same product+character+ref combo
        seen = set()
        deduped = []
        for t in tasks:
            key = (t.product_path, t.character_path, t.reference_video_path)
            if key not in seen:
                seen.add(key)
                deduped.append(t)
            # else skip duplicate

        self._log(f"任务矩阵: {len(deduped)} 个任务 (去重前 {len(tasks)})")
        return deduped

    def start(self, worker_fn: Callable):
        """Start processing the task queue."""
        self._worker_fn = worker_fn
        self._running = True
        self._cancelled = False
        self.stats = BatchStats(
            total=len(self.tasks),
            queued=len(self.tasks),
            started_at=datetime.now().isoformat(),
        )

        # Fill the queue
        self.task_queue = deque(self.tasks)
        self._emit_stats()

        # Launch worker threads
        threads = []
        for _ in range(min(self.max_concurrent, len(self.tasks))):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            threads.append(t)

        # Wait for completion (non-blocking — caller should use callback)
        def wait_all():
            for t in threads:
                t.join(timeout=3600)
            self._running = False
            if self.on_all_complete:
                self.on_all_complete(self.stats.to_dict())
            self._save_log()

        threading.Thread(target=wait_all, daemon=True).start()

    def cancel(self):
        self._cancelled = True
        self._running = False
        with self._lock:
            self.task_queue.clear()
            for t in self.tasks:
                if t.status == TaskStatus.QUEUED:
                    t.status = TaskStatus.SKIPPED
        self._emit_stats()
        self._save_log()

    def _worker_loop(self):
        """Worker thread: pull tasks from queue and execute."""
        while self._running and not self._cancelled:
            task = None
            with self._lock:
                if self.task_queue:
                    task = self.task_queue.popleft()

            if task is None:
                time.sleep(0.5)
                continue

            self._execute_task(task)

        # Mark remaining as skipped if cancelled
        with self._lock:
            while self.task_queue:
                t = self.task_queue.popleft()
                t.status = TaskStatus.SKIPPED

    def _execute_task(self, task: BatchTask):
        """Execute a single task with retry logic."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        self._update_counts()
        if self.on_task_start:
            self.on_task_start(task.task_id)

        for attempt in range(1, task.max_attempts + 1):
            if self._cancelled:
                task.status = TaskStatus.SKIPPED
                return
            task.attempts = attempt

            try:
                if self._worker_fn:
                    result = self._worker_fn(task)
                    if result and result.get("status") == "completed":
                        task.status = TaskStatus.COMPLETED
                        task.output_dir = result.get("output_dir")
                        task.video_path = (
                            result.get("videos", [None])[0]
                            if result.get("videos") else None
                        )
                        task.completed_at = datetime.now().isoformat()
                        self._update_counts()
                        if self.on_task_complete:
                            self.on_task_complete(task.task_id, task.output_dir, task.video_path)
                        self._emit_stats()
                        return
                    else:
                        raise RuntimeError(result.get("error", "Unknown error") if result else "No result")
            except Exception as e:
                task.error = str(e)[:300]
                if attempt < task.max_attempts:
                    self._log(f"  ↻ {task.task_id} 重试 {attempt}/{task.max_attempts}: {e}")
                    with self._lock:
                        self.stats.retried += 1
                    time.sleep(self.RETRY_DELAY)
                else:
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now().isoformat()
                    self._update_counts()
                    if self.on_task_fail:
                        self.on_task_fail(task.task_id, task.error)
                    self._emit_stats()

    def _update_counts(self):
        """Refresh stats from current task states."""
        with self._lock:
            counts = {s: 0 for s in TaskStatus}
            for t in self.tasks:
                counts[t.status] += 1
            self.stats.queued = counts[TaskStatus.QUEUED]
            self.stats.running = counts[TaskStatus.RUNNING]
            self.stats.completed = counts[TaskStatus.COMPLETED]
            self.stats.failed = counts[TaskStatus.FAILED]
            self.stats.skipped = counts[TaskStatus.SKIPPED]
            if self.stats.started_at:
                elapsed = (datetime.now() - datetime.fromisoformat(self.stats.started_at)).total_seconds()
                self.stats.elapsed_seconds = elapsed

    def _emit_stats(self):
        if self.on_stats_update:
            self.on_stats_update(self.stats.to_dict())

    def _log(self, msg):
        logger.info(msg)
        if self.on_log:
            self.on_log(msg)

    def _save_log(self):
        """Persist batch log for crash recovery."""
        if not self.LOG_PATH:
            return
        try:
            log = {
                "saved_at": datetime.now().isoformat(),
                "stats": self.stats.to_dict(),
                "tasks": [t.to_dict() for t in self.tasks],
            }
            Path(self.LOG_PATH).write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save batch log: {e}")

    def recover_from_log(self, log_path: str) -> List[BatchTask]:
        """Recover incomplete tasks from a previous batch log."""
        try:
            data = json.loads(Path(log_path).read_text(encoding="utf-8"))
            tasks = []
            for td in data.get("tasks", []):
                t = BatchTask(
                    task_id=td["task_id"],
                    product_path=td["product_path"],
                    character_path=td["character_path"],
                    reference_video_path=td["reference_video_path"],
                    country=td.get("country", "美国"),
                    style=td.get("style", "TikTok UGC"),
                    attempts=td.get("attempts", 0),
                )
                t.status = TaskStatus(td.get("status", "queued"))
                t.output_dir = td.get("output_dir")
                t.error = td.get("error")
                if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED):
                    continue  # already done
                tasks.append(t)
            self._log(f"恢复 {len(tasks)} 个未完成任务")
            return tasks
        except Exception as e:
            self._log(f"恢复日志失败: {e}")
            return []

    # ---- Cost Estimation ----

    @staticmethod
    def estimate_costs(task_count: int, videos_per_product: int) -> Dict[str, Any]:
        """
        Estimate API costs for a batch.

        Pricing assumptions (per task/video):
          - GPT-4o script:        ~2000 tokens in, ~800 tokens out  → $0.005
          - GPT Image (DALL-E 3): 6 keyframes @ $0.04 each          → $0.24
          - ElevenLabs TTS:       25s audio                          → $0.05
          - Seedance:             6 segments @ ~$0.02 each           → $0.12
          Total per video:                                            → ~$0.42
        """
        per_video = {
            "GPT-4o (脚本+口播)": 0.005,
            "GPT Image (6关键帧)": 0.24,
            "ElevenLabs (TTS)": 0.05,
            "Seedance (6段)": 0.12,
        }
        per_video_total = sum(per_video.values())

        estimates = {
            "task_count": task_count,
            "estimated_videos": task_count * videos_per_product,
            "per_video_cost": per_video_total,
            "per_video_breakdown": per_video,
            "total_cost": task_count * per_video_total,
            "estimated_time_per_task_seconds": 90,
            "total_estimated_seconds": task_count * 90,
            "total_estimated_str": str(timedelta(seconds=task_count * 90)),
        }
        # With concurrency
        estimates["with_concurrency_seconds"] = task_count * 90 / 3
        estimates["with_concurrency_str"] = str(timedelta(seconds=int(task_count * 90 / 3)))

        return estimates
