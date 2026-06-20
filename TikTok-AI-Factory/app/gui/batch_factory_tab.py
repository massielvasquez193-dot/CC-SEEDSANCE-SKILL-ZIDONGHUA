"""
TikTok AI Factory Pro — Batch Factory Tab
===========================================
Enterprise-scale batch video production UI.

Layout:
  ┌──────────────────────────────────────────────────────┐
  │  🏭 批量工厂                                          │
  │                                                      │
  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐     │
  │  │ 产品目录  │ │ 人物目录  │ │ 参考视频目录      │     │
  │  │ 12 个    │ │ 5 个     │ │ 20 个            │     │
  │  │ [扫描]   │ │ [扫描]   │ │ [扫描]           │     │
  │  └──────────┘ └──────────┘ └──────────────────┘     │
  │                                                      │
  │  国家: [▼]  模式: [▼]  每产品视频: [▼]  并发: [▼]    │
  │                                                      │
  │  ┌─────────── Dashboard ─────────────────────────┐   │
  │  │ 总:100 完成:45 失败:2 排队:53 进度:45%         │   │
  │  │ ████████████░░░░░░░░░░░░░░ 45%                 │   │
  │  │ ETA: 18分钟  已用: 12分钟                       │   │
  │  └──────────────────────────────────────────────┘   │
  │                                                      │
  │  [🚀 开始批量生成] [⏹ 停止] [📊 导出报告]            │
  │                                                      │
  │  ┌─────────── 实时日志 ─────────────────────────┐   │
  │  │ ...                                          │   │
  │  └──────────────────────────────────────────────┘   │
  │                                                      │
  │  ┌─────────── 成本预估 ─────────────────────────┐   │
  │  │ 总视频:100 | 单视频:$0.42 | 总成本:$42.00     │   │
  │  │ GPT:$0.50 DALL-E:$24 ElevenLabs:$5 Seed:$12  │   │
  │  └──────────────────────────────────────────────┘   │
  └──────────────────────────────────────────────────────┘
"""

import os
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QProgressBar, QTextEdit, QGroupBox, QScrollArea,
    QFrame, QMessageBox, QGridLayout, QFileDialog,
)
from PySide6.QtCore import Qt, QThread, Signal


class BatchWorker(QThread):
    """Background worker for batch production."""
    stats_signal = Signal(dict)
    log_signal = Signal(str)
    task_signal = Signal(str, str, object)  # event, task_id, data
    done_signal = Signal(dict)

    def __init__(self, controller, country, style, videos_per_product, mode, max_concurrent):
        super().__init__()
        self.controller = controller
        self.country = country
        self.style = style
        self.videos_per_product = videos_per_product
        self.mode = mode
        self.max_concurrent = max_concurrent

    def run(self):
        result = self.controller.run_batch(
            country=self.country,
            style=self.style,
            videos_per_product=self.videos_per_product,
            mode=self.mode,
            max_concurrent=self.max_concurrent,
            stats_callback=lambda s: self.stats_signal.emit(s),
            log_callback=lambda m: self.log_signal.emit(m),
            task_callback=lambda e, t, d: self.task_signal.emit(e, t, d),
            done_callback=lambda r: self.done_signal.emit(r),
        )
        if result.get("status") == "error":
            self.done_signal.emit(result)

    def stop(self):
        if self.controller:
            self.controller.cancel()


