# TikTok AI Factory Pro — Case Library Report

## 概述

标准案例库系统，包含 3 个 K-Beauty 护肤品牌完整案例。每个案例包含 10 项完整资产，可直接用于演示、培训或作为客户参考模板。

## 案例库结构

```
case_library/
├── case_index.json          # 案例索引 (自动更新)
│
├── Medicube/                # 16 项资产
│   ├── 01_PRODUCT_Medicube.png
│   ├── 02_CHARACTER_Medicube.png
│   ├── 03_SCRIPT_Medicube.md
│   ├── 04_CHARACTER_SETTING_Medicube.json
│   ├── 05_KEYFRAMES/        (5 PNGs + index)
│   ├── 06_STORYBOARD_Medicube.png
│   ├── 07_VOICEOVER_Medicube.md
│   ├── 08_SUBTITLES_Medicube.srt
│   ├── 09_VIDEO_Medicube.mp4
│   └── 10_PERFORMANCE_REPORT_Medicube.md
│
├── Anua/                    # 16 项资产
│   └── (同上结构)
│
└── COSRX/                   # 16 项资产
    └── (同上结构)
```

## 3 个品牌案例

### 1. Medicube — Deep Vita C Pad

| 属性 | 值 |
|------|-----|
| 品牌 | Medicube (韩国医美级护肤) |
| 产品 | Deep Vita C Pad (维生素C棉片) |
| 人物 | Jisoo — 22-28岁，清纯邻家 |
| 风格 | TikTok UGC |
| 角度 | Vitamin C before/after transformation |
| UGC 评分 | 42/50 (B+) |

### 2. Anua — Heartleaf 77% Soothing Toner

| 属性 | 值 |
|------|-----|
| 品牌 | Anua (韩国天然护肤) |
| 产品 | Heartleaf 77% Soothing Toner (鱼腥草舒缓爽肤水) |
| 人物 | Hana — 20-26岁，温柔护肤达人 |
| 风格 | Beauty Review |
| 角度 | Redness relief — sensitive skin savior |
| UGC 评分 | 42/50 (B+) |

### 3. COSRX — Advanced Snail 96 Mucin Power Essence

| 属性 | 值 |
|------|-----|
| 品牌 | COSRX (韩国功效护肤) |
| 产品 | Advanced Snail 96 Mucin Power Essence (蜗牛粘液精华) |
| 人物 | Yuna — 25-32岁，成熟真实体验分享 |
| 风格 | Testimonial |
| 角度 | Snail mucin transformation — TikTok viral |
| UGC 评分 | 42/50 (B+) |

## 10 项资产说明

| # | 资产 | 格式 | 说明 |
|---|------|------|------|
| 01 | 产品图 | PNG 1080×1080 | 品牌产品卡片，含成分/价格/包装 |
| 02 | 人物图 | PNG 1200×800 | 人物一致性档案，3 个姿态框 |
| 03 | GPT 脚本 | Markdown | 5 段式完整脚本 (Hook→CTA) |
| 04 | 人物设定 | JSON | Character Canon — 锁定所有外观参数 |
| 05 | 关键帧 | 5×PNG 1080×1920 | 每镜头一张风格化关键帧 |
| 06 | Storyboard | PNG 1600×900 | 5 面板可视化分镜表 |
| 07 | 口播脚本 | Markdown | 带时间轴的 TTS 口播 |
| 08 | 字幕 | SRT | 8 条 SRT 字幕 |
| 09 | 成品视频 | MP4 1080×1920 | 30 秒演示视频 |
| 10 | 性能报告 | Markdown | 完整性能分析 + 成本估算 |

## GUI 案例浏览器

主界面新增「📚 案例库」标签页：

- **左侧**: 品牌列表 (Medicube / Anua / COSRX)
- **右侧**: 10 项资产卡片预览
- **查看**: 点击「查看」按钮打开图片/视频/脚本
- **一键复制**: 导出完整配置到 JSON

## 生成与使用

```bash
# 生成所有案例
python tools/case_generator.py

# 生成结果
# case_library/ — 3 品牌 × 10 资产 = 30+ 文件
```

## 扩展方式

添加新品牌案例：

1. 编辑 `tools/case_generator.py` 中的 `CASES` 字典
2. 添加品牌定义（产品、人物、风格、角度）
3. 运行 `python tools/case_generator.py`
4. 重启 GUI 即可在案例库中看到新品牌

---

*生成时间: 2026-06-14*
*工具: tools/case_generator.py + app/gui/case_browser.py*
