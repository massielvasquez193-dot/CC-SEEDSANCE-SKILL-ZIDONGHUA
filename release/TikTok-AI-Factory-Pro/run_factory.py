#!/usr/bin/env python3
"""
TikTok AI Video Factory - 主入口
全自动TikTok AI视频生产工厂

用法:
    python run_factory.py                    # 全自动模式
    python run_factory.py --mode script      # 仅生成脚本
    python run_factory.py --mode storyboard  # 仅生成分镜
    python run_factory.py --mode prompt      # 仅生成Prompt
    python run_factory.py --mode single      # 单任务模式
    python run_factory.py --status           # 查看状态
    python run_factory.py --max-tasks 5      # 限制任务数
    python run_factory.py --pairing one_to_one  # 1对1配对模式

环境变量:
    TIKTOK_FACTORY_AI_PROVIDER   AI提供商 (openai/claude/deepseek/gemini)
    OPENAI_API_KEY               OpenAI API密钥
    ANTHROPIC_API_KEY            Claude API密钥
    DEEPSEEK_API_KEY             DeepSeek API密钥
    GEMINI_API_KEY               Gemini API密钥
"""

import sys
import time
import argparse
import logging
from pathlib import Path

# 加载 .env 文件 (必须在其他import之前)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    # python-dotenv 未安装，手动加载
    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        import os as _os
        for _line in _env_path.read_text(encoding="utf-8").split("\n"):
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _os.environ[_k.strip()] = _v.strip().strip('"').strip("'")

# 修复Windows GBK编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 确保项目根目录在Python路径中
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import LOGS_DIR, LOG_LEVEL, OUTPUT_DIR
from workflows.factory_workflow import FactoryWorkflow


def setup_logging():
    """配置日志"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOGS_DIR / "factory.log", encoding="utf-8"),
        ],
    )


def create_ai_client(provider: str = None):
    """
    创建AI Provider (新版统一接口)

    支持: openai | claude | gemini | deepseek | seedance | veo3 | jimeng | runway | kling
    """
    from config.settings import DEFAULT_AI_PROVIDER
    from providers import create_provider

    provider_name = provider or DEFAULT_AI_PROVIDER
    instance = create_provider(provider_name)

    if instance is None:
        logging.warning(
            f"Provider '{provider_name}' 不可用。"
            f"请设置 {provider_name.upper()}_API_KEY 环境变量或检查依赖库。"
        )
        return None

    logging.info(f"Provider '{provider_name}' 已就绪 (model={instance.model})")
    return instance


def safe_print(text):
    """安全打印，处理Windows编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def print_banner():
    """打印横幅"""
    banner = r"""
╔══════════════════════════════════════════════════════╗
║                                                      ║
║   ████████╗██╗██╗  ██╗████████╗ ██████╗ ██╗  ██╗     ║
║   ╚══██╔══╝██║██║ ██╔╝╚══██╔══╝██╔═══██╗██║ ██╔╝     ║
║      ██║   ██║█████╔╝    ██║   ██║   ██║█████╔╝      ║
║      ██║   ██║██╔═██╗    ██║   ██║   ██║██╔═██╗      ║
║      ██║   ██║██║  ██╗   ██║   ╚██████╔╝██║  ██╗     ║
║      ╚═╝   ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝     ║
║                                                      ║
║        AI Video Factory - 全自动视频生产工厂           ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
"""
    safe_print(banner)


def print_status(workflow: FactoryWorkflow):
    """打印状态"""
    status = workflow.show_status()
    safe_print("\n[*] 当前状态:")
    safe_print(f"  产品图片: {status['input_files']['products']} 个")
    safe_print(f"  参考视频: {status['input_files']['videos']} 个")
    safe_print(f"  人物图片: {status['input_files']['characters']} 个")
    safe_print(f"  输出目录: {status['output_dir']}")
    safe_print(f"  就绪状态: {'[OK] 可以启动' if status['ready'] else '[X] 请放入所有必需的输入文件'}")
    safe_print("")

    # Provider信息
    provider_info = status.get("provider", {})
    if provider_info:
        caps = provider_info.get("capabilities", {})
        safe_print(f"  Provider: {provider_info.get('name', 'N/A')} | model={caps.get('model', 'N/A')}")
        safe_print(f"  能力: text={caps.get('supports_text', False)} image={caps.get('supports_image', False)} video={caps.get('supports_video', False)}")

    if not status["ready"]:
        safe_print("[>] 请将文件放入以下目录:")
        safe_print("  input/products/        - 产品图片 (.jpg/.png/.webp)")
        safe_print("  input/reference_videos/ - 参考视频 (.mp4/.mov)")
        safe_print("  input/characters/      - 人物图片 (.jpg/.png/.webp)")
        safe_print("")