class BatchFactoryTab(QWidget):
    """Batch Factory — enterprise-scale video production UI."""

    COUNTRIES = ["美国", "英国", "马来西亚", "印尼", "德国", "法国", "西班牙"]
    MODES = ["随机模式", "固定模式", "爆款复刻模式"]
    VIDEO_COUNTS = [1, 3, 5, 10]
    CONCURRENCY = [1, 2, 3, 5]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = None
        self.worker = None
        self._scanned = {"products": [], "characters": [], "reference_videos": []}

        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # ---- Header ----
        header = QHBoxLayout()
        title = QLabel("🏭 批量工厂")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e94560;")
        desc = QLabel("无人值守 · 批量生产 · 企业级")
        desc.setStyleSheet("font-size: 12px; color: #8b949e; padding-top: 6px;")
        header.addWidget(title)
        header.addWidget(desc)
        header.addStretch()
        layout.addLayout(header)

        # ---- Input Scan Row ----
        scan_row = QHBoxLayout()
        scan_row.setSpacing(12)

        self.scan_cards = {}
        for key, icon, label in [
            ("products", "📦", "产品目录"),
            ("characters", "👤", "人物目录"),
            ("reference_videos", "🎥", "参考视频"),
        ]:
            group, btn, lbl = self._make_scan_card(icon, label, key)
            btn.clicked.connect(lambda checked, k=key: self._scan_input(k))
            scan_row.addWidget(group)
            self.scan_cards[key] = {"btn": btn, "lbl": lbl}

        layout.addLayout(scan_row)

        # ---- Config Row ----
        cfg_row = QHBoxLayout()
        cfg_row.setSpacing(12)

        cfg_row.addWidget(self._cfg_label("目标国家"))
        self.country_combo = QComboBox()
        self.country_combo.addItems(self.COUNTRIES)
        self.country_combo.setStyleSheet(self._combo_style())
        cfg_row.addWidget(self.country_combo)

        cfg_row.addWidget(self._cfg_label("生成模式"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(self.MODES)
        self.mode_combo.setStyleSheet(self._combo_style())
        self.mode_combo.setToolTip("随机: 随机配对 | 固定: 1:1:1 | 爆款复刻: 每个产品匹配所有参考视频")
        cfg_row.addWidget(self.mode_combo)

        cfg_row.addWidget(self._cfg_label("每产品视频"))
        self.count_combo = QComboBox()
        for c in self.VIDEO_COUNTS:
            self.count_combo.addItem(str(c), c)
        self.count_combo.setStyleSheet(self._combo_style())
        cfg_row.addWidget(self.count_combo)

        cfg_row.addWidget(self._cfg_label("并发数"))
        self.concurrency_combo = QComboBox()
        for c in self.CONCURRENCY:
            self.concurrency_combo.addItem(str(c), c)
        self.concurrency_combo.setCurrentText("3")
        self.concurrency_combo.setStyleSheet(self._combo_style())
        cfg_row.addWidget(self.concurrency_combo)

        cfg_row.addStretch()
        layout.addLayout(cfg_row)

        # ---- Dashboard Card ----
        dash_group = QGroupBox("📊 Dashboard")
        dash_group.setStyleSheet(self._section_style())
        dash_layout = QVBoxLayout()

        # Stats row
        stats_row = QHBoxLayout()
        self.stat_labels = {}
        for key, color in [
            ("total", "#58a6ff"), ("completed", "#238636"), ("failed", "#da3633"),
            ("queued", "#d29922"), ("running", "#1f6feb"), ("remaining", "#8b949e"),
        ]:
            lbl = QLabel(f"{key}: --")
            lbl.setStyleSheet(f"font-size: 13px; color: {color}; font-weight: bold; padding: 2px 8px;")
            stats_row.addWidget(lbl)
            self.stat_labels[key] = lbl
        stats_row.addStretch()
        dash_layout.addLayout(stats_row)

        # Progress bar
        self.batch_progress = QProgressBar()
        self.batch_progress.setFixedHeight(10)
        self.batch_progress.setStyleSheet("""
            QProgressBar { border: none; border-radius: 5px; background-color: #21262d; }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #e94560, stop:0.5 #ff6b3d, stop:1 #238636);
                border-radius: 5px;
            }
        """)
        dash_layout.addWidget(self.batch_progress)

        # ETA row
        eta_row = QHBoxLayout()
        self.eta_label = QLabel("ETA: --  已用: --")
        self.eta_label.setStyleSheet("font-size: 12px; color: #8b949e;")
        eta_row.addWidget(self.eta_label)
        eta_row.addStretch()
        dash_layout.addLayout(eta_row)

        dash_group.setLayout(dash_layout)
        layout.addWidget(dash_group)

        # ---- Action Buttons ----
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.start_btn = QPushButton("🚀 开始批量生成")
        self.start_btn.setMinimumSize(220, 50)
        self.start_btn.clicked.connect(self._start_batch)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560; color: white;
                border: none; border-radius: 8px;
                font-size: 16px; font-weight: bold; padding: 10px 32px;
            }
            QPushButton:hover { background-color: #ff6b81; }
            QPushButton:disabled { background-color: #21262d; color: #484f58; }
        """)
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setMinimumSize(100, 50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_batch)
        self.stop_btn.setStyleSheet("""
            QPushButton { background-color: #da3633; color: white; border: none;
                border-radius: 8px; font-size: 14px; font-weight: bold; padding: 12px 20px; }
            QPushButton:hover { background-color: #f85149; }
            QPushButton:disabled { background-color: #21262d; color: #484f58; }
        """)
        btn_row.addWidget(self.stop_btn)

        self.export_btn = QPushButton("📊 导出报告")
        self.export_btn.setMinimumSize(120, 50)
        self.export_btn.clicked.connect(self._export_report)
        self.export_btn.setStyleSheet("""
            QPushButton { background-color: #1f6feb; color: white; border: none;
                border-radius: 8px; font-size: 14px; font-weight: bold; padding: 10px 20px; }
            QPushButton:hover { background-color: #388bfd; }
            QPushButton:disabled { background-color: #21262d; color: #484f58; }
        """)
        btn_row.addWidget(self.export_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ---- Log Area ----
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(140)
        self.log_view.setMaximumHeight(200)
        self.log_view.setPlaceholderText("点击「扫描」检测输入文件，然后「开始批量生成」...")
        self.log_view.setStyleSheet("""
            QTextEdit { background-color: #0d1117; color: #c9d1d9;
                border: 1px solid #30363d; border-radius: 8px;
                font-family: 'Consolas', monospace; font-size: 11px; padding: 10px; }
        """)
        layout.addWidget(self.log_view)

        # ---- Cost Estimate Card ----
        cost_group = QGroupBox("💰 成本预估")
        cost_group.setStyleSheet(self._section_style())
        cost_layout = QHBoxLayout()
        self.cost_label = QLabel("请先扫描输入目录...")
        self.cost_label.setStyleSheet("font-size: 12px; color: #8b949e;")
        self.cost_label.setWordWrap(True)
        cost_layout.addWidget(self.cost_label)
        cost_layout.addStretch()
        cost_group.setLayout(cost_layout)
        layout.addWidget(cost_group)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # Auto-scan on init
        QThread.msleep(200)  # let UI paint
        for key in self.scan_cards:
            self._scan_input(key, silent=True)

    # ---- Scan Card ----
    def _make_scan_card(self, icon, title, key):
        group = QGroupBox()
        group.setStyleSheet(f"""
            QGroupBox {{ color: #c9d1d9; border: 1px solid #30363d;
                border-radius: 10px; margin-top: 14px; padding-top: 22px;
                font-weight: bold; font-size: 12px; background-color: #161b22; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 6px; }}
        """)
        group.setTitle(f"{icon} {title}")
        group.setMinimumHeight(100)

        v = QVBoxLayout()
        v.setSpacing(6)
        btn = QPushButton("🔄 扫描")
        btn.setMinimumHeight(50)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background-color: #21262d; border: 1px dashed #30363d;
                border-radius: 8px; color: #8b949e; font-size: 18px; }
            QPushButton:hover { background-color: #30363d; border-color: #58a6ff; color: #c9d1d9; }
        """)
        v.addWidget(btn)
        lbl = QLabel("0 个文件")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #484f58; font-size: 11px;")
        v.addWidget(lbl)
        group.setLayout(v)
        return group, btn, lbl

    # ---- Scan Inputs ----
    def _scan_input(self, key, silent=False):
        from app.gui.batch_controller import BatchController
        if self.controller is None:
            self.controller = BatchController()

        inputs = self.controller.scan_inputs()
        self._scanned = inputs
        count = len(inputs.get(key, []))

        card = self.scan_cards[key]
        card["btn"].setText(f"✓ {count} 个文件")
        card["btn"].setStyleSheet("""
            QPushButton { background-color: #0d1117; border: 2px solid #238636;
                border-radius: 8px; color: #238636; font-size: 16px; font-weight: bold; }
        """)
        card["lbl"].setText(f"input/{key}/")

        if not silent:
            self._log(f"📂 {key}: 发现 {count} 个文件")

        self._update_cost_estimate()

    def _update_cost_estimate(self):
        """Update the cost estimate display."""
        p = len(self._scanned.get("products", []))
        c = len(self._scanned.get("characters", []))
        v = len(self._scanned.get("reference_videos", []))
        vpp = self.count_combo.currentData()

        if p == 0:
            self.cost_label.setText("请先扫描输入目录...")
            return

        from tools.cost_report import estimate_batch_cost
        est = estimate_batch_cost(p, vpp)
        self.cost_label.setText(
            f"产品: {p} | 人物: {c} | 参考: {v} | "
            f"预估视频: {est['total_videos']} | "
            f"单视频: ${est['per_video_cost']} | "
            f"总成本: ${est['total_cost']:.2f} | "
            f"预估耗时: {self._format_time(est['total_videos'] * 90 // 3)}"
        )

    # ---- Start / Stop ----
    def _start_batch(self):
        p = len(self._scanned.get("products", []))
        if p == 0:
            QMessageBox.warning(self, "无产品", "请先扫描输入目录，确保至少有一个产品图片。")
            return

        if self.controller is None:
            self.controller = BatchController()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_view.clear()
        self.export_btn.setEnabled(False)

        self.worker = BatchWorker(
            self.controller,
            self.country_combo.currentText(),
            self.mode_combo.currentText(),
            self.count_combo.currentData(),
            self.mode_combo.currentText(),
            self.concurrency_combo.currentData(),
        )
        self.worker.stats_signal.connect(self._on_stats)
        self.worker.log_signal.connect(self._on_batch_log)
        self.worker.task_signal.connect(self._on_task_event)
        self.worker.done_signal.connect(self._on_batch_done)
        self.worker.start()

    def _stop_batch(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait(3000)
        self._log("⏹ 用户停止了批量生产")
        self._reset_ui()

    def _on_stats(self, stats):
        self.stat_labels["total"].setText(f"总: {stats.get('total', 0)}")
        self.stat_labels["completed"].setText(f"完成: {stats.get('completed', 0)}")
        self.stat_labels["failed"].setText(f"失败: {stats.get('failed', 0)}")
        self.stat_labels["queued"].setText(f"排队: {stats.get('queued', 0)}")
        self.stat_labels["running"].setText(f"运行: {stats.get('running', 0)}")
        self.stat_labels["remaining"].setText(f"剩余: {stats.get('remaining', 0)}")
        self.batch_progress.setValue(stats.get("progress_pct", 0))
        self.eta_label.setText(
            f"ETA: {stats.get('eta_str', '--')}  "
            f"已用: {self._format_time(stats.get('elapsed_seconds', 0))}"
        )

    def _on_batch_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        if "✓" in msg or "完成" in msg or "COMPLETE" in msg:
            color = "#238636"
        elif "⚠" in msg or "跳过" in msg or "retry" in msg.lower():
            color = "#d29922"
        elif "✗" in msg or "失败" in msg or "FAIL" in msg:
            color = "#da3633"
        elif msg.startswith("="):
            color = "#8b949e"
        else:
            color = "#c9d1d9"
        self.log_view.append(f'<span style="color:{color}">[{ts}] {msg}</span>')

    def _on_task_event(self, event, task_id, data):
        if event == "complete":
            self._log(f"  ✅ {task_id} → {data.get('output', '?')}")
        elif event == "fail":
            self._log(f"  ❌ {task_id} 失败: {data.get('error', '?')[:80]}")
        elif event == "start":
            self._log(f"  ▶ {task_id} 开始...")

    def _on_batch_done(self, result):
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        if result.get("status") == "error":
            self._log(f"❌ 批量生产失败: {result.get('message', '未知错误')}")
            QMessageBox.critical(self, "批量生产失败", result.get("message", "未知错误"))
        else:
            stats = result.get("stats", {})
            cost = result.get("total_estimated_cost", 0)
            self._log("")
            self._log("=" * 50)
            self._log(f"  🎉 批量生产完成！")
            self._log(f"  完成: {stats.get('completed', 0)}")
            self._log(f"  失败: {stats.get('failed', 0)}")
            self._log(f"  预估总成本: ${cost:.2f}")
            self._log(f"  输出: {result.get('output_dir', '')}")
            self._log("=" * 50)
            QMessageBox.information(
                self, "批量生产完成",
                f"批量视频生产已完成！\n\n"
                f"完成: {stats.get('completed', 0)} 个\n"
                f"失败: {stats.get('failed', 0)} 个\n"
                f"预估成本: ${cost:.2f}\n\n"
                f"输出目录: {result.get('output_dir', '')}"
            )

    # ---- Export ----
    def _export_report(self):
        if self.controller is None:
            return

        out_dir = Path(self.controller.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Export cost report
        cost_path = self.controller.export_cost_report(out_dir / "batch_cost_report.csv")
        self._log(f"📊 成本报告: {cost_path}")

        # Also generate full cost estimate XLSX
        from tools.cost_report import estimate_batch_cost, export_to_excel
        p = len(self._scanned.get("products", []))
        vpp = self.count_combo.currentData()
        est = estimate_batch_cost(p, vpp)
        xlsx_path = out_dir / "batch_cost_report.xlsx"
        export_to_excel(est, xlsx_path)
        self._log(f"📊 Excel 报告: {xlsx_path}")

        # Open folder
        os.startfile(str(out_dir))
        QMessageBox.information(self, "导出完成", f"报告已导出到:\n{out_dir}")

    # ---- Helpers ----
    def _log(self, msg):
        self._on_batch_log(msg)

    def _reset_ui(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    @staticmethod
    def _format_time(seconds):
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            return f"{int(seconds//60)}分{int(seconds%60)}秒"
        return f"{int(seconds//3600)}时{int(seconds%3600//60)}分"

    @staticmethod
    def _cfg_label(text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: bold;")
        return lbl

    @staticmethod
    def _combo_style():
        return """
            QComboBox { background-color: #21262d; color: #c9d1d9;
                border: 1px solid #30363d; border-radius: 6px;
                padding: 6px 12px; font-size: 12px; }
            QComboBox:hover { border-color: #58a6ff; }
            QComboBox QAbstractItemView { background-color: #161b22; color: #c9d1d9;
                selection-background-color: #1f6feb; border: 1px solid #30363d; }
        """

    @staticmethod
    def _section_style():
        return """
            QGroupBox { color: #c9d1d9; border: 1px solid #30363d;
                border-radius: 10px; margin-top: 14px; padding-top: 22px;
                font-weight: bold; font-size: 13px; background-color: #161b22; }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
        """
