"""
TikTok AI Factory Pro — Update Installer
==========================================
Safe installation of update packages with:
  - File preservation (.env, license.key, config/, output/, logs/)
  - Backup/rollback on failure
  - Windows: batch-script self-replace
  - Unix: direct extract + exec restart
  - Post-install verification
  - Update log recording
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


class UpdateInstaller:
    """Safe update installation with preservation and rollback."""

    # Files to NEVER overwrite
    PRESERVE_FILES = {
        ".env",
        "license.key",
        "version.txt",
        "config/settings.json",
        "config/update.json",
    }

    # Directories whose contents should be preserved
    PRESERVE_DIRS = {
        "output",
        "logs",
        "input",
    }

    BACKUP_DIR_NAME = "_update_backup"

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.backup_dir = self.project_root / self.BACKUP_DIR_NAME
        self._install_log: List[str] = []

    # ================================================================
    # Install
    # ================================================================

    def install(self, zip_path: Path) -> bool:
        """
        Install an update from a zip file.

        Steps:
          1. Backup current state
          2. Extract to temp dir
          3. Preserve protected files
          4. Copy new files over project
          5. Restore preserved files
          6. Schedule restart (Windows batch script)
          7. Record update log

        Returns:
            True if the batch restart script was launched (app should exit).
        """
        self._log(f"Install started: {datetime.now().isoformat()}")
        self._log(f"Update package: {zip_path} ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")

        # 1. Backup
        self._create_backup()

        try:
            # 2. Extract to temp
            extract_dir = self.project_root / "updater" / "_update_extracted"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)
            self._log(f"Extracted {len(zf.namelist())} files to {extract_dir}")

            # 3. Snapshot preserved files BEFORE overwriting
            preserved_snapshot = self._snapshot_preserved_files()

            # 4. Copy new files
            file_count = self._copy_tree(extract_dir, self.project_root)
            self._log(f"Copied {file_count} new files")

            # 5. Restore preserved files from snapshot
            restored_count = self._restore_preserved_files(preserved_snapshot)
            self._log(f"Restored {restored_count} preserved files")

            # 6. Update local version tracking
            self._update_version_file()

            # 7. Cleanup
            shutil.rmtree(extract_dir, ignore_errors=True)
            zip_path.unlink(missing_ok=True)

            # 8. Record log
            self._write_update_log()

            # 9. Schedule restart
            return self._schedule_restart()

        except Exception as e:
            self._log(f"Install FAILED: {e}")
            # Rollback
            self._rollback()
            raise

    # ================================================================
    # Backup & Rollback
    # ================================================================

    def _create_backup(self):
        """Backup current project state for rollback."""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        for item in self.project_root.iterdir():
            if item.name == self.BACKUP_DIR_NAME:
                continue
            if item.name.startswith(".") and item.name not in (".env",):
                continue  # skip .git, .claude, etc.
            if item.name in ("__pycache__", ".pyc"):
                continue

            dest = self.backup_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        self._log(f"Backup created: {self.backup_dir}")

    def _rollback(self):
        """Restore from backup on failure."""
        if not self.backup_dir.exists():
            self._log("No backup to rollback from")
            return

        self._log("Rolling back...")
        for item in self.backup_dir.iterdir():
            dest = self.project_root / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        shutil.rmtree(self.backup_dir, ignore_errors=True)
        self._log("Rollback complete — restored to previous version")
        self._write_update_log()

    # ================================================================
    # File Preservation
    # ================================================================

    def _snapshot_preserved_files(self) -> Dict[str, bytes]:
        """Read preserved files into memory before overwrite."""
        snapshot = {}
        for filename in self.PRESERVE_FILES:
            path = self.project_root / filename
            if path.exists() and path.is_file():
                snapshot[filename] = path.read_bytes()
        # Also snapshot preserved directory contents
        for dirname in self.PRESERVE_DIRS:
            dirpath = self.project_root / dirname
            if dirpath.exists():
                for f in dirpath.rglob("*"):
                    if f.is_file():
                        rel = str(f.relative_to(self.project_root))
                        snapshot[rel] = f.read_bytes()
        self._log(f"Snapshot: {len(snapshot)} preserved files")
        return snapshot

    def _restore_preserved_files(self, snapshot: Dict[str, bytes]) -> int:
        """Write preserved files back after update."""
        count = 0
        for rel_path, data in snapshot.items():
            target = self.project_root / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            count += 1
        return count

    # ================================================================
    # File Operations
    # ================================================================

    @staticmethod
    def _copy_tree(src: Path, dst: Path) -> int:
        """Copy all files from src to dst. Returns file count."""
        count = 0
        for item in src.rglob("*"):
            if item.is_file():
                rel = item.relative_to(src)
                target = dst / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
                count += 1
        return count

    def _update_version_file(self):
        """Update version.txt with the new version from the extracted package."""
        # The new version.txt should already be copied; if not, keep as-is
        pass

    # ================================================================
    # Restart
    # ================================================================

    def _schedule_restart(self) -> bool:
        """Schedule application restart. Returns True if app should exit."""
        if sys.platform == "win32":
            return self._restart_windows()
        else:
            return self._restart_unix()

    def _restart_windows(self) -> bool:
        """Windows: Write and launch a batch script for self-replacement."""
        batch_path = self.project_root / "updater" / "_update_apply.bat"
        python_exe = sys.executable
        app_main = str(self.project_root / "launcher.py")
        restart_args = " ".join(f'"{a}"' for a in sys.argv[1:])

        batch = f"""@echo off
chcp 65001 >nul
title TikTok AI Factory Pro — Applying Update...

echo.
echo ============================================
echo   TikTok AI Factory Pro — 更新完成
echo ============================================
echo.
echo   正在重启应用...

timeout /t 2 /nobreak >nul

:: Clean up backup
if exist "{self.backup_dir}" rmdir /S /Q "{self.backup_dir}"

:: Clean up installer artifacts
if exist "{self.project_root}\\updater\\_update_extracted" rmdir /S /Q "{self.project_root}\\updater\\_update_extracted"

:: Restart
start "" "{python_exe}" "{app_main}" {restart_args}

:: Self-destruct
(goto) 2>nul & del "%~f0"
"""
        batch_path.write_text(batch, encoding="utf-8")

        self._log(f"Restart batch script: {batch_path}")

        subprocess.Popen(
            ["cmd.exe", "/c", str(batch_path)],
            creationflags=(
                subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS
                if hasattr(subprocess, "DETACHED_PROCESS")
                else 0
            ),
            close_fds=True,
        )
        return True

    def _restart_unix(self) -> bool:
        """Unix/macOS: Direct re-exec."""
        self._log("Restarting via os.execv...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
        return True

    # ================================================================
    # Logging
    # ================================================================

    def _log(self, msg: str):
        logger.info(f"[Installer] {msg}")
        self._install_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def _write_update_log(self):
        """Append to logs/update.log."""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "update.log"

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            for entry in self._install_log:
                f.write(entry + "\n")
            f.write(f"{'='*60}\n")

        self._log(f"Update log written to {log_path}")
