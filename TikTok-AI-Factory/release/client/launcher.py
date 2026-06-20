#!/usr/bin/env python3
"""
TikTok AI Factory Pro — Launcher
=================================
Double-click to start GUI mode.
python launcher.py          → GUI mode
python launcher.py --cli    → CLI mode
python launcher.py --skip-update  → Skip auto-update check
"""

import sys
import os
from pathlib import Path

# Ensure project root in path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env before anything else
try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


def check_for_updates():
    """Check for updates on startup (unless --skip-update is passed)."""
    if "--skip-update" in sys.argv:
        sys.argv.remove("--skip-update")
        return

    # Honor env var to disable update check
    if os.getenv("TIKTOK_FACTORY_SKIP_UPDATE", "").lower() in ("true", "1", "yes"):
        return

    # Don't check in dev mode
    if os.getenv("TIKTOK_FACTORY_DEV_MODE", "").lower() in ("true", "1", "yes"):
        return

    try:
        from updater import check_for_updates as do_check
        updated = do_check(PROJECT_ROOT, silent=False)
        if updated:
            # The update dialog already handles exit;
            # if we get here with True, exit cleanly.
            sys.exit(0)
    except Exception as e:
        # Never let update failure block startup
        print(f"[Updater] 更新检查失败（不影响启动）: {e}")


def launch_gui():
    """Launch the PySide6 GUI"""
    try:
        from PySide6.QtWidgets import QApplication
        from app.gui.gui import main as gui_main
        gui_main()
    except ImportError:
        print("PySide6 not installed. Install with: pip install PySide6")
        print("Falling back to CLI mode...")
        launch_cli()


def launch_cli():
    """Launch CLI mode"""
    import run_factory
    # Pass remaining args to CLI
    sys.argv = [sys.argv[0]] + sys.argv[2:] if len(sys.argv) > 2 else [sys.argv[0]]
    # Simulate CLI run
    print("Starting CLI mode...")
    import subprocess
    subprocess.run([sys.executable, "run_factory.py"] + sys.argv[1:], cwd=Path(__file__).resolve().parent)


if __name__ == "__main__":
    # Auto-update check before launch
    check_for_updates()

    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        launch_cli()
    else:
        launch_gui()
