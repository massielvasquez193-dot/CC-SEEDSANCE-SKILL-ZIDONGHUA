"""
TikTok AI Factory Pro — Release Builder (v1.0)
=================================================
Builds a clean client release package.
Excludes all dev artifacts, reports, tests, and source tools.
Only customer-facing runtime files are included.
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.0.0"
RELEASE_DIR = PROJECT_ROOT / "release" / "client"

# ================================================================
# Keep / Exclude rules
# ================================================================

# Directories to copy in full
KEEP_DIRS = [
    "app", "agents", "providers", "config", "license", "updater",
    "workflows", "skills", "prompts", "installer",
    "case_library",
]
# NOTE: server/ is intentionally excluded — the SaaS License Server runs
# on the vendor's infrastructure, not on the customer's machine.
# See SERVER_AUDIT.md for full analysis.

# Directories to create empty (no content from dev)
EMPTY_DIRS = ["input/products", "input/characters", "input/reference_videos", "output", "logs"]

# Single files to include
KEEP_FILES = [
    "launcher.py", "run_factory.py", "version.txt", "requirements.txt",
    ".env.example",
]

# Patterns to ALWAYS exclude
EXCLUDE_PATTERNS = [
    "__pycache__", "*.pyc", "*.pyo", ".gitkeep",
    ".DS_Store", "Thumbs.db",
    "*.db", "*.db-journal", "*.db-wal",
]

# Files to delete from copied dirs
STRIP_FILES = [
    # Reports
    "*_REPORT*.md", "*_AUDIT*.md", "PHASE*.md", "PROJECT_*.md",
    "PROVIDER_*.md", "VIDEO_*.md", "GUI_TEST*.md", "TEST_*.md",
    "PRODUCTION_*.md", "SEEDANCE_*.md", "REAL_API*.md",
    "INSTALLER_BUILD.md", "RUN_PRODUCTION.md", "RELEASE_*.md",
    "RC_TEST_REPORT.md",
    # Dev docs
    "CHARACTER_CONSISTENCY.md", "DEMO_SCRIPT.md",
    "UGC_SCRIPT_ENGINE.md", "VIDEO_VALIDATION.md",
    "LICENSE_SETUP.md",
    # Build artifacts
    "installer/setup.iss", "installer/build_installer.bat",
    # Specific files
    "SKILL(2).md", ".env", ".gitignore",
]

# Root-level files to DELETE
ROOT_EXCLUDES = [
    ".gitignore", ".env", "SKILL(2).md", "license.key",
    "DEMO_SALES_SCRIPT.md",
] + [f for f in os.listdir(str(PROJECT_ROOT)) if f.endswith(".docx")]

# ================================================================
# Builder
# ================================================================

class ReleaseBuilder:
    def __init__(self):
        self.root = PROJECT_ROOT
        self.release = RELEASE_DIR
        self.manifest = {"kept": [], "excluded": [], "empty_dirs": EMPTY_DIRS}
        self._kept_count = 0
        self._excluded_count = 0

    def build(self):
        print(f"\n{'='*60}")
        print(f"  TikTok AI Factory Pro — Release Builder v{VERSION}")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}\n")

        # Clean (ignore locks from background processes)
        if self.release.exists():
            shutil.rmtree(self.release, ignore_errors=True)
        self.release.mkdir(parents=True, exist_ok=True)

        # 1. Copy directories
        print("[1/5] Copying runtime packages...")
        for d in KEEP_DIRS:
            src = self.root / d
            if not src.exists():
                continue
            dst = self.release / d
            shutil.copytree(src, dst, ignore=self._ignore_patterns, dirs_exist_ok=True)
            count = len(list(dst.rglob("*")))
            self.manifest["kept"].append(f"{d}/ ({count} files)")
            self._kept_count += count
            print(f"  ✓ {d}/")

        # 2. Copy root files
        print("\n[2/5] Copying root files...")
        for f in KEEP_FILES:
            src = self.root / f
            if src.exists():
                shutil.copy2(src, self.release / f)
                self.manifest["kept"].append(f)
                self._kept_count += 1
                print(f"  ✓ {f}")

        # Copy .env.example as .env
        env_example = self.release / ".env.example"
        if env_example.exists():
            shutil.copy2(env_example, self.release / ".env")
            self.manifest["kept"].append(".env (from .env.example)")
            self._kept_count += 1

        # 3. Create empty dirs
        print("\n[3/5] Creating empty directories...")
        for d in EMPTY_DIRS:
            (self.release / d).mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {d}/ (empty)")

        # 4. Strip excluded files
        print("\n[4/5] Stripping dev artifacts...")
        self._strip_files()
        # After stripping, recompute
        print(f"  Excluded files: {len(self.manifest['excluded'])}")

        # 5. Generate docs
        print("\n[5/5] Generating release documents...")
        self._gen_readme()
        self._gen_quickstart()
        self._gen_manifest()

        # Compute final size
        total_size = sum(f.stat().st_size for f in self.release.rglob("*") if f.is_file())
        total_files = len(list(self.release.rglob("*")))

        print(f"\n{'='*60}")
        print(f"  ✅ Release package built!")
        print(f"  Location: {self.release}")
        print(f"  Size:     {total_size / 1024 / 1024:.1f} MB")
        print(f"  Files:    {total_files}")
        print(f"  Version:  v{VERSION}")
        print(f"{'='*60}\n")

    def _ignore_patterns(self, directory, files):
        """shutil.copytree ignore callback."""
        ignored = set()
        for f in files:
            # Skip cache
            if f == "__pycache__":
                ignored.add(f)
                continue
            # Skip .pyc
            if f.endswith(".pyc"):
                ignored.add(f)
                continue
            # Skip .gitkeep
            if f == ".gitkeep":
                ignored.add(f)
                continue
            # Skip DB files
            if f.endswith(".db") or f.endswith(".db-journal") or f.endswith(".db-wal"):
                ignored.add(f)
                continue
            # Skip report/audit files
            fl = f.lower()
            if any(kw in fl for kw in ["_report.md", "_audit.md", "phase2", "phase3",
                                         "project_audit", "provider_audit",
                                         "video_provider_audit", "gui_test_report",
                                         "test_report", "production_acceptance",
                                         "seedance_connection", "seedance_production",
                                         "real_api_mode", "installer_build",
                                         "run_production", "release_report",
                                         "rc_test_report", "update_test_report"]):
                rel = str(Path(directory) / f).replace(str(self.root), "")
                self.manifest["excluded"].append(rel)
                self._excluded_count += 1
                ignored.add(f)
                continue
            # Skip build scripts
            if f in ("setup.iss", "build_installer.bat"):
                rel = str(Path(directory) / f).replace(str(self.root), "")
                self.manifest["excluded"].append(rel)
                self._excluded_count += 1
                ignored.add(f)
                continue
        return ignored

    def _strip_files(self):
        """Post-copy cleanup of excluded files."""
        # Delete root-level excluded files
        for f in ROOT_EXCLUDES:
            path = self.release / f
            if path.exists():
                path.unlink()
                self.manifest["excluded"].append(f)

        # Delete specific unwanted files from copied dirs
        for pattern in ["setup.iss", "build_installer.bat", "SKILL(2).md",
                        "RELEASE_REPORT.md", "RELEASE_PACKAGE_REPORT.md"]:
            for p in self.release.rglob(pattern):
                rel = str(p.relative_to(self.release))
                self.manifest["excluded"].append(rel)
                p.unlink()

    def _gen_readme(self):
        readme = f"""# TikTok AI Factory Pro v{VERSION}

