"""
TikTok AI Factory Pro — Version Checker
=========================================
Fetches remote version.json, parses version info, compares with local.

Remote version.json format:
{
  "latest_version": "3.1.0",
  "release_date": "2026-06-15",
  "download_url": "https://your-domain/releases/TikTok-AI-Factory-Pro-v3.1.0.zip",
  "force_update": false,
  "sha256": "abc123...",
  "release_notes": ["优化GPT Image", "新增批量工厂", "修复Seedance"],
  "min_required_version": "3.0.0"
}
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import requests

logger = logging.getLogger(__name__)


@dataclass
class VersionInfo:
    """Parsed version information."""
    version: str
    release_date: str
    download_url: str
    force_update: bool = False
    sha256: str = ""
    release_notes: List[str] = field(default_factory=list)
    min_required_version: str = "0.0.0"
    channel: str = "stable"
    file_size_mb: float = 0.0


@dataclass
class UpdateCheckResult:
    """Result of an update check."""
    update_available: bool
    force_update: bool = False
    local_version: str = ""
    remote_version: str = ""
    release_date: str = ""
    download_url: str = ""
    sha256: str = ""
    release_notes: List[str] = field(default_factory=list)
    error: Optional[str] = None


class VersionChecker:
    """Handles remote version fetching and comparison."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self._update_config = None

    # ---- Parse helpers ----

    @staticmethod
    def parse_semver(version_str: str) -> Tuple[int, int, int]:
        """Parse '3.0.0' / 'v3.1.0' / '3.0' → (3, 0, 0)."""
        v = version_str.strip().lstrip("vV")
        parts = v.split(".")
        major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        return (major, minor, patch)

    @staticmethod
    def is_newer(remote: str, local: str) -> bool:
        """True if remote version > local version."""
        return VersionChecker.parse_semver(remote) > VersionChecker.parse_semver(local)

    @staticmethod
    def is_minimum_met(current: str, minimum: str) -> bool:
        """True if current version >= minimum required version."""
        return VersionChecker.parse_semver(current) >= VersionChecker.parse_semver(minimum)

    # ---- Local version ----

    def get_local_version(self) -> str:
        """Read current version from version.txt."""
        version_path = self.project_root / "version.txt"
        if version_path.exists():
            content = version_path.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.lower().startswith("version:"):
                    return line.split(":", 1)[1].strip()
        # Fallback to update.json
        config = self._load_update_config()
        return config.get("current_version", "0.0.0")

    def _load_update_config(self) -> dict:
        if self._update_config is None:
            path = self.project_root / "config" / "update.json"
            if path.exists():
                try:
                    self._update_config = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    self._update_config = {}
            else:
                self._update_config = {}
        return self._update_config

    def save_update_config(self, updates: dict):
        config = self._load_update_config()
        config.update(updates)
        path = self.project_root / "config" / "update.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        self._update_config = config

    def get_update_server_url(self) -> str:
        """Get remote version.json URL from env or config."""
        url = os.getenv("TIKTOK_FACTORY_UPDATE_URL", "")
        if url:
            return url
        config = self._load_update_config()
        return config.get("update_server", "https://your-domain/version.json")

    def get_update_channel(self) -> str:
        config = self._load_update_config()
        return config.get("update_channel", "stable")

    # ---- Remote fetch ----

    def fetch_remote_version(self) -> VersionInfo:
        """
        Fetch version.json from remote server.

        Raises:
            requests.RequestException: Network error
            json.JSONDecodeError: Invalid response
            ValueError: Missing required fields
        """
        url = self.get_update_server_url()
        logger.info(f"[VersionChecker] Fetching {url}")

        resp = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "TikTok-AI-Factory-Pro-Update/3.0"},
        )
        resp.raise_for_status()
        data = resp.json()

        # Validate required fields
        version = data.get("latest_version")
        if not version:
            raise ValueError("Remote version.json missing 'latest_version' field")
        download_url = data.get("download_url")
        if not download_url:
            raise ValueError("Remote version.json missing 'download_url' field")

        return VersionInfo(
            version=version,
            release_date=data.get("release_date", ""),
            download_url=download_url,
            force_update=data.get("force_update", False),
            sha256=data.get("sha256", ""),
            release_notes=data.get("release_notes", []),
            min_required_version=data.get("min_required_version", "0.0.0"),
            channel=data.get("channel", "stable"),
            file_size_mb=data.get("file_size_mb", 0.0),
        )

    # ---- Check ----

    def check(self) -> UpdateCheckResult:
        """
        Full update check — fetch remote, compare, return result.

        Never raises — errors are captured in result.error.
        """
        local = self.get_local_version()

        try:
            remote_info = self.fetch_remote_version()
        except requests.RequestException as e:
            logger.debug(f"[VersionChecker] Network error: {e}")
            return UpdateCheckResult(
                update_available=False,
                local_version=local,
                error=f"Network error: {e}",
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[VersionChecker] Invalid remote data: {e}")
            return UpdateCheckResult(
                update_available=False,
                local_version=local,
                error=f"Invalid server response: {e}",
            )
        except Exception as e:
            logger.error(f"[VersionChecker] Unexpected error: {e}")
            return UpdateCheckResult(
                update_available=False,
                local_version=local,
                error=str(e),
            )

        # Check channel
        channel = self.get_update_channel()
        if channel != "stable" and remote_info.channel not in (channel, "stable"):
            logger.info(f"[VersionChecker] Channel '{remote_info.channel}' not in target '{channel}'")
            return UpdateCheckResult(
                update_available=False,
                local_version=local,
                remote_version=remote_info.version,
            )

        # Compare versions
        available = self.is_newer(remote_info.version, local)

        # Save last checked timestamp
        self.save_update_config({"last_checked": datetime.now().isoformat()})

        if not available:
            logger.info(
                f"[VersionChecker] Up-to-date (local={local}, remote={remote_info.version})"
            )

        # Check if current version meets minimum required
        if available and remote_info.min_required_version != "0.0.0":
            if not self.is_minimum_met(local, remote_info.min_required_version):
                logger.warning(
                    f"[VersionChecker] Version {local} below minimum {remote_info.min_required_version}"
                )
                remote_info.force_update = True  # escalate to force update

        return UpdateCheckResult(
            update_available=available,
            force_update=remote_info.force_update,
            local_version=local,
            remote_version=remote_info.version,
            release_date=remote_info.release_date,
            download_url=remote_info.download_url,
            sha256=remote_info.sha256,
            release_notes=remote_info.release_notes,
        )