def _run_watch_mode(workflow, args):
    """启动 Watch Mode"""
    from app.watcher import WatchMode

    safe_print("")
    safe_print("=" * 50)
    safe_print("  Watch Mode - 文件监控模式")
    safe_print("=" * 50)
    safe_print(f"  监控目录: input/")
    safe_print(f"  - input/products/       产品图片")
    safe_print(f"  - input/reference_videos/ 参考视频")
    safe_print(f"  - input/characters/     人物图片")
    safe_print(f"  轮询间隔: {args.interval}s")
    safe_print(f"  冷却时间: {args.cooldown}s")
    safe_print(f"  自动执行: {'否' if args.no_auto else '是'}")
    if args.use_watchdog:
        safe_print(f"  模式: watchdog (事件驱动)")
    else:
        safe_print(f"  模式: polling (轮询)")
    safe_print("=" * 50)
    safe_print("")
    safe_print("[>] 开始监控... 将文件放入 input/ 目录即可自动处理")
    safe_print("[>] 按 Ctrl+C 停止监控")
    safe_print("")

    # 创建 WatchMode
    watcher = WatchMode(
        pipeline=workflow.pipeline,
        poll_interval=args.interval,
        cooldown=args.cooldown,
        auto_execute=not args.no_auto,
        use_watchdog=args.use_watchdog,
    )

    # 设置事件回调
    def on_new_files(events):
        for e in events:
            safe_print(f"  [NEW] {e.event_type}: {e.file_path.name}")

    def on_task_created(tasks):
        for t in tasks:
            safe_print(f"  [TASK] {t.task_id}: {t.product_image.name} + {t.reference_video.name} + {t.character_image.name}")

    def on_task_completed(task):
        safe_print(f"  [DONE] {task.task_id} → {task.output_dir}")
        safe_print(f"         product.json | character.json | script.md | storyboard.png | seedance.txt | veo3.txt | subtitle.srt | summary.json")

    watcher.on_new_files = on_new_files
    watcher.on_task_created = on_task_created
    watcher.on_task_completed = on_task_completed

    # 先执行一次扫描，处理已有文件
    safe_print("[>] 初始扫描...")
    existing = watcher.force_scan_now()
    if existing:
        safe_print(f"[>] 初始扫描完成: 处理了 {len(existing)} 个任务")
    else:
        safe_print("[>] 初始扫描完成: 无待处理文件")

    # 启动监控
    watcher.start()

    # 保持主线程运行
    try:
        while watcher.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        safe_print("\n[>] 收到中断信号，正在停止...")
        watcher.stop()
        status = watcher.get_status()
        safe_print(f"[OK] Watch Mode 已停止")
        safe_print(f"     共创建任务: {status['total_tasks_created']}")
        safe_print(f"     共完成任务: {status['total_tasks_executed']}")
        safe_print(f"     已处理文件: {status['processed_files']}")


def _run_force_scan(workflow):
    """强制执行一次扫描"""
    from app.watcher import WatchMode

    safe_print("[>] 强制执行扫描...")
    watcher = WatchMode(
        pipeline=workflow.pipeline,
        auto_execute=True,
    )
    tasks = watcher.force_scan_now()
    if tasks:
        safe_print(f"[OK] 扫描完成: 处理了 {len(tasks)} 个任务")
        for t in tasks:
            safe_print(f"  {t.task_id} → {t.output_dir}")
    else:
        safe_print("[>] 扫描完成: 无新文件需要处理")


