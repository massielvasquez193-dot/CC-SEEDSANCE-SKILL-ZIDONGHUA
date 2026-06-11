# 客户端使用指南 — TikTok AI Factory Pro

---

## 快速开始 (3步)

```
1. 放素材 → input/ 目录
2. 双击 → 启动工厂.bat
3. 查看 → output/ 目录
```

---

## 一、目录说明

```
项目目录/
├── input/                     ← 放素材 (你只需要操作这个目录)
│   ├── products/              放产品图片
│   ├── reference_videos/      放参考视频
│   └── characters/            放人物图片
│
├── output/                    ← 生成结果 (自动创建)
│   ├── output001/             第1个视频的所有文件
│   ├── output002/             第2个视频的所有文件
│   └── ...
│
├── start/
│   ├── 启动工厂.bat            ← 双击运行
│   └── 启动监控模式.bat         ← 持续监控模式
│
└── .env                        ← API密钥配置
```

---

## 二、素材准备

### 2.1 产品图

| 要求 | 说明 |
|------|------|
| 格式 | JPG / PNG / WebP |
| 大小 | 不超过 20MB |
| 背景 | 建议白色或干净背景 |
| 内容 | 产品主体清晰可见 |

**命名建议**: `品牌_产品名_颜色.jpg`
```
lumiere_serum_gold.jpg
```

### 2.2 参考视频

| 要求 | 说明 |
|------|------|
| 格式 | MP4 / MOV |
| 大小 | 不超过 500MB |
| 时长 | 不超过 180秒 |
| 内容 | TikTok爆款产品视频, 竖屏9:16 |

**tips**: 选择你觉得"拍得好"的TikTok视频。系统会分析它的结构、节奏和爆款元素。

### 2.3 人物图

| 要求 | 说明 |
|------|------|
| 格式 | JPG / PNG / WebP |
| 大小 | 不超过 20MB |
| 内容 | 正面照片, 自然光线 |

---

## 三、运行模式

### 模式1: 全自动生产

```bash
双击: start/启动工厂.bat
```

系统自动:
1. 扫描 input/ 目录
2. 将产品+视频+人物按顺序配对
3. 逐对生成视频
4. 结果保存到 output/output001, output002...

### 模式2: 单任务模式

双击启动后选择 `[2] 单任务模式`，使用 sample_input/ 中的示例素材。

### 模式3: 监控模式 (Watch Mode)

```bash
双击: start/启动监控模式.bat
```

系统持续监控 input/ 目录。你随时放入新素材，系统自动检测并生成。无需手动操作。

### 模式4: 桌面GUI

```bash
python launcher.py
```

打开图形界面，拖拽上传文件，点击生成。

---

## 四、输出说明

每个任务生成独立目录，包含:

```
output001/
├── master_script.md          视频脚本 (UGC真人风格)
├── voiceover.txt             口播文本 (带情绪+停顿标记)
├── voice.mp3                 真人配音 (ElevenLabs)
├── subtitle.srt              字幕文件 (时间轴精确)
├── storyboard.md + .png      分镜表 + 可视化图
├── character_reference.png   人物参考图 (GPT Image生成)
├── keyframes/                关键帧图片 (每镜头一张)
│   ├── keyframe_01.png
│   ├── keyframe_02.png
│   └── ...
├── seedance_segments/        视频生成Prompt包
│   ├── seedance_segment_01.txt
│   └── ...
├── video.mp4                 最终视频 (视频+配音+字幕)
├── summary.json              任务总览
└── ugc_score_report.json     UGC质量评分
```

---

## 五、批量生产

放入多组素材，系统自动1对1配对:

```
input/products/           input/reference_videos/     input/characters/
  product01.jpg    →        video01.mp4         →      character01.jpg   → output001
  product02.jpg    →        video02.mp4         →      character02.jpg   → output002
  product03.jpg    →        video03.mp4         →      character03.jpg   → output003
```

---

## 六、查看结果

```bash
# 打开输出目录
双击 output/ 文件夹

# 或命令行
start output/output001
```

每个 outputXXX/ 文件夹是一个完整的视频项目。

---

## 七、成本参考

| 项目 | 单视频成本 |
|------|-----------|
| GPT脚本 | ~$0.02 |
| GPT Image关键帧 (6张) | ~$0.72 |
| Seedance视频 (7段) | ~$4.80 |
| ElevenLabs配音 | ~$0.15 |
| **合计** | **~$5.69/视频** |

---

*详细技术文档见 PRODUCTION_ACCEPTANCE_REPORT.md*
