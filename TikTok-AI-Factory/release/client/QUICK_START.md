# TikTok AI Factory Pro — 快速开始

## 5 分钟上手

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 API Key
打开 `.env`，填入：
```bash
OPENAI_API_KEY=sk-你的key
ARK_API_KEY=ark-你的key
ELEVENLABS_API_KEY=el_你的key
```

### 3. 放入素材
- `input/products/` → 产品图片 (.jpg/.png/.webp)
- `input/characters/` → 人物图片 (.jpg/.png)
- `input/reference_videos/` → 参考视频 (.mp4)

### 4. 启动
```bash
python launcher.py
```

### 5. 生成视频
切换到「🎬 一键生成」→ 上传 3 个素材 → 点击「开始生成」

输出在 `output/` 目录。

---

**需要帮助？** 联系供应商获取支持。
