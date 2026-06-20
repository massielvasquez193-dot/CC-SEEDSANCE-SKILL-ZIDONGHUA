"""
TikTok AI Factory Pro — Settings Center Tab
=============================================
API key management, video model selection, country/language,
default character type, and environment health check.

No more .env editing — everything is GUI-driven.
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QGroupBox, QScrollArea, QFrame,
    QLineEdit, QGridLayout, QSpacerItem, QSizePolicy,
    QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont


class ApiTestWorker(QThread):
    """Background worker for testing API connections."""
    result_signal = Signal(str, bool, str)  # key_name, ok, message

    def __init__(self, key_name, api_key):
        super().__init__()
        self.key_name = key_name
        self.api_key = api_key

    def run(self):
        from config.api_validator import APIValidator

        test_map = {
            "OPENAI_API_KEY": APIValidator.test_openai,
            "ELEVENLABS_API_KEY": APIValidator.test_elevenlabs,
            "ARK_API_KEY": APIValidator.test_ark,
            "ANTHROPIC_API_KEY": APIValidator.test_claude,
            "DEEPSEEK_API_KEY": APIValidator.test_deepseek,
        }

        fn = test_map.get(self.key_name)
        if fn:
            result = fn(self.api_key)
            self.result_signal.emit(self.key_name, result["ok"], result["message"])
        else:
            self.result_signal.emit(self.key_name, False, "不支持的测试类型")


class EnvCheckWorker(QThread):
    """Background worker for full environment check."""
    finished_signal = Signal(str)  # formatted report

    def run(self):
        from config.api_validator import APIValidator
        report = APIValidator.check_environment()
        formatted = APIValidator.format_env_report(report)
        self.finished_signal.emit(formatted)


class SettingsTab(QWidget):
    """Settings Center — API keys + app configuration."""

    TESTABLE_KEYS = [
        ("OPENAI_API_KEY", "OpenAI API Key", "sk-...", "用于 GPT-4o 文本生成 + DALL-E 3 图像生成"),
        ("ELEVENLABS_API_KEY", "ElevenLabs API Key", "el_...", "用于 TTS 语音合成（口播配音）"),
        ("ARK_API_KEY", "火山引擎 ARK API Key", "ark-...", "用于 Seedance 视频生成"),
    ]

    EXTRA_KEYS = [
        ("ANTHROPIC_API_KEY", "Claude API Key", "sk-ant-...", "可选：替代 OpenAI 进行文本生成"),
        ("DEEPSEEK_API_KEY", "DeepSeek API Key", "sk-...", "可选：DeepSeek 文本生成"),
    ]

    COUNTRIES = {
        "English (US)": ("US", "en"),
        "English (UK)": ("GB", "en"),
        "Malay": ("MY", "ms"),
        "Indonesian": ("ID", "id"),
        "Spanish": ("ES", "es"),
        "German": ("DE", "de"),
        "French": ("FR", "fr"),
    }

    CHARACTERS = [
        "UGC Female",
        "UGC Male",
        "Beauty Creator",
        "Skincare Expert",
        "Lifestyle Creator",
    ]

    VIDEO_PROVIDERS = ["Seedance", "Jimeng", "Runway", "Veo3"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_mgr = None
        self._key_inputs = {}
        self._status_labels = {}
        self._test_workers = []

        self._build_ui()

    def showEvent(self, event):
        """Load settings when tab becomes visible."""
        super().showEvent(event)
        self._load_current_settings()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ---- Header ----
        header = QHBoxLayout()
        title = QLabel("⚙️ 设置中心")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e94560;")
        desc = QLabel("管理 API 配置和应用设置")
        desc.setStyleSheet("font-size: 12px; color: #8b949e; padding-top: 6px;")
        header.addWidget(title)
        header.addWidget(desc)
        header.addStretch()

        # Environment check button
        self.env_btn = QPushButton("🔍 环境检测")
        self.env_btn.setMinimumWidth(130)
        self.env_btn.clicked.connect(self._run_env_check)
        self.env_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb; color: white;
                border: none; border-radius: 6px;
                padding: 8px 16px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #388bfd; }
        """)
        header.addWidget(self.env_btn)
        layout.addLayout(header)

        # ---- Section 1: API Keys ----
        api_group = self._make_section("🔑 API Key 配置")
        api_layout = QVBoxLayout()

        for key_name, display, placeholder, hint in self.TESTABLE_KEYS:
            row = self._make_api_key_row(key_name, display, placeholder, hint)
            api_layout.addLayout(row)

        # Separator for optional keys
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border-color: #30363d; margin: 8px 0;")
        api_layout.addWidget(sep)

        for key_name, display, placeholder, hint in self.EXTRA_KEYS:
            row = self._make_api_key_row(key_name, display, placeholder, hint, testable=True)
            api_layout.addLayout(row)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # ---- Section 2: App Settings ----
        app_group = self._make_section("🎛️ 应用设置")
        app_layout = QGridLayout()
        app_layout.setSpacing(14)

        # Video model
        app_layout.addWidget(self._make_setting_label("视频模型"), 0, 0)
        self.video_provider_combo = QComboBox()
        self.video_provider_combo.addItems(self.VIDEO_PROVIDERS)
        self.video_provider_combo.setStyleSheet(self._combo_style())
        app_layout.addWidget(self.video_provider_combo, 0, 1)

        # Country/Language
        app_layout.addWidget(self._make_setting_label("国家 / 语言"), 1, 0)
        self.country_combo = QComboBox()
        for label in self.COUNTRIES.keys():
            self.country_combo.addItem(label)
        self.country_combo.setStyleSheet(self._combo_style())
        app_layout.addWidget(self.country_combo, 1, 1)
        app_layout.addWidget(self._make_setting_label("默认人物"), 2, 0)

        # Character type
        self.character_combo = QComboBox()
        self.character_combo.addItems(self.CHARACTERS)
        self.character_combo.setStyleSheet(self._combo_style())
        app_layout.addWidget(self.character_combo, 2, 1)

        # AI provider
        app_layout.addWidget(self._make_setting_label("AI 文本模型"), 3, 0)
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems(["claude", "openai", "deepseek", "gemini"])
        self.ai_provider_combo.setStyleSheet(self._combo_style())
        app_layout.addWidget(self.ai_provider_combo, 3, 1)

        # Update URL
        app_layout.addWidget(self._make_setting_label("更新服务器"), 4, 0)
        self.update_url_input = QLineEdit()
        self.update_url_input.setPlaceholderText("https://your-domain/version.json")
        self.update_url_input.setStyleSheet(self._input_style())
        app_layout.addWidget(self.update_url_input, 4, 1)

        app_group.setLayout(app_layout)
        layout.addWidget(app_group)

        # ---- Save Button ----
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.setMinimumSize(200, 48)
        self.save_btn.clicked.connect(self._save_all)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: white;
                border: none; border-radius: 8px;
                font-size: 15px; font-weight: bold;
                padding: 10px 32px;
            }
            QPushButton:hover { background-color: #2ea043; }
            QPushButton:disabled { background-color: #21262d; color: #484f58; }
        """)
        btn_row.addWidget(self.save_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ---- Environment Report ----
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setMinimumHeight(120)
        self.report_view.setMaximumHeight(220)
        self.report_view.setPlaceholderText("点击「环境检测」查看系统状态报告...")
        self.report_view.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117; color: #c9d1d9;
                border: 1px solid #30363d; border-radius: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px; padding: 10px;
            }
        """)
        layout.addWidget(self.report_view)
        layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ---- API Key Row Builder ----
    def _make_api_key_row(self, key_name, display, placeholder, hint, testable=True):
        row = QHBoxLayout()
        row.setSpacing(10)

        # Label
        lbl = QLabel(display)
        lbl.setStyleSheet("color: #c9d1d9; font-size: 12px; font-weight: bold; min-width: 140px;")
        lbl.setToolTip(hint)
        row.addWidget(lbl)

        # Input
        input_widget = QLineEdit()
        input_widget.setPlaceholderText(placeholder)
        input_widget.setEchoMode(QLineEdit.Password)
        input_widget.setStyleSheet(self._input_style())
        input_widget.setMinimumWidth(280)
        self._key_inputs[key_name] = input_widget

        # Show/hide toggle
        show_btn = QPushButton("👁")
        show_btn.setFixedSize(32, 32)
        show_btn.setToolTip("显示/隐藏 Key")
        show_btn.setCheckable(True)
        show_btn.toggled.connect(lambda checked, inp=input_widget: (
            inp.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        ))
        show_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262d; border: 1px solid #30363d;
                border-radius: 4px; font-size: 14px;
            }
            QPushButton:checked { background-color: #1f6feb; }
        """)

        row.addWidget(input_widget)
        row.addWidget(show_btn)

        # Test button
        if testable:
            test_btn = QPushButton("测试连接")
            test_btn.setStyleSheet("""
                QPushButton {
                    background-color: #21262d; color: #58a6ff;
                    border: 1px solid #30363d; border-radius: 6px;
                    padding: 6px 14px; font-size: 11px;
                }
                QPushButton:hover { background-color: #30363d; }
            """)
            test_btn.clicked.connect(lambda checked, kn=key_name, inp=input_widget: self._test_api(kn, inp.text()))
            row.addWidget(test_btn)

        # Status label
        status_lbl = QLabel("")
        status_lbl.setStyleSheet("font-size: 11px; min-width: 140px;")
        self._status_labels[key_name] = status_lbl
        row.addWidget(status_lbl)

        return row

    # ---- Build helpers ----
    def _make_section(self, title):
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: #c9d1d9; border: 1px solid #30363d;
                border-radius: 10px; margin-top: 14px; padding-top: 22px;
                font-weight: bold; font-size: 13px; background-color: #161b22;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
        """)
        return group

    @staticmethod
    def _make_setting_label(text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: bold;")
        return lbl

    @staticmethod
    def _combo_style():
        return """
            QComboBox {
                background-color: #21262d; color: #c9d1d9;
                border: 1px solid #30363d; border-radius: 6px;
                padding: 7px 12px; font-size: 12px; min-width: 160px;
            }
            QComboBox:hover { border-color: #58a6ff; }
            QComboBox QAbstractItemView {
                background-color: #161b22; color: #c9d1d9;
                selection-background-color: #1f6feb;
                border: 1px solid #30363d;
            }
        """

    @staticmethod
    def _input_style():
        return """
            QLineEdit {
                background-color: #0d1117; color: #c9d1d9;
                border: 1px solid #30363d; border-radius: 6px;
                padding: 7px 12px; font-size: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QLineEdit:focus { border-color: #58a6ff; }
        """

    # ---- Load / Save ----
    def _load_current_settings(self):
        """Populate UI from current .env and settings.json."""
        if self.settings_mgr is None:
            from config.settings_manager import SettingsManager
            self.settings_mgr = SettingsManager()

        sm = self.settings_mgr

        # API keys
        for key_name in self._key_inputs:
            val = sm.get_api_key(key_name)
            if val:
                self._key_inputs[key_name].setText(val)

        # App settings from settings.json
        sj = sm.read_settings_json()

        # Video provider
        vp = sm.get_video_provider()
        idx = self.video_provider_combo.findText(vp.capitalize() if vp else "Seedance")
        if idx >= 0:
            self.video_provider_combo.setCurrentIndex(idx)

        # Country/Language
        country, lang = sm.get_country_language()
        for i, (label, (c, l)) in enumerate(self.COUNTRIES.items()):
            if c == country:
                self.country_combo.setCurrentIndex(i)
                break

        # Character
        char_type = sm.get_default_character()
        idx = self.character_combo.findText(char_type)
        if idx >= 0:
            self.character_combo.setCurrentIndex(idx)

        # AI provider
        ai_prov = os.getenv("TIKTOK_FACTORY_AI_PROVIDER", "claude")
        idx = self.ai_provider_combo.findText(ai_prov)
        if idx >= 0:
            self.ai_provider_combo.setCurrentIndex(idx)

        # Update URL
        update_url = os.getenv("TIKTOK_FACTORY_UPDATE_URL", "")
        if update_url and "your-domain" not in update_url:
            self.update_url_input.setText(update_url)

    def _save_all(self):
        """Save all settings to .env and settings.json."""
        if self.settings_mgr is None:
            from config.settings_manager import SettingsManager
            self.settings_mgr = SettingsManager()

        sm = self.settings_mgr

        # Collect API keys
        api_updates = {}
        for key_name, inp in self._key_inputs.items():
            val = inp.text().strip()
            if val:
                api_updates[key_name] = val
                os.environ[key_name] = val

        # Write .env
        sm.write_env(api_updates)

        # Collect app settings
        country_label = self.country_combo.currentText()
        country, lang = self.COUNTRIES.get(country_label, ("US", "en"))
        settings = {
            "video": {"provider": self.video_provider_combo.currentText().lower()},
            "target": {"country": country, "language": lang},
            "character": {"default_type": self.character_combo.currentText()},
        }
        sm.write_settings_json(settings)

        # Also write env vars for app settings
        env_settings = {
            "TIKTOK_FACTORY_AI_PROVIDER": self.ai_provider_combo.currentText(),
            "TIKTOK_FACTORY_COUNTRY": country,
            "TIKTOK_FACTORY_LANGUAGE": lang,
            "TIKTOK_FACTORY_VIDEO_PROVIDER": self.video_provider_combo.currentText().lower(),
            "TIKTOK_FACTORY_DEFAULT_CHARACTER": self.character_combo.currentText(),
        }
        update_url = self.update_url_input.text().strip()
        if update_url:
            env_settings["TIKTOK_FACTORY_UPDATE_URL"] = update_url
        sm.write_env(env_settings)

        QMessageBox.information(self, "保存成功", "✅ 所有配置已保存！\n\n.env 和 settings.json 已更新。")

    # ---- API Test ----
    def _test_api(self, key_name, key_value):
        if not key_value.strip():
            self._status_labels[key_name].setText("⚠ 请先输入 Key")
            self._status_labels[key_name].setStyleSheet("color: #d29922; font-size: 11px; min-width: 140px;")
            return

        self._status_labels[key_name].setText("⏳ 正在测试...")
        self._status_labels[key_name].setStyleSheet("color: #58a6ff; font-size: 11px; min-width: 140px;")

        worker = ApiTestWorker(key_name, key_value.strip())
        worker.result_signal.connect(self._on_test_result)
        worker.start()
        self._test_workers.append(worker)

    def _on_test_result(self, key_name, ok, message):
        if key_name in self._status_labels:
            color = "#238636" if ok else "#da3633"
            self._status_labels[key_name].setText(message)
            self._status_labels[key_name].setStyleSheet(f"color: {color}; font-size: 11px; min-width: 140px;")

    # ---- Environment Check ----
    def _run_env_check(self):
        self.env_btn.setEnabled(False)
        self.env_btn.setText("⏳ 检测中...")
        self.report_view.setPlainText("正在检测环境，请稍候...")

        self.env_worker = EnvCheckWorker()
        self.env_worker.finished_signal.connect(self._on_env_report)
        self.env_worker.start()

    def _on_env_report(self, report_text):
        self.env_btn.setEnabled(True)
        self.env_btn.setText("🔍 环境检测")
        self.report_view.setPlainText(report_text)