def main():
    parser = argparse.ArgumentParser(
        description="TikTok AI Video Factory - 全自动视频生产工厂",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_factory.py                     # 全自动运行
  python run_factory.py --status            # 查看状态
  python run_factory.py --watch             # Watch Mode 持续监控
  python run_factory.py --watch --interval 5  # 每5秒扫描一次
  python run_factory.py --watch --no-auto   # 监控但不自动执行
  python run_factory.py --max-tasks 3       # 最多处理3个任务
  python run_factory.py --pairing one_to_one # 1对1配对
  python run_factory.py --provider openai   # 使用OpenAI
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["full_auto", "script", "storyboard", "prompt", "single"],
        default="full_auto",
        help="工作流模式 (默认: full_auto)",
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="仅显示当前状态",
    )
    parser.add_argument(
        "--max-tasks", "-n",
        type=int,
        default=None,
        help="最大处理任务数",
    )
    parser.add_argument(
        "--pairing",
        choices=["cartesian", "one_to_one"],
        default="one_to_one",
        help="任务配对模式 (默认: one_to_one 批量模式)",
    )
    parser.add_argument(
        "--provider", "-p",
        type=str,
        default=None,
        help="AI提供商 (openai/claude/deepseek/gemini)",
    )
    parser.add_argument(
        "--product",
        type=str,
        help="单任务模式: 产品图片路径",
    )
    parser.add_argument(
        "--video",
        type=str,
        help="单任务模式: 参考视频路径",
    )
    parser.add_argument(
        "--character",
        type=str,
        help="单任务模式: 人物图片路径",
    )
    parser.add_argument(
        "--task-id",
        type=str,
        default="custom_task",
        help="单任务模式: 任务ID",
    )

    # Watch Mode 参数
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="启动 Watch Mode: 持续监控input目录，自动检测新文件并执行",
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=3.0,
        help="Watch Mode 轮询间隔(秒，默认3.0)",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=10.0,
        help="Watch Mode 冷却时间(秒，默认10.0)",
    )
    parser.add_argument(
        "--no-auto",
        action="store_true",
        help="Watch Mode 下检测到新文件但不自动执行",
    )
    parser.add_argument(
        "--use-watchdog",
        action="store_true",
        help="使用watchdog库替代轮询 (需 pip install watchdog)",
    )
    parser.add_argument(
        "--force-scan",
        action="store_true",
        help="强制执行一次扫描 (可与 --watch 组合)",
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)

    # 打印横幅
    print_banner()

    # 创建Provider (新版统一接口)
    provider = create_ai_client(args.provider)
    provider_name = args.provider or "default"

    if provider:
        caps = provider.get_capabilities()
        safe_print(
            f"[AI] Provider: {provider_name} | model={provider.model} | "
            f"text={caps['supports_text']} image={caps['supports_image']} "
            f"video={caps['supports_video']} vision={caps['supports_vision']}"
        )
    else:
        safe_print("[!] Provider不可用，将使用模板生成模式")

    # 创建工作流 (传入provider)
    workflow = FactoryWorkflow(
        ai_client=provider,
        provider_name=provider_name,
        provider_instance=provider,
    )

    # Watch Mode
    if args.watch:
        _run_watch_mode(workflow, args)
        return

    # 仅显示状态
    if args.status:
        print_status(workflow)
        return

    # 强制执行一次扫描
    if args.force_scan:
        _run_force_scan(workflow)
        return

    # 根据模式运行
    if args.mode == "full_auto":
        print_status(workflow)
        safe_print(f"[>] 启动全自动模式 (配对: {args.pairing})...")
        safe_print(f"[>] 最大任务数: {args.max_tasks or '无限制'}")

        workflow.pipeline.pairing_mode = args.pairing
        result = workflow.run_full_auto(max_tasks=args.max_tasks)

        safe_print("\n[OK] 工厂运行完成!")
        summary = result.get("summary", {})
        safe_print(f"   总任务: {summary.get('total', 0)}")
        safe_print(f"   完成: {summary.get('completed', 0)}")
        safe_print(f"   失败: {summary.get('failed', 0)}")
        safe_print(f"   输出目录: {OUTPUT_DIR}")

    elif args.mode == "script":
        if not all([args.product, args.video, args.character]):
            safe_print("[X] 脚本模式需要 --product, --video, --character 参数")
            sys.exit(1)
        script = workflow.run_script_only(args.product, args.video, args.character)
        safe_print(script)

    elif args.mode == "storyboard":
        if not all([args.product, args.video, args.character]):
            safe_print("[X] 分镜模式需要 --product, --video, --character 参数")
            sys.exit(1)
        # 先生成脚本
        script = workflow.run_script_only(args.product, args.video, args.character)
        storyboard = workflow.run_storyboard_only(script, args.product, args.character, args.video)
        safe_print(storyboard)

    elif args.mode == "prompt":
        if not all([args.product, args.video, args.character]):
            safe_print("[X] Prompt模式需要 --product, --video, --character 参数")
            sys.exit(1)
        script = workflow.run_script_only(args.product, args.video, args.character)
        storyboard = workflow.run_storyboard_only(script, args.product, args.character, args.video)
        prompts = workflow.run_prompt_only(storyboard, args.product, args.character)
        for k, v in prompts.items():
            safe_print(f"\n{'='*60}")
            safe_print(f"  {k.upper()}")
            safe_print(f"{'='*60}")
            safe_print(v[:500] + "..." if len(v) > 500 else v)

    elif args.mode == "single":
        if not all([args.product, args.video, args.character]):
            safe_print("[X] 单任务模式需要 --product, --video, --character 参数")
            sys.exit(1)
        result = workflow.run_single_task(
            args.product, args.video, args.character, args.task_id
        )
        safe_print(f"\n[OK] 单任务完成: {result}")


if __name__ == "__main__":
    main()
