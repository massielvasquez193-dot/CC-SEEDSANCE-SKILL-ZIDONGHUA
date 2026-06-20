"""
TikTok AI Factory Pro — Settings Manager
==========================================
Unified read/write for .env (API keys) and settings.json (app config).

No more manual .env editing — everything goes through this module.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional


class SettingsManager:
    """Central configuration manager for .env and settings.json."""

    # Known API key env vars and their .env file keys
    API_KEYS = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "DEEPSEEK_API_KEY",
        "GEMINI_API_KEY",
        "ELEVENLABS_API_KEY",
        "ARK_API_KEY",
        "SEEDANCE_API_KEY",
        "VEO3_API_KEY",
        "JIMENG_API_KEY",
        "RUNWAY_API_KEY",
        "KLING_API_KEY",
    ]

    APP_SETTINGS = [
        "TIKTOK_FACTORY_AI_PROVIDER",
        "TIKTOK_FACTORY_COUNTRY",
        "TIKTOK_FACTORY_LANGUAGE",
        "TIKTOK_FACTORY_VIDEO_DURATION",
        "TIKTOK_FACTORY_OUTPUT_COUNT",
        "TIKTOK_FACTORY_PAIRING_MODE",
        "TIKTOK_FACTORY_MAX_CONCURRENT",
        "TIKTOK_FACTORY_LOG_LEVEL",
        "TIKTOK_FACTORY_UPDATE_URL",
        "TIKTOK_FACTORY_SKIP_UPDATE",
        "TIKTOK_FACTORY_DEV_MODE",
        "TIKTOK_FACTORY_VIDEO_PROVIDER",
        "TIKTOK_FACTORY_DEFAULT_CHARACTER",
    ]

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.env_path = self.project_root / ".env"
        self.settings_json_path = self.project_root / "config" / "settings.json"

    # ================================================================
    # .env file operations
    # ================================================================

    def read_env(self) -> Dict[str, str]:
        """Read all key-value pairs from .env file."""
        result = {}
        if not self.env_path.exists():
            return result

        for line in self.env_path.read_text(encoding="utf-8").split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and v:
                result[k] = v
        return result

    def write_env(self, updates: Dict[str, str], preserve_existing: bool = True):
        """
        Write key-value pairs to .env file.

        Args:
            updates: Dict of KEY=VALUE to write
            preserve_existing: If True, merge with existing .env content
        """
        if preserve_existing:
            current = self.read_env()
            current.update(updates)
            final = current
        else:
            final = updates

        lines = []
        # Preserve comments and structure from original
        if self.env_path.exists():
            existing_keys = set()
            for line in self.env_path.read_text(encoding="utf-8").split("\n"):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    lines.append(line)
                    continue
                if "=" in stripped:
                    k = stripped.split("=", 1)[0].strip()
                    if k in final:
                        lines.append(f"{k}={final[k]}")
                        existing_keys.add(k)
                    elif preserve_existing:
                        lines.append(line)
                    # else skip (not in updates and not preserving)
                else:
                    lines.append(line)

            # Append any new keys not in original file
            for k, v in final.items():
                if k not in existing_keys:
                    lines.append(f"{k}={v}")
        else:
            for k, v in final.items():
                lines.append(f"{k}={v}")

        self.env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        # Update os.environ for current process
        for k, v in final.items():
            os.environ[k] = str(v)

    def get_api_key(self, key_name: str) -> str:
        """Get a single API key from env."""
        return os.getenv(key_name, self.read_env().get(key_name, ""))

    def set_api_key(self, key_name: str, value: str):
        """Set a single API key in .env and os.environ."""
        os.environ[key_name] = value
        self.write_env({key_name: value})

    # ================================================================
    # settings.json operations
    # ================================================================

    def read_settings_json(self) -> Dict[str, Any]:
        """Read the entire settings.json file."""
        if not self.settings_json_path.exists():
            return self._default_settings()
        try:
            return json.loads(self.settings_json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return self._default_settings()

    def write_settings_json(self, updates: Dict[str, Any], merge: bool = True):
        """Write to settings.json, optionally merging with existing."""
        if merge:
            current = self.read_settings_json()
            self._deep_update(current, updates)
            final = current
        else:
            final = updates

        self.settings_json_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_json_path.write_text(
            json.dumps(final, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_setting(self, path: str, default: Any = None) -> Any:
        """Get a dot-separated setting path. e.g. 'video.provider' or 'target.country'."""
        data = self.read_settings_json()
        keys = path.split(".")
        for k in keys:
            if isinstance(data, dict):
                data = data.get(k, default)
            else:
                return default
        return data if data is not None else default

    def set_setting(self, path: str, value: Any):
        """Set a dot-separated setting path and save."""
        data = self.read_settings_json()
        keys = path.split(".")
        target = data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self.write_settings_json(data, merge=False)

    # ================================================================
    # Convenience methods for Settings Center
    # ================================================================

    def get_all_api_status(self) -> Dict[str, Dict]:
        """Get all API keys with masked values for display."""
        result = {}
        for key in self.API_KEYS:
            val = self.get_api_key(key)
            result[key] = {
                "configured": bool(val),
                "masked": self._mask_key(val) if val else "",
                "length": len(val) if val else 0,
            }
        return result

    def get_video_provider(self) -> str:
        """Get the configured video generation provider."""
        return self.get_setting("video.provider", "seedance")

    def set_video_provider(self, provider: str):
        """Set the video generation provider."""
        self.set_setting("video.provider", provider)
        self.write_env({"TIKTOK_FACTORY_VIDEO_PROVIDER": provider})

    def get_country_language(self) -> tuple:
        """Get (country_code, language) tuple."""
        country = self.get_setting("target.country", "US")
        language = self.get_setting("target.language", "en")
        return (country, language)

    def set_country_language(self, country: str, language: str):
        """Set country and language."""
        self.set_setting("target.country", country)
        self.set_setting("target.language", language)
        self.write_env({
            "TIKTOK_FACTORY_COUNTRY": country,
            "TIKTOK_FACTORY_LANGUAGE": language,
        })

    def get_default_character(self) -> str:
        """Get the default character type."""
        return self.get_setting("character.default_type", "UGC Female")

    def set_default_character(self, char_type: str):
        """Set the default character type."""
        self.set_setting("character.default_type", char_type)
        self.write_env({"TIKTOK_FACTORY_DEFAULT_CHARACTER": char_type})

    def save_all_settings(self, api_keys: Dict[str, str], settings: Dict[str, Any]):
        """Save everything at once."""
        if api_keys:
            self.write_env(api_keys)
        if settings:
            self.write_settings_json(settings)

    # ================================================================
    # Helpers
    # ================================================================

    @staticmethod
    def _mask_key(key: str) -> str:
        """Mask an API key for display, showing first 4 and last 4 chars."""
        if not key or len(key) < 8:
            return "*" * min(len(key), 8)
        return key[:4] + "*" * (len(key) - 8) + key[-4:]

    @staticmethod
    def _deep_update(target: dict, updates: dict):
        """Recursively update a nested dict."""
        for k, v in updates.items():
            if isinstance(v, dict) and isinstance(target.get(k), dict):
                SettingsManager._deep_update(target[k], v)
            else:
                target[k] = v

    @staticmethod
    def _default_settings() -> dict:
        return {
            "video": {"provider": "seedance", "duration": 15},
            "target": {"country": "US", "language": "en"},
            "character": {"default_type": "UGC Female"},
            "factory": {"version": "3.0.0"},
        }
