# RUN PRODUCTION — 从0开始运行TikTok AI Video Factory

---

## 1. 环境准备

### 1.1 系统要求

- Python 3.10+
- ffmpeg (视频分析必需)
- tesseract (OCR字幕提取，可选)
- whisper (语音转文字，可选)

### 1.2 安装

```bash
# 进入项目目录
cd TikTok-AI-Factory

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows

# 安装依赖
pip install -r requirements.txt

# 安装可选依赖
pip install Pillow opencv-python           # 图像处理
pip install openai anthropic               # AI Provider SDK
pip install google-generativeai            # Gemini
pip install watchdog                       # 文件监控 (Watch Mode)
pip install openai-whisper                 # 语音转文字
```

### 1.3 配置API密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的API密钥
# 至少配置一个AI Provider:
#   OPENAI_API_KEY=sk-xxx
#   ANTHROPIC_API_KEY=sk-ant-xxx
#   DEEPSEEK_API_KEY=sk-xxx
#   GEMINI_API_KEY=xxx
```

### 1.4 检查环境

```bash
# 查看状态 — 确认所有组件就绪
python run_factory.py --status
```

---

## 2. 放入素材

### 2.1 目录结构

```
input/
├── products/            ← 放产品图片
├── reference_videos/    ← 放爆款参考视频
└── characters/          ← 放人物/人设图片
```

### 2.2 支持格式

| 类型 | 格式 | 最大大小 |
|------|------|----------|
| 产品图 | jpg, jpeg, png, webp | 20MB |
| 参考视频 | mp4, mov | 500MB / 180s |
| 人物图 | jpg, jpeg, png, webp | 20MB |

### 2.3 素材命名建议

```
产品图:    品牌_产品名_颜色.jpg
           lumiere_glow_serum_gold.jpg

人物图:    角色名_风格.jpg
           emma_natural_beauty.jpg

参考视频:  内容描述_平台.mp4
           viral_skincare_review.mp4
```

### 2.4 示例素材

`sample_input/` 目录提供了一套完整示例：

```bash
# 复制示例素材到input目录
cp sample_input/product.jpg   input/products/
cp sample_input/reference.mp4 input/reference_videos/
cp sample_input/character.jpg input/characters/
```

---

## 3. 运行

### 3.1 一键运行 (全自动)

```bash
python run_factory.py
```

系统自动执行：
1. 扫描 input/ 目录
2. 提取产品信息 → product.json
3. 分析参考视频 → viral_analysis.json
4. 提取人物特征 → character.json
5. 创建任务队列
6. 视频复制分析
7. 生成脚本 → script.md
8. 生成分镜 → storyboard.md
9. 生成图片Prompt → image_prompt.md
10. 生成Storyboard图 → storyboard.png
11. 生成Seedance Prompt → seedance.txt
12. 生成VEO3 Prompt → veo3.txt
13. 生成即梦Prompt → jimeng.txt
14. 生成云镜Prompt → yunjing.txt
15. 生成字幕 → subtitle.srt
16. 导出总结 → summary.json

### 3.2 输出位置

```
output/output001/
├── product.jpg           # 产品图副本
├── reference.mp4         # 参考视频副本
├── character.jpg         # 人物图副本
├── product.json          # 产品结构化信息
├── character.json        # 人物结构化信息
├── viral_analysis.json   # 视频分析报告
├── script.md             # 视频脚本
├── storyboard.md         # 分镜表
├── storyboard.png        # 可视化分镜图
├── image_prompt.md       # 图片生成Prompt
├── seedance.txt          # Seedance分段Prompt
├── veo3.txt              # VEO3完整Prompt
├── jimeng.txt            # 即梦Prompt
├── yunjing.txt           # 云镜Prompt
├── subtitle.srt          # 字幕文件
└── summary.json          # 任务总结
```

### 3.3 常用命令

```bash
# 查看状态
python run_factory.py --status

# 限制任务数
python run_factory.py --max-tasks 3

# 1对1配对模式 (而非笛卡尔积)
python run_factory.py --pairing one_to_one

# Watch Mode — 持续监控，放入素材自动处理
python run_factory.py --watch

# 自定义轮询间隔
python run_factory.py --watch --interval 5

# 强制执行一次扫描
python run_factory.py --force-scan

# 单任务模式 (手动指定文件)
python run_factory.py --mode single \
  --product input/products/my_product.jpg \
  --video input/reference_videos/my_video.mp4 \
  --character input/characters/my_character.jpg \
  --task-id my_custom_task
