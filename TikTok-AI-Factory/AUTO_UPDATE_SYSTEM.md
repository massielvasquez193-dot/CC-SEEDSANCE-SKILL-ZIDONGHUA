# TikTok AI Factory Pro — 自动更新系统

## 架构

```
updater/
├── __init__.py              # 统一导出
├── version_checker.py       # 远程版本检查 + 语义版本比较
├── download_manager.py      # 下载引擎（重试 + 进度 + SHA256）
├── update_installer.py      # 安全安装（备份 + 保留 + 回滚）
└── update_manager.py        # 编排器（UI对话框 + 流程控制）

config/
└── update.json              # 更新配置文件
```

## 更新流程

```
launcher.py 启动
  │
  ├─→ check_for_updates()
  │     │
  │     ├─ VersionChecker.fetch_remote_version()
  │     │   GET {server}/version.json
  │     │
  │     ├─ 版本比较 (semver: major.minor.patch)
  │     │
  │     ├─ 有新版本?
  │     │   ├─ NO  → 直接启动
  │     │   └─ YES → 弹窗
  │     │
  │     └─ 用户点击 [立即更新]
  │           │
  │           ├─ DownloadManager.download()
  │           │   ├─ 流式下载 + 进度回调
  │           │   ├─ 自动重试 3 次
  │           │   └─ SHA-256 校验
  │           │
  │           ├─ UpdateInstaller.install()
  │           │   ├─ 备份当前版本 (_update_backup/)
  │           │   ├─ 解压到临时目录
  │           │   ├─ 快照受保护文件 (.env, license.key, ...)
  │           │   ├─ 覆盖安装新文件
  │           │   ├─ 恢复受保护文件
  │           │   ├─ 记录 logs/update.log
  │           │   └─ 失败 → 自动回滚
  │           │
  │           └─ 重启应用 (Windows: batch / Unix: exec)
```

## 远程 version.json 格式

```json
{
  "latest_version": "3.1.0",
  "release_date": "2026-06-15",
  "download_url": "https://your-domain.com/releases/TikTok-AI-Factory-Pro-v3.1.0.zip",
  "force_update": false,
  "sha256": "abc123def456789...",
  "release_notes": [
    "优化 GPT Image 人物一致性",
    "新增批量工厂模式",
    "修复 Seedance 生成问题"
  ],
  "min_required_version": "3.0.0",
  "channel": "stable",
  "file_size_mb": 45.2
}
```

## 配置文件 (config/update.json)

```json
{
  "current_version": "3.0.0",
  "update_channel": "stable",
  "auto_check": true,
  "settings": {
    "check_on_startup": true,
    "download_retries": 3,
    "verify_checksum": true,
    "auto_restart": true,
    "preserve_files": [".env", "license.key", "config/settings.json"],
    "preserve_dirs": ["output", "logs", "input"]
  }
}
```

## GUI 功能

### 菜单栏
- **帮助 → 检查更新**：手动触发更新检查
- **帮助 → 关于软件**：显示版本号、授权状态、上次检查时间

### 更新对话框
```
┌──────────────────────────────────────┐
│  🎉 发现新版本                        │
│                                      │
│  当前版本：3.0.0                      │
│  最新版本：3.1.0                      │
│  发布日期：2026-06-15                  │
│                                      │
│  更新内容：                           │
│  • 优化 GPT Image 人物一致性          │
│  • 新增批量工厂模式                   │
│  • 修复 Seedance 生成问题             │
│                                      │
│  ████████████░░░░░░░░  65%           │
│  12.5 / 18.2 MB  3.2 MB/s           │
│                                      │
│     [稍后提醒]    [🚀 立即更新]        │
└──────────────────────────────────────┘
```

### 强制更新模式
当 `force_update: true` 时：
- "稍后提醒" 按钮禁用
- 显示红色警告："当前版本已停止支持，必须更新后才能继续使用"
- 用户无法跳过更新

## 文件保护

更新时**永远不会覆盖**以下文件：

| 类型 | 文件/目录 |
|------|-----------|
| API 配置 | `.env` |
| 授权 | `license.key` |
| 应用设置 | `config/settings.json` |
| 更新配置 | `config/update.json` |
| 用户数据 | `output/`, `logs/`, `input/` |

## 回滚机制

如果安装过程中出现任何异常：
1. 从 `_update_backup/` 恢复所有原始文件
2. 清理临时文件
3. 记录失败日志到 `logs/update.log`
4. 应用继续使用旧版本正常运行

## 更新日志

所有更新操作记录在 `logs/update.log`：

```
============================================================
[12:30:15] Install started: 2026-06-14T12:30:15
[12:30:15] Update package: update.zip (18.2 MB)
[12:30:16] Backup created: _update_backup/
[12:30:18] Extracted 145 files to updater/_update_extracted/
[12:30:19] Snapshot: 8 preserved files
[12:30:20] Copied 138 new files
[12:30:20] Restored 8 preserved files
[12:30:21] Restart batch script: updater/_update_apply.bat
[12:30:21] Update log written to logs/update.log
============================================================
```

## 环境变量

```bash
TIKTOK_FACTORY_UPDATE_URL=https://your-domain/version.json
TIKTOK_FACTORY_SKIP_UPDATE=false
TIKTOK_FACTORY_DEV_MODE=true     # 开发模式自动跳过更新
```

## CLI 使用

```bash
# 手动检查更新
python -m updater.update_manager --check

# 静默检查
python -m updater.update_manager --check --silent

# 跳过本次更新检查
python launcher.py --skip-update
```
