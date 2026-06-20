# Updater 目录审计报告

## 审计范围

`release/client/updater/` — 57 KB, 5 个文件, 1,218 行

---

## 逐文件分析

### 1. `__init__.py`
- **行数:** 20
- **用途:** Python 包标记，统一导出 7 个公共符号
- **导出:** `VersionChecker`, `UpdateCheckResult`, `VersionInfo`, `DownloadManager`, `UpdateInstaller`, `UpdateManager`, `check_for_updates`
- **分类:** ✅ 客户端 — 包定义
- **判定:** **保留**

### 2. `version_checker.py`
- **行数:** 249
- **用途:** 客户端版本检查引擎
  - `get_local_version()` — 读取本地 `version.txt`
  - `fetch_remote_version()` — GET 远程 `version.json`
  - `parse_semver()` / `is_newer()` — 语义版本比较
  - `check()` — 完整更新检查，返回 `UpdateCheckResult`
- **依赖:** `requests` (HTTP), `pathlib` (文件读取)
- **分类:** ✅ 客户端 — 检查更新
- **判定:** **保留**

### 3. `download_manager.py`
- **行数:** 180
- **用途:** 客户端下载引擎
  - `download()` — 流式下载 + 3 次自动重试 + 进度回调 + SHA256 校验
  - `_verify_sha256()` — 校验下载文件完整性（客户端使用）
  - `compute_sha256()` ⚠️ — **静态方法，用于服务端计算发布包的 SHA256 哈希值**
- **依赖:** `requests` (HTTP), `hashlib` (SHA256)
- **分类:** ✅ 客户端 — 下载更新（含 1 个服务端工具方法）
- **判定:** **保留**（删除 `compute_sha256` 方法）

> ⚠️ `compute_sha256()` 是发布流程使用的工具方法，用于在构建 release ZIP 后计算 SHA256 值填入 `version.json`。客户端下载时只使用 `_verify_sha256()`。建议将此方法移至 `tools/` 目录或保留但标记为构建工具。

### 4. `update_installer.py`
- **行数:** 304
- **用途:** 客户端安全安装引擎
  - `install()` — 解压 → 备份 → 快照受保护文件 → 覆盖 → 恢复 → 回滚
  - `_create_backup()` — 安装前完整备份
  - `_rollback()` — 安装失败自动回滚
  - `_snapshot_preserved_files()` / `_restore_preserved_files()` — `.env`/`license.key`/`config/` 等保护
  - `_restart_windows()` — Windows 批处理脚本自替换重启
  - `_restart_unix()` — Unix `os.execv()` 重启
  - `_write_update_log()` — 记录 `logs/update.log`
- **依赖:** `zipfile`, `shutil`, `subprocess`, `sys`
- **分类:** ✅ 客户端 — 自动安装
- **判定:** **保留**

### 5. `update_manager.py`
- **行数:** 465
- **用途:** 客户端更新编排器
  - `check_for_updates()` — 启动入口（`launcher.py` 调用）
  - `prompt_and_update()` — 完整更新流程：检查 → 弹窗 → 下载 → 安装 → 重启
  - `_try_pyside6_dialog()` — PySide6 GUI 更新对话框（含进度条、release notes）
  - `_try_tkinter_dialog()` — tkinter 回退对话框
  - `_cli_prompt()` — 纯命令行提示
  - `_execute_update()` — 协调 download_manager + update_installer
  - `__main__` 块 — CLI 工具：`python -m updater.update_manager --check`
- **依赖:** PySide6 (可选), tkinter (可选), requests
- **分类:** ✅ 客户端 — 检查更新 + 提示 + 下载 + 安装
- **判定:** **保留**

---

## 分类汇总

| 文件 | 行数 | 分类 | 判定 |
|------|------|------|:--:|
| `__init__.py` | 20 | 客户端 — 包定义 | ✅ 保留 |
| `version_checker.py` | 249 | 客户端 — 检查更新 | ✅ 保留 |
| `download_manager.py` | 180 | 客户端 — 下载更新 | ✅ 保留* |
| `update_installer.py` | 304 | 客户端 — 自动安装 | ✅ 保留 |
| `update_manager.py` | 465 | 客户端 — 编排器 + GUI | ✅ 保留 |

\* `compute_sha256()` 方法属于服务端构建工具，非客户端功能。

---

## 功能矩阵

| 功能 | 实现文件 | 客户端需要? |
|------|----------|:--:|
| 读取本地版本 | `version_checker.get_local_version()` | ✅ |
| 获取远程版本 | `version_checker.fetch_remote_version()` | ✅ |
| 版本号比较 | `version_checker.is_newer()` | ✅ |
| 下载安装包 | `download_manager.download()` | ✅ |
| 下载进度回调 | `download_manager.download(progress_callback=...)` | ✅ |
| SHA256 校验下载 | `download_manager._verify_sha256()` | ✅ |
| SHA256 计算签名 | `download_manager.compute_sha256()` | ❌ 服务端 |
| 安全安装 | `update_installer.install()` | ✅ |
| 保护用户文件 | `update_installer._snapshot_preserved_files()` | ✅ |
| 安装失败回滚 | `update_installer._rollback()` | ✅ |
| Windows 自替换重启 | `update_installer._restart_windows()` | ✅ |
| 记录更新日志 | `update_installer._write_update_log()` | ✅ |
| GUI 更新对话框 | `update_manager._try_pyside6_dialog()` | ✅ |
| 强制更新 block | `update_manager._show_dialog()` force_update=true | ✅ |
| Release notes 显示 | `update_manager._try_pyside6_dialog()` | ✅ |
| CLI 更新检查 | `update_manager.__main__` | ✅ (调试用) |
| 一键完整更新流程 | `update_manager.prompt_and_update()` | ✅ |

---

## 未发现的"应删除"内容

审计确认此目录中**不存在**以下类型的文件：

| 检查项 | 结果 |
|--------|------|
| 发布工具 (build/release/pack) | ❌ 不存在 |
| 签名工具 (sign/cert/keygen) | ❌ 不存在（仅 `compute_sha256` 算签名） |
| 管理员工具 (admin/manage dashboard) | ❌ 不存在 |
| 服务端代码 (server-side only) | ❌ 不存在 |
| 测试文件 (test_*) | ❌ 不存在 |

---

## 最终判定

### ✅ 全部 5 个文件保留

`updater/` 目录中的所有文件都是**客户端运行时必需的**：
- `version_checker.py` — 检查更新
- `download_manager.py` — 下载更新
- `update_installer.py` — 自动安装
- `update_manager.py` — 编排以上三者 + GUI 对话框
- `__init__.py` — 包定义

### 建议微型优化

`download_manager.py:174` 中的 `compute_sha256()` 静态方法是**唯一**属于服务端发布流程的方法。客户下载更新时调用的是 `_verify_sha256()`（验证），不需要计算签名。

**选项 A（推荐）:** 保留不动 — 方法只有 7 行，不影响客户端运行，且方便维护时使用。

**选项 B:** 提取到 `tools/release_builder.py` 中，从客户端包删除。但影响很小（7 行代码，约 200 字节）。

### 操作记录

| 操作 | 文件 | 说明 |
|------|------|------|
| 无需操作 | 全部 5 个 | 均为客户端必须，全部保留 |

---

*审计时间: 2026-06-14*
*审计范围: release/client/updater/*
*结论: 无需删除任何文件*
