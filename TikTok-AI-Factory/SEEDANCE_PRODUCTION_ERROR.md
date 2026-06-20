# SEEDANCE PRODUCTION ERROR

**运行时间**: 2026-06-10 15:15:54
**任务ID**: task001
**Provider**: Seedance (`doubao-seedance-2-0-260128`)
**API**: 火山引擎 ARK

---

## 1. 流水线执行状态

| 步骤 | 名称 | 状态 |
|------|------|:---:|
| 1 | 扫描输入文件 | ✅ |
| 2 | 提取产品信息 | ✅ |
| 3 | 分析参考视频 | ✅ |
| 4 | 提取人物特征 | ✅ |
| 5 | 建立任务队列 | ✅ (1 task) |
| 6 | 视频复制分析 | ✅ |
| 7 | 生成脚本 | ✅ |
| 8 | 生成分镜 | ✅ |
| 9 | 生成图片Prompt | ✅ |
| 10 | 生成Storyboard图 | ✅ |
| 11 | 生成Seedance Prompt | ✅ |
| **11.5** | **Seedance视频生成** | **❌ FAILED** |
| 12-16 | (未执行) | ⏸️ |

---

## 2. 请求详情

```
Method:  POST
URL:     https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
Headers:
  Authorization: Bearer ark-c8***c0d5
  Content-Type: application/json
```

### Payload (镜头1/7)

```json
{
  "model": "doubao-seedance-2-0-260128",
  "content": [
    {
      "type": "text",
      "text": "### 镜头 1 (0.0s-1.5s)\n| 项目 | 内容 |\n|------|------|\n| 景别 | 特写 |\n| 运镜 | 静态→快速推 |\n| 时长 | 1.5秒 |\n| 画面描述 | Hook开场：product产品特写快速出现，色包装惊艳亮相 |\n| 人物动作 | character自然展示产品，表情亲切 / 邻家 |\n| 产品位置 | 画面中央 |\n| 字幕 | 🔥 发现宝藏product！ |\n| 口播 | 天呐！这个product也太好用了吧！ |\n| 音效 | TikTok热门BGM卡点重拍 |\n| 转场 | 快切 |"
    }
  ],
  "parameters": {
    "duration": 5,
    "resolution": "1080p",
    "fps": 24,
    "generate_audio": true,
    "negative_prompt": "\nblurry, distorted face, extra limbs, deformed hands, bad anatomy, watermark, text overlay, low quality, grainy, overexposed, underexposed, harsh shadows, cluttered background, logo, brand name, unrealistic colors"
  }
}
```

---

## 3. 错误信息

```
HTTP Status:  400 Bad Request
URL:          https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
Error Type:   requests.exceptions.HTTPError
Message:      400 Client Error: Bad Request
```

**完整异常栈**:
```
File "app/pipeline.py", line 265, in _process_task
  seedance_video_result = self._step_seedance_video(task)
File "app/pipeline.py", line 372, in _step_seedance_video
  result = seedance.generate_from_seedance_txt(...)
File "providers/seedance_provider.py", line 104, in generate_from_seedance_txt
  result = self._call_ark_api(seg, width, height, fps, **kwargs)
File "providers/seedance_provider.py", line 166, in _call_ark_api
  resp.raise_for_status()    ← HTTP 400
```

---

## 4. 根因分析

### 数据流追踪

```
seedance_generator.generate()
  ↓ 输出 AI 系统提示词 + 分镜表 (Markdown)
seedance.txt (= 完整AI prompt + 嵌入的Markdown分镜表)
  ↓ _parse_seedance_txt() 正则匹配 "### 镜头 N"
解析出 7 个 segment
  ↓ 每个 segment 的 positive_prompt = Markdown 表格文本
_call_ark_api() POST 到 ARK API
  ↓ content[0].text = "| 项目 | 内容 | ... | 景别 | 特写 | ..."  ← 表格文本
ARK API 无法解析 Markdown 表格 → HTTP 400
```

### 格式不匹配

| 层级 | 期望格式 | 实际格式 |
|------|---------|---------|
| `_parse_seedance_txt` | `### 镜头 N\n[正面Prompt]\nCamera movement: ...` | `### 镜头 N (0.0s-1.5s)\n\| 项目 \| 内容 \|` |
| `_call_ark_api` content.text | 视频描述文本 ("A rose blooming...") | Markdown 表格 ("\| 景别 \| 特写 \|") |
| ARK API | 自然语言视频描述 | ❌ 收到 Markdown 表格语法 |

### 已验证对比

**成功的请求** (手动测试 — HTTP 200):
```json
{
  "content": [{
    "type": "text",
    "text": "A single rose blooming in soft morning light, 5 seconds, cinematic"
  }]
}
```

**失败的请求** (Factory 流水线 — HTTP 400):
```json
{
  "content": [{
    "type": "text",
    "text": "### 镜头 1 (0.0s-1.5s)\n| 项目 | 内容 |\n|------|------|\n| 景别 | 特写 |..."
  }]
}
```

---

## 5. 修复方案

`agents/seedance_generator.py` 输出的 `seedance.txt` 格式与 `providers/seedance_provider.py` 的 `_parse_seedance_txt()` 解析器不匹配。

需要对齐两者:
1. **方案A**: 修改 `seedance_generator` 输出纯 `[正面Prompt]` / `[负面Prompt]` 格式（不含系统提示词和Markdown表格）
2. **方案B**: 修改 `_parse_seedance_txt()` 能同时解析 Markdown 分镜表和 `[正面Prompt]` 格式
3. **方案C**: 流水线步骤11直接传 `video_analysis` 数据给 Provider，跳过 seedance.txt 文本解析

---

## 6. 输出验证

| 文件 | 存在 | 内容 |
|------|:---:|------|
| `output/output001/product.json` | ✅ | 产品结构化信息 |
| `output/output001/character.json` | ✅ | 人物特征 |
| `output/output001/viral_analysis.json` | ✅ | 视频分析报告 |
| `output/output001/script.md` | ✅ | 视频脚本 |
| `output/output001/storyboard.md` | ✅ | 分镜表 |
| `output/output001/seedance.txt` | ✅ | Seedance Prompt (格式问题) |
| `output/output001/video.mp4` | ❌ | **未生成 — 流程在第11.5步失败** |
