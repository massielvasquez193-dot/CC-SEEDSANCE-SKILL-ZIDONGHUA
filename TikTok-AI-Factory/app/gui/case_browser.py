"""
TikTok AI Factory Pro — Case Browser
=======================================
GUI tab for browsing the case library. Click a brand → preview all 10 assets.

Features:
  - Brand selector (Medicube / Anua / COSRX)
  - Asset grid with thumbnails
  - Script / Storyboard / Character preview
  - One-click copy settings to current session
  - Video playback
"""

import json
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QGroupBox, QScrollArea, QFrame, QGridLayout,
    QMessageBox, QListWidget, QListWidgetItem, QSplitter,
    QSpacerItem, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon


class CaseBrowser(QWidget):
    """Case Library Browser — browse, preview, and copy case settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.case_root = self.project_root / "case_library"
        self._current_case = None
        self._case_data = None
        self._build_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_case_index()

    # ================================================================
    # UI
    # ================================================================

    def _build_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        # LEFT: Brand list
        left = self._build_left_panel()
        splitter.addWidget(left)

        # RIGHT: Preview area
        right = self._build_right_panel()
        splitter.addWidget(right)

        splitter.setSizes([280, 1000])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(splitter)

    def _build_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 8, 16)
        layout.setSpacing(10)

        title = QLabel("📚 案例库")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e94560;")
        layout.addWidget(title)

        desc = QLabel("K-Beauty 护肤品牌案例\n点击品牌查看完整资产")
        desc.setStyleSheet("font-size: 11px; color: #8b949e;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(8)

        self.brand_list = QListWidget()
        self.brand_list.setStyleSheet("""
            QListWidget { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; }
            QListWidget::item { padding: 14px; border-bottom: 1px solid #21262d; color: #c9d1d9; font-size: 13px; }
            QListWidget::item:selected { background: #1f6feb; color: white; }
            QListWidget::item:hover { background: #161b22; }
        """)
        self.brand_list.currentRowChanged.connect(self._on_brand_selected)
        layout.addWidget(self.brand_list, 1)

        # Copy button
        self.copy_btn = QPushButton("📋 一键复制配置")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_config)
        self.copy_btn.setStyleSheet("""
            QPushButton { background: #238636; color: white; border: none;
                border-radius: 6px; padding: 10px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background: #2ea043; }
            QPushButton:disabled { background: #21262d; color: #484f58; }
        """)
        layout.addWidget(self.copy_btn)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._load_case_index)
        refresh_btn.setStyleSheet("""
            QPushButton { background: #21262d; color: #8b949e; border: 1px solid #30363d;
                border-radius: 6px; padding: 6px; font-size: 12px; }
            QPushButton:hover { background: #30363d; }
        """)
        layout.addWidget(refresh_btn)

        return panel

    def _build_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        self.case_title = QLabel("选择一个品牌查看案例")
        self.case_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #c9d1d9;")
        header.addWidget(self.case_title)
        header.addStretch()
        self.case_meta = QLabel("")
        self.case_meta.setStyleSheet("font-size: 11px; color: #8b949e;")
        header.addWidget(self.case_meta)
        layout.addLayout(header)

        # Asset grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.asset_content = QWidget()
        self.asset_layout = QVBoxLayout(self.asset_content)
        self.asset_layout.setSpacing(10)

        # Placeholder
        self.placeholder = QLabel(
            "👈 从左侧选择一个品牌案例\n\n"
            "案例库包含以下 K-Beauty 品牌：\n"
            "• Medicube — Deep Vita C Pad\n"
            "• Anua — Heartleaf 77% Soothing Toner\n"
            "• COSRX — Advanced Snail 96 Mucin Power Essence\n\n"
            "每个案例包含 10 项完整资产：\n"
            "产品图 · 人物图 · GPT脚本 · 人物设定 ·\n"
            "关键帧 · Storyboard · 口播 · 字幕 · 视频 · 报告"
        )
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("font-size: 13px; color: #484f58; padding: 80px;")
        self.asset_layout.addWidget(self.placeholder)

        scroll.setWidget(self.asset_content)
        layout.addWidget(scroll, 1)

        return panel

    # ================================================================
    # Data
    # ================================================================

    def _load_case_index(self):
        """Load the case library index and populate the brand list."""
        self.brand_list.clear()
        index_path = self.case_root / "case_index.json"

        if not index_path.exists():
            self.brand_list.addItem("案例库为空 — 运行 tools/case_generator.py")
            return

        try:
            self._case_data = json.loads(index_path.read_text(encoding="utf-8"))
            for brand in self._case_data.get("brands", []):
                item = QListWidgetItem(f"{brand['name']}\n{brand['product']}")
                item.setData(Qt.UserRole, brand)
                item.setSizeHint(QSize(0, 60))
                self.brand_list.addItem(item)
        except Exception as e:
            self.brand_list.addItem(f"加载失败: {e}")

    def _on_brand_selected(self, row):
        if row < 0:
            return
        item = self.brand_list.item(row)
        brand = item.data(Qt.UserRole)
        if not brand:
            return
        self._current_case = brand
        self._show_case(brand)

    def _show_case(self, brand: dict):
        """Display all 10 assets for the selected brand."""
        self.case_title.setText(f"{brand['name']} — {brand['product']}")
        self.case_meta.setText(f"{brand['category']} | {brand['assets']} assets")
        self.copy_btn.setEnabled(True)

        # Clear placeholder
        self.placeholder.hide()
        # Clear existing asset cards
        while self.asset_layout.count():
            w = self.asset_layout.takeAt(0)
            if w.widget():
                w.widget().deleteLater()

        brand_dir = self.case_root / brand["name"]

        # Asset definitions
        assets = [
            ("01_PRODUCT", "📦 产品图", "Product image card", ".png"),
            ("02_CHARACTER", "👤 人物图", "Character profile sheet", ".png"),
            ("03_SCRIPT", "📝 GPT脚本", "Master script (Hook→CTA)", ".md"),
            ("04_CHARACTER_SETTING", "⚙️ 人物设定", "Character canon JSON", ".json"),
            ("05_KEYFRAMES", "🖼️ 关键帧", "5 keyframe images", ""),
            ("06_STORYBOARD", "🎬 Storyboard", "Visual storyboard grid", ".png"),
            ("07_VOICEOVER", "🎤 口播脚本", "Voiceover with TTS settings", ".md"),
            ("08_SUBTITLES", "💬 字幕", "SRT subtitle file", ".srt"),
            ("09_VIDEO", "🎥 Final Video", "30s composite video", ".mp4"),
            ("10_PERFORMANCE_REPORT", "📊 性能报告", "Full performance analysis", ".md"),
        ]

        for prefix, title, desc, ext in assets:
            card = self._make_asset_card(brand_dir, brand["name"], prefix, title, desc, ext)
            self.asset_layout.addWidget(card)

        self.asset_layout.addStretch()

    def _make_asset_card(self, brand_dir, brand_name, prefix, title, desc, ext):
        """Create a clickable asset preview card."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background: #161b22; border: 1px solid #30363d;
                border-radius: 8px; padding: 12px; }
            QFrame:hover { border-color: #58a6ff; }
        """)
        card.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Icon + title
        text_layout = QVBoxLayout()
        name_lbl = QLabel(title)
        name_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #c9d1d9;")
        text_layout.addWidget(name_lbl)
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("font-size: 11px; color: #8b949e;")
        text_layout.addWidget(desc_lbl)
        layout.addLayout(text_layout, 1)

        # Status badge
        found = False
        if ext:
            path = brand_dir / f"{prefix}_{brand_name}{ext}"
            found = path.exists()
        else:
            # Directory check (keyframes)
            path = brand_dir / prefix
            found = path.exists() and path.is_dir() and len(list(path.glob("*"))) > 0

        badge = QLabel("✅ 就绪" if found else "⚠ 未生成")
        badge.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {'#238636' if found else '#8b949e'};")
        layout.addWidget(badge)

        # View button
        if found:
            view_btn = QPushButton("查看")
            view_btn.setFixedSize(60, 30)
            view_btn.clicked.connect(lambda checked, p=path: self._view_asset(p, prefix))
            view_btn.setStyleSheet("""
                QPushButton { background: #1f6feb; color: white; border: none;
                    border-radius: 4px; font-size: 11px; }
                QPushButton:hover { background: #388bfd; }
            """)
            layout.addWidget(view_btn)

        return card

    def _view_asset(self, path: Path, prefix: str):
        """Open or display an asset."""
        if not path.exists():
            return

        if path.suffix in (".png", ".jpg", ".jpeg"):
            os.startfile(str(path))
        elif path.suffix in (".mp4", ".mov"):
            os.startfile(str(path))
        elif path.suffix in (".md", ".txt", ".srt"):
            # Show in a dialog
            content = path.read_text(encoding="utf-8")
            dlg = QMessageBox(self)
            dlg.setWindowTitle(path.name)
            dlg.setText(content[:2000])
            dlg.setDetailedText(content)
            dlg.exec()
        elif path.is_dir():
            os.startfile(str(path))
        elif path.suffix == ".json":
            content = path.read_text(encoding="utf-8")
            try:
                formatted = json.dumps(json.loads(content), indent=2, ensure_ascii=False)
            except Exception:
                formatted = content
            dlg = QMessageBox(self)
            dlg.setWindowTitle(path.name)
            dlg.setText(formatted[:2000])
            dlg.setDetailedText(formatted)
            dlg.exec()

    def _copy_config(self):
        """Copy the current case's settings for use in the main pipeline."""
        if not self._current_case:
            return

        brand = self._current_case
        brand_dir = self.case_root / brand["name"]

        # Collect all settings
        settings = {"brand": brand["name"], "product": brand["product"], "copied_at": __import__('datetime').datetime.now().isoformat()}

        # Read character setting
        char_path = brand_dir / f"04_CHARACTER_SETTING_{brand['name']}.json"
        if char_path.exists():
            try:
                settings["character_canon"] = json.loads(char_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Read script
        script_path = brand_dir / f"03_SCRIPT_{brand['name']}.md"
        if script_path.exists():
            settings["script"] = script_path.read_text(encoding="utf-8")

        # Read performance report
        report_path = brand_dir / f"10_PERFORMANCE_REPORT_{brand['name']}.md"
        if report_path.exists():
            settings["performance_report"] = report_path.read_text(encoding="utf-8")

        # Save to clipboard-friendly JSON
        copy_path = self.case_root / f"copied_config_{brand['name']}.json"
        copy_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")

        QMessageBox.information(
            self,
            "配置已复制",
            f"✅ {brand['name']} 的完整配置已导出！\n\n"
            f"📁 保存位置:\n{copy_path}\n\n"
            f"包含:\n"
            f"• 产品信息\n"
            f"• 人物设定 (character canon)\n"
            f"• GPT 脚本\n"
            f"• 性能报告\n\n"
            f"可以直接导入到主流水线中使用。"
        )
