# TikTok AI Factory Pro — 快速开始

## 5 分钟上手

### 第 1 步：安装依赖
```bash
pip install -r requirements.txt
```

### 第 2 步：配置 API Key
打开 `.env` 文件，填入你的 API 密钥：
```bash
OPENAI_API_KEY=sk-your-openai-key
ARK_API_KEY=ark-your-ark-key
ELEVENLABS_API_KEY=el-your-elevenlabs-key
```

### 第 3 步：放入素材
将文件放入 `input/` 目录：
- `input/products/` → 产品图片 (.jpg/.png/.webp)
- `input/characters/` → 人物图片 (.jpg/.png)
- `input/reference_videos/` → 参考视频 (.mp4)

### 第 4 步：启动
```bash
# GUI 模式 (推荐)
python launcher.py

# CLI 模式
python launcher.py --cli

# 全自动模式
python run_factory.py --max-tasks 1
```

### 第 5 步：获取视频
- **一键生成**：上传 3 个素材 → 点击「开始生成」→ 获得视频
- **批量工厂**：放入目录 → 自动扫描 → 点击「开始批量生成」
- 输出在 `output/` 目录

## 5 个标签页一览

| 标签页 | 用途 |
|--------|------|
| 🎬 一键生成 | 上传 3 个素材，一键出片 |
| 🏭 批量工厂 | 目录级批量生产 |
| 🛠️ 手动模式 | 分步控制每个环节 |
| ⚙️ 设置中心 | 配置 API Key 和应用设置 |
| 👤 客户中心 | 查看授权/成本/视频/系统状态 |

## 常见问题

**Q: 没有 API Key 能运行吗？**
A: 可以。开发模式下使用模板生成和占位图，功能完整但质量受限。

**Q: 支持什么格式？**
A: 图片: JPG/PNG/WEBP。视频: MP4/MOV。输出: MP4。

**Q: 如何获得授权？**
A: 联系供应商获取 `license.key` 或 License Server 地址。

---

[完整用户指南 →](CLIENT_USER_GUIDE.md)
[常见问题 →](FAQ.md)
