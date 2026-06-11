"""
TikTok AI Factory Pro — Desktop GUI (PySide6)
================================================
Left:  Upload product / character / reference video
Right: Preview script / voiceover / storyboard
Bottom: Start / Stop / Open output / Progress bar
"""

import json
import os
import sys
import threading
import shutil
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QProgressBar, QFileDialog,
    QGroupBox, QSplitter, QTabWidget, QMessageBox, QFrame, QScrollArea,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor, QPalette


class FactoryWorker(QThread):
    """后台工厂执行线程"""
    progress = Signal(str, int)    # message, percentage
    step_update = Signal(str)       # step name
    finished = Signal(bool, str)    # success, message
    output_ready = Signal(str)      # output directory

    def __init__(self, product_path, video_path, character_path):
        super().__init__()
        self.product_path = product_path
        self.video_path = video_path
        self.character_path = character_path
        self._stopped = False

    def stop(self):
        self._stopped = True

    def run(self):
        try:
            from pathlib import Path
            import subprocess
            import os

            # Prepare input files
            input_dir = Path("input")
            input_dir.mkdir(parents=True, exist_ok=True)
            (input_dir / "products").mkdir(parents=True, exist_ok=True)
            (input_dir / "reference_videos").mkdir(parents=True, exist_ok=True)
            (input_dir / "characters").mkdir(parents=True, exist_ok=True)

            shutil.copy(self.product_path, input_dir / "products" / Path(self.product_path).name)
            shutil.copy(self.video_path, input_dir / "reference_videos" / Path(self.video_path).name)
            shutil.copy(self.character_path, input_dir / "characters" / Path(self.character_path).name)

            self.progress.emit("Files prepared. Starting factory pipeline...", 5)
            self.step_update.emit("STEP 1: Input Ready")

            # Run the factory via subprocess — captures real pipeline output
            factory_script = Path(__file__).resolve().parent.parent.parent / "run_factory.py"

            self.progress.emit("Running factory pipeline...", 10)
            self.step_update.emit("STEP 2: Pipeline Starting")

            steps = [
                (20, "STEP 3: Video Analysis"),
                (30, "STEP 4: Product + Character Extraction"),
                (40, "STEP 5: Master Script Generation"),
                (50, "STEP 6: Storyboard Generation"),
                (60, "STEP 7: Voiceover Generation"),
                (70, "STEP 8: Keyframe Generation"),
                (85, "STEP 9: Seedance Segments"),
                (95, "STEP 10: Final Export"),
            ]

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"

            proc = subprocess.Popen(
                [sys.executable, str(factory_script), "--max-tasks", "1"],
                cwd=str(Path(__file__).resolve().parent.parent.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )

            line_count = 0
            for line in proc.stdout:
                if self._stopped:
                    proc.terminate()
                    self.finished.emit(False, "Stopped by user")
                    return

                line = line.strip()
                if line:
                    line_count += 1

                    # Parse step progress from log output
                    if "STEP" in line and "步骤" in line:
                        for pct, label in steps:
                            if label.split(":")[1].strip()[:8] in line or any(
                                kw in line for kw in label.split(":")[1].strip().split()
                            ):
                                self.progress.emit(line.strip(), pct)
                                self.step_update.emit(label)
                                break
                    elif "完成" in line or "complete" in line.lower():
                        self.progress.emit(line.strip(), 95)
                    elif "FAIL" in line or "ERROR" in line.upper() or "失败" in line:
                        self.step_update.emit(f"[WARN] {line.strip()[:80]}")

                # Periodic progress bumps
                if line_count % 5 == 0:
                    pct = min(10 + (line_count // 5), 90)
                    self.progress.emit("Processing...", pct)

            proc.wait()

            # Find output directory
            from config.settings import OUTPUT_DIR
            output_dirs = sorted(OUTPUT_DIR.glob("output*"))
            if output_dirs:
                output_dir = str(output_dirs[-1])
            else:
                output_dir = str(OUTPUT_DIR / "output001")

            self.progress.emit("Complete!", 100)
            self.output_ready.emit(output_dir)
            self.finished.emit(True, f"Generation complete!\nOutput: {output_dir}")

        except Exception as e:
            import traceback
            self.finished.emit(False, f"Error: {str(e)}\n{traceback.format_exc()}")


class TikTokFactoryGUI(QMainWindow):
    """TikTok AI Factory Pro — Desktop Application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TikTok AI Factory Pro — AI Video Factory")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 660)
        self.setStyleSheet(self._style())

        self.product_path = None
        self.video_path = None
        self.character_path = None
        self.worker = None
        self.output_dir = None

        self._build_ui()

    def _style(self) -> str:
        return """
        QMainWindow { background-color: #0d1117; }
        QGroupBox {
            color: #c9d1d9; border: 1px solid #30363d; border-radius: 8px;
            margin-top: 12px; padding-top: 20px; font-weight: bold; font-size: 13px;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        QPushButton {
            background-color: #238636; color: white; border: none;
            border-radius: 6px; padding: 10px 20px; font-size: 13px; font-weight: bold;
        }
        QPushButton:hover { background-color: #2ea043; }
        QPushButton:pressed { background-color: #196c2e; }
        QPushButton:disabled { background-color: #21262d; color: #484f58; }
        QPushButton#stopBtn { background-color: #da3633; }
        QPushButton#stopBtn:hover { background-color: #f85149; }
        QPushButton#uploadBtn { background-color: #21262d; border: 1px dashed #30363d; padding: 40px; font-size: 14px; }
        QPushButton#uploadBtn:hover { background-color: #30363d; border-color: #58a6ff; }
        QLabel { color: #c9d1d9; font-size: 12px; }
        QTextEdit {
            background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d;
            border-radius: 6px; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;
            padding: 8px;
        }
        QProgressBar {
            border: none; border-radius: 4px; background-color: #21262d; height: 8px; text-align: center;
        }
        QProgressBar::chunk { background-color: #238636; border-radius: 4px; }
        QTabWidget::pane { border: 1px solid #30363d; background-color: #161b22; border-radius: 6px; }
        QTabBar::tab {
            background-color: #21262d; color: #8b949e; padding: 8px 20px;
            border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px;
        }
        QTabBar::tab:selected { background-color: #161b22; color: #c9d1d9; border-bottom: 2px solid #e94560; }
        QScrollArea { border: none; background: transparent; }
        QSplitter::handle { background-color: #30363d; width: 2px; }
        """

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # === Header ===
        header = QHBoxLayout()
        title = QLabel("TikTok AI Factory Pro")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e94560;")
        version = QLabel("v3.0.0")
        version.setStyleSheet("font-size: 12px; color: #8b949e; padding-top: 8px;")
        header.addWidget(title)
        header.addWidget(version)
        header.addStretch()
        self.status_label = QLabel("Ready. Upload files to begin.")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 12px; padding-top: 8px;")
        header.addWidget(self.status_label)
        root.addLayout(header)

        # === Main Splitter ===
        splitter = QSplitter(Qt.Horizontal)

        # LEFT: Upload panel
        left = self._build_upload_panel()
        splitter.addWidget(left)

        # RIGHT: Preview panel
        right = self._build_preview_panel()
        splitter.addWidget(right)

        splitter.setSizes([420, 820])
        root.addWidget(splitter, 1)

        # === Bottom: Progress + Actions ===
        bottom = self._build_bottom_panel()
        root.addLayout(bottom)

    def _build_upload_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(8)

        # Product
        product_group = QGroupBox("Product Image")
        pg = QVBoxLayout()
        self.product_btn = QPushButton("Click to Upload\nProduct Image\n(.jpg .png .webp)")
        self.product_btn.setObjectName("uploadBtn")
        self.product_btn.setMinimumHeight(130)
        self.product_btn.clicked.connect(lambda: self._upload_file("product"))
        self.product_label = QLabel("No file selected")
        self.product_label.setStyleSheet("color: #484f58; text-align: center;")
        self.product_label.setAlignment(Qt.AlignCenter)
        pg.addWidget(self.product_btn)
        pg.addWidget(self.product_label)
        product_group.setLayout(pg)
        layout.addWidget(product_group)

        # Character
        char_group = QGroupBox("Character Image")
        cg = QVBoxLayout()
        self.char_btn = QPushButton("Click to Upload\nCharacter Image\n(.jpg .png .webp)")
        self.char_btn.setObjectName("uploadBtn")
        self.char_btn.setMinimumHeight(130)
        self.char_btn.clicked.connect(lambda: self._upload_file("character"))
        self.char_label = QLabel("No file selected")
        self.char_label.setStyleSheet("color: #484f58; text-align: center;")
        self.char_label.setAlignment(Qt.AlignCenter)
        cg.addWidget(self.char_btn)
        cg.addWidget(self.char_label)
        char_group.setLayout(cg)
        layout.addWidget(char_group)

        # Video
        video_group = QGroupBox("Reference Video")
        vg = QVBoxLayout()
        self.video_btn = QPushButton("Click to Upload\nReference Video\n(.mp4 .mov)")
        self.video_btn.setObjectName("uploadBtn")
        self.video_btn.setMinimumHeight(130)
        self.video_btn.clicked.connect(lambda: self._upload_file("video"))
        self.video_label = QLabel("No file selected")
        self.video_label.setStyleSheet("color: #484f58; text-align: center;")
        self.video_label.setAlignment(Qt.AlignCenter)
        vg.addWidget(self.video_btn)
        vg.addWidget(self.video_label)
        video_group.setLayout(vg)
        layout.addWidget(video_group)

        layout.addStretch()
        return panel

    def _build_preview_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 0, 0, 0)

        tabs = QTabWidget()

        # Script tab
        self.script_preview = QTextEdit()
        self.script_preview.setReadOnly(True)
        self.script_preview.setPlaceholderText("Master script will appear here...")
        tabs.addTab(self.script_preview, "Master Script")

        # Voiceover tab
        self.voiceover_preview = QTextEdit()
        self.voiceover_preview.setReadOnly(True)
        self.voiceover_preview.setPlaceholderText("Voiceover text will appear here...")
        tabs.addTab(self.voiceover_preview, "Voiceover")

        # Storyboard tab
        self.storyboard_preview = QTextEdit()
        self.storyboard_preview.setReadOnly(True)
        self.storyboard_preview.setPlaceholderText("Storyboard will appear here...")
        tabs.addTab(self.storyboard_preview, "Storyboard")

        # Log tab
        self.log_preview = QTextEdit()
        self.log_preview.setReadOnly(True)
        self.log_preview.setPlaceholderText("Generation log...")
        tabs.addTab(self.log_preview, "Log")

        layout.addWidget(tabs)
        return panel

    def _build_bottom_panel(self) -> QHBoxLayout:
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        bottom.addWidget(self.progress_bar, 1)

        self.start_btn = QPushButton("Start Generation")
        self.start_btn.setMinimumWidth(170)
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_generation)
        bottom.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setMinimumWidth(100)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_generation)
        bottom.addWidget(self.stop_btn)

        self.open_btn = QPushButton("Open Output")
        self.open_btn.setMinimumWidth(120)
        self.open_btn.setStyleSheet("background-color: #1f6feb;")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_output)
        bottom.addWidget(self.open_btn)

        return bottom

    # ================================================================
    # Upload
    # ================================================================
    def _upload_file(self, file_type: str):
        filters = {
            "product": "Images (*.jpg *.jpeg *.png *.webp)",
            "character": "Images (*.jpg *.jpeg *.png *.webp)",
            "video": "Videos (*.mp4 *.mov)",
        }
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select {file_type} file", "", filters.get(file_type, "All files (*)")
        )
        if not file_path:
            return

        name = Path(file_path).name
        size_mb = Path(file_path).stat().st_size / (1024 * 1024)

        if file_type == "product":
            self.product_path = file_path
            self.product_label.setText(f"{name}\n{size_mb:.1f} MB")
            self.product_label.setStyleSheet("color: #238636; font-weight: bold;")
        elif file_type == "character":
            self.character_path = file_path
            self.char_label.setText(f"{name}\n{size_mb:.1f} MB")
            self.char_label.setStyleSheet("color: #238636; font-weight: bold;")
        elif file_type == "video":
            self.video_path = file_path
            self.video_label.setText(f"{name}\n{size_mb:.1f} MB")
            self.video_label.setStyleSheet("color: #238636; font-weight: bold;")

        self._check_ready()

    def _check_ready(self):
        all_ready = all([self.product_path, self.video_path, self.character_path])
        self.start_btn.setEnabled(all_ready)
        if all_ready:
            self.status_label.setText("All files ready. Click 'Start Generation' to begin.")
            self.status_label.setStyleSheet("color: #238636; font-size: 12px; padding-top: 8px;")

    # ================================================================
    # Generation
    # ================================================================
    def _start_generation(self):
        if not all([self.product_path, self.video_path, self.character_path]):
            QMessageBox.warning(self, "Missing Files", "Please upload all 3 files first.")
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.open_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_preview.clear()

        self.worker = FactoryWorker(self.product_path, self.video_path, self.character_path)
        self.worker.progress.connect(self._on_progress)
        self.worker.step_update.connect(self._on_step)
        self.worker.finished.connect(self._on_finished)
        self.worker.output_ready.connect(self._on_output_ready)
        self.worker.start()

    def _stop_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait(3000)
        self._reset_ui()
        self.status_label.setText("Generation stopped by user.")
        self.status_label.setStyleSheet("color: #da3633; font-size: 12px; padding-top: 8px;")

    def _on_progress(self, msg: str, pct: int):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)
        self.log_preview.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def _on_step(self, step: str):
        self.log_preview.append(f"  >> {step}")

    def _on_output_ready(self, output_dir: str):
        self.output_dir = output_dir
        self.open_btn.setEnabled(True)
        self._load_previews(output_dir)

    def _on_finished(self, success: bool, msg: str):
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        if success:
            self.status_label.setText("Generation complete!")
            self.status_label.setStyleSheet("color: #238636; font-size: 12px; padding-top: 8px; font-weight: bold;")
        else:
            self.status_label.setText("Generation failed.")
            self.status_label.setStyleSheet("color: #da3633; font-size: 12px; padding-top: 8px;")
            self.log_preview.append(f"\n[ERROR] {msg}")
        self.progress_bar.setVisible(False)

    def _load_previews(self, output_dir: str):
        """Load generated files into preview tabs"""
        out = Path(output_dir)

        script_file = out / "master_script.md"
        if script_file.exists():
            self.script_preview.setPlainText(script_file.read_text(encoding="utf-8"))

        voice_file = out / "voiceover.txt"
        if voice_file.exists():
            self.voiceover_preview.setPlainText(voice_file.read_text(encoding="utf-8"))

        storyboard_file = out / "storyboard.md"
        if storyboard_file.exists():
            self.storyboard_preview.setPlainText(storyboard_file.read_text(encoding="utf-8"))

        summary_file = out / "summary.json"
        if summary_file.exists():
            self.log_preview.append(f"\n--- Summary ---")
            self.log_preview.append(summary_file.read_text(encoding="utf-8"))

    def _open_output(self):
        if self.output_dir:
            os.startfile(self.output_dir)
        else:
            os.startfile("output")

    def _reset_ui(self):
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(13, 17, 23))
    palette.setColor(QPalette.WindowText, QColor(201, 209, 217))
    palette.setColor(QPalette.Base, QColor(22, 27, 34))
    palette.setColor(QPalette.Text, QColor(201, 209, 217))
    palette.setColor(QPalette.Button, QColor(33, 38, 45))
    palette.setColor(QPalette.ButtonText, QColor(201, 209, 217))
    palette.setColor(QPalette.Highlight, QColor(35, 134, 54))
    app.setPalette(palette)

    window = TikTokFactoryGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
