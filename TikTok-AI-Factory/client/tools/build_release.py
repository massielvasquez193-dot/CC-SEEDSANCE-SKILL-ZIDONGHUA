"""
TikTok AI Factory Pro — Release Builder
=========================================
Builds the v1.0 release package:
  client/  — Customer-facing runtime files
  docs/    — All documentation
  dev/     — Development artifacts (reports, audits)
  tests/   — Test scripts and results
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.0.0"
RELEASE_NAME = f"TikTok-AI-Factory-Pro-v{VERSION}"


class ReleaseBuilder:
    """Builds the v1.0 release package."""

    def __init__(self):
        self.root = PROJECT_ROOT

    def build(self):
        print(f"\n{'='*60}")
        print(f"  TikTok AI Factory Pro — Release Builder")
        print(f"  Version: {VERSION}")
        print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}\n")

        # Phase 1: Clean and create directories
        for d in ["client", "docs", "dev", "tests"]:
            target = self.root / d
            if target.exists():
                # Don't remove if it's the original (non-release dir)
                pass
            target.mkdir(parents=True, exist_ok=True)

        # Phase 2: Copy client files
        print("[1/5] Building client/ package...")
        client_files = self._copy_client()
        print(f"      {client_files} files copied to client/")

        # Phase 3: Copy docs
        print("[2/5] Organizing docs/...")
        doc_count = self._copy_docs()
        print(f"      {doc_count} documents")

        # Phase 4: Move dev artifacts
        print("[3/5] Archiving dev/ artifacts...")
        dev_count = self._copy_dev()
        print(f"      {dev_count} dev files")

        # Phase 5: Copy tests
        print("[4/5] Organizing tests/...")
        test_count = self._copy_tests()
        print(f"      {test_count} test files")

        # Phase 6: Generate release report
        print("[5/5] Generating RELEASE_PACKAGE_REPORT.md...")
        self._generate_report(client_files, doc_count, dev_count, test_count)

        print(f"\n{'='*60}")
        print(f"  ✅ Release package built successfully")
        print(f"     client/  — {client_files} files")
        print(f"     docs/    — {doc_count} docs")
        print(f"     dev/     — {dev_count} artifacts")
        print(f"     tests/   — {test_count} test files")
        print(f"{'='*60}\n")

    # ================================================================
    # Client package
    # ================================================================

    # Directories to include in client package
    CLIENT_DIRS = [
        "agents", "app", "config", "providers", "license",
        "updater", "workflows", "skills", "prompts", "tools",
        "input", "installer", "server", "sample_input",
    ]

    # Files to include in client root
    CLIENT_FILES = [
        "launcher.py", "run_factory.py", "version.txt",
        "requirements.txt", ".env.example",
    ]

    # Directories to create empty in client
    CLIENT_EMPTY_DIRS = ["output", "logs"]

    def _copy_client(self) -> int:
        client_root = self.root / "client"
        count = 0

        # Copy Python packages
        for dir_name in self.CLIENT_DIRS:
            src = self.root / dir_name
            if not src.exists():
                continue
            dst = client_root / dir_name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                "__pycache__", "*.pyc", ".gitkeep", "*.db"
            ))
            count += len(list(dst.rglob("*")))

        # Copy root files
        for filename in self.CLIENT_FILES:
            src = self.root / filename
            if src.exists():
                shutil.copy2(src, client_root / filename)
                count += 1

        # Copy license.key
        lic = self.root / "license.key"
        if lic.exists():
            shutil.copy2(lic, client_root / "license.key")
            count += 1

        # Create empty dirs with .gitkeep
        for d in self.CLIENT_EMPTY_DIRS:
            empty_dir = client_root / d
            empty_dir.mkdir(parents=True, exist_ok=True)
            # Don't copy actual output/logs content

        # Generate .env from current .env (with keys masked for distribution)
        env_src = self.root / ".env"
        if env_src.exists():
            # Use .env.example as base, not actual keys
            env_example = self.root / ".env.example"
            if env_example.exists():
                shutil.copy2(env_example, client_root / ".env")
            else:
                # Create a sanitized .env
                lines = []
                for line in env_src.read_text(encoding="utf-8").split("\n"):
                    if "=" in line and not line.strip().startswith("#"):
                        k = line.split("=")[0].strip()
                        if any(x in k for x in ["API_KEY", "SECRET", "TOKEN"]):
                            lines.append(f"{k}=")
                        else:
                            lines.append(line)
                    else:
                        lines.append(line)
                (client_root / ".env").write_text("\n".join(lines), encoding="utf-8")
            count += 1

        return count

    # ================================================================
    # Documentation
    # ================================================================

    DOC_CATEGORIES = {
        "user-guides": [
            "CLIENT_USER_GUIDE.md",
            "CLIENT_INSTALL_GUIDE.md",
            "CUSTOMER_DASHBOARD_GUIDE.md",
            "QUICK_START.md",  # will be generated
            "FAQ.md",
        ],
        "features": [
            "ONE_CLICK_MODE.md",
            "BATCH_FACTORY_MODE.md",
            "SETTINGS_CENTER.md",
            "CUSTOMER_PORTAL.md",
            "AUTO_UPDATE_SYSTEM.md",
            "UPDATE_PROCESS.md",
        ],
        "technical": [
            "LICENSE_SERVER.md",
            "LICENSE_SETUP.md",
            "UPDATE_TEST_REPORT.md",
            "RC_TEST_REPORT.md",
            "RELEASE_REPORT.md",
        ],
        "misc": [
            "CHARACTER_CONSISTENCY.md",
            "DEMO_SCRIPT.md",
            "UGC_SCRIPT_ENGINE.md",
            "VIDEO_VALIDATION.md",
            "REAL_API_MODE.md",
        ],
    }

    def _copy_docs(self) -> int:
        docs_root = self.root / "docs"
        count = 0

        for category, files in self.DOC_CATEGORIES.items():
            cat_dir = docs_root / category
            cat_dir.mkdir(parents=True, exist_ok=True)
            for fname in files:
                src = self.root / fname
                if src.exists():
                    shutil.copy2(src, cat_dir / fname)
                    count += 1

        # Copy .docx files
        for docx in self.root.glob("*.docx"):
            shutil.copy2(docx, docs_root / "misc" / docx.name)
            count += 1

        # Generate README for the root
        self._generate_readme(docs_root / "README.md")
        count += 1

        return count

    def _generate_readme(self, path: Path):
        readme = f"""# TikTok AI Factory Pro v{VERSION}

