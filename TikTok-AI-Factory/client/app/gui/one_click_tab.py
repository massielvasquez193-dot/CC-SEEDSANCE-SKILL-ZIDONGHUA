"""
TikTok AI Factory Pro — One Click Generate Tab
================================================
Upload + click → auto-pipeline → final video.

Layout:
  ┌─────────────────────────────────────────────┐
  │  🎬 一键生成                                 │
  │                                             │
  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐│
  │  │ 产品图片  │ │ 人物图片  │ │ 参考视频      ││
  │  │ [上传]   │ │ [上传]   │ │ [上传]       ││
  │  └──────────┘ └──────────┘ └──────────────┘│
  │                                             │
  │  国家: [▼]  数量: [▼]  风格: [▼]            │
  │                                             │
  │  [  🚀 开始生成  ]                          │
  │                                             │
  │  ████████████░░░░░░░░  65%                   │
  │                                             │
  │  STEP1 ✓  STEP2 ✓  STEP3 ●  STEP4 …  …     │
  │                                             │
  │  实时日志:                                   │
  │  ┌─────────────────────────────────────────┐│
  │  │ ...                                     ││
  │  └─────────────────────────────────────────┘│
  │                                             │
  │  输出:                                       │
  │  video_001.mp4  video_002.mp4  ...          │
  └─────────────────────────────────────────────┘
"""

import os
import sys
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QProgressBar, QTextEdit, QFileDialog, QGroupBox,
    QScrollArea, QFrame, QMessageBox, QGridLayout, QSizePolicy,
    QSpacerItem,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont


class OneClickWorker(QThread):
    """Background worker that runs the one-click pipeline."""
    progress_signal = Signal(int, str)       # percent, message
    step_signal = Signal(int, str)           # step_number, step_name
    log_signal = Signal(str)                 # log line
    finished_signal = Signal(bool, object)   # success, results

    def __init__(self, product_path, character_path, video_path,
                 country, video_count, style):
        super().__init__()
        self.product_path = product_path
        self.character_path = character_path
        self.video_path = video_path
        self.country = country
        self.video_count = video_count
        self.style = style
        self._controller = None

    def stop(self):
        if self._controller:
            self._controller.cancel()

    def run(self):
        try:
            from app.gui.one_click_controller import OneClickController
            self._controller = OneClickController()

            result = self._controller.run(
                product_path=self.product_path,
                character_path=self.character_path,
                video_path=self.video_path,
                country=self.country,
                video_count=self.video_count,
                style=self.style,
                progress_callback=lambda p, m: self.progress_signal.emit(p, m),
                step_callback=lambda n, name: self.step_signal.emit(n, name),
                log_callback=lambda m: self.log_signal.emit(m),
            )
            self.finished_signal.emit(True, result)
        except Exception as e:
            import traceback
            self.finished_signal.emit(False, {"error": str(e), "trace": traceback.format_exc()})


