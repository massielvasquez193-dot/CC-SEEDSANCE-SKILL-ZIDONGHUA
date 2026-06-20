"""
TikTok AI Video Factory - Watch Mode (文件监控)
监听 input/ 目录，检测新产品/新视频/新人设 → 自动创建任务 → 自动执行
"""

import json
import logging
import threading
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
from queue import Queue

from config.settings import (
    PRODUCTS_DIR,
    REFERENCE_VIDEOS_DIR,
    CHARACTERS_DIR,
    OUTPUT_DIR,
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_VIDEO_FORMATS,
)

logger = logging.getLogger(__name__)


# ================================================================
# 文件状态追踪
# ================================================================
class FileStateTracker:
    """追踪已处理的文件，避免重复处理"""

    def __init__(self, state_file: Path = None):
        self.state_file = state_file or OUTPUT_DIR / ".watch_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.processed: dict[str, str] = {}  # file_path → file_hash
        self._load()

    def _load(self):
        """加载已处理文件记录"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.processed = json.load(f)
                logger.info(f"加载监控状态: {len(self.processed)} 个已处理文件")
            except Exception:
                self.processed = {}

    def _save(self):
        """保存已处理文件记录"""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.processed, f, ensure_ascii=False, indent=2)

    def _hash_file(self, filepath: Path) -> str:
        """计算文件哈希 (快速，只读前64KB)"""
        try:
            hasher = hashlib.sha256()
            with open(filepath, "rb") as f:
                hasher.update(f.read(65536))
            return hasher.hexdigest()
        except Exception:
            return ""

    def is_new(self, filepath: Path) -> bool:
        """检查文件是否是新的/未处理的"""
        path_str = str(filepath.resolve())
        current_hash = self._hash_file(filepath)

        if path_str not in self.processed:
            return True

        # 文件已记录但内容变化了 → 重新处理
        if self.processed[path_str] != current_hash:
            return True

        return False

    def mark_processed(self, filepath: Path):
        """标记文件已处理"""
        path_str = str(filepath.resolve())
        current_hash = self._hash_file(filepath)
        self.processed[path_str] = current_hash
        self._save()

    def get_new_files(self, directory: Path, extensions: tuple) -> list[Path]:
        """获取目录中的新文件"""
        new_files = []
        if not directory.exists():
            return new_files
        for ext in extensions:
            for f in directory.glob(f"*{ext}"):
                if self.is_new(f):
                    new_files.append(f)
            for f in directory.glob(f"*{ext.upper()}"):
                if self.is_new(f):
                    new_files.append(f)
        return sorted(set(new_files))


# ================================================================
# 事件队列
# ================================================================
class WatchEvent:
    """监控事件"""
    def __init__(self, event_type: str, file_path: Path, category: str, timestamp: float = None):
        self.event_type = event_type    # "new_product" | "new_video" | "new_character"
        self.file_path = file_path
        self.category = category        # "products" | "reference_videos" | "characters"
        self.timestamp = timestamp or time.time()

    def __repr__(self):
        return f"<WatchEvent {self.event_type}: {self.file_path.name}>"


# ================================================================
# 输入目录扫描器
# ================================================================
class InputScanner:
    """扫描 input/ 目录，检测所有输入文件"""

    def __init__(self, state_tracker: FileStateTracker):
        self.tracker = state_tracker

    def scan_all(self) -> list[WatchEvent]:
        """全量扫描，返回新文件事件列表"""
        events = []

        # 产品图片
        for f in self.tracker.get_new_files(PRODUCTS_DIR, SUPPORTED_IMAGE_FORMATS):
            events.append(WatchEvent("new_product", f, "products"))

        # 参考视频
        for f in self.tracker.get_new_files(REFERENCE_VIDEOS_DIR, SUPPORTED_VIDEO_FORMATS):
            events.append(WatchEvent("new_video", f, "reference_videos"))

        # 人物图片
        for f in self.tracker.get_new_files(CHARACTERS_DIR, SUPPORTED_IMAGE_FORMATS):
            events.append(WatchEvent("new_character", f, "characters"))

        return events

    def scan_category(self, category: str) -> list[WatchEvent]:
        """扫描特定类别"""
        cat_map = {
            "products": (PRODUCTS_DIR, SUPPORTED_IMAGE_FORMATS, "new_product"),
            "reference_videos": (REFERENCE_VIDEOS_DIR, SUPPORTED_VIDEO_FORMATS, "new_video"),
            "characters": (CHARACTERS_DIR, SUPPORTED_IMAGE_FORMATS, "new_character"),
        }
        if category not in cat_map:
            return []

        directory, extensions, event_type = cat_map[category]
        events = []
        for f in self.tracker.get_new_files(directory, extensions):
            events.append(WatchEvent(event_type, f, category))
        return events


# ================================================================
# 任务构建器
# ================================================================
class WatchTaskBuilder:
    """将检测到的新文件组合成可执行的任务"""

    def __init__(self, task_manager, file_scanner):
        from app.task_manager import TaskManager
        from app.scanner import FileScanner
        self.task_manager = task_manager
        self.file_scanner = file_scanner

    def build_from_events(self, events: list[WatchEvent]) -> list:
        """
        根据事件构建任务
        策略: 当3类文件都有新文件时，自动创建配对任务
        """
        new_products = []
        new_videos = []
        new_characters = []

        for evt in events:
            if evt.event_type == "new_product":
                new_products.append(evt.file_path)
            elif evt.event_type == "new_video":
                new_videos.append(evt.file_path)
            elif evt.event_type == "new_character":
                new_characters.append(evt.file_path)

        # 需要至少1个产品+1个视频+1个人物才能创建任务
        if not (new_products and new_videos and new_characters):
            return []

        # 1对1配对: 新文件按索引配对
        from app.task_manager import Task
        tasks = []
        max_n = max(len(new_videos), len(new_products), len(new_characters))

        # 获取当前任务计数
        current_count = len(self.task_manager.tasks)

        for i in range(max_n):
            vid = new_videos[i % len(new_videos)]
            prod = new_products[i % len(new_products)]
            char = new_characters[i % len(new_characters)]

            task_id = f"task{current_count + i + 1:03d}"
            output_dir = OUTPUT_DIR / f"output{current_count + i + 1:03d}"
            task = Task(
                task_id=task_id,
                product_image=prod,
                reference_video=vid,
                character_image=char,
                output_dir=output_dir,
            )
            self.task_manager.tasks.append(task)
            tasks.append(task)

        logger.info(f"从 {len(events)} 个事件构建了 {len(tasks)} 个新任务")
        return tasks


# ================================================================
# Watch Mode 主控制器
# ================================================================
class WatchMode:
    """
    文件监控主控制器

    功能:
    - 轮询或事件驱动检测 input/ 目录变化
    - 发现新文件 → 自动组合任务 → 自动执行
    - 支持去重（相同文件不重复处理）
    - 支持 cooldown（防抖，避免频繁触发）
    - 检测到所有3类输入就绪后自动触发
    """

    def __init__(
        self,
        pipeline,
        poll_interval: float = 3.0,
        cooldown: float = 10.0,
        auto_execute: bool = True,
        use_watchdog: bool = False,
    ):
        """
        Args:
            pipeline: FactoryPipeline 实例
            poll_interval: 轮询间隔(秒)
            cooldown: 任务执行冷却时间(秒)，避免重复触发
            auto_execute: 是否自动执行检测到的任务
            use_watchdog: 是否使用watchdog库 (否则使用轮询)
        """
        self.pipeline = pipeline
        self.poll_interval = poll_interval
        self.cooldown = cooldown
        self.auto_execute = auto_execute
        self.use_watchdog = use_watchdog

        # 内部组件
        self.tracker = FileStateTracker()
        self.scanner = InputScanner(self.tracker)
        self.builder = WatchTaskBuilder(
            task_manager=pipeline.task_manager,
            file_scanner=pipeline.scanner,
        )

        # 运行时状态
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_execution_time: float = 0
        self._event_buffer: list[WatchEvent] = []
        self._buffer_lock = threading.Lock()
        self._observer = None
        self._total_tasks_created = 0
        self._total_tasks_executed = 0

        # 回调
        self.on_new_files: Optional[Callable] = None
        self.on_task_created: Optional[Callable] = None
        self.on_task_completed: Optional[Callable] = None

    # ================================================================
    # 启动/停止
    # ================================================================
    def start(self):
        """启动监控"""
        if self._running:
            logger.warning("Watch Mode 已在运行中")
            return

        self._running = True
        logger.info("=" * 50)
        logger.info("Watch Mode 启动")
        logger.info(f"  监控目录: {PRODUCTS_DIR.parent}")
        logger.info(f"  轮询间隔: {self.poll_interval}s")
        logger.info(f"  冷却时间: {self.cooldown}s")
        logger.info(f"  自动执行: {self.auto_execute}")
        logger.info("=" * 50)

        if self.use_watchdog:
            self._start_watchdog()
        else:
            self._start_polling()

    def stop(self):
        """停止监控"""
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Watch Mode 已停止")

    def is_running(self) -> bool:
        return self._running

    # ================================================================
    # 轮询模式 (跨平台，不需要额外依赖)
    # ================================================================
    def _start_polling(self):
        """启动轮询线程"""
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="WatchMode")
        self._thread.start()

    def _poll_loop(self):
        """轮询循环"""
        while self._running:
            try:
                self._poll_once()
            except Exception as e:
                logger.error(f"Watch Mode 轮询异常: {e}", exc_info=True)
            time.sleep(self.poll_interval)

    def _poll_once(self):
        """单次轮询"""
        # 1. 扫描所有新文件
        events = self.scanner.scan_all()

        if not events:
            return

        logger.info(f"[Watch] 检测到 {len(events)} 个新文件")

        # 分类统计
        product_count = sum(1 for e in events if e.event_type == "new_product")
        video_count = sum(1 for e in events if e.event_type == "new_video")
        character_count = sum(1 for e in events if e.event_type == "new_character")
        logger.info(
            f"  新产品: {product_count} | 新视频: {video_count} | 新人设: {character_count}"
        )

        # 2. 触发回调
        if self.on_new_files:
            try:
                self.on_new_files(events)
            except Exception as e:
                logger.error(f"on_new_files 回调异常: {e}")

        # 3. 防抖：检查冷却时间
        now = time.time()
        if now - self._last_execution_time < self.cooldown:
            # 缓冲事件，等待冷却结束
            with self._buffer_lock:
                self._event_buffer.extend(events)
            logger.debug(f"冷却中 ({now - self._last_execution_time:.1f}s < {self.cooldown}s)，缓冲 {len(events)} 个事件")
            return

        # 4. 合并缓冲事件
        with self._buffer_lock:
            if self._event_buffer:
                events = self._event_buffer + events
                self._event_buffer = []
                # 去重
                seen = set()
                events_unique = []
                for e in events:
                    key = str(e.file_path)
                    if key not in seen:
                        seen.add(key)
                        events_unique.append(e)
                events = events_unique

        # 5. 检查是否满足任务创建条件
        if not self._can_create_task(events):
            # 条件不满足，放回缓冲
            with self._buffer_lock:
                self._event_buffer.extend(events)
            logger.debug(f"暂不满足任务条件，{len(events)} 个事件放回缓冲")
            return

        # 6. 创建任务
        tasks = self.builder.build_from_events(events)
        if not tasks:
            return

        self._total_tasks_created += len(tasks)
        logger.info(f"[Watch] 创建了 {len(tasks)} 个新任务")

        if self.on_task_created:
            try:
                self.on_task_created(tasks)
            except Exception as e:
                logger.error(f"on_task_created 回调异常: {e}")

        # 7. 标记文件为已处理
        for evt in events:
            self.tracker.mark_processed(evt.file_path)

        # 8. 自动执行
        if self.auto_execute:
            self._execute_tasks(tasks)

        self._last_execution_time = time.time()

    def _can_create_task(self, events: list[WatchEvent]) -> bool:
        """检查是否满足任务创建条件（至少要有产品+视频+人物各1个）"""
        has_product = any(e.event_type == "new_product" for e in events)
        has_video = any(e.event_type == "new_video" for e in events)
        has_character = any(e.event_type == "new_character" for e in events)

        # 如果有全部3类 → 立即创建任务
        if has_product and has_video and has_character:
            return True

        # 如果只有1-2类，等待30秒看看是否有补齐
        with self._buffer_lock:
            oldest = min((e.timestamp for e in events), default=time.time())
            waited = time.time() - oldest
            if waited > 30:
                logger.debug("等待新文件超时(30s)，仍然尝试创建任务")
                return has_product and has_video  # 至少需要产品和视频

        return False

    def _execute_tasks(self, tasks: list, force: bool = False):
        """执行任务列表"""
        for task in tasks:
            if not force and not self._running:
                break
            try:
                logger.info(f"[Watch] 执行任务: {task.task_id}")
                task.mark_running()
                self.pipeline._process_task(task)
                task.mark_completed()
                self._total_tasks_executed += 1
                logger.info(f"[Watch] 任务完成: {task.task_id} → {task.output_dir}")

                if self.on_task_completed:
                    try:
                        self.on_task_completed(task)
                    except Exception as e:
                        logger.error(f"on_task_completed 回调异常: {e}")

            except Exception as e:
                logger.error(f"[Watch] 任务 {task.task_id} 执行失败: {e}", exc_info=True)
                task.mark_failed(str(e))

    # ================================================================
    # Watchdog模式 (更高效的事件驱动，需要安装watchdog)
    # ================================================================
    def _start_watchdog(self):
        """启动watchdog监听"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            logger.warning("watchdog未安装，降级为轮询模式。安装: pip install watchdog")
            self._start_polling()
            return

        watch_dir = str(PRODUCTS_DIR.parent)

        class InputHandler(FileSystemEventHandler):
            def __init__(self, watcher):
                self.watcher = watcher

            def on_created(self, event):
                if event.is_directory:
                    return
                path = Path(event.src_path)
                self.watcher._on_file_event(path)

            def on_modified(self, event):
                if event.is_directory:
                    return
                path = Path(event.src_path)
                self.watcher._on_file_event(path)

        handler = InputHandler(self)
        self._observer = Observer()
        self._observer.schedule(handler, watch_dir, recursive=True)
        self._observer.start()
        logger.info(f"Watchdog 监听已启动: {watch_dir}")

        # 同时启动轮询线程作为补充（watchdog可能漏事件）
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="WatchMode-Fallback")
        self._thread.start()

    def _on_file_event(self, file_path: Path):
        """Watchdog事件回调"""
        # 检查是否是支持的文件类型
        if file_path.suffix.lower() in [f.lower() for f in SUPPORTED_IMAGE_FORMATS + SUPPORTED_VIDEO_FORMATS]:
            if not self.tracker.is_new(file_path):
                return

            # 确定类别
            try:
                rel = file_path.resolve().relative_to(PRODUCTS_DIR.parent.resolve())
                parent = str(rel.parent)
                if "products" in parent:
                    category = "products"
                    event_type = "new_product"
                elif "reference_videos" in parent:
                    category = "reference_videos"
                    event_type = "new_video"
                elif "characters" in parent:
                    category = "characters"
                    event_type = "new_character"
                else:
                    return
            except ValueError:
                return

            event = WatchEvent(event_type, file_path, category)
            with self._buffer_lock:
                self._event_buffer.append(event)
            logger.info(f"[Watchdog] 检测到: {event_type}: {file_path.name}")

    # ================================================================
    # 状态查询
    # ================================================================
    def get_status(self) -> dict:
        """获取监控状态"""
        with self._buffer_lock:
            buffered = len(self._event_buffer)

        return {
            "running": self._running,
            "mode": "watchdog" if self.use_watchdog and self._observer else "polling",
            "poll_interval": self.poll_interval,
            "cooldown": self.cooldown,
            "auto_execute": self.auto_execute,
            "processed_files": len(self.tracker.processed),
            "buffered_events": buffered,
            "total_tasks_created": self._total_tasks_created,
            "total_tasks_executed": self._total_tasks_executed,
            "last_execution": datetime.fromtimestamp(self._last_execution_time).isoformat() if self._last_execution_time else None,
        }

    def force_scan_now(self) -> list:
        """强制执行一次扫描并处理"""
        logger.info("[Watch] 强制执行扫描...")
        events = self.scanner.scan_all()
        if not events:
            logger.info("[Watch] 未发现新文件")
            return []

        tasks = self.builder.build_from_events(events)
        if tasks and self.auto_execute:
            self._execute_tasks(tasks, force=True)

        for evt in events:
            self.tracker.mark_processed(evt.file_path)

        return tasks
