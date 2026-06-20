"""
TikTok AI Video Factory - 批量任务队列管理
支持无限批量任务、状态追踪、dashboard生成、去重
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from itertools import product
from typing import Optional

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)


class Task:
    """单个任务"""

    def __init__(
        self,
        task_id: str,
        product_image: Path,
        reference_video: Path,
        character_image: Path,
        output_dir: Path,
    ):
        self.task_id = task_id
        self.product_image = product_image
        self.reference_video = reference_video
        self.character_image = character_image
        self.output_dir = output_dir
        self.status = "pending"
        self.started_at = None
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.error = None
        self.output_files = []
        self.duration_seconds = 0.0
        self._hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """计算任务唯一哈希 (用于去重)"""
        raw = f"{self.product_image.name}|{self.reference_video.name}|{self.character_image.name}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    @property
    def dedup_key(self) -> str:
        return self._hash

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "dedup_key": self._hash,
            "product_image": self.product_image.name,
            "reference_video": self.reference_video.name,
            "character_image": self.character_image.name,
            "output_dir": str(self.output_dir),
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "output_files": self.output_files,
        }

    def mark_running(self):
        self.status = "running"
        self.started_at = datetime.now().isoformat()

    def mark_completed(self):
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()
        if self.started_at:
            try:
                start = datetime.fromisoformat(self.started_at)
                end = datetime.fromisoformat(self.completed_at)
                self.duration_seconds = round((end - start).total_seconds(), 1)
            except Exception:
                pass
        if self.output_dir.exists():
            self.output_files = sorted([
                f.name for f in self.output_dir.iterdir() if f.is_file()
            ])

    def mark_failed(self, error: str):
        self.status = "failed"
        self.error = str(error)[:500]
        self.completed_at = datetime.now().isoformat()
        if self.started_at:
            try:
                start = datetime.fromisoformat(self.started_at)
                end = datetime.fromisoformat(self.completed_at)
                self.duration_seconds = round((end - start).total_seconds(), 1)
            except Exception:
                pass
        if self.output_dir.exists():
            self.output_files = sorted([
                f.name for f in self.output_dir.iterdir() if f.is_file()
            ])


class TaskManager:
    """批量任务队列管理器"""

    def __init__(self):
        self.tasks: list[Task] = []
        self.task_counter = 0
        self._seen_hashes: set[str] = set()

    def build_tasks(
        self,
        products: list[Path],
        reference_videos: list[Path],
        characters: list[Path],
    ) -> list[Task]:
        """笛卡尔积组合"""
        self.tasks = []
        self.task_counter = 0
        self._seen_hashes = set()

        for vid, prod, char in product(reference_videos, products, characters):
            self._add_task(prod, vid, char)

        logger.info(f"[批量] 建立了 {len(self.tasks)} 个任务 (笛卡尔积)")
        self.save_dashboard()
        return self.tasks

    def build_tasks_one_to_one(
        self,
        products: list[Path],
        reference_videos: list[Path],
        characters: list[Path],
    ) -> list[Task]:
        """1对1配对 — 按索引匹配"""
        self.tasks = []
        self.task_counter = 0
        self._seen_hashes = set()

        max_len = max(len(reference_videos), len(products), len(characters))

        for i in range(max_len):
            vid = reference_videos[i % len(reference_videos)] if reference_videos else None
            prod = products[i % len(products)] if products else None
            char = characters[i % len(characters)] if characters else None

            if vid and prod and char:
                self._add_task(prod, vid, char)

        logger.info(f"[批量] 建立了 {len(self.tasks)} 个任务 (1对1配对)")
        self.save_dashboard()
        return self.tasks

    def _add_task(self, product_img: Path, video: Path, char_img: Path):
        """添加任务 (带去重)"""
        self.task_counter += 1
        task_id = f"task{self.task_counter:03d}"
        output_dir = OUTPUT_DIR / f"output{self.task_counter:03d}"

        task = Task(
            task_id=task_id,
            product_image=product_img,
            reference_video=video,
            character_image=char_img,
            output_dir=output_dir,
        )

        # 去重检查
        if task.dedup_key in self._seen_hashes:
            logger.debug(f"  跳过重复任务: {task.dedup_key}")
            self.task_counter -= 1
            return

        self._seen_hashes.add(task.dedup_key)
        self.tasks.append(task)

    def add_single_task(self, product_img: Path, video: Path, char_img: Path) -> Optional[Task]:
        """手动添加单个任务"""
        self._add_task(product_img, video, char_img)
        if self.tasks:
            t = self.tasks[-1]
            logger.info(f"[批量] 新增任务: {t.task_id}")
            self.save_dashboard()
            return t
        return None

    def get_pending_tasks(self) -> list[Task]:
        return [t for t in self.tasks if t.status == "pending"]

    def get_running_tasks(self) -> list[Task]:
        return [t for t in self.tasks if t.status == "running"]

    def get_task(self, task_id: str) -> Optional[Task]:
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    def get_summary(self) -> dict:
        status_count = {"pending": 0, "running": 0, "completed": 0, "failed": 0}
        for t in self.tasks:
            s = t.status
            status_count[s] = status_count.get(s, 0) + 1
        return {
            "total": len(self.tasks),
            **status_count,
            "updated_at": datetime.now().isoformat(),
        }

    def save_dashboard(self) -> Path:
        """保存 factory_dashboard.json"""
        dashboard = {
            "factory": "TikTok AI Video Factory",
            "updated_at": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "tasks": [t.to_dict() for t in self.tasks],
        }
        json_path = OUTPUT_DIR / "factory_dashboard.json"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dashboard, f, ensure_ascii=False, indent=2)
        return json_path

    def load_state(self) -> bool:
        """从 factory_dashboard.json 恢复任务状态"""
        state_path = OUTPUT_DIR / "factory_dashboard.json"
        if not state_path.exists():
            return False
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.tasks = []
            self._seen_hashes = set()
            for td in data.get("tasks", []):
                task = Task(
                    task_id=td["task_id"],
                    product_image=Path(td.get("product_image", "")),
                    reference_video=Path(td.get("reference_video", "")),
                    character_image=Path(td.get("character_image", "")),
                    output_dir=Path(td.get("output_dir", "")),
                )
                task.status = td.get("status", "pending")
                task.created_at = td.get("created_at", "")
                task.completed_at = td.get("completed_at")
                task.error = td.get("error")
                self._seen_hashes.add(task.dedup_key)
                self.tasks.append(task)
            self.task_counter = len(self.tasks)
            logger.info(f"[批量] 从dashboard恢复 {len(self.tasks)} 个任务")
            return True
        except Exception as e:
            logger.warning(f"[批量] 恢复状态失败: {e}")
            return False
