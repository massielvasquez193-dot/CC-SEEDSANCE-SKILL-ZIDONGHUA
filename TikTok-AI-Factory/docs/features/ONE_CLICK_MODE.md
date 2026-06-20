# TikTok AI Factory Pro — 一键生成模式

## 概述

一键生成模式是 TikTok AI Factory Pro 的最简工作流。客户无需理解脚本、分镜、提示图、Seedance、TTS 等概念——只需上传 3 个素材，点击一个按钮，即可获得成品视频。

## 界面

```
┌─────────────────────────────────────────────────┐
│  🎬 一键生成                                      │
│  上传素材 → 点击开始 → 获得视频                     │
│                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │ 📦 产品图 │ │ 👤 人物图 │ │ 🎥 参考视频   │    │
│  │ [上传]   │ │ [上传]   │ │ [上传]       │    │
│  └──────────┘ └──────────┘ └──────────────┘    │
│                                                 │
│  目标国家: [▼ 美国]  数量: [▼ 3]  风格: [▼ UGC]   │
│                                                 │
│  [        🚀 开始生成        ]  [⏹ 停止]         │
│                                                 │
│  ████████████░░░░░░░░░░░  65%                    │
│                                                 │
│  ✓GPT脚本 ✓人物分析 ●分镜 ○关键帧 ○视频 ...         │
│                                                 │
│  实时日志                                        │
│  ┌──────────────────────────────────────────┐   │
│  │ STEP 1: GPT脚本生成 ✅                     │   │
│  │ STEP 2: 人物分析 ✅                       │   │
│  │ STEP 3: 分镜生成 ● 进行中...              │   │
│  └──────────────────────────────────────────┘   │
│                                                 │
│  📂 输出目录  [打开]                             │
└─────────────────────────────────────────────────┘
```

## 生成流程

点击「开始生成」后，9 个步骤自动执行：

| 步骤 | 名称 | 输入 | 输出 |
|------|------|------|------|
| 1 | GPT 脚本生成 | 产品图 + 参考视频 | `master_script.md` |
| 2 | 人物分析 | 人物图 | `character.json` |
| 3 | 分镜生成 | 脚本 + 人物数据 | `storyboard.md` |
| 4 | 关键帧生成 | 分镜表 | `keyframes/keyframe_NN.png` |
| 5 | Seedance Prompt | 关键帧 + 分镜 | `seedance_segments/` |
| 6 | 视频生成 | Seedance API | `segment_NN.mp4` |
| 7 | ElevenLabs 口播 | 口播文本 | `voice.mp3` |
| 8 | 字幕生成 | 字幕文本 | `subtitle.srt` |
| 9 | FFmpeg 合成 | 视频 + 音频 + 字幕 | `video_final.mp4` |

## 视频风格

| 风格 | 特点 | 适用场景 |
|------|------|----------|
| **TikTok UGC** | 真实创作者、手机自拍、自然光 | 通用产品推广 |
| **Beauty Review** | 美妆测评、细节展示、专家感 | 护肤品、化妆品 |
| **Problem Solution** | 痛点 → 解决方案、快速转场 | 解决问题型产品 |
| **Before After** | 前后对比、视觉证明 | 效果型产品 |
| **Testimonial** | 用户证言、情感连接 | 信任建立 |
| **POV Story** | 第一人称、日常记录 | 生活方式产品 |

## 目标国家

| 国家 | 语言 | 口音 |
|------|------|------|
| 美国 | English | American |
| 英国 | English | British |
| 马来西亚 | Malay | Malay |
| 印尼 | Indonesian | Indonesian |
| 德国 | German | German |
| 法国 | French | French |
| 西班牙 | Spanish | Spanish |

## 输出目录结构

```
output/oneclick_20260614_120000/
├── product.jpg                # 产品原图
├── character.jpg              # 人物原图
├── reference.mp4              # 参考视频
├── master_script.md           # 主脚本
├── character.json             # 人物圣经
├── storyboard.md              # 分镜表
├── voiceover.txt              # 口播文本
├── voice.mp3                  # TTS 语音
├── subtitle.srt               # 字幕
├── keyframes/                 # 关键帧图片
│   ├── keyframe_01.png
│   ├── keyframe_02.png
│   └── ...
├── seedance_segments/         # Seedance 分段 Prompt
│   ├── seedance_segment_01.txt
│   └── ...
├── segment_01.mp4             # 原始视频段
├── segment_02.mp4
├── video_final.mp4            # 最终合成视频 ✨
└── oneclick_summary.json      # 生成总结
```

## 文件清单

```
app/gui/
├── one_click_tab.py           # 一键生成 GUI 标签页（~450 行）
└── one_click_controller.py   # 流水线编排控制器（~540 行）

ONE_CLICK_MODE.md              # 本文档
```

## 使用方式

1. 启动 GUI：`python launcher.py`
2. 切换到「🎬 一键生成」标签页
3. 上传产品图片、人物图片、参考视频
4. 选择目标国家、视频数量、视频风格
5. 点击「🚀 开始生成」
6. 等待完成，点击「📂 打开输出目录」

## 技术说明

- 所有步骤都在后台线程执行，UI 不阻塞
- 用户可以随时点击「停止」取消生成
- 如果某个步骤失败（如 API 不可用），会跳过该步骤继续执行
- 开发模式下使用模板脚本和 PIL 占位图，不依赖外部 API
