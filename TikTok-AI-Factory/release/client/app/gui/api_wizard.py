"""
TikTok AI Factory Pro — First-Run API Configuration Wizard
============================================================
Shown on first launch. Walks user through configuring API keys.
Saves to .env automatically. Never shown again after completion.
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QProgressBar, QMessageBox, QFrame, QApplication,
)
from PySide6.QtCore import Qt, QThread, Signal


class ApiTestWorker(QThread):
    """Background API test thread."""
    result = Signal(str, bool, str)  # key_name, ok, message

    def __init__(self, key_name, api_key):
        super().__init__()
        self.key_name = key_name
        self.api_key = api_key

    def run(self):
        from config.api_validator import APIValidator
        tests = {
            "OPENAI_API_KEY": APIValidator.test_openai,
            "ELEVENLABS_API_KEY": APIValidator.test_elevenlabs,
            "ARK_API_KEY": APIValidator.test_ark,
        }
        fn = tests.get(self.key_name)
        if fn:
            r = fn(self.api_key)
            self.result.emit(self.key_name, r["ok"], r["message"])
        else:
            self.result.emit(self.key_name, False, "Unknown key")


class ApiConfigWizard(QDialog):
    """First-run API configuration wizard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API 配置向导 — TikTok AI Factory Pro")
        self.setFixedSize(560, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; }
            QLabel#title { font-size: 20px; font-weight: bold; color: #e94560; }
            QLabel#subtitle { font-size: 12px; color: #8b949e; }
            QLabel#key_label { font-size: 12px; font-weight: bold; color: #c9d1d9; margin-top: 8px; }
            QLabel#hint { font-size: 10px; color: #8b949e; }
            QLineEdit { background: #0d1117; color: #c9d1d9; border: 1px solid #30363d;
                border-radius: 6px; padding: 8px 12px; font-size: 12px;
                font-family: 'Consolas', monospace; }
            QLineEdit:focus { border-color: #58a6ff; }
            QPushButton#test_btn { background: #21262d; color: #58a6ff; border: 1px solid #30363d;
                border-radius: 4px; padding: 6px 14px; font-size: 11px; }
            QPushButton#test_btn:hover { background: #30363d; }
            QPushButton#primary { background: #238636; color: white; border: none;
                border-radius: 6px; padding: 12px 32px; font-size: 14px; font-weight: bold; }
            QPushButton#primary:hover { background: #2ea043; }
            QPushButton#primary:disabled { background: #21262d; color: #484f58; }
            QPushButton#skip { background: transparent; color: #8b949e; border: 1px solid #30363d;
                border-radius: 6px; padding: 12px 24px; font-size: 13px; }
            QLabel#status { font-size: 11px; min-width: 100px; }
            QProgressBar { border: none; border-radius: 4px; background: #21262d; height: 6px; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #e94560, stop:1 #238636); border-radius: 4px; }
        """)

        self._keys = {
            "OPENAI_API_KEY": {"label": "OpenAI API Key", "hint": "用于 GPT-4o 文本 + DALL-E 3 图像生成 · 获取: platform.openai.com", "placeholder": "sk-..."},
            "ELEVENLABS_API_KEY": {"label": "ElevenLabs API Key", "hint": "用于 TTS 语音合成 · 获取: elevenlabs.io", "placeholder": "el_..."},
            "ARK_API_KEY": {"label": "火山引擎 ARK API Key", "hint": "用于 Seedance 视频生成 · 获取: console.volcengine.com", "placeholder": "ark-..."},
        }
        self._inputs = {}
        self._status_labels = {}
        self._test_results = {}

        self._build_ui()
        self._load_existing()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 20)
        layout.setSpacing(6)

        # Header
        title = QLabel("🚀 欢迎使用 TikTok AI Factory Pro")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("首次使用需要配置 API Key。可跳过，稍后在设置中心配置。")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Progress indicator
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        layout.addSpacing(6)

        # API Key inputs
        for key_name, cfg in self._keys.items():
            lbl = QLabel(cfg["label"])
            lbl.setObjectName("key_label")
            layout.addWidget(lbl)

            hint = QLabel(cfg["hint"])
            hint.setObjectName("hint")
            layout.addWidget(hint)

            row = QHBoxLayout()
            row.setSpacing(8)

            inp = QLineEdit()
            inp.setPlaceholderText(cfg["placeholder"])
            inp.setEchoMode(QLineEdit.Password)
            self._inputs[key_name] = inp
            row.addWidget(inp, 1)

            test_btn = QPushButton("测试连接")
            test_btn.setObjectName("test_btn")
            test_btn.clicked.connect(lambda checked, k=key_name, i=inp: self._test_key(k, i.text()))
            row.addWidget(test_btn)

            status = QLabel("")
            status.setObjectName("status")
            self._status_labels[key_name] = status
            row.addWidget(status)

            layout.addLayout(row)

        layout.addSpacing(12)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        skip_btn = QPushButton("跳过，稍后配置")
        skip_btn.setObjectName("skip")
        skip_btn.clicked.connect(self._skip)
        btn_row.addWidget(skip_btn)

        btn_row.addSpacing(12)

        self.save_btn = QPushButton("💾 保存并开始使用")
        self.save_btn.setObjectName("primary")
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.save_btn)
        btn_row.addStretch()

        layout.addLayout(btn_row)

    def _load_existing(self):
        """Pre-fill with existing env values."""
        for key_name in self._keys:
            val = os.getenv(key_name, "")
            if val:
                self._inputs[key_name].setText(val)

    def _test_key(self, key_name, value):
        if not value.strip():
            self._status_labels[key_name].setText("⚠ 请输入 Key")
            self._status_labels[key_name].setStyleSheet("color: #d29922;")
            return

        self._status_labels[key_name].setText("⏳")
        self._status_labels[key_name].setStyleSheet("color: #58a6ff;")

        worker = ApiTestWorker(key_name, value.strip())
        worker.result.connect(self._on_test_result)
        worker.start()

    def _on_test_result(self, key_name, ok, message):
        self._test_results[key_name] = ok
        color = "#238636" if ok else "#da3633"
        self._status_labels[key_name].setText(message[:60])
        self._status_labels[key_name].setStyleSheet(f"color: {color};")
        self._update_progress()

    def _update_progress(self):
        tested = len(self._test_results)
        total = len(self._keys)
        self.progress.setValue(int(tested / total * 100))

    def _save(self):
        """Save API keys to .env."""
        from config.settings_manager import SettingsManager
        sm = SettingsManager()

        updates = {}
        for key_name, inp in self._inputs.items():
            val = inp.text().strip()
            if val:
                updates[key_name] = val
                os.environ[key_name] = val

        if updates:
            sm.write_env(updates)

        # Mark wizard as completed
        sm.write_env({"TIKTOK_FACTORY_WIZARD_COMPLETED": "true"})

        QMessageBox.information(
            self, "配置完成",
            "✅ API Key 已保存！\n\n"
            "现在可以开始使用 TikTok AI Factory Pro 了。\n\n"
            "提示：随时可以在「⚙️ 设置中心」修改配置。"
        )
        self.accept()

    def _skip(self):
        """Skip wizard — user can configure later."""
        reply = QMessageBox.question(
            self, "跳过配置",
            "确定跳过 API 配置？\n\n"
            "没有 API Key，软件将以模板模式运行：\n"
            "• 脚本使用模板生成\n"
            "• 关键帧使用占位图\n"
            "• 视频生成跳过\n\n"
            "可以稍后在「⚙️ 设置中心」配置。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            from config.settings_manager import SettingsManager
            SettingsManager().write_env({"TIKTOK_FACTORY_WIZARD_COMPLETED": "true"})
            self.accept()


def should_show_wizard() -> bool:
    """Check if the first-run wizard should be shown."""
    if os.getenv("TIKTOK_FACTORY_WIZARD_COMPLETED", "").lower() in ("true", "1", "yes"):
        return False
    # Check if any API key is already configured
    if any(os.getenv(k) for k in ["OPENAI_API_KEY", "ELEVENLABS_API_KEY", "ARK_API_KEY"]):
        return False
    return True


def show_wizard_if_needed(parent=None) -> bool:
    """Show the wizard if it hasn't been completed yet. Returns True if shown."""
    if not should_show_wizard():
        return False
    wizard = ApiConfigWizard(parent)
    wizard.exec()
    return True