```

---

## 4. 切换AI模型

### 4.1 命令行切换

```bash
# 使用OpenAI
python run_factory.py --provider openai

# 使用Claude
python run_factory.py --provider claude

# 使用DeepSeek
python run_factory.py --provider deepseek

# 使用Gemini
python run_factory.py --provider gemini
```

### 4.2 环境变量切换 (永久)

编辑 `.env` 文件:

```bash
# 切换为OpenAI
TIKTOK_FACTORY_AI_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini

# 切换为DeepSeek
TIKTOK_FACTORY_AI_PROVIDER=deepseek
DEEPSEEK_MODEL=deepseek-chat
```

### 4.3 配置文件切换

编辑 [config/providers.json](config/providers.json):

```json
{
  "default": "openai",
  "providers": {
    "openai": {
      "model": "gpt-4o-mini",
      "temperature": 0.5
    }
  }
}
```

### 4.4 可用模型列表

| Provider | 文本模型 | 视觉模型 |
|----------|---------|---------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo | gpt-4o, gpt-4o-mini |
| Claude | claude-sonnet-4-6, claude-opus-4-8, claude-haiku-4-5 | 全部支持vision |
| DeepSeek | deepseek-chat, deepseek-reasoner | — |
| Gemini | gemini-2.0-flash, gemini-2.0-pro, gemini-2.5-pro | 全部支持vision |

---

## 5. 切换目标国家

编辑 [config/factory.json](config/factory.json) 或设置环境变量:

```bash
# 环境变量方式
export TIKTOK_FACTORY_COUNTRY=US
export TIKTOK_FACTORY_LANGUAGE=en

# 印尼市场
export TIKTOK_FACTORY_COUNTRY=ID
export TIKTOK_FACTORY_LANGUAGE=id

# 日本市场
export TIKTOK_FACTORY_COUNTRY=JP
export TIKTOK_FACTORY_LANGUAGE=ja
```

支持的13个国家:

| 代码 | 国家 | 语言 |
|------|------|------|
| US | 美国 | en |
| GB | 英国 | en |
| ID | 印尼 | id |
| BR | 巴西 | pt |
| TH | 泰国 | th |
| VN | 越南 | vi |
| PH | 菲律宾 | en |
| MX | 墨西哥 | es |
| JP | 日本 | ja |
| KR | 韩国 | ko |
| SA | 沙特 | ar |
| AE | 阿联酋 | ar |
| CN | 中国 | zh |

---

## 6. 调整视频参数

编辑 `config/factory.json`:

```json
{
  "video": {
    "duration_seconds": 15,
    "available_durations": [8, 15, 30, 60]
  },
  "output": {
    "count": 1,
    "pairing_mode": "one_to_one"
  }
}
```

或环境变量:

```bash
export TIKTOK_FACTORY_VIDEO_DURATION=30
export TIKTOK_FACTORY_OUTPUT_COUNT=3
```

---

## 7. 生产环境建议

### 7.1 Docker部署

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg tesseract-ocr
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run_factory.py", "--watch"]
```

### 7.2 定时运行 (crontab)

```bash
# 每小时运行一次
0 * * * * cd /path/to/TikTok-AI-Factory && python run_factory.py
```

### 7.3 Watch Mode 后台运行

```bash
# 使用 nohup 后台持续监控
nohup python run_factory.py --watch --interval 10 > logs/factory.log 2>&1 &

# 使用 systemd (Linux)
sudo cp factory.service /etc/systemd/system/
sudo systemctl enable factory
sudo systemctl start factory
```

### 7.4 日志查看

```bash
# 实时日志
tail -f logs/factory.log

# 查看今天运行了多少任务
cat output/factory_summary.json
```

---

## 8. 故障排查

| 问题 | 解决方案 |
|------|---------|
| `ffprobe not found` | 安装 ffmpeg: `apt install ffmpeg` 或 `brew install ffmpeg` |
| `Provider not available` | 检查 `.env` 中的 API Key 是否正确设置 |
| `No input files found` | 确认 `input/` 三个子目录中都有文件 |
| `UnicodeEncodeError on Windows` | 项目已内置 Windows GBK 编码修复，如果仍有问题运行 `chcp 65001` |
| Watch Mode 未触发 | 等待冷却时间(默认10秒)结束，或使用 `--force-scan` 强制执行 |
| 输出目录为空 | 检查日志: `cat logs/factory.log` |

---

## 9. 快速参考

```bash
# 最小化运行 (3步)
cp sample_input/* input/            # 1. 放素材
cp .env.example .env && nano .env   # 2. 配密钥
python run_factory.py --provider openai   # 3. 运行
```
