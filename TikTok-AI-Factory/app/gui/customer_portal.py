"""
TikTok AI Factory Pro — Customer Portal
=========================================
Full customer dashboard: License, Usage, Cost, Video History,
Task Stats, Update Center, System Status.

7 modules in a single scrollable tab with card-based layout.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QProgressBar, QTextEdit, QGroupBox, QScrollArea,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QSpacerItem, QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QBrush


class CustomerPortal(QWidget):
    """Customer Portal — dashboard for license, usage, cost, and system status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self._cost_tracker = None
        self._video_history = None

        self._build_ui()

    def showEvent(self, event):
        """Refresh data when tab becomes visible."""
        super().showEvent(event)
        self.refresh_all()

    # ================================================================
    # UI Build
    # ================================================================

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
        title = QLabel("👤 客户中心")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e94560;")
        self.header_subtitle = QLabel("")
        self.header_subtitle.setStyleSheet("font-size: 12px; color: #8b949e; padding-top: 6px;")
        header.addWidget(title)
        header.addWidget(self.header_subtitle)
        header.addStretch()

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_all)
        refresh_btn.setStyleSheet("""
            QPushButton { background: #21262d; color: #58a6ff; border: 1px solid #30363d;
                border-radius: 6px; padding: 6px 14px; font-size: 12px; }
            QPushButton:hover { background: #30363d; }
        """)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # ---- Row 1: License + Quick Stats ----
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        row1.addWidget(self._build_license_card(), 1)
        row1.addWidget(self._build_usage_card(), 1)
        row1.addWidget(self._build_cost_card(), 1)

        layout.addLayout(row1)

        # ---- Row 2: Task Stats + System Status ----
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        row2.addWidget(self._build_task_stats_card(), 1)
        row2.addWidget(self._build_system_status_card(), 1)
        row2.addWidget(self._build_update_card(), 1)

        layout.addLayout(row2)

        # ---- Section: Video History Table ----
        layout.addWidget(self._build_video_history_section())

        # ---- Bottom actions ----
        actions = QHBoxLayout()
        actions.addStretch()

        export_csv_btn = QPushButton("📊 导出 CSV")
        export_csv_btn.clicked.connect(self._export_csv)
        export_csv_btn.setStyleSheet(self._btn_style("#1f6feb"))
        actions.addWidget(export_csv_btn)

        actions.addStretch()
        layout.addLayout(actions)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ================================================================
    # Card 1: License
    # ================================================================

    def _build_license_card(self):
        group = self._make_card("🔑 授权信息")
        v = QVBoxLayout()
        v.setSpacing(6)

        self.lic_plan = QLabel("计划: --")
        self.lic_plan.setStyleSheet("font-size: 16px; font-weight: bold; color: #e94560;")
        v.addWidget(self.lic_plan)

        self.lic_company = QLabel("客户: --")
        self.lic_company.setStyleSheet("font-size: 12px; color: #c9d1d9;")
        v.addWidget(self.lic_company)

        self.lic_key = QLabel("Key: --")
        self.lic_key.setStyleSheet("font-size: 10px; color: #8b949e; font-family: monospace;")
        self.lic_key.setWordWrap(True)
        v.addWidget(self.lic_key)

        self.lic_expire = QLabel("到期: --")
        self.lic_expire.setStyleSheet("font-size: 12px; color: #c9d1d9;")
        v.addWidget(self.lic_expire)

        self.lic_status = QLabel("状态: --")
        self.lic_status.setStyleSheet("font-size: 13px; font-weight: bold;")
        v.addWidget(self.lic_status)

        self.lic_device = QLabel("设备: --")
        self.lic_device.setStyleSheet("font-size: 11px; color: #8b949e;")
        v.addWidget(self.lic_device)

        v.addStretch()

        btn_row = QHBoxLayout()
        renew_btn = QPushButton("续费")
        renew_btn.setStyleSheet(self._btn_small("#238636"))
        renew_btn.clicked.connect(lambda: QMessageBox.information(self, "续费", "请联系客服续费。\nEmail: support@tiktok-ai-factory.com"))
        btn_row.addWidget(renew_btn)

        support_btn = QPushButton("联系客服")
        support_btn.setStyleSheet(self._btn_small("#21262d"))
        support_btn.clicked.connect(lambda: QMessageBox.information(self, "客服", "📧 support@tiktok-ai-factory.com"))
        btn_row.addWidget(support_btn)
        v.addLayout(btn_row)

        group.setLayout(v)
        return group

    # ================================================================
    # Card 2: Usage Stats
    # ================================================================

    def _build_usage_card(self):
        group = self._make_card("📊 使用统计")
        v = QVBoxLayout()
        v.setSpacing(8)

        self.usage_today = self._stat_row("今日", "--")
        self.usage_week = self._stat_row("本周", "--")
        self.usage_month = self._stat_row("本月", "--")
        self.usage_total = self._stat_row("累计", "--")

        for lbl in [self.usage_today, self.usage_week, self.usage_month, self.usage_total]:
            v.addLayout(lbl)

        v.addStretch()
        group.setLayout(v)
        return group

    def _stat_row(self, label, value):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        row.addWidget(lbl)
        row.addStretch()
        val = QLabel(value)
        val.setStyleSheet("color: #c9d1d9; font-size: 14px; font-weight: bold;")
        val.setObjectName(f"stat_{label}")
        row.addWidget(val)
        return row

    # ================================================================
    # Card 3: Cost Stats
    # ================================================================

    def _build_cost_card(self):
        group = self._make_card("💰 成本统计")
        v = QVBoxLayout()
        v.setSpacing(6)

        self.cost_openai = QLabel("OpenAI: --")
        self.cost_openai.setStyleSheet("font-size: 11px; color: #8b949e;")
        v.addWidget(self.cost_openai)

        self.cost_image = QLabel("GPT Image: --")
        self.cost_image.setStyleSheet("font-size: 11px; color: #8b949e;")
        v.addWidget(self.cost_image)

        self.cost_tts = QLabel("ElevenLabs: --")
        self.cost_tts.setStyleSheet("font-size: 11px; color: #8b949e;")
        v.addWidget(self.cost_tts)

        self.cost_video = QLabel("Seedance: --")
        self.cost_video.setStyleSheet("font-size: 11px; color: #8b949e;")
        v.addWidget(self.cost_video)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border-color: #30363d;")
        v.addWidget(sep)

        self.cost_total = QLabel("总计: --")
        self.cost_total.setStyleSheet("font-size: 15px; font-weight: bold; color: #e94560;")
        v.addWidget(self.cost_total)

        self.cost_avg = QLabel("单视频: --")
        self.cost_avg.setStyleSheet("font-size: 11px; color: #8b949e;")
        v.addWidget(self.cost_avg)

        v.addStretch()
        group.setLayout(v)
        return group

    # ================================================================
    # Card 4: Task Stats
    # ================================================================

    def _build_task_stats_card(self):
        group = self._make_card("📋 任务统计")
        v = QVBoxLayout()
        v.setSpacing(8)

        self.task_success = self._stat_row("成功", "--")
        self.task_failed = self._stat_row("失败", "--")
        self.task_rate = self._stat_row("成功率", "--")

        for lbl in [self.task_success, self.task_failed, self.task_rate]:
            v.addLayout(lbl)

        # Mini progress bar
        self.task_progress = QProgressBar()
        self.task_progress.setFixedHeight(8)
        self.task_progress.setStyleSheet("""
            QProgressBar { border:none; border-radius:4px; background:#21262d; }
            QProgressBar::chunk { background:#238636; border-radius:4px; }
        """)
        v.addWidget(self.task_progress)

        v.addStretch()
        group.setLayout(v)
        return group

    # ================================================================
    # Card 5: System Status
    # ================================================================

    def _build_system_status_card(self):
        group = self._make_card("🖥️ 系统状态")
        v = QVBoxLayout()
        v.setSpacing(6)

        self.sys_items = {}
        for key, label in [
            ("python", "Python"), ("ffmpeg", "FFmpeg"),
            ("openai", "OpenAI"), ("ark", "ARK"),
            ("elevenlabs", "ElevenLabs"), ("license", "License"),
        ]:
            row = QHBoxLayout()
            name = QLabel(label)
            name.setStyleSheet("color: #8b949e; font-size: 11px;")
            row.addWidget(name)
            row.addStretch()
            status = QLabel("--")
            status.setStyleSheet("font-size: 11px; font-weight: bold;")
            row.addWidget(status)
            v.addLayout(row)
            self.sys_items[key] = status

        v.addStretch()
        group.setLayout(v)
        return group

    # ================================================================
    # Card 6: Update Center
    # ================================================================

    def _build_update_card(self):
        group = self._make_card("🔄 更新中心")
        v = QVBoxLayout()
        v.setSpacing(6)

        self.upd_current = self._stat_row("当前版本", "--")
        self.upd_latest = self._stat_row("最新版本", "--")
        self.upd_checked = self._stat_row("上次检查", "--")

        for lbl in [self.upd_current, self.upd_latest, self.upd_checked]:
            v.addLayout(lbl)

        v.addSpacing(8)

        check_btn = QPushButton("检查更新")
        check_btn.clicked.connect(self._check_update)
        check_btn.setStyleSheet(self._btn_small("#1f6feb"))
        v.addWidget(check_btn)

        # Release notes
        self.upd_notes = QLabel("")
        self.upd_notes.setWordWrap(True)
        self.upd_notes.setStyleSheet("font-size: 10px; color: #8b949e; margin-top: 4px;")
        self.upd_notes.setMaximumHeight(80)
        v.addWidget(self.upd_notes)

        v.addStretch()
        group.setLayout(v)
        return group

    # ================================================================
    # Section: Video History Table
    # ================================================================

    def _build_video_history_section(self):
        group = QGroupBox("🎬 视频生成记录（最近 100 条）")
        group.setStyleSheet(self._card_style())
        v = QVBoxLayout()

        self.video_table = QTableWidget()
        self.video_table.setColumnCount(7)
        self.video_table.setHorizontalHeaderLabels([
            "时间", "产品", "人物", "参考视频", "时长", "状态", "操作"
        ])
        self.video_table.horizontalHeader().setStretchLastSection(True)
        self.video_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.video_table.setMinimumHeight(220)
        self.video_table.setMaximumHeight(400)
        self.video_table.setStyleSheet("""
            QTableWidget { background: #0d1117; color: #c9d1d9; border: 1px solid #30363d;
                border-radius: 6px; gridline-color: #21262d; font-size: 11px; }
            QTableWidget::item { padding: 6px 8px; }
            QTableWidget::item:selected { background: #1f6feb; }
            QHeaderView::section { background: #161b22; color: #8b949e; font-weight: bold;
                padding: 8px; border: none; border-bottom: 1px solid #30363d; }
        """)
        v.addWidget(self.video_table)

        group.setLayout(v)
        return group

    # ================================================================
    # Data Refresh
    # ================================================================

    def refresh_all(self):
        """Reload all data from filesystem."""
        self._refresh_license()
        self._refresh_usage()
        self._refresh_cost()
        self._refresh_task_stats()
        self._refresh_system_status()
        self._refresh_update()
        self._refresh_video_history()

    def _refresh_license(self):
        try:
            from license.license_manager import get_license_manager
            lm = get_license_manager()
            lm.validate()
            status = lm.get_status()

            plan = status.get("type", "PRO").upper()
            self.lic_plan.setText(f"计划: {plan} 版")
            self.lic_company.setText(f"客户: {status.get('client', 'Licensed User')}")
            self.lic_key.setText(f"Key: {status.get('machine_code', '--')}")
            days = status.get("days_remaining", 0)
            self.lic_expire.setText(f"到期: {status.get('expiry_date', '--')} ({days}天)")

            if days > 30:
                self.lic_status.setText("状态: ✅ 有效")
                self.lic_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #238636;")
            elif days > 0:
                self.lic_status.setText(f"状态: ⚠️ 即将到期 ({days}天)")
                self.lic_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #d29922;")
            else:
                self.lic_status.setText("状态: ❌ 已过期")
                self.lic_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #da3633;")

            self.lic_device.setText(f"设备: {status.get('machine_code', '--')[:16]}")
        except Exception as e:
            self.lic_plan.setText("计划: 离线模式")
            self.lic_status.setText(f"状态: ⚠️ {str(e)[:40]}")

    def _refresh_usage(self):
        try:
            from app.gui.cost_tracker import CostTracker
            ct = CostTracker(self.project_root)
            counts = ct.count_videos()
            self._cost_tracker = ct

            self.usage_today.findChild(QLabel, "stat_今日").setText(f"{counts['today']} 个")
            self.usage_week.findChild(QLabel, "stat_本周").setText(f"{counts['this_week']} 个")
            self.usage_month.findChild(QLabel, "stat_本月").setText(f"{counts['this_month']} 个")
            self.usage_total.findChild(QLabel, "stat_累计").setText(f"{counts['total']} 个")
        except Exception as e:
            pass

    def _refresh_cost(self):
        try:
            if self._cost_tracker is None:
                from app.gui.cost_tracker import CostTracker
                self._cost_tracker = CostTracker(self.project_root)
            costs = self._cost_tracker.calculate_costs()

            self.cost_openai.setText(f"OpenAI: ${costs['openai_cost']:.2f}")
            self.cost_image.setText(f"GPT Image: ${costs['openai_image_cost']:.2f}")
            self.cost_tts.setText(f"ElevenLabs: ${costs['elevenlabs_cost']:.2f}")
            self.cost_video.setText(f"Seedance: ${costs['seedance_cost']:.2f}")
            self.cost_total.setText(f"总计: ${costs['total_cost']:.2f}")
            self.cost_avg.setText(f"单视频: ${costs['avg_cost_per_video']:.3f}")
        except Exception:
            pass

    def _refresh_task_stats(self):
        try:
            if self._cost_tracker is None:
                from app.gui.cost_tracker import CostTracker
                self._cost_tracker = CostTracker(self.project_root)
            stats = self._cost_tracker.get_task_stats()

            self.task_success.findChild(QLabel, "stat_成功").setText(f"{stats['success']} 个")
            self.task_failed.findChild(QLabel, "stat_失败").setText(f"{stats['failed']} 个")
            self.task_rate.findChild(QLabel, "stat_成功率").setText(f"{stats['success_rate']}%")

            self.task_progress.setValue(int(stats['success_rate']))
        except Exception:
            pass

    def _refresh_system_status(self):
        checks = {
            "python": ("✓", "#238636"),
            "ffmpeg": ("✓" if self._has_ffmpeg() else "✗", "#238636" if self._has_ffmpeg() else "#da3633"),
            "openai": ("✓" if os.getenv("OPENAI_API_KEY") else "—", "#238636" if os.getenv("OPENAI_API_KEY") else "#8b949e"),
            "ark": ("✓" if os.getenv("ARK_API_KEY") else "—", "#238636" if os.getenv("ARK_API_KEY") else "#8b949e"),
            "elevenlabs": ("✓" if os.getenv("ELEVENLABS_API_KEY") else "—", "#238636" if os.getenv("ELEVENLABS_API_KEY") else "#8b949e"),
            "license": ("✓", "#238636"),
        }
        try:
            from license.license_manager import get_license_manager
            lm = get_license_manager()
            if not lm.validate():
                checks["license"] = ("✗", "#da3633")
        except Exception:
            checks["license"] = ("✗", "#da3633")

        for key, (text, color) in checks.items():
            if key in self.sys_items:
                self.sys_items[key].setText(text)
                self.sys_items[key].setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color};")

    def _refresh_update(self):
        try:
            from updater.version_checker import VersionChecker
            vc = VersionChecker(self.project_root)
            local = vc.get_local_version()
            self.upd_current.findChild(QLabel, "stat_当前版本").setText(f"v{local}")

            config = json.loads((self.project_root / "config" / "update.json").read_text(encoding="utf-8"))
            last_check = config.get("last_checked", "从未检查")
            if last_check and last_check != "从未检查":
                try:
                    dt = datetime.fromisoformat(last_check)
                    last_check = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
            self.upd_checked.findChild(QLabel, "stat_上次检查").setText(last_check)

            # Try to fetch remote version (non-blocking, fall back silently)
            try:
                remote = vc.fetch_remote_version()
                self.upd_latest.findChild(QLabel, "stat_最新版本").setText(f"v{remote.version}")
                if vc.is_newer(remote.version, local):
                    self.upd_notes.setText("🆕 有新版本可用！\n" + "\n".join(f"• {n}" for n in remote.release_notes[:3]))
            except Exception:
                self.upd_latest.findChild(QLabel, "stat_最新版本").setText("检查失败")
        except Exception:
            pass

    def _refresh_video_history(self):
        try:
            from app.gui.video_history import VideoHistory
            vh = VideoHistory(self.project_root)
            records = vh.get_recent(limit=100)

            self.video_table.setRowCount(len(records))
            for i, r in enumerate(records):
                ts = r.get("timestamp", "")[:19] if r.get("timestamp") else ""
                self.video_table.setItem(i, 0, QTableWidgetItem(ts))
                self.video_table.setItem(i, 1, QTableWidgetItem(r.get("product", "")))
                self.video_table.setItem(i, 2, QTableWidgetItem(r.get("character", "")))
                self.video_table.setItem(i, 3, QTableWidgetItem(r.get("reference", "")))
                dur = r.get("duration", 0)
                self.video_table.setItem(i, 4, QTableWidgetItem(f"{dur}s"))

                status_item = QTableWidgetItem(r.get("status", "unknown"))
                if r.get("status") == "completed":
                    status_item.setForeground(QBrush(QColor("#238636")))
                elif r.get("status") == "failed":
                    status_item.setForeground(QBrush(QColor("#da3633")))
                self.video_table.setItem(i, 5, status_item)

                # Action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(2, 2, 2, 2)
                action_layout.setSpacing(4)

                if r.get("output_dir"):
                    open_btn = QPushButton("📂")
                    open_btn.setFixedSize(28, 28)
                    out_dir = r["output_dir"]
                    open_btn.clicked.connect(lambda checked, d=out_dir: os.startfile(d) if os.path.exists(d) else None)
                    open_btn.setStyleSheet("QPushButton { background:transparent; border:none; font-size:14px; } QPushButton:hover { background:#21262d; }")
                    action_layout.addWidget(open_btn)

                if r.get("video_path") and os.path.exists(r["video_path"]):
                    play_btn = QPushButton("▶")
                    play_btn.setFixedSize(28, 28)
                    vp = r["video_path"]
                    play_btn.clicked.connect(lambda checked, p=vp: os.startfile(p))
                    play_btn.setStyleSheet("QPushButton { background:transparent; border:none; font-size:14px; } QPushButton:hover { background:#21262d; }")
                    action_layout.addWidget(play_btn)

                action_layout.addStretch()
                self.video_table.setCellWidget(i, 6, action_widget)
        except Exception:
            pass

    # ================================================================
    # Actions
    # ================================================================

    def _check_update(self):
        try:
            from updater import check_for_updates as do_check
            updated = do_check(self.project_root, silent=False)
            if not updated:
                QMessageBox.information(self, "检查更新", "当前已是最新版本。")
        except Exception as e:
            QMessageBox.warning(self, "检查更新", f"检查失败: {e}")

    def _export_csv(self):
        """Export video history as CSV."""
        import csv
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "video_history.csv", "CSV (*.csv)")
        if not path:
            return

        try:
            from app.gui.video_history import VideoHistory
            vh = VideoHistory(self.project_root)
            records = vh.get_recent(limit=1000)

            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "timestamp", "task_id", "product", "character", "reference",
                    "duration", "status", "cost", "style", "country", "output_dir",
                ])
                writer.writeheader()
                writer.writerows(records)

            QMessageBox.information(self, "导出成功", f"已导出 {len(records)} 条记录到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    # ================================================================
    # Helpers
    # ================================================================

    @staticmethod
    def _has_ffmpeg():
        import subprocess
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            return True
        except Exception:
            return False

    @staticmethod
    def _make_card(title):
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox { color: #c9d1d9; border: 1px solid #30363d;
                border-radius: 10px; margin-top: 14px; padding: 18px 14px 12px 14px;
                font-weight: bold; font-size: 12px; background-color: #161b22; }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
        """)
        group.setMinimumHeight(200)
        return group

    @staticmethod
    def _card_style():
        return """
            QGroupBox { color: #c9d1d9; border: 1px solid #30363d;
                border-radius: 10px; margin-top: 14px; padding: 18px 14px 12px 14px;
                font-weight: bold; font-size: 13px; background-color: #161b22; }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
        """

    @staticmethod
    def _btn_style(color):
        return f"""
            QPushButton {{ background: {color}; color: white; border: none;
                border-radius: 6px; padding: 8px 18px; font-size: 12px; font-weight: bold; }}
            QPushButton:hover {{ opacity: 0.8; }}
        """

    @staticmethod
    def _btn_small(color):
        return f"""
            QPushButton {{ background: {color}; color: white; border: none;
                border-radius: 4px; padding: 4px 10px; font-size: 11px; }}
            QPushButton:hover {{ opacity: 0.8; }}
        """
