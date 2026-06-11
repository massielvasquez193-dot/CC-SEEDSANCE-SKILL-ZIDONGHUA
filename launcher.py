#!/usr/bin/env python3
"""
TikTok AI Factory Pro — Launcher
=================================
Double-click to start GUI mode.
python launcher.py          → GUI mode
python launcher.py --cli    → CLI mode
"""

import sys
import os
from pathlib import Path

# Ensure project root in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Load .env before anything else
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


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
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        launch_cli()
    else:
        launch_gui()
