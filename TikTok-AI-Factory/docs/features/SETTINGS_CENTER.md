# TikTok AI Factory Pro — 设置中心

## 概述

设置中心让用户无需编辑 `.env` 文件，全部 API 配置通过 GUI 完成。

## 功能

### 🔑 API Key 配置

| Key | 用途 | 测试方式 |
|-----|------|----------|
| OpenAI API Key | GPT-4o 文本 + DALL-E 3 图像 | 调用 `GET /v1/models` |
| ElevenLabs API Key | TTS 语音合成 | 调用 `GET /v1/voices` |
| 火山引擎 ARK API Key | Seedance 视频生成 | 调用 `POST /v3/chat/completions` |
| Claude API Key | 替代 OpenAI 文本生成 | 调用 `GET /v1/models` |
| DeepSeek API Key | DeepSeek 文本生成 | 调用 `GET /v1/models` |

每个 Key 输入框支持：
- **密码隐藏**：默认隐藏 Key 内容
- **显示/隐藏**：点击 👁 按钮切换
- **测试连接**：点击「测试连接」按钮，实时验证 API Key 有效性
- **状态显示**：✓ 已连接（绿色）/ ✗ 连接失败（红色）

### 🎛️ 应用设置

| 设置项 | 选项 | 保存位置 |
|--------|------|----------|
| 视频模型 | Seedance / Jimeng / Runway / Veo3 | `settings.json` |
| 国家 / 语言 | EN(US) / EN(UK) / Malay / Indonesian / Spanish / German / French | `settings.json` + `.env` |
| 默认人物 | UGC Female / UGC Male / Beauty Creator / Skincare Expert / Lifestyle Creator | `settings.json` + `.env` |
| AI 文本模型 | claude / openai / deepseek / gemini | `.env` |
| 更新服务器 | 自定义 URL | `.env` |

### 🔍 环境检测

点击「环境检测」按钮，自动检查：

```
=============================================
  TikTok AI Factory Pro — 环境检测报告
=============================================
  检测时间: 2026-06-14T12:00:00
  Python:   3.12.9
  平台:     win32

  [系统组件]
  ✓ Python 3.12.9 正常
  ✓ FFmpeg 正常
  ✓ Pillow 正常
  ✓ License 有效 · 364 天剩余

  [API 连接]
  ✗ OpenAI 未配置
  ✓ ElevenLabs 已连接 · 47 个语音可用
  ✓ ARK (火山引擎) 已连接
  ✗ Claude 未配置
  ✗ DeepSeek 未配置

  通过: 6  失败: 0  未配置: 3
=============================================
  环境状态: ⚠️ 基本可用，建议配置缺失的 API Key。
```

## 数据流

```
GUI 输入
  │
  ├─→ 测试连接: api_validator.py → HTTP 请求 → 实时显示结果
  │
  ├─→ 保存: settings_manager.py
  │       ├─→ .env          (API keys + 简单键值)
  │       └─→ settings.json (结构化应用配置)
  │
  └─→ 启动时: settings_tab.py.load_settings()
          ├─→ 读取 .env → 填充 Key 输入框
          └─→ 读取 settings.json → 填充下拉菜单
```

## 文件清单

```
config/
├── settings_manager.py       # 统一配置读写（.env + settings.json）
└── api_validator.py          # API 连接测试 + 环境检测

app/gui/
└── settings_tab.py           # 设置中心 GUI 标签页（~470 行）

SETTINGS_CENTER.md            # 本文档
```

## 技术说明

### settings_manager.py

`SettingsManager` 类提供：
- `read_env()` / `write_env()` — 操作 `.env` 文件
- `read_settings_json()` / `write_settings_json()` — 操作 `settings.json`
- `get_api_key()` / `set_api_key()` — 单个 Key 读写
- `get_setting()` / `set_setting()` — 点路径读写（如 `video.provider`）
- `get_all_api_status()` — 获取所有 Key 的配置状态（含掩码值）
- `save_all_settings()` — 批量保存

关键特性：
- 保存时保留 `.env` 中的注释和结构
- 自动同步 `os.environ` 以便当前进程生效
- 支持深度合并 `settings.json`

### api_validator.py

`APIValidator` 类提供：
- `test_openai(api_key)` — 测试 OpenAI 连接
- `test_elevenlabs(api_key)` — 测试 ElevenLabs 连接
- `test_ark(api_key)` — 测试火山引擎 ARK 连接
- `test_claude(api_key)` — 测试 Claude 连接
- `test_deepseek(api_key)` — 测试 DeepSeek 连接
- `check_environment()` — 完整环境检测
- `format_env_report()` — 格式化环境报告

所有测试都是纯 HTTP 请求，不依赖项目内部 SDK。
