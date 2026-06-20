# TikTok AI Factory Pro — 安装包报告

## 版本信息

| 项目 | 值 |
|------|-----|
| 版本号 | **v1.0.0** |
| 安装包名称 | `TikTok-AI-Factory-Pro-v1.0-Setup.exe` |
| 发布日期 | 2026-06-14 |
| 目标平台 | Windows 10+ / 11 |

---

## 安装包内容

### 构建方式

两层打包：

```
Python source → PyInstaller → launcher.exe (single .exe)
launcher.exe + runtime files → Inno Setup → Setup.exe (installer)
```

### 安装包大小估算

| 组件 | 大小 |
|------|------|
| Python 运行时 (embedded) | ~15 MB |
| 应用程序代码 | ~3 MB |
| 案例库资源 | ~1.5 MB |
| 配置文件 + 文档 | ~0.5 MB |
| Inno Setup 压缩后 | **~25-35 MB** (lzma2 压缩) |

### 安装到客户机器后

| 目录 | 大小 | 说明 |
|------|------|------|
| `C:\Program Files\TikTok-AI-Factory-Pro\` | ~40-50 MB | 安装根目录 |
| `launcher.exe` | ~20 MB | PyInstaller 打包的主程序 |
| `agents/` | ~200 KB | AI Agent 引擎 |
| `app/` | ~400 KB | 应用核心 + GUI |
| `providers/` | ~100 KB | 9 个 AI 提供商 |
| `config/` | ~55 KB | 配置文件 |
| `case_library/` | ~1.5 MB | 3 个品牌案例 |
| `input/` | 空 | 素材目录 |
| `output/` | 空 | 输出目录 |
| `logs/` | 空 | 日志目录 |

---

## 依赖项

### 系统依赖

| 依赖 | 版本 | 必选? | 说明 |
|------|------|:--:|------|
| Python | 3.10+ | ✅ | PyInstaller 已打包进 launcher.exe，无需单独安装 |
| FFmpeg | 任意 | ⚠️ | 视频合成需要。未安装时跳过视频生成步骤 |

### Python 依赖 (PyInstaller 已打包)

| 包 | 用途 |
|------|------|
| `openai` | OpenAI GPT-4o + DALL-E 3 |
| `anthropic` | Claude API |
| `google-generativeai` | Gemini API |
| `Pillow` | 图像生成 |
| `opencv-python` | 视频分析 |
| `python-dotenv` | .env 配置 |
| `requests` | HTTP / 更新 / License |
| `PySide6` | GUI (需单独 `pip install PySide6`) |

---

## 安装目录结构

```
C:\Program Files\TikTok-AI-Factory-Pro\
├── launcher.exe              # PyInstaller 主程序
├── .env                      # 配置文件 (首次启动向导生成)
├── .env.example              # 配置模板
├── version.txt               # 版本号 v1.0.0
├── requirements.txt          # Python 依赖清单
├── README.md                 # 项目说明
├── QUICK_START.md            # 快速开始
│
├── agents/                   # AI Agent 引擎
├── app/                      # 应用核心
│   └── gui/                  # GUI 界面
├── providers/                # AI 提供商
├── config/                   # 配置文件
├── license/                  # 授权系统
├── updater/                  # 自动更新
├── workflows/                # 工作流
├── skills/                   # 视频复刻
├── prompts/                  # 系统提示词
├── tools/                    # 工具集
├── case_library/             # 案例库 (Medicube/Anua/COSRX)
│
├── input/                    # 素材目录 (空)
│   ├── products/
│   ├── characters/
│   └── reference_videos/
├── output/                   # 视频输出 (空)
├── logs/                     # 日志 (空)
└── installer/                # 依赖安装脚本
    └── install_deps.bat
```

---

## 首次启动流程

```
1. 用户双击桌面快捷方式 / launcher.exe
       │
2. API 配置向导弹出
   ┌──────────────────────────────────────┐
   │  🚀 欢迎使用 TikTok AI Factory Pro    │
   │                                      │
   │  OpenAI API Key:    [sk-...] [测试]   │
   │  ElevenLabs API Key:[el_...] [测试]   │
   │  ARK API Key:       [ark-...][测试]   │
   │                                      │
   │  ████████░░░░ 67%                    │
   │                                      │
   │  [跳过，稍后配置] [💾 保存并开始使用]   │
   └──────────────────────────────────────┘
       │
3. 保存到 .env → 进入主界面 (6 标签页)
```

- 可点击「跳过」— 模板模式运行
- 稍后可在「⚙️ 设置中心」补填
- 向导只显示一次 (`.env` 中 `TIKTOK_FACTORY_WIZARD_COMPLETED=true`)

---

## 升级方式

### 自动更新
软件启动时自动检查 `config/update.json` 中配置的更新服务器。
发现新版本后弹窗 → 一键下载 → 自动安装 → 重启。

### 手动更新
1. 下载新版本 `Setup.exe`
2. 覆盖安装（保留 `.env`、`license.key`、`output/`、`logs/`）
3. 启动

---

## 卸载方式

### 方式 1: Windows 控制面板
设置 → 应用 → TikTok AI Factory Pro → 卸载

### 方式 2: 开始菜单
开始菜单 → TikTok AI Factory Pro → 卸载 TikTok AI Factory Pro

### 卸载行为
- ✅ 删除程序文件
- ✅ 删除快捷方式
- ⚠️ **保留** `output/` 和 `logs/` 目录（用户视频数据）
- ⚠️ **保留** `.env` 文件（API Key）
- 完全删除需手动清空安装目录

---

## 构建文件清单

| 文件 | 说明 |
|------|------|
| `installer/launcher.spec` | PyInstaller 打包配置 |
| `installer/setup_v1.iss` | Inno Setup 安装脚本 |
| `installer/install_deps.bat` | 依赖安装批处理 |
| `installer/BUILD_INSTRUCTIONS.md` | 构建指南 |
| `app/gui/api_wizard.py` | 首次启动 API 配置向导 |
| `INSTALL_PACKAGE_REPORT.md` | 本报告 |

---

*报告生成: 2026-06-14*
