# TikTok AI Factory Pro — 更新发布流程

## 版本号规则

语义化版本：`major.minor.patch`

| 变更类型 | 版本 | 示例 |
|----------|------|------|
| Bug 修复 | patch++ | 3.0.0 → 3.0.1 |
| 新功能 | minor++ | 3.0.0 → 3.1.0 |
| 大版本/不兼容 | major++ | 3.0.0 → 4.0.0 |

## 发布步骤

### 1. 更新本地版本号

```bash
# 编辑 version.txt
echo "Version: 3.1.0" > version.txt
echo "Build: 20260615" >> version.txt
echo "Codename: TikTok AI Factory Pro" >> version.txt
```

### 2. 更新 config/update.json

```json
{
  "current_version": "3.1.0",
  ...
}
```

### 3. 打包发布包

```bash
# Windows PowerShell
Compress-Archive -Path * -DestinationPath TikTok-AI-Factory-Pro-v3.1.0.zip

# 排除不需要的目录
# zip -r TikTok-AI-Factory-Pro-v3.1.0.zip . \
#   -x "output/*" "logs/*" ".git/*" "__pycache__/*" "*.pyc" \
#   "_update_backup/*" "updater/_update_extracted/*"
```

### 4. 计算 SHA-256

```bash
# Windows
certutil -hashfile TikTok-AI-Factory-Pro-v3.1.0.zip SHA256

# 或使用 Python
python -c "from updater.download_manager import DownloadManager; print(DownloadManager.compute_sha256('TikTok-AI-Factory-Pro-v3.1.0.zip'))"
```

### 5. 上传到服务器

将 `TikTok-AI-Factory-Pro-v3.1.0.zip` 上传到你的下载服务器。

### 6. 更新 version.json

编辑服务器上的 `version.json`：

```json
{
  "latest_version": "3.1.0",
  "release_date": "2026-06-15",
  "download_url": "https://your-domain.com/releases/TikTok-AI-Factory-Pro-v3.1.0.zip",
  "force_update": false,
  "sha256": "abc123...",
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

### 7. 验证

客户端下次启动即可收到更新通知。

## 强制更新

设置 `"force_update": true` 时：
- 所有旧版本客户端启动时会被阻止
- 用户必须更新才能继续使用
- 用于：安全修复、重大 API 变更、授权策略变更

## 多 Channel 支持

| Channel | 说明 |
|---------|------|
| `stable` | 正式版（默认） |
| `beta` | 测试版（需要 `update_channel: "beta"` 配置） |

客户在 `config/update.json` 中设置 `"update_channel": "beta"` 即可接收测试版更新。

## 回滚操作（紧急）

如果新版本有严重问题：

1. 服务器 `version.json` 将 `latest_version` 改回旧版本
2. 客户端重新下载安装旧版本
3. 或：客户端从 `_update_backup/` 手动恢复