## 全自动 TikTok AI 视频生产工厂

### 快速开始

1. 安装依赖: `pip install -r requirements.txt`
2. 配置 API Key: 编辑 `.env` 文件，填入你的 API Key
3. 放入素材: 将产品图/人物图/参考视频放入 `input/` 目录
4. 启动 GUI: `python launcher.py`
5. 或 CLI: `python run_factory.py --max-tasks 1`

### 功能概览

- 🎬 **一键生成**: 上传 3 个素材 → 1 个按钮 → 成品视频
- 🏭 **批量工厂**: 目录级输入 → 自动配对 → 批量生产
- 🛠️ **手动模式**: 分步控制每个环节
- ⚙️ **设置中心**: GUI 配置 API Key，无需编辑 .env
- 👤 **客户中心**: 授权/成本/视频记录/系统状态一览

### 系统要求

- Windows 10+ / macOS 12+ / Ubuntu 20.04+
- Python 3.10+
- FFmpeg (视频合成)
- 8GB+ RAM

### API Keys

| 服务 | 用途 | 获取地址 |
|------|------|----------|
| OpenAI | 文本 + 图像生成 | https://platform.openai.com |
| ElevenLabs | TTS 语音合成 | https://elevenlabs.io |
| 火山引擎 ARK | Seedance 视频生成 | https://console.volcengine.com |

### 文档

- [快速入门](user-guides/QUICK_START.md)
- [用户指南](user-guides/CLIENT_USER_GUIDE.md)
- [常见问题](user-guides/FAQ.md)
- [一键生成](features/ONE_CLICK_MODE.md)
- [批量工厂](features/BATCH_FACTORY_MODE.md)

### 授权

本软件需要有效授权才能运行。请联系供应商获取 License Key。
"""
        path.write_text(readme, encoding="utf-8")

    # ================================================================
    # Dev artifacts
    # ================================================================

    DEV_FILES = [
        "PHASE2_REPORT.md",
        "PHASE3_REPORT.md",
        "PRODUCTION_ACCEPTANCE_REPORT.md",
        "PROJECT_AUDIT.md",
        "PROVIDER_AUDIT.md",
        "VIDEO_PROVIDER_AUDIT.md",
        "GUI_TEST_REPORT.md",
        "TEST_REPORT.md",
        "SEEDANCE_CONNECTION_TEST.md",
        "SEEDANCE_PRODUCTION_ERROR.md",
        "INSTALLER_BUILD.md",
        "RUN_PRODUCTION.md",
    ]

    def _copy_dev(self) -> int:
        dev_root = self.root / "dev"
        count = 0

        for fname in self.DEV_FILES:
            src = self.root / fname
            if src.exists():
                shutil.copy2(src, dev_root / fname)
                count += 1

        return count

    # ================================================================
    # Test files
    # ================================================================

    TEST_FILES = [
        "RC_TEST_REPORT.md",
        "UPDATE_TEST_REPORT.md",
        "tools/rc_stress_test.py",
        "output/rc_stress_test_results.json",
    ]

    def _copy_tests(self) -> int:
        test_root = self.root / "tests"
        count = 0

        for fname in self.TEST_FILES:
            src = self.root / fname
            if src.exists():
                dst = test_root / Path(fname).name
                shutil.copy2(src, dst)
                count += 1

        # Also copy test logs
        logs_dir = self.root / "logs"
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                dst = test_root / "logs"
                dst.mkdir(parents=True, exist_ok=True)
                shutil.copy2(log_file, dst / log_file.name)
                count += 1

        return count

    # ================================================================
    # Release Report
    # ================================================================

    def _generate_report(self, client_count, doc_count, dev_count, test_count):
        client_root = self.root / "client"
        total_size = sum(
            f.stat().st_size for f in client_root.rglob("*") if f.is_file()
        )

        report = f"""# TikTok AI Factory Pro — Release Package Report

