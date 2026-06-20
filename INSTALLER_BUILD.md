# INSTALLER BUILD — TikTok AI Factory Pro Windows 安装版

---

## 构建方式

### 方式1: Inno Setup (推荐 — 专业安装包)

```bash
# 1. 安装 Inno Setup 6+
#    https://jrsoftware.org/isinfo.php

# 2. 编译
iscc installer/setup.iss

# 3. 输出
installer/output/TikTok-AI-Factory-Pro-Setup-v3.0.0.exe
```

**特点**: 标准Windows安装向导、开始菜单、桌面快捷方式、卸载程序、中英文界面

---

### 方式2: PyInstaller (单文件)

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 编译
pyinstaller --onefile --windowed --name "TikTok-AI-Factory-Pro-Setup" ^
    --add-data "start;start" ^
    --add-data "install;install" ^
    --add-data ".env.example;." ^
    --add-data "requirements.txt;." ^
    installer/setup_script.py

# 3. 输出
dist/TikTok-AI-Factory-Pro-Setup.exe
```

**特点**: 单文件、无需Inno Setup、Python脚本内置安装逻辑

---

### 方式3: 一键构建

```bash
双击: installer/build_installer.bat
选择: [1] Inno Setup / [2] PyInstaller / [3] NSIS
```

---

## 安装包功能

| 步骤 | 功能 | 自动 |
|------|------|:---:|
| 1 | 检测 Python 环境 | ✅ |
| 2 | 无Python则自动下载安装 | ✅ |
| 3 | 安装 requirements.txt 所有依赖 | ✅ |
| 4 | 检测 ffmpeg | ✅ |
| 5 | 无ffmpeg则自动下载安装 | ✅ |
| 6 | 从 .env.example 创建 .env | ✅ |
| 7 | 创建 input/output/logs 目录 | ✅ |
| 8 | 桌面生成快捷方式 | ✅ |
| 9 | 开始菜单添加快捷方式 | ✅ (Inno Setup) |
| 10 | 卸载程序 | ✅ (Inno Setup) |

---

## 客户安装流程

```
双击 Setup.exe
  → 选择安装目录
  → 勾选"创建桌面快捷方式"
  → 点击 Install
  → 等待自动安装完成
  → 编辑 .env 填入API密钥
  → 桌面双击"TikTok AI Factory"启动
```

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `installer/setup_script.py` | Python安装脚本 (可编译为.exe) |
| `installer/setup.iss` | Inno Setup 安装包脚本 |
| `installer/build_installer.bat` | 构建工具 (命令行/双击) |

---

## 编译要求

| 工具 | 下载 | 用于 |
|------|------|------|
| Inno Setup 6+ | https://jrsoftware.org/isinfo.php | 标准Windows安装包 |
| PyInstaller | `pip install pyinstaller` | 单文件安装包 |
| NSIS 3+ | https://nsis.sourceforge.io/ | 备选安装包 |
