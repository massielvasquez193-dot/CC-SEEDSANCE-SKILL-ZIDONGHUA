# TikTok AI Factory Pro — 客户操作手册

> 全自动TikTok视频生产工厂。无需懂代码，3步生成真人级UGC视频。

---

## 快速开始 (3步)

### 第1步: 安装

```
双击: install/01_安装依赖.bat
双击: install/02_检测环境.bat
```

### 第2步: 配置API密钥

复制 `.env.example` 为 `.env`，填入你的API密钥:

```ini
OPENAI_API_KEY=sk-xxx           # GPT-5.5 + GPT Image (必需)
ELEVENLABS_API_KEY=xxx          # 真人配音 (可选)
ARK_API_KEY=ark-xxx             # Seedance视频生成 (可选)
```

### 第3步: 放素材 + 启动

```
1. 将产品图片放入  input/products/
2. 将参考视频放入  input/reference_videos/
3. 将人物图片放入  input/characters/
4. 双击: start/启动工厂.bat
```

---

## 目录说明

```
TikTok-AI-Factory-Pro/
├── start/                     ← 启动脚本
│   ├── 启动工厂.bat            一键运行
│   └── 启动监控模式.bat        持续监控自动处理
├── install/                   ← 安装脚本
│   ├── 01_安装依赖.bat
│   └── 02_检测环境.bat
├── input/                     ← 放素材的目录
│   ├── products/              产品图片 (.jpg .png .webp)
│   ├── reference_videos/      参考视频 (.mp4 .mov)
│   └── characters/            人物图片 (.jpg .png .webp)
├── output/                    ← 生成结果输出
│   ├── output001/             每个任务一个独立目录
│   │   ├── master_script.md   视频脚本
│   │   ├── voiceover.txt      口播文本
│   │   ├── voice.mp3          口播音轨
│   │   ├── subtitle.srt       字幕文件
│   │   ├── storyboard.png     分镜图
│   │   ├── character_reference.png  人物参考图
│   │   ├── keyframes/         关键帧图片
│   │   └── video.mp4          最终视频
│   └── factory_dashboard.json 任务状态总览
├── config/                    ← 配置文件
├── .env.example               ← API密钥模板
├── LICENSE.txt
└── version.txt
```

---

## 素材要求

| 类型 | 格式 | 大小限制 | 建议 |
|------|------|---------|------|
| 产品图 | jpg/png/webp | 20MB | 白色/干净背景，产品居中 |
| 参考视频 | mp4/mov | 500MB, ≤180s | TikTok爆款视频，竖屏9:16 |
| 人物图 | jpg/png/webp | 20MB | 正面，自然光线，真人照片 |

---

## 输出说明

每个任务生成独立目录 `output/outputXXX/`，包含:

| 文件 | 说明 |
|------|------|
| `master_script.md` | 6段式UGC脚本 (Hook→Problem→Agitate→Solution→Result→CTA) |
| `voiceover.txt` | 口播文本，带情绪和停顿标记 |
| `voice.mp3` | ElevenLabs真人配音 (需API Key) |
| `subtitle.srt` | 时间轴精确字幕 |
| `storyboard.png` | 可视化分镜图 |
| `character_reference.png` | GPT Image生成的真人参考图 |
| `keyframes/keyframe_01~06.png` | GPT Image生成的每镜头关键帧 |
| `seedance_segments/` | Seedance视频生成Prompt包 |
| `video.mp4` | 最终合成视频 (视频+配音+字幕) |
| `summary.json` | 任务总览 |
| `ugc_score_report.json` | UGC质量评分 |

---

## 常见问题

**Q: 需要什么API密钥？**
最少需要 `OPENAI_API_KEY` (GPT脚本+GPT Image关键帧)。完整效果需 `ELEVENLABS_API_KEY` (配音) 和 `ARK_API_KEY` (Seedance视频)。

**Q: 生成一个视频要多久？**
约30-40分钟 (GPT Image关键帧~2分钟 + Seedance视频~30分钟 + 配音+合成~2分钟)。

**Q: 成本多少？**
约$5.91/视频 (Seedance $4.80 + GPT Image $0.96 + ElevenLabs $0.15)。

**Q: 支持什么语言？**
脚本支持中文/英文。口播支持ElevenLabs的29种语言。字幕支持中英文。

**Q: 可以批量生成吗？**
可以。在 `input/` 放入多组素材 (产品+视频+人物)，系统自动1对1配对批量生成。

---

## 技术支持

- 文档: `PRODUCTION_ACCEPTANCE_REPORT.md`
- 仓库: https://github.com/massielvasquez193-dot/CC-SEEDSANCE-SKILL-ZIDONGHUA