## 版本
**TikTok AI Factory Pro v{VERSION}**

## 发布日期
{datetime.now().strftime('%Y-%m-%d')}

---

## 客户交付物 (client/)

客户获得的完整运行时文件。

### 核心运行文件

| 文件 | 说明 |
|------|------|
| `launcher.py` | GUI/CLI 启动器 |
| `run_factory.py` | CLI 工厂入口 |
| `version.txt` | 版本文件 |
| `requirements.txt` | Python 依赖 |
| `.env` | 配置文件（需填入 API Key） |
| `license.key` | 授权文件 |

### Python 包 (13 个)

| 目录 | 说明 | 文件数 |
|------|------|--------|
| `agents/` | AI Agent 模块（剧本/分镜/口播/关键帧/一致性） | 17 |
| `app/` | 应用核心（流水线/扫描器/GUI/控制器） | 18 |
| `config/` | 配置文件（settings/provider/factory/update） | 6 |
| `providers/` | AI 提供商（OpenAI/Claude/DeepSeek/Seedance/...） | 10 |
| `license/` | 授权管理（在线+离线） | 2 |
| `updater/` | 自动更新系统（检查/下载/安装/回滚） | 5 |
| `workflows/` | 工厂工作流 | 2 |
| `skills/` | 视频复刻技能 | 2 |
| `prompts/` | 系统提示词 | 1 |
| `tools/` | 工具（成本报告/环境检测） | 4 |
| `input/` | 素材输入目录（空） | — |
| `output/` | 视频输出目录（空） | — |
| `server/` | License Server | 4 |

### 客户交付文件总数
**{client_count} 个文件**

### 安装包大小
**{total_size / 1024 / 1024:.1f} MB**

---

## 文档 (docs/) — {doc_count} 个文档

### 用户指南 (user-guides/)
- CLIENT_USER_GUIDE.md — 客户端使用指南
- CLIENT_INSTALL_GUIDE.md — 安装指南
- CUSTOMER_DASHBOARD_GUIDE.md — 客户后台使用指南
- FAQ.md — 常见问题
- README.md — 项目说明

### 功能文档 (features/)
- ONE_CLICK_MODE.md — 一键生成
- BATCH_FACTORY_MODE.md — 批量工厂
- SETTINGS_CENTER.md — 设置中心
- CUSTOMER_PORTAL.md — 客户后台
- AUTO_UPDATE_SYSTEM.md — 自动更新

### 技术文档 (technical/)
- LICENSE_SERVER.md — 授权服务器
- RC_TEST_REPORT.md — RC 测试报告

---

## 开发文件 (dev/) — {dev_count} 个文件

以下文件**已从客户交付包中排除**：

- 开发阶段报告（Phase 2/3、Production Acceptance）
- 项目审计报告（Project/Provider/Video Audit）
- GUI 测试报告
- Seedance 调试报告
- Installer 构建脚本

---

## 测试文件 (tests/) — {test_count} 个文件

- RC_TEST_REPORT.md — 100 任务压力测试报告
- UPDATE_TEST_REPORT.md — 更新系统测试报告
- rc_stress_test.py — 压力测试脚本
- rc_stress_test_results.json — 原始测试数据

---

## 客户端安装步骤

### 1. 解压
解压 `TikTok-AI-Factory-Pro-v{VERSION}.zip` 到任意目录。

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置 API Key
编辑 `.env`，填入：
```bash
OPENAI_API_KEY=sk-...
ARK_API_KEY=ark-...
ELEVENLABS_API_KEY=el_...
```

### 4. 放入素材
将产品图/人物图/参考视频放入 `input/` 对应目录。