## 全自动 TikTok AI 视频生产工厂

### 快速开始

```
1. pip install -r requirements.txt
2. 编辑 .env → 填入 API Key
3. 素材放入 input/ 目录
4. python launcher.py
```

### 5 个核心功能

| 标签页 | 说明 |
|--------|------|
| 🎬 一键生成 | 上传 3 素材 → 1 按钮 → 成品视频 |
| 🏭 批量工厂 | 目录级输入 → 自动批量生产 |
| 📚 案例库 | 3 个 K-Beauty 品牌完整案例 |
| ⚙️ 设置中心 | GUI 配置 API Key 和系统设置 |
| 👤 客户中心 | 授权/成本/视频/系统状态仪表盘 |

### API Keys

| 服务 | 用途 | 获取 |
|------|------|------|
| OpenAI | 文本 + 图像 | https://platform.openai.com |
| ElevenLabs | TTS 语音 | https://elevenlabs.io |
| 火山引擎 ARK | Seedance 视频 | https://console.volcengine.com |

### 系统要求
- Windows 10+ / macOS 12+ / Ubuntu 20.04+
- Python 3.10+ | FFmpeg | 8GB+ RAM
- PySide6 (GUI): `pip install PySide6`

### 授权
联系供应商获取 license.key。支持在线 SaaS 授权或离线文件授权。

---
TikTok AI Factory Pro v{VERSION} | {datetime.now().year}
"""
        (self.release / "README.md").write_text(readme, encoding="utf-8")

    def _gen_quickstart(self):
        qs = """# TikTok AI Factory Pro — 快速开始

## 5 分钟上手

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 API Key
打开 `.env`，填入：
```bash
OPENAI_API_KEY=sk-你的key
ARK_API_KEY=ark-你的key
ELEVENLABS_API_KEY=el_你的key
```

