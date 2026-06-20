# TikTok AI Factory Pro — 自动更新系统

## 概述

软件启动时自动检查新版本，发现更新后弹窗提示、一键下载安装、自动重启。

```
启动 → 检查 version.json → 比较版本 → [弹窗] → 下载 → 替换文件 → 重启
```

## 远程配置

### version.json 格式

在你的服务器上放置一个 `version.json` 文件：

```json
{
  "version": "3.0.1",
  "download_url": "https://your-domain.com/releases/tiktok-factory-3.0.1.zip",
  "force": false,
  "sha256": "a1b2c3d4e5f6... (可选，用于校验)"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | ✅ | 最新版本号，格式 `major.minor.patch` |
| `download_url` | string | ✅ | 更新包 .zip 下载地址 |
| `force` | bool | ❌ | `true` = 强制更新，用户无法跳过 |
| `sha256` | string | ❌ | zip 文件 SHA-256 校验和 |

### 更新包结构

`update.zip` 解压后直接覆盖项目根目录：

```
update.zip
├── launcher.py
├── run_factory.py
├── agents/
├── app/
├── providers/
├── updater/
├── config/
├── license/
├── version.txt       ← 必须包含新版本号
└── requirements.txt  ← 如有新的依赖
```

## 配置方式

在 `.env` 中设置：

```bash
# 远程 version.json 地址
TIKTOK_FACTORY_UPDATE_URL=https://your-domain.com/releases/version.json

# 设为 true 跳过自动更新检查
TIKTOK_FACTORY_SKIP_UPDATE=false

# 开发模式下自动跳过更新检查
TIKTOK_FACTORY_DEV_MODE=true
```

## 启动行为

| 环境 | 行为 |
|------|------|
| 生产模式 | 启动时自动检查更新 |
| 开发模式 (`TIKTOK_FACTORY_DEV_MODE=true`) | 自动跳过 |
| `TIKTOK_FACTORY_SKIP_UPDATE=true` | 自动跳过 |
| `--skip-update` 命令行参数 | 本次启动跳过 |

```bash
# 跳过更新检查
python launcher.py --skip-update
python run_factory.py --skip-update --max-tasks 1
```

## UI 模式

### PySide6 GUI（优先）

```
┌──────────────────────────────────────────┐
│  🎉 发现新版本                            │
│                                          │
│  当前版本：3.0.0                          │
│  最新版本：3.0.1                          │
│                                          │
│  ████████████░░░░░░░░  65%               │
│  12.5 / 18.2 MB                          │
│                                          │
│        [稍后提醒]  [🚀 立即更新]           │
└──────────────────────────────────────────┘
```

- 实时下载进度条
- 强制更新时「稍后提醒」按钮禁用
- 下载失败显示错误信息，可重试

### tkinter 回退（无 PySide6 时）

功能一致的 tkinter 窗口，样式简化但交互逻辑相同。

### CLI 模式（无 GUI 环境）

```
=============================================
  🎉 发现新版本
=============================================
  当前版本：3.0.0
  最新版本：3.0.1
=============================================
  是否立即更新? [Y/n]: y
  正在下载... ✓
  正在安装... ✓
  更新完成！正在重启...
```

## 更新流程详解

### Windows

1. 下载 `update.zip` 到临时目录
2. 解压到 `updater/_update_extracted/`
3. 生成 `updater/_update_apply.bat` 批处理脚本
4. 启动批处理（独立进程），主程序退出
5. 批处理：等待 2 秒 → `xcopy` 覆盖文件 → 清理临时文件 → 重启应用 → 自删除

### macOS / Linux

1. 下载 `update.zip`
2. 直接解压覆盖项目文件
3. `os.execv()` 原地重启进程

## 版本号规则

使用语义化版本 `major.minor.patch`：

```
3.0.0 → 3.0.1  = patch（bug 修复）
3.0.0 → 3.1.0  = minor（新功能）
3.0.0 → 4.0.0  = major（大版本）
```

比较逻辑：`major > minor > patch`，只要远程版本号严格大于本地版本号即提示更新。

## 安全

- 支持 SHA-256 校验（在 `version.json` 中提供 `sha256` 字段）
- 下载使用 HTTPS
- 更新失败不会影响当前运行版本（先在临时目录解压，再批量覆盖）
- 更新检查失败不影响正常启动

## 独立使用

```bash
# 手动检查更新
python -m updater.update_manager --check

# 静默检查（不弹 UI，仅返回状态码）
python -m updater.update_manager --check --silent

# 手动应用本地更新包
python -m updater.update_manager --force-apply /path/to/update.zip
```

## 版本发布流程

1. 修改 `version.txt` 中的版本号
2. 打包新版本：`zip -r update.zip . -x "output/*" "logs/*" ".git/*" "__pycache__/*" "*.pyc"`
3. 上传 `update.zip` 到服务器
4. 更新服务器上的 `version.json`
5. 客户端下次启动即可自动检测

## 文件清单

```
updater/
├── __init__.py           # 包定义
├── update_manager.py     # 核心更新逻辑（~400 行）
└── _update_apply.bat     # 运行时生成，Windows 更新脚本

version.txt               # 当前版本号

.env 配置项:
  TIKTOK_FACTORY_UPDATE_URL    # 远程 version.json 地址
  TIKTOK_FACTORY_SKIP_UPDATE   # 跳过更新检查
```