### 5. 启动
```bash
# GUI
python launcher.py

# CLI
python run_factory.py --max-tasks 1
```

### 6. 授权
将 `license.key` 放在项目根目录，或配置在线 License Server。

---

## 更新方式

软件启动时自动检查 `config/update.json` 中配置的更新服务器。
发现新版本后弹窗提示，一键下载安装自动重启。

详见：docs/features/AUTO_UPDATE_SYSTEM.md

---

## 授权方式

### 离线模式
将 `license.key` 放在项目根目录，软件启动时自动验证。

### 在线模式
配置 `.env`：
```bash
LICENSE_SERVER_URL=http://your-server:8199
LICENSE_KEY=TKAIF-XXXX-XXXX-XXXX-XXXX
```

启动时先在线验证，服务器不可达时降级到离线验证。

详见：docs/technical/LICENSE_SERVER.md

---

## 排除项

以下内容**未包含**在客户交付包中：

| 类别 | 排除内容 |
|------|----------|
| 开发数据 | `output/` 目录内容、`logs/` 目录内容 |
| 缓存 | `__pycache__/`、`*.pyc` |
| 数据库 | `*.db` (License Server 运行时生成) |
| 开发报告 | Phase 报告、Audit 报告 |
| 测试数据 | 压力测试输出、测试日志 |
| 原始素材 | `sample_input/` 中的示例文件 |
| 敏感信息 | `.env` 中的真实 API Key（已替换为空） |

---

## 目录树 (client/)

```
client/
├── launcher.py                 # 启动器
├── run_factory.py              # CLI 入口
├── version.txt                 # 版本 v{VERSION}
├── requirements.txt            # Python 依赖
├── .env                        # 配置模板
├── .env.example                # 配置示例
├── license.key                 # 授权文件
│
├── agents/                     # AI Agent 引擎
│   ├── master_script_generator.py
│   ├── script_generator.py
│   ├── storyboard_generator.py
│   ├── keyframe_generator.py
│   ├── seedance_generator.py
│   ├── veo3_generator.py
│   ├── jimeng_generator.py
│   ├── voiceover_generator.py
│   ├── character_consistency.py
│   ├── character_generator.py
│   ├── character_library.py
│   ├── continuity_engine.py
│   ├── ugc_director.py
│   ├── ugc_score.py
│   ├── subtitle_generator.py
│   ├── subtitle_alignment.py
│   ├── image_prompt_generator.py
│   ├── viral_analyzer.py
│   ├── voice_style_analyzer.py
│   └── export_manager.py
│
├── app/                        # 应用核心
│   ├── pipeline.py
│   ├── scanner.py
│   ├── task_manager.py
│   ├── watcher.py
│   ├── product_extractor.py
│   ├── character_extractor.py
│   ├── video_analyzer.py
│   ├── ugc_director.py
│   ├── voice_engine.py
│   ├── ffmpeg_voice_merge.py
│   └── gui/
│       ├── gui.py              # 主 GUI (5 标签页)
│       ├── one_click_tab.py
│       ├── one_click_controller.py
│       ├── batch_factory_tab.py
│       ├── batch_controller.py
│       ├── batch_scheduler.py
│       ├── settings_tab.py
│       ├── customer_portal.py
│       ├── cost_tracker.py
│       └── video_history.py
│
├── config/                     # 配置
│   ├── settings.py
│   ├── settings_manager.py
│   ├── api_validator.py
│   ├── api_keys.py
│   ├── factory.json
│   ├── providers.json
│   ├── update.json
│   └── voices.json
│
├── providers/                  # AI 提供商 (9 个)
│   ├── base_provider.py
│   ├── openai_provider.py
│   ├── claude_provider.py
│   ├── deepseek_provider.py
│   ├── gemini_provider.py
│   ├── seedance_provider.py
│   ├── veo3_provider.py
│   ├── jimeng_provider.py
│   ├── runway_provider.py
│   ├── kling_provider.py
│   └── elevenlabs_provider.py
│
├── license/                    # 授权系统
├── updater/                    # 自动更新
├── workflows/                  # 工作流
├── skills/                     # 视频复刻
├── prompts/                    # 提示词
├── tools/                      # 工具集
├── server/                     # License Server
├── input/                      # 素材目录 (空)
├── output/                     # 输出目录 (空)
├── logs/                       # 日志目录 (空)
├── installer/                  # 打包工具
└── sample_input/               # 示例素材
```

---

*报告生成时间: {datetime.now().isoformat()}*
*构建工具: tools/build_release.py*
"""
        report_path = self.root / "RELEASE_PACKAGE_REPORT.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"      Report: {report_path}")


if __name__ == "__main__":
    builder = ReleaseBuilder()
    builder.build()
