"""
TikTok AI Factory Pro — Auto Update Manager (Orchestrator)
=============================================================
Coordinates version_checker → download_manager → update_installer

Flow:
  1. VersionChecker fetches remote version.json
  2. Compare versions → prompt user (GUI/CLI)
  3. DownloadManager downloads update.zip with retry + SHA256
  4. UpdateInstaller extracts, preserves files, schedules restart

Supports:
  - PySide6 GUI dialog with release notes + progress
  - tkinter fallback
  - CLI mode
  - Force update (blocking)
  - Graceful error handling (no crash on network failure)
"""

import json
import logging
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from .version_checker import VersionChecker, UpdateCheckResult

logger = logging.getLogger(__name__)


class UpdateManager:
    """Master orchestrator for the auto-update system."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.checker = VersionChecker(self.project_root)
        self._last_result: Optional[UpdateCheckResult] = None

    def check_for_updates(self, silent: bool = False) -> Optional[UpdateCheckResult]:
        """
        Check if a newer version is available.

        Args:
            silent: If True, only log — no UI shown

        Returns:
            UpdateCheckResult if update available, None otherwise
        """
        result = self.checker.check()
        self._last_result = result

        if result.error:
            if not silent:
                logger.debug(f"[Updater] Check failed: {result.error}")
            return None

        if not result.update_available:
            if not silent:
                logger.info(
                    f"[Updater] Up-to-date — "
                    f"local={result.local_version}, remote={result.remote_version}"
                )
            return None

        logger.info(
            f"[Updater] Update available: "
            f"{result.local_version} → {result.remote_version}"
            + (" [FORCED]" if result.force_update else "")
        )
        return result

    def prompt_and_update(self, result: UpdateCheckResult = None) -> bool:
        """
        Show update dialog and execute the full update if user accepts.

        Returns:
            True if the update was applied (app should exit for restart).
        """
        if result is None:
            result = self._last_result
        if result is None or not result.update_available:
            return False

        # Show dialog
        accepted = self._show_dialog(result)
        if not accepted:
            return False

        # Execute update
        try:
            return self._execute_update(result)
        except Exception as e:
            logger.error(f"[Updater] Update failed: {e}")
            self._show_error(str(e))
            return False

    def _execute_update(self, result: UpdateCheckResult) -> bool:
        """Download + verify + install + restart."""
        from .download_manager import DownloadManager
        from .update_installer import UpdateInstaller

        # 1. Download
        logger.info("[Updater] Starting download...")
        dm = DownloadManager()

        # Progress tracking for GUI
        last_pct = [0]

        def progress_cb(received, total, speed, eta):
            if total > 0:
                pct = int(received / total * 100)
                if pct != last_pct[0]:
                    last_pct[0] = pct
                    self._on_download_progress(received, total, speed, eta)

        self._on_download_start(result.download_url, result.file_size_mb)

        zip_path = dm.download(
            url=result.download_url,
            expected_sha256=result.sha256,
            progress_callback=progress_cb,
        )

        self._on_download_complete(zip_path)

        # 2. Install
        logger.info("[Updater] Installing update...")
        installer = UpdateInstaller(self.project_root)
        should_exit = installer.install(zip_path)

        if should_exit:
            self._on_install_complete()

        # 3. Exit for restart
        if should_exit:
            sys.exit(0)

        return True

    # ================================================================
    # GUI Dialog
    # ================================================================

    def _show_dialog(self, result: UpdateCheckResult) -> bool:
        """Show update dialog. Returns True if user accepts."""
        # Try PySide6
        accepted = self._try_pyside6_dialog(result)
        if accepted is not None:
            return accepted
        # Try tkinter
        accepted = self._try_tkinter_dialog(result)
        if accepted is not None:
            return accepted
        # CLI fallback
        return self._cli_prompt(result)

    def _try_pyside6_dialog(self, result: UpdateCheckResult):
        try:
            from PySide6.QtWidgets import (
                QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                QLabel, QPushButton, QProgressBar, QTextEdit,
            )
            from PySide6.QtCore import Qt
        except ImportError:
            return None

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv[:1])

        dlg = QDialog()
        dlg.setWindowTitle("发现新版本 — TikTok AI Factory Pro")
        dlg.setFixedSize(500, 420)
        dlg.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel#title { font-size: 18px; font-weight: bold; color: #e94560; }
            QLabel#info { font-size: 13px; color: #cccccc; background-color: #16213e;
                border-radius: 6px; padding: 12px; }
            QPushButton#btn_update { background-color: #e94560; color: white; border: none;
                border-radius: 6px; padding: 10px 24px; font-size: 14px; font-weight: bold; }
            QPushButton#btn_update:hover { background-color: #ff6b81; }
            QPushButton#btn_cancel { background: transparent; color: #888; border: 1px solid #444;
                border-radius: 6px; padding: 10px 24px; font-size: 13px; }
            QPushButton#btn_cancel:hover { background: #2a2a4a; }
            QProgressBar { border: none; border-radius: 4px; background: #16213e; height: 22px; }
            QProgressBar::chunk { background: #e94560; border-radius: 4px; }
            QTextEdit { background: #0d1117; color: #c9d1d9; border: 1px solid #30363d;
                border-radius: 6px; font-size: 12px; }
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Title
        title = QLabel("🎉 发现新版本" if not result.force_update else "⚠️ 必须更新")
        title.setObjectName("title")
        layout.addWidget(title)

        # Version info
        force_note = (
            "<br><span style='color:#ff6b81;font-weight:bold;'>⚠ 当前版本已停止支持，必须更新后才能继续使用。</span>"
            if result.force_update else ""
        )
        info = QLabel(
            f"<b>当前版本：</b>{result.local_version}<br>"
            f"<b>最新版本：</b>{result.remote_version}<br>"
            f"<b>发布日期：</b>{result.release_date}"
            f"{force_note}"
        )
        info.setObjectName("info")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Release notes
        if result.release_notes:
            notes_label = QLabel("更新内容：")
            notes_label.setStyleSheet("font-size: 12px; color: #8b949e; font-weight: bold;")
            layout.addWidget(notes_label)

            notes_text = QTextEdit()
            notes_text.setReadOnly(True)
            notes_text.setMaximumHeight(100)
            notes_html = "".join(f"• {n}<br>" for n in result.release_notes)
            notes_text.setHtml(notes_html)
            layout.addWidget(notes_text)

        # Progress bar (hidden)
        self._dlg_progress = QProgressBar()
        self._dlg_progress.setVisible(False)
        layout.addWidget(self._dlg_progress)

        self._dlg_status = QLabel("")
        self._dlg_status.setStyleSheet("font-size: 11px; color: #8b949e;")
        self._dlg_status.setVisible(False)
        layout.addWidget(self._dlg_status)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._dlg_cancel_btn = QPushButton("稍后提醒")
        self._dlg_cancel_btn.setObjectName("btn_cancel")
        if result.force_update:
            self._dlg_cancel_btn.setEnabled(False)
            self._dlg_cancel_btn.setText("（必须更新）")
        self._dlg_cancel_btn.clicked.connect(dlg.reject)
        btn_layout.addWidget(self._dlg_cancel_btn)

        self._dlg_update_btn = QPushButton("🚀 立即更新")
        self._dlg_update_btn.setObjectName("btn_update")
        btn_layout.addWidget(self._dlg_update_btn)
        layout.addLayout(btn_layout)

        # Connect signals
        self._dlg_accepted = False

        def on_accept():
            self._dlg_accepted = True
            dlg.accept()

        self._dlg_update_btn.clicked.connect(on_accept)
        # Override progress callbacks for this dialog
        self._orig_progress_cb = None
        self._orig_dl_start = None
        self._orig_dl_done = None
        self._orig_install_done = None

        # Store refs for callbacks during download
        self._dlg = dlg

        dlg.exec()

        return self._dlg_accepted

    def _try_tkinter_dialog(self, result: UpdateCheckResult):
        try:
            import tkinter as tk
            from tkinter import messagebox, ttk
        except ImportError:
            return None

        root = tk.Tk()
        root.title("发现新版本 — TikTok AI Factory Pro")
        root.geometry("460x340")
        root.resizable(False, False)
        root.configure(bg="#1a1a2e")

        accepted = [False]

        tk.Label(
            root,
            text="⚠️ 必须更新" if result.force_update else "🎉 发现新版本",
            font=("Microsoft YaHei", 14, "bold"),
            fg="#e94560", bg="#1a1a2e",
        ).pack(pady=(20, 10))

        info = (
            f"当前版本：{result.local_version}\n"
            f"最新版本：{result.remote_version}\n"
            f"发布日期：{result.release_date}"
        )
        if result.force_update:
            info += "\n\n⚠ 当前版本已停止支持，必须更新后才能继续使用。"

        tk.Label(
            root, text=info,
            font=("Microsoft YaHei", 11),
            fg="#cccccc", bg="#1a1a2e", justify="left",
        ).pack(pady=10)

        if result.release_notes:
            tk.Label(
                root, text="更新内容：",
                font=("Microsoft YaHei", 10, "bold"),
                fg="#8b949e", bg="#1a1a2e",
            ).pack(anchor="w", padx=40)
            for note in result.release_notes:
                tk.Label(
                    root, text=f"• {note}",
                    font=("Microsoft YaHei", 10),
                    fg="#8b949e", bg="#1a1a2e",
                ).pack(anchor="w", padx=60)

        btn_frame = tk.Frame(root, bg="#1a1a2e")
        btn_frame.pack(pady=20)

        cancel_state = "normal" if not result.force_update else "disabled"
        tk.Button(
            btn_frame,
            text="稍后提醒" if not result.force_update else "（必须更新）",
            command=root.destroy,
            bg="#2a2a4a", fg="#888888",
            font=("Microsoft YaHei", 10),
            relief="flat", padx=16, pady=6,
            state=cancel_state,
        ).pack(side="left", padx=8)

        def do_update():
            accepted[0] = True
            root.destroy()

        tk.Button(
            btn_frame, text="🚀 立即更新",
            command=do_update,
            bg="#e94560", fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            relief="flat", padx=16, pady=6,
        ).pack(side="left", padx=8)

        root.mainloop()

        if accepted[0] and sys.platform == "win32":
            # proceed to download
            pass
        return accepted[0]

    def _cli_prompt(self, result: UpdateCheckResult) -> bool:
        print()
        print("=" * 55)
        print("  🎉 发现新版本" if not result.force_update else "  ⚠️ 必须更新")
        print("=" * 55)
        print(f"  当前版本：{result.local_version}")
        print(f"  最新版本：{result.remote_version}")
        print(f"  发布日期：{result.release_date}")
        if result.release_notes:
            print("  更新内容：")
            for n in result.release_notes:
                print(f"    • {n}")
        if result.force_update:
            print("  ⚠ 当前版本已停止支持，必须更新后才能继续使用。")
        print("=" * 55)

        if result.force_update:
            input("  按 Enter 开始更新...")
            return True

        try:
            answer = input("  是否立即更新? [Y/n]: ").strip().lower()
            return not answer or answer in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    # ================================================================
    # Callbacks (overridden for GUI progress)
    # ================================================================

    def _on_download_start(self, url: str, size_mb: float):
        if hasattr(self, "_dlg_progress") and self._dlg_progress:
            self._dlg_progress.setVisible(True)
            self._dlg_progress.setValue(0)
        if hasattr(self, "_dlg_status") and self._dlg_status:
            self._dlg_status.setVisible(True)
            self._dlg_status.setText("正在下载更新...")

    def _on_download_progress(self, received: int, total: int, speed: float, eta: float):
        if hasattr(self, "_dlg_progress") and self._dlg_progress:
            if total > 0:
                pct = int(received / total * 100)
                self._dlg_progress.setValue(pct)
                mb_r = received / 1024 / 1024
                mb_t = total / 1024 / 1024
                self._dlg_progress.setFormat(
                    f"{mb_r:.1f} / {mb_t:.1f} MB  ({pct}%)  {speed:.1f} MB/s"
                )

    def _on_download_complete(self, zip_path: Path):
        if hasattr(self, "_dlg_status") and self._dlg_status:
            self._dlg_status.setText("正在安装更新...")

    def _on_install_complete(self):
        if hasattr(self, "_dlg_status") and self._dlg_status:
            self._dlg_status.setText("更新完成！正在重启...")

    def _show_error(self, message: str):
        try:
            from PySide6.QtWidgets import QMessageBox, QApplication
            QMessageBox.critical(None, "更新失败", f"更新过程中出现错误：\n\n{message}")
        except ImportError:
            print(f"\n[ERROR] 更新失败: {message}\n")


# ================================================================
# Convenience entry point
# ================================================================

def check_for_updates(
    project_root: Path = None,
    silent: bool = False,
) -> bool:
    """
    Quick entry point for startup check.
    Returns True if update was applied (app should exit).
    """
    mgr = UpdateManager(project_root)
    result = mgr.check_for_updates(silent=silent)
    if result and result.update_available:
        return mgr.prompt_and_update(result)
    return False


# ================================================================
# CLI
# ================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser(description="TikTok AI Factory Pro — Update Manager")
    parser.add_argument("--check", action="store_true", help="Check for updates")
    parser.add_argument("--silent", action="store_true", help="Silent check (no UI)")
    args = parser.parse_args()

    if args.check:
        updated = check_for_updates(silent=args.silent)
        if not updated:
            print("No update needed.")
    else:
        parser.print_help()