class OneClickTab(QWidget):
    """One Click Generate — the simplest workflow UI."""

    COUNTRIES = ["美国", "英国", "马来西亚", "印尼", "德国", "法国", "西班牙"]
    VIDEO_COUNTS = [1, 3, 5, 10]
    STYLES = [
        "TikTok UGC", "Beauty Review", "Problem Solution",
        "Before After", "Testimonial", "POV Story",
    ]

    STYLE_LABELS = {
        "TikTok UGC": "TikTok UGC — 真实创作者风格",
        "Beauty Review": "Beauty Review — 美妆测评",
        "Problem Solution": "Problem Solution — 痛点解决",
        "Before After": "Before After — 前后对比",
        "Testimonial": "Testimonial — 用户证言",
        "POV Story": "POV Story — 第一人称故事",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.product_path = None
        self.character_path = None
        self.video_path = None
        self.worker = None
        self.video_outputs = []

        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # ---- Header ----
        header = QHBoxLayout()
        title = QLabel("🎬 一键生成")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e94560;")
        subtitle = QLabel("上传素材 → 点击开始 → 获得视频")
        subtitle.setStyleSheet("font-size: 12px; color: #8b949e; padding-top: 6px;")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch()
        layout.addLayout(header)

        # ---- Upload Cards Row ----
        uploads = QHBoxLayout()
        uploads.setSpacing(12)

        self.product_card = self._make_upload_card("📦 产品图片", "jpg / png / webp", "#e94560")
        self.product_card["btn"].clicked.connect(lambda: self._upload("product"))
        uploads.addWidget(self.product_card["group"])

        self.char_card = self._make_upload_card("👤 人物图片", "jpg / png", "#1f6feb")
        self.char_card["btn"].clicked.connect(lambda: self._upload("character"))
        uploads.addWidget(self.char_card["group"])

        self.video_card = self._make_upload_card("🎥 参考视频", "mp4", "#238636")
        self.video_card["btn"].clicked.connect(lambda: self._upload("video"))
        uploads.addWidget(self.video_card["group"])

        layout.addLayout(uploads)

        # ---- Config Row ----
        config_row = QHBoxLayout()
        config_row.setSpacing(12)

        # Country
        config_row.addWidget(self._make_label("目标国家"))
        self.country_combo = QComboBox()
        self.country_combo.addItems(self.COUNTRIES)
        self.country_combo.setStyleSheet(self._combo_style())
        self.country_combo.setMinimumWidth(100)
        config_row.addWidget(self.country_combo)

        config_row.addSpacing(20)

        # Video count
        config_row.addWidget(self._make_label("视频数量"))
        self.count_combo = QComboBox()
        for c in self.VIDEO_COUNTS:
            self.count_combo.addItem(str(c), c)
        self.count_combo.setStyleSheet(self._combo_style())
        self.count_combo.setMinimumWidth(70)
        config_row.addWidget(self.count_combo)

        config_row.addSpacing(20)

        # Style
        config_row.addWidget(self._make_label("视频风格"))
        self.style_combo = QComboBox()
        for s in self.STYLES:
            self.style_combo.addItem(self.STYLE_LABELS.get(s, s), s)
        self.style_combo.setStyleSheet(self._combo_style())
        self.style_combo.setMinimumWidth(200)
        config_row.addWidget(self.style_combo)

        config_row.addStretch()
        layout.addLayout(config_row)

        # ---- Start Button ----
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.start_btn = QPushButton("🚀 开始生成")
        self.start_btn.setMinimumSize(240, 52)
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560; color: white;
                border: none; border-radius: 8px;
                font-size: 17px; font-weight: bold;
                padding: 12px 40px;
            }
            QPushButton:hover { background-color: #ff6b81; }
            QPushButton:disabled { background-color: #21262d; color: #484f58; }
        """)
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setMinimumSize(100, 52)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #da3633; color: white;
                border: none; border-radius: 8px;
                font-size: 14px; font-weight: bold;
                padding: 12px 20px;
            }
            QPushButton:hover { background-color: #f85149; }
            QPushButton:disabled { background-color: #21262d; color: #484f58; }
        """)
        btn_row.addWidget(self.stop_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ---- Progress Bar ----
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none; border-radius: 5px;
                background-color: #21262d;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e94560, stop:0.5 #ff6b3d, stop:1 #238636);
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # ---- Step Indicators ----
        self.step_labels = {}
        step_row = QHBoxLayout()
        step_row.setSpacing(8)
        step_names = [
            (1, "GPT脚本"), (2, "人物分析"), (3, "分镜生成"),
            (4, "关键帧"), (5, "Seedance"), (6, "视频生成"),
            (7, "口播"), (8, "字幕"), (9, "合成"),
        ]
        for num, name in step_names:
            lbl = QLabel(f"○ {name}")
            lbl.setStyleSheet("font-size: 10px; color: #484f58; padding: 2px 6px;")
            step_row.addWidget(lbl)
            self.step_labels[num] = lbl
        step_row.addStretch()
        layout.addLayout(step_row)

        # ---- Log Area ----
        log_label = QLabel("实时日志")
        log_label.setStyleSheet("font-size: 12px; color: #8b949e; font-weight: bold;")
        layout.addWidget(log_label)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(160)
        self.log_view.setMaximumHeight(260)
        self.log_view.setPlaceholderText("上传素材后点击「开始生成」，日志将在此显示...")
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117; color: #c9d1d9;
                border: 1px solid #30363d; border-radius: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px; padding: 10px;
            }
        """)
        layout.addWidget(self.log_view)

        # ---- Output Videos ----
        self.output_label = QLabel("")
        self.output_label.setWordWrap(True)
        self.output_label.setStyleSheet("font-size: 12px; color: #238636;")
        layout.addWidget(self.output_label)

        self.open_btn = QPushButton("📂 打开输出目录")
        self.open_btn.setVisible(False)
        self.open_btn.clicked.connect(self._open_output)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb; color: white;
                border: none; border-radius: 6px;
                padding: 8px 16px; font-size: 12px;
            }
            QPushButton:hover { background-color: #388bfd; }
        """)
        layout.addWidget(self.open_btn)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ---- Upload card helper ----
    def _make_upload_card(self, title, formats, accent_color):
        group = QGroupBox()
        group.setStyleSheet(f"""
            QGroupBox {{
                color: #c9d1d9; border: 1px solid #30363d;
                border-radius: 10px; margin-top: 14px; padding-top: 22px;
                font-weight: bold; font-size: 12px;
                background-color: #161b22;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 14px; padding: 0 6px;
            }}
        """)
        group.setTitle(title)
        group.setMinimumHeight(140)

        v = QVBoxLayout()
        btn = QPushButton(f"+ 点击上传")
        btn.setMinimumHeight(90)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0d1117;
                border: 2px dashed {accent_color};
                border-radius: 8px;
                color: {accent_color};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {accent_color}22;
                border-color: {accent_color};
            }}
        """)
        v.addWidget(btn)

        lbl = QLabel(formats)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #484f58; font-size: 10px;")
        v.addWidget(lbl)
        group.setLayout(v)
        return {"group": group, "btn": btn, "label": lbl}

    @staticmethod
    def _make_label(text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: bold;")
        return lbl

    @staticmethod
    def _combo_style():
        return """
            QComboBox {
                background-color: #21262d; color: #c9d1d9;
                border: 1px solid #30363d; border-radius: 6px;
                padding: 6px 12px; font-size: 12px;
            }
            QComboBox:hover { border-color: #58a6ff; }
            QComboBox QAbstractItemView {
                background-color: #161b22; color: #c9d1d9;
                selection-background-color: #1f6feb;
                border: 1px solid #30363d;
            }
        """

    # ---- Upload ----
    def _upload(self, file_type):
        filters = {
            "product": "Images (*.jpg *.jpeg *.png *.webp)",
            "character": "Images (*.jpg *.jpeg *.png)",
            "video": "Videos (*.mp4)",
        }
        path, _ = QFileDialog.getOpenFileName(self, f"选择{file_type}文件", "", filters[file_type])
        if not path:
            return

        name = Path(path).name
        size_mb = Path(path).stat().st_size / (1024 * 1024)

        if file_type == "product":
            self.product_path = path
            card = self.product_card
        elif file_type == "character":
            self.character_path = path
            card = self.char_card
        else:
            self.video_path = path
            card = self.video_card

        card["btn"].setText(f"✓ {name}")
        card["btn"].setStyleSheet(card["btn"].styleSheet().replace(
            "border: 2px dashed", "border: 2px solid").replace(
            "color:", "color: #238636;"))
        card["label"].setText(f"{size_mb:.1f} MB")
        card["label"].setStyleSheet("color: #238636; font-size: 10px;")

        self._check_ready()

    def _check_ready(self):
        ready = all([self.product_path, self.character_path, self.video_path])
        self.start_btn.setEnabled(ready)
        if ready:
            self.start_btn.setText("🚀 开始生成")
        else:
            self.start_btn.setText("📎 请上传全部 3 个素材")

    # ---- Start / Stop ----
    def _start(self):
        if not all([self.product_path, self.character_path, self.video_path]):
            QMessageBox.warning(self, "缺少素材", "请先上传产品图片、人物图片和参考视频。")
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_view.clear()
        self.open_btn.setVisible(False)
        self.output_label.setText("")
        self.video_outputs = []

        # Reset step indicators
        for lbl in self.step_labels.values():
            lbl.setStyleSheet("font-size: 10px; color: #484f58; padding: 2px 6px;")

        self.worker = OneClickWorker(
            self.product_path, self.character_path, self.video_path,
            self.country_combo.currentText(),
            self.count_combo.currentData(),
            self.style_combo.currentData(),
        )
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.step_signal.connect(self._on_step)
        self.worker.log_signal.connect(self._on_log)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait(3000)
        self._log_msg("⏹ 用户停止了生成")
        self._reset_ui()

    def _on_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.progress_bar.setFormat(f"{msg}  {pct}%")

    def _on_step(self, num, name):
        # Update step indicators
        for n, lbl in self.step_labels.items():
            if n < num:
                lbl.setText(f"✓ {lbl.text()[2:]}")
                lbl.setStyleSheet("font-size: 10px; color: #238636; font-weight: bold; padding: 2px 6px;")
            elif n == num:
                lbl.setText(f"● {name}")
                lbl.setStyleSheet("font-size: 10px; color: #e94560; font-weight: bold; padding: 2px 6px;")

    def _on_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        # Color ANSI-style markers
        if msg.startswith("✅") or "完成" in msg:
            color = "#238636"
        elif msg.startswith("⚠") or "跳过" in msg:
            color = "#d29922"
        elif msg.startswith("❌") or "失败" in msg:
            color = "#da3633"
        elif msg.startswith("="):
            color = "#8b949e"
        else:
            color = "#c9d1d9"
        self.log_view.append(f'<span style="color:{color}">[{ts}] {msg}</span>')

    def _on_finished(self, success, result):
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success and result.get("status") == "completed":
            self.video_outputs = result.get("videos", [])
            output_dir = result.get("output_dir", "")
            elapsed = result.get("elapsed_seconds", 0)
            count = len(self.video_outputs)

            self.output_label.setText(
                f"✅ 生成完成！用时 {elapsed:.0f} 秒 · 输出 {count} 个视频\n"
                f"📁 {output_dir}"
            )
            self.output_label.setStyleSheet("font-size: 13px; color: #238636; font-weight: bold; padding: 8px 0;")
            self.open_btn.setVisible(True)
            self._output_dir = output_dir

            for vpath in self.video_outputs:
                self._log_msg(f"🎬 输出视频: {vpath}")

            # Show completion dialog
            QMessageBox.information(
                self, "生成完成",
                f"视频已生成完毕！\n\n"
                f"输出目录: {output_dir}\n"
                f"视频数量: {count} 个\n"
                f"用时: {elapsed:.0f} 秒"
            )
        else:
            error = result.get("error", "未知错误") if isinstance(result, dict) else str(result)
            self._log_msg(f"❌ 生成失败: {error}")
            self.output_label.setText(f"❌ 生成失败: {error[:100]}")
            self.output_label.setStyleSheet("font-size: 12px; color: #da3633; padding: 8px 0;")

    def _log_msg(self, msg):
        self._on_log(msg)

    def _open_output(self):
        if hasattr(self, '_output_dir') and self._output_dir:
            os.startfile(self._output_dir)

    def _reset_ui(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
