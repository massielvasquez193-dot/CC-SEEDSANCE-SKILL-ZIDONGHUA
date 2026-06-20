"""
TikTok AI Factory Pro — Auto Update System
===========================================
Modular update system with version checking, download, and safe installation.
"""

from .version_checker import VersionChecker, UpdateCheckResult, VersionInfo
from .download_manager import DownloadManager
from .update_installer import UpdateInstaller
from .update_manager import UpdateManager, check_for_updates

__all__ = [
    "VersionChecker",
    "UpdateCheckResult",
    "VersionInfo",
    "DownloadManager",
    "UpdateInstaller",
    "UpdateManager",
    "check_for_updates",
]
