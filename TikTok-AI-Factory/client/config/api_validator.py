"""
TikTok AI Factory Pro — API Validator
=======================================
Test connections to each AI provider.
Used by the Settings Center's [测试连接] buttons and [环境检测].
"""

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)


class APIValidator:
    """Tests API connectivity for each provider."""

    TIMEOUT = 10  # seconds

    # ================================================================
    # Individual API tests
    # ================================================================

    @staticmethod
    def test_openai(api_key: str) -> Dict[str, Any]:
        """
        Test OpenAI API key by calling the models endpoint.
        GET https://api.openai.com/v1/models
        Returns 200 on valid key.
        """
        if not api_key or not api_key.startswith(("sk-", "sk-proj-")):
            return {"ok": False, "message": "API Key 格式不正确（应为 sk- 开头）", "status_code": None}

        try:
            resp = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=APIValidator.TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                model_count = len(data.get("data", []))
                return {
                    "ok": True,
                    "message": f"✓ 已连接 · {model_count} 个模型可用",
                    "status_code": 200,
                    "model_count": model_count,
                }
            elif resp.status_code == 401:
                return {"ok": False, "message": "✗ 连接失败 · API Key 无效", "status_code": 401}
            else:
                return {"ok": False, "message": f"✗ 连接失败 · HTTP {resp.status_code}", "status_code": resp.status_code}
        except requests.Timeout:
            return {"ok": False, "message": "✗ 连接超时 · 请检查网络", "status_code": None}
        except requests.ConnectionError:
            return {"ok": False, "message": "✗ 无法连接 · 请检查网络/代理", "status_code": None}
        except Exception as e:
            return {"ok": False, "message": f"✗ 连接失败 · {str(e)[:80]}", "status_code": None}

    @staticmethod
    def test_elevenlabs(api_key: str) -> Dict[str, Any]:
        """
        Test ElevenLabs API key by calling the voices endpoint.
        GET https://api.elevenlabs.io/v1/voices
        """
        if not api_key:
            return {"ok": False, "message": "API Key 未配置", "status_code": None}

        try:
            resp = requests.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": api_key},
                timeout=APIValidator.TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                voice_count = len(data.get("voices", []))
                return {
                    "ok": True,
                    "message": f"✓ 已连接 · {voice_count} 个语音可用",
                    "status_code": 200,
                    "voice_count": voice_count,
                }
            elif resp.status_code == 401:
                return {"ok": False, "message": "✗ 连接失败 · API Key 无效", "status_code": 401}
            else:
                return {"ok": False, "message": f"✗ 连接失败 · HTTP {resp.status_code}", "status_code": resp.status_code}
        except requests.Timeout:
            return {"ok": False, "message": "✗ 连接超时", "status_code": None}
        except requests.ConnectionError:
            return {"ok": False, "message": "✗ 无法连接", "status_code": None}
        except Exception as e:
            return {"ok": False, "message": f"✗ 连接失败 · {str(e)[:80]}", "status_code": None}

    @staticmethod
    def test_ark(api_key: str) -> Dict[str, Any]:
        """
        Test 火山引擎 ARK API key by calling the chat/completions endpoint.
        POST https://ark.cn-beijing.volces.com/api/v3/chat/completions
        """
        if not api_key:
            return {"ok": False, "message": "API Key 未配置", "status_code": None}

        try:
            resp = requests.post(
                "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "ep-20240601",  # generic endpoint model
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 10,
                },
                timeout=APIValidator.TIMEOUT,
            )
            # ARK returns 200 even for the test call if key is valid
            # 401/403 if invalid
            if resp.status_code == 200:
                return {"ok": True, "message": "✓ 已连接 · 火山引擎 ARK 正常", "status_code": 200}
            elif resp.status_code in (401, 403):
                return {"ok": False, "message": f"✗ 连接失败 · API Key 无效或权限不足", "status_code": resp.status_code}
            else:
                # Might be model not found but key is valid
                if resp.status_code == 404 or "model" in resp.text.lower():
                    return {"ok": True, "message": "✓ 已连接 · ARK 服务可达", "status_code": 200}
                return {"ok": False, "message": f"✗ 连接失败 · HTTP {resp.status_code}", "status_code": resp.status_code}
        except requests.Timeout:
            return {"ok": False, "message": "✗ 连接超时", "status_code": None}
        except requests.ConnectionError:
            return {"ok": False, "message": "✗ 无法连接", "status_code": None}
        except Exception as e:
            return {"ok": False, "message": f"✗ 连接失败 · {str(e)[:80]}", "status_code": None}

    @staticmethod
    def test_claude(api_key: str) -> Dict[str, Any]:
        """Test Claude API key via a lightweight models list request."""
        if not api_key or not api_key.startswith("sk-ant-"):
            return {"ok": False, "message": "API Key 格式不正确（应为 sk-ant- 开头）", "status_code": None}

        try:
            resp = requests.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                timeout=APIValidator.TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                model_count = len(data.get("data", []))
                return {"ok": True, "message": f"✓ 已连接 · {model_count} 个模型可用", "status_code": 200}
            elif resp.status_code == 401 or resp.status_code == 403:
                return {"ok": False, "message": "✗ 连接失败 · API Key 无效", "status_code": resp.status_code}
            else:
                return {"ok": False, "message": f"✗ 连接失败 · HTTP {resp.status_code}", "status_code": resp.status_code}
        except Exception as e:
            return {"ok": False, "message": f"✗ 连接失败 · {str(e)[:80]}", "status_code": None}

    @staticmethod
    def test_deepseek(api_key: str) -> Dict[str, Any]:
        """Test DeepSeek API key."""
        if not api_key:
            return {"ok": False, "message": "API Key 未配置", "status_code": None}

        try:
            resp = requests.get(
                "https://api.deepseek.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=APIValidator.TIMEOUT,
            )
            if resp.status_code == 200:
                return {"ok": True, "message": "✓ 已连接", "status_code": 200}
            elif resp.status_code == 401:
                return {"ok": False, "message": "✗ 连接失败 · API Key 无效", "status_code": 401}
            else:
                return {"ok": False, "message": f"✗ 连接失败 · HTTP {resp.status_code}", "status_code": resp.status_code}
        except Exception as e:
            return {"ok": False, "message": f"✗ 连接失败 · {str(e)[:80]}", "status_code": None}

    # ================================================================
    # Environment check
    # ================================================================

    @staticmethod
    def check_environment() -> Dict[str, Any]:
        """
        Full environment health check.
        Returns a report dict with status for each component.
        """
        report = {
            "checked_at": datetime.now().isoformat(),
            "platform": sys.platform,
            "python_version": sys.version,
            "components": {},
            "api_status": {},
            "overall": {"pass": 0, "fail": 0, "warn": 0},
        }

        # 1. Python
        try:
            v = sys.version_info
            report["components"]["Python"] = {
                "status": "pass",
                "message": f"✓ Python {v.major}.{v.minor}.{v.micro} 正常",
                "detail": sys.executable,
            }
        except Exception as e:
            report["components"]["Python"] = {"status": "fail", "message": f"✗ {e}"}

        # 2. FFmpeg
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=10)
            if result.returncode == 0:
                ver_line = result.stdout.decode().split("\n")[0] if result.stdout else "unknown"
                report["components"]["FFmpeg"] = {
                    "status": "pass",
                    "message": f"✓ FFmpeg 正常",
                    "detail": ver_line[:100],
                }
            else:
                report["components"]["FFmpeg"] = {"status": "fail", "message": "✗ FFmpeg 未安装或不可用"}
        except FileNotFoundError:
            report["components"]["FFmpeg"] = {"status": "fail", "message": "✗ FFmpeg 未安装"}
        except Exception as e:
            report["components"]["FFmpeg"] = {"status": "fail", "message": f"✗ {e}"}

        # 3. Pillow
        try:
            from PIL import Image
            report["components"]["Pillow"] = {"status": "pass", "message": "✓ Pillow 正常"}
        except ImportError:
            report["components"]["Pillow"] = {"status": "fail", "message": "✗ Pillow 未安装"}

        # 4. API keys — read from .env
        from config.settings_manager import SettingsManager
        sm = SettingsManager()

        api_tests = {
            "OpenAI": ("OPENAI_API_KEY", APIValidator.test_openai),
            "ElevenLabs": ("ELEVENLABS_API_KEY", APIValidator.test_elevenlabs),
            "ARK (火山引擎)": ("ARK_API_KEY", APIValidator.test_ark),
            "Claude": ("ANTHROPIC_API_KEY", APIValidator.test_claude),
            "DeepSeek": ("DEEPSEEK_API_KEY", APIValidator.test_deepseek),
        }

        for name, (env_key, test_fn) in api_tests.items():
            key = sm.get_api_key(env_key)
            if not key:
                report["api_status"][name] = {"status": "warn", "message": "⚠ 未配置"}
            else:
                result = test_fn(key)
                report["api_status"][name] = {
                    "status": "pass" if result["ok"] else "fail",
                    "message": result["message"],
                }

        # 5. License
        try:
            from license.license_manager import get_license_manager
            lm = get_license_manager()
            if lm.validate():
                status_info = lm.get_status()
                report["components"]["License"] = {
                    "status": "pass",
                    "message": f"✓ License 有效 · {status_info.get('days_remaining', '?')} 天剩余",
                }
            else:
                report["components"]["License"] = {"status": "fail", "message": f"✗ {lm.error_message[:80]}"}
        except Exception as e:
            report["components"]["License"] = {"status": "fail", "message": f"✗ {e}"}

        # Tally
        for cat in [report["components"], report["api_status"]]:
            for item in cat.values():
                s = item.get("status", "warn")
                report["overall"][s] = report["overall"].get(s, 0) + 1
        # Count "warn" items
        report["overall"]["warn"] = sum(
            1 for cat in [report["components"], report["api_status"]]
            for item in cat.values()
            if item.get("status") == "warn"
        )
        report["overall"]["pass"] = sum(
            1 for cat in [report["components"], report["api_status"]]
            for item in cat.values()
            if item.get("status") == "pass"
        )
        report["overall"]["fail"] = sum(
            1 for cat in [report["components"], report["api_status"]]
            for item in cat.values()
            if item.get("status") == "fail"
        )

        return report

    @staticmethod
    def format_env_report(report: Dict[str, Any]) -> str:
        """Format the environment check report as readable text."""
        lines = []
        lines.append("=" * 55)
        lines.append("  TikTok AI Factory Pro — 环境检测报告")
        lines.append("=" * 55)
        lines.append(f"  检测时间: {report['checked_at'][:19]}")
        lines.append(f"  Python:   {report['python_version'].split()[0]}")
        lines.append(f"  平台:     {report['platform']}")
        lines.append("")

        lines.append("  [系统组件]")
        for name, info in report.get("components", {}).items():
            lines.append(f"  {info['message']}")

        lines.append("")
        lines.append("  [API 连接]")
        for name, info in report.get("api_status", {}).items():
            lines.append(f"  {info['message']}")

        lines.append("")
        overall = report.get("overall", {})
        lines.append(f"  通过: {overall.get('pass', 0)}  "
                     f"失败: {overall.get('fail', 0)}  "
                     f"未配置: {overall.get('warn', 0)}")
        lines.append("=" * 55)

        if overall.get("fail", 0) == 0 and overall.get("warn", 0) <= 3:
            lines.append("  环境状态: ✅ 良好，可以开始使用。")
        elif overall.get("fail", 0) == 0:
            lines.append("  环境状态: ⚠️ 基本可用，建议配置缺失的 API Key。")
        else:
            lines.append("  环境状态: ❌ 存在错误，请修复后使用。")

        return "\n".join(lines)
