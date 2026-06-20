# TikTok AI Factory Pro v1.0.0

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
