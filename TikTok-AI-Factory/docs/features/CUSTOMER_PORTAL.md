# TikTok AI Factory Pro — Customer Portal

## 概述

客户后台仪表盘，无需查看代码即可了解授权状态、使用统计、成本分析、视频记录和系统健康状态。

## 7 大模块

### 🔑 授权信息
- License Key / 机器码
- 到期时间 / 剩余天数
- 状态指示（有效/即将到期/已过期）
- 续费 / 联系客服按钮

### 📊 使用统计
- 今日生成视频数
- 本周生成视频数
- 本月生成视频数
- 累计生成视频数

### 💰 成本统计
- OpenAI 文本成本
- GPT Image 图像成本
- ElevenLabs TTS 成本
- Seedance 视频成本
- 总成本 / 单视频平均成本
- 数据来源：`output/cost_dashboard.json`

### 📋 任务统计
- 成功任务数 / 失败任务数
- 成功率（进度条可视化）
- 数据来源：`output/batch_log.json` + `output/*/summary.json`

### 🎬 视频生成记录
- 最近 100 条视频
- 字段：时间、产品、人物、参考视频、时长、状态
- 操作：打开目录 📂 / 播放视频 ▶
- 导出 CSV

### 🔄 更新中心
- 当前版本 / 最新版本
- 上次检查时间
- 检查更新按钮
- 更新日志显示

### 🖥️ 系统状态
- Python / FFmpeg / OpenAI / ARK / ElevenLabs / License
- 实时状态：✓ 正常 / ✗ 异常 / — 未配置

## 数据来源

| 数据 | 来源 |
|------|------|
| 授权信息 | `license/license_manager.py` |
| 使用统计 | `output/` 目录扫描 |
| 成本统计 | `app/gui/cost_tracker.py` → `output/cost_dashboard.json` |
| 视频记录 | `app/gui/video_history.py` 扫描 output 目录 |
| 系统状态 | `.env` + 系统检测 |

## 文件清单

```
app/gui/
├── customer_portal.py     # 客户后台主界面（~500 行）
├── cost_tracker.py        # 成本统计引擎（~200 行）
└── video_history.py       # 视频记录扫描器（~160 行）

CUSTOMER_PORTAL.md         # 本文档
CUSTOMER_DASHBOARD_GUIDE.md # 用户使用指南
```

## 导出功能

- **CSV 导出**：视频历史记录导出为 CSV

## 自动刷新

每次切换到「👤 客户中心」标签页时自动刷新所有数据。
