"""
TikTok AI Factory Pro — Commercial License Manager
====================================================
机器码 + 授权码 + 到期时间 + 版本号
启动前验证 license.key
"""

import hashlib
import json
import logging
import os
import platform
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LicenseManager:
    """商业授权管理器"""

    LICENSE_FILE = "license.key"
    PUBLIC_KEY_PIN = "TKAIF-PRO-M9X2"  # 公钥指纹

    def __init__(self):
        self.machine_code = self._generate_machine_code()
        self.license_data: Optional[dict] = None
        self.valid = False
        self.error_message = ""

    # ================================================================
    # 机器码生成 (硬件指纹)
    # ================================================================
    def _generate_machine_code(self) -> str:
        """基于硬件特征生成唯一机器码"""
        components = []

        # 1. MAC 地址
        try:
            node = uuid.getnode()
            components.append(f"MAC:{node:012x}")
        except Exception:
            components.append("MAC:unknown")

        # 2. 主机名
        components.append(f"HOST:{platform.node()}")

        # 3. 处理器
        components.append(f"CPU:{platform.processor() or platform.machine()}")

        # 4. 系统信息
        components.append(f"OS:{platform.system()}_{platform.release()}")

        # 5. 磁盘序列号 (Windows)
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "diskdrive", "get", "serialnumber"],
                    capture_output=True, text=True, timeout=5,
                )
                serial = result.stdout.strip().split("\n")[-1].strip()
                if serial:
                    components.append(f"DISK:{serial}")
        except Exception:
            pass

        # 生成哈希
        raw = "|".join(components)
        return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()

    # ================================================================
    # 授权码生成 (离线模式 — 由授权服务器生成)
    # ================================================================
    @staticmethod
    def generate_license_key(
        machine_code: str,
        product_version: str,
        expiry_date: str,
        client_name: str = "",
        secret: str = None,
    ) -> str:
        """
        生成授权码 (仅授权服务器使用)

        Args:
            machine_code: 机器码
            product_version: 版本号 (如 "3.0.0")
            expiry_date: 到期日 (如 "2027-06-11")
            client_name: 客户名称
            secret: 签名密钥

        Returns:
            完整 license.key 文件内容 (JSON)
        """
        secret = secret or "TKAIF-PRO-DEFAULT-KEY-2026"

        # 构建授权数据
        license_data = {
            "machine_code": machine_code,
            "product": "TikTok AI Factory Pro",
            "version": product_version,
            "client": client_name or "Licensed User",
            "issued_at": datetime.now().strftime("%Y-%m-%d"),
            "expiry_date": expiry_date,
            "type": "commercial",
            "features": [
                "full_pipeline",
                "batch_mode",
                "watch_mode",
                "seedance_integration",
                "gpt_image_keyframes",
                "elevenlabs_tts",
                "ugc_scoring",
            ],
        }

        # 生成签名
        payload = json.dumps(license_data, sort_keys=True, ensure_ascii=False)
        signature = hashlib.sha256(
            f"{payload}:{secret}:{machine_code}".encode()
        ).hexdigest()

        license_data["signature"] = signature
        return json.dumps(license_data, indent=2, ensure_ascii=False)

    # ================================================================
    # 验证授权
    # ================================================================
    def validate(self, license_path: Path = None) -> bool:
        """
        验证 license.key

        Returns:
            True if license is valid
        """
        self.valid = False
        self.error_message = ""

        # 查找 license.key
        if license_path is None:
            license_path = self._find_license_file()

        if license_path is None or not license_path.exists():
            self.error_message = (
                f"授权文件未找到: {self.LICENSE_FILE}\n"
                f"请将 license.key 放在项目根目录。\n"
                f"获取授权: 联系供应商并提供机器码 → {self.machine_code}"
            )
            return False

        # 读取授权文件
        try:
            content = license_path.read_text(encoding="utf-8").strip()
            self.license_data = json.loads(content)
        except json.JSONDecodeError:
            self.error_message = "授权文件格式错误 — 无效的 JSON"
            return False
        except Exception as e:
            self.error_message = f"读取授权文件失败: {e}"
            return False

        # === 验证1: 机器码匹配 ===
        lic_machine = self.license_data.get("machine_code", "")
        if lic_machine != self.machine_code:
            self.error_message = (
                f"机器码不匹配。\n"
                f"  授权机器: {lic_machine}\n"
                f"  当前机器: {self.machine_code}\n"
                f"联系供应商更新授权。"
            )
            return False

        # === 验证2: 签名校验 ===
        expected_sig = self.license_data.get("signature", "")
        if not self._verify_signature(expected_sig):
            self.error_message = "授权签名无效 — 文件可能被篡改"
            return False

        # === 验证3: 到期时间 ===
        expiry_str = self.license_data.get("expiry_date", "")
        try:
            expiry = datetime.strptime(expiry_str, "%Y-%m-%d")
            now = datetime.now()
            if now > expiry:
                days_overdue = (now - expiry).days
                self.error_message = (
                    f"授权已过期。\n"
                    f"  到期日: {expiry_str}\n"
                    f"  已过期: {days_overdue} 天\n"
                    f"联系供应商续费。"
                )
                return False

            # 提前30天警告
            remaining = (expiry - now).days
            if remaining <= 30:
                logger.warning(
                    f"⚠️ 授权将在 {remaining} 天后到期 ({expiry_str})，请及时续费。"
                )
        except ValueError:
            self.error_message = f"到期日期格式错误: {expiry_str}"
            return False

        # === 验证4: 版本号检查 ===
        lic_version = self.license_data.get("version", "0.0.0")
        if not self._check_version(lic_version):
            self.error_message = (
                f"软件版本不兼容。\n"
                f"  授权版本: {lic_version}\n"
                f"  当前版本: {self._get_current_version()}\n"
                f"升级授权或降级软件。"
            )
            return False

        # === 全部通过 ===
        self.valid = True
        return True

    # ================================================================
    # 签名验证
    # ================================================================
    def _verify_signature(self, signature: str) -> bool:
        """验证授权签名"""
        if not signature:
            return False

        data = {k: v for k, v in self.license_data.items() if k != "signature"}
        payload = json.dumps(data, sort_keys=True, ensure_ascii=False)

        # 使用默认密钥验证 (生产环境使用注册表/远程验证)
        secret = os.getenv("LICENSE_SECRET", "TKAIF-PRO-DEFAULT-KEY-2026")
        expected = hashlib.sha256(
            f"{payload}:{secret}:{self.machine_code}".encode()
        ).hexdigest()

        return signature == expected

    # ================================================================
    # 版本检查
    # ================================================================
    def _check_version(self, lic_version: str) -> bool:
        """检查当前软件版本是否与授权版本兼容"""
        current = self._get_current_version()

        try:
            lic_parts = [int(x) for x in lic_version.split(".")]
            cur_parts = [int(x) for x in current.split(".")]

            # 主版本号必须匹配
            if lic_parts[0] != cur_parts[0]:
                return False

            # 次版本号: 授权版本 >= 当前版本
            for i in range(min(len(lic_parts), len(cur_parts))):
                if lic_parts[i] > cur_parts[i]:
                    return True  # 授权更新，可以通过
                elif lic_parts[i] < cur_parts[i]:
                    return False  # 软件比授权新，不兼容

            return True  # 版本完全匹配
        except (ValueError, IndexError):
            return False

    def _get_current_version(self) -> str:
        """获取当前软件版本"""
        try:
            version_path = Path(__file__).resolve().parent.parent / "version.txt"
            if version_path.exists():
                content = version_path.read_text(encoding="utf-8")
                for line in content.split("\n"):
                    if line.startswith("Version:"):
                        return line.split(":")[1].strip()
        except Exception:
            pass
        return "3.0.0"

    # ================================================================
    # 辅助
    # ================================================================
    def _find_license_file(self) -> Optional[Path]:
        """查找 license.key"""
        # 1. 项目根目录
        root = Path(__file__).resolve().parent.parent
        candidate = root / self.LICENSE_FILE
        if candidate.exists():
            return candidate

        # 2. 当前工作目录
        candidate = Path.cwd() / self.LICENSE_FILE
        if candidate.exists():
            return candidate

        return None

    # ================================================================
    # 在线验证
    # ================================================================
    def _try_online_validation(self) -> bool:
        """
        尝试连接 License Server 进行在线验证。

        环境变量:
          LICENSE_SERVER_URL   License Server 地址 (如 http://your-server:8199)
          LICENSE_KEY          客户端授权码

        Returns:
          True if server confirms valid, False otherwise.
        """
        import requests

        server_url = os.getenv("LICENSE_SERVER_URL", "")
        license_key = os.getenv("LICENSE_KEY", "")

        if not server_url or not license_key:
            return False  # 未配置在线验证，走离线 fallback

        try:
            resp = requests.post(
                f"{server_url.rstrip('/')}/api/license/check",
                json={
                    "license_key": license_key.strip(),
                    "machine_id": self.machine_code,
                },
                timeout=10,
                headers={"User-Agent": "TikTok-AI-Factory-Pro/3.0"},
            )

            if resp.status_code != 200:
                logger.warning(f"[License] Server returned {resp.status_code}")
                return False

            data = resp.json()
            if data.get("valid"):
                # 在线验证通过 — 更新本地数据
                self.valid = True
                self.license_data = {
                    "machine_code": self.machine_code,
                    "product": "TikTok AI Factory Pro",
                    "version": "3.0.0",
                    "client": data.get("company", "Licensed User"),
                    "issued_at": datetime.now().strftime("%Y-%m-%d"),
                    "expiry_date": data.get("expire", ""),
                    "type": "commercial",
                    "plan": data.get("plan", "PRO"),
                    "features": [
                        "full_pipeline", "batch_mode", "watch_mode",
                        "seedance_integration", "gpt_image_keyframes",
                        "elevenlabs_tts", "ugc_scoring",
                    ],
                    "signature": "online-verified",
                }
                logger.info(
                    f"[License] Online verified ✓ — {data.get('company')} "
                    f"({data.get('plan')}) — {data.get('days_remaining', '?')}d remaining"
                )
                return True
            else:
                logger.warning(
                    f"[License] Online check denied: {data.get('reason')} — {data.get('message')}"
                )
                # If server explicitly denies, don't fall back to offline
                self.error_message = data.get("message", "在线验证失败")
                self.valid = False
                self.print_banner()
                sys.exit(1)

        except requests.ConnectionError:
            logger.warning("[License] Cannot reach license server — using offline fallback")
        except requests.Timeout:
            logger.warning("[License] License server timeout — using offline fallback")
        except Exception as e:
            logger.warning(f"[License] Online check error: {e} — using offline fallback")

        return False  # Fall through to offline validation

    # ================================================================
    # SaaS 扩展 — 心跳 + 续费检测 + 计划信息
    # ================================================================
    def send_heartbeat(self) -> bool:
        """Send periodic heartbeat to SaaS license server."""
        import requests
        server_url = os.getenv("LICENSE_SERVER_URL", "")
        if not server_url:
            return False
        try:
            resp = requests.post(
                f"{server_url.rstrip('/')}/api/license/heartbeat",
                json={"machine_id": self.machine_code},
                timeout=5,
            )
            return resp.status_code == 200 and resp.json().get("alive", False)
        except Exception:
            return False

    def get_plan_info(self) -> dict:
        """Get current plan features from SaaS server."""
        import requests
        server_url = os.getenv("LICENSE_SERVER_URL", "")
        license_key = os.getenv("LICENSE_KEY", "")
        if not server_url or not license_key:
            # Fall back to local license data
            if self.license_data:
                return {
                    "plan": self.license_data.get("plan", "PRO"),
                    "features": self.license_data.get("features", []),
                    "device_limit": 1,
                    "video_limit": 50,
                }
            return {"plan": "UNKNOWN", "features": [], "device_limit": 0, "video_limit": 0}

        try:
            resp = requests.post(
                f"{server_url.rstrip('/')}/api/license/check",
                json={"license_key": license_key.strip(), "machine_id": self.machine_code},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid"):
                    return {
                        "plan": data.get("plan", "PRO"),
                        "features": data.get("features", []),
                        "device_limit": data.get("device_limit", 1),
                        "video_limit": data.get("video_limit", 50),
                        "expire": data.get("expire", ""),
                        "days_remaining": data.get("days_remaining", 0),
                    }
        except Exception:
            pass
        return {"plan": "PRO", "features": [], "device_limit": 1, "video_limit": 50}

    def check_renewal_needed(self) -> dict:
        """Check if renewal is needed soon."""
        info = self.get_plan_info()
        days = info.get("days_remaining", 365)
        if days <= 0:
            return {"needed": True, "urgent": True, "message": "授权已过期，请立即续费", "days": days}
        elif days <= 7:
            return {"needed": True, "urgent": True, "message": f"授权将在 {days} 天后到期", "days": days}
        elif days <= 30:
            return {"needed": True, "urgent": False, "message": f"授权将在 {days} 天后到期", "days": days}
        return {"needed": False, "urgent": False, "message": "", "days": days}

    def get_status(self) -> dict:
        """获取授权状态信息"""
        if not self.license_data:
            return {
                "valid": False,
                "machine_code": self.machine_code,
                "error": self.error_message or "未加载授权",
            }

        expiry_str = self.license_data.get("expiry_date", "")
        try:
            expiry = datetime.strptime(expiry_str, "%Y-%m-%d")
            remaining = (expiry - datetime.now()).days
        except ValueError:
            remaining = 0

        return {
            "valid": self.valid,
            "machine_code": self.machine_code,
            "client": self.license_data.get("client", ""),
            "version": self.license_data.get("version", ""),
            "expiry_date": expiry_str,
            "days_remaining": remaining,
            "type": self.license_data.get("type", ""),
            "features": self.license_data.get("features", []),
        }

    def print_banner(self):
        """打印授权状态横幅"""
        if self.valid:
            status = self.get_status()
            print(f"""
╔══════════════════════════════════════╗
║  [LICENSED] TikTok AI Factory Pro    ║
╠══════════════════════════════════════╣
║  Client: {status['client']:<28} ║
║  Version: {status['version']:<27} ║
║  Expiry: {status['expiry_date']} ({status['days_remaining']} days left){'':<9} ║
╚══════════════════════════════════════╝
""")
        else:
            print(f"""
╔══════════════════════════════════════╗
║  [UNLICENSED] License Check Failed   ║
╠══════════════════════════════════════╣
║  Machine: {self.machine_code:<26} ║
╠══════════════════════════════════════╣
║  {self.error_message[:40]:<35}║
╚══════════════════════════════════════╝
""")


# ================================================================
# 全局实例
# ================================================================
_license_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager


def check_license() -> bool:
    """启动前检查授权 — run_factory.py 调用

    验证顺序:
      1. 在线验证 (如果配置了 LICENSE_SERVER_URL)
      2. 离线验证 (license.key fallback)
    """
    lm = get_license_manager()

    # 1) Try online validation first
    if lm._try_online_validation():
        lm.print_banner()
        return True

    # 2) Fall back to offline license.key
    if not lm.validate():
        lm.print_banner()
        return False

    lm.print_banner()
    return True