### 3. 放入素材
- `input/products/` → 产品图片 (.jpg/.png/.webp)
- `input/characters/` → 人物图片 (.jpg/.png)
- `input/reference_videos/` → 参考视频 (.mp4)

### 4. 启动
```bash
python launcher.py
```

### 5. 生成视频
切换到「🎬 一键生成」→ 上传 3 个素材 → 点击「开始生成」

输出在 `output/` 目录。

---

**需要帮助？** 联系供应商获取支持。
"""
        (self.release / "QUICK_START.md").write_text(qs, encoding="utf-8")

    def _gen_manifest(self):
        """Generate RELEASE_MANIFEST.md."""
        total_size = sum(f.stat().st_size for f in self.release.rglob("*") if f.is_file())
        total_files = len(list(self.release.rglob("*")))
        py_count = len(list(self.release.rglob("*.py")))

        # Build directory tree
        tree = self._build_tree(self.release)

        lines = [
            f"# TikTok AI Factory Pro — Release Manifest",
            f"",
            f"## 版本信息",
            f"- **版本号:** v{VERSION}",
            f"- **发布日期:** {datetime.now().strftime('%Y-%m-%d')}",
            f"- **包大小:** {total_size / 1024 / 1024:.1f} MB",
            f"- **总文件数:** {total_files}",
            f"- **Python 文件:** {py_count}",
            f"",
            f"## 包含的运行时包",
        ]
        for d in KEEP_DIRS:
            p = self.release / d
            if p.exists():
                files = len(list(p.rglob("*")))
                lines.append(f"- **{d}/** — {files} 个文件")

        lines += [
            "",
            "## 包含的根文件",
        ]
        for f in KEEP_FILES:
            lines.append(f"- `{f}`")
        lines.append("- `.env` (从 .env.example 生成)")
        lines.append("- `README.md`")
        lines.append("- `QUICK_START.md`")

        lines += [
            "",
            "## 从客户包中排除的文件",
            "",
            "### 开发报告 (已排除)",
        ]
        for e in self.manifest.get("excluded", [])[:30]:
            lines.append(f"- `{e}`")
        if len(self.manifest.get("excluded", [])) > 30:
            lines.append(f"- ... 及其他 {len(self.manifest['excluded']) - 30} 个文件")

        lines += [
            "",
            "### 排除类别",
            "- 所有 *REPORT*.md / *AUDIT*.md",
            "- 开发阶段文档 (PHASE2/3, PRODUCTION_ACCEPTANCE 等)",
            "- 测试文件 (RC_TEST_REPORT, UPDATE_TEST_REPORT 等)",
            "- 构建脚本 (setup.iss, build_installer.bat)",
            "- 开发工具源码 (demo_generator.py, rc_stress_test.py 等)",
            "- 缓存文件 (__pycache__/, *.pyc)",
            "- 数据库文件 (*.db)",
            "- 敏感文件 (.env 真实 Key)",
            "- .docx 文件",
            "- .gitignore, .git/",
            "",
            "## 空目录 (运行时填充)",
        ]
        for d in EMPTY_DIRS:
            lines.append(f"- `{d}/`")

        lines += [
            "",
            "## 目录树",
            "```",
            tree,
            "```",
            "",
            f"---",
            f"*生成时间: {datetime.now().isoformat()}*",
            f"*构建工具: tools/release_builder.py*",
        ]

        manifest = "\n".join(lines)
        (self.release / "RELEASE_MANIFEST.md").write_text(manifest, encoding="utf-8")
        # Also save to project root
        (self.root / "RELEASE_MANIFEST.md").write_text(manifest, encoding="utf-8")
        print(f"  ✓ RELEASE_MANIFEST.md")

    def _build_tree(self, root: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
        """Build an ASCII directory tree."""
        if current_depth >= max_depth:
            return ""

        lines = []
        entries = sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name))

        for i, entry in enumerate(entries):
            if entry.name in ("__pycache__", ".git", "__init__.py"):
                continue
            if entry.name.endswith(".pyc"):
                continue
            if entry.name.startswith(".") and entry.name not in (".env", ".env.example"):
                continue

            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            new_prefix = prefix + ("    " if is_last else "│   ")

            if entry.is_dir():
                name = entry.name + "/"
                # Count files inside
                file_count = len([f for f in entry.rglob("*") if f.is_file() and "__pycache__" not in str(f)])
                lines.append(f"{prefix}{connector}{name} ({file_count} files)")
                if current_depth + 1 < max_depth:
                    subtree = self._build_tree(entry, new_prefix, max_depth, current_depth + 1)
                    if subtree:
                        lines.append(subtree)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

        return "\n".join(lines)


if __name__ == "__main__":
    builder = ReleaseBuilder()
    builder.build()
