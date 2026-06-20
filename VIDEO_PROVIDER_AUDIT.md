# VIDEO PROVIDER AUDIT — Seedance & 即梦 (Jimeng)

**审计日期**: 2026-06-10
**审计目标**: 验证Seedance Provider和即梦Provider是否能真实调用API
**审计方法**: DNS解析验证 + 代码路径追踪 + HTTP连通性测试

---

## 1. 执行摘要

| 发现 | Seedance | Jimeng |
|------|:---:|:---:|
| API Endpoint 真实存在 | ❌ | ❌ |
| DNS可解析 | ❌ NXDOMAIN | ❌ NXDOMAIN |
| HTTP可连通 | ❌ 000 | ❌ NXDOMAIN |
| 存在Mock数据 | ✅ 3个mock方法 | ✅ 3个mock方法 |
| 存在占位视频生成 | ✅ ffmpeg占位 | ✅ ffmpeg占位 |
| **能真实调用API** | **❌ 不能** | **❌ 不能** |

**结论**: 两个Provider都是**伪接口**。API Endpoint不存在于公网DNS，所有API调用都会触发exception → mock fallback → 占位视频。

---

## 2. Seedance Provider

### 2.1 Endpoint验证

```
API_BASE = "https://api.seedance.ai/v1"
```

| 测试 | 结果 |
|------|------|
| DNS解析 | ❌ **NXDOMAIN** — `api.seedance.ai` 域名不存在 |
| HTTP连通 | ❌ HTTP 000 — 无法建立连接 |
| 实际归属 | `seedance.cn` → `overdue.aliyun.com` (域名已过期) |

### 2.2 完整请求结构

#### POST — 提交生成任务
```
URL:    https://api.seedance.ai/v1/generate   ← 虚假URL
Method: POST
Headers:
  Authorization: Bearer {self.api_key}
  Content-Type: application/json
Payload:
  {
    "mode": "text_to_video" | "image_to_video",
    "prompt": "{positive_prompt}",
    "negative_prompt": "{negative_prompt}",
    "duration": 2.1,
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "motion_scale": 0.5,
    "seed": -1,
    "reference_image": "data:image/jpeg;base64,..."   // 仅image_to_video模式
  }
```

#### GET — 查询任务状态
```
URL:    https://api.seedance.ai/v1/task/{task_id}    ← 虚假URL
Method: GET
Headers:
  Authorization: Bearer {self.api_key}
Response (期望):
  {
    "status": "completed" | "processing" | "failed",
    "video_url": "https://...",
    "progress": 0-100
  }
```

### 2.3 代码路径分析

```
generate_from_seedance_txt()
  │
  ├─ _parse_seedance_txt()           ← ✅ 真实实现 (正则解析)
  ├─ _match_keyframes()              ← ✅ 真实实现 (文件匹配)
  │
  ├─ for each segment:
  │   ├─ if self.api_key:
  │   │   └─ _generate_segment()     ← ⚠️ 调用虚假API
  │   │       ├─ POST /generate      ← ❌ 虚假URL → 必抛异常
  │   │       ├─ poll query_task()   ← ❌ 虚假URL → 必抛异常
  │   │       └─ on any failure → _mock_segment_result()
  │   │
  │   └─ else:
  │       └─ _mock_segment_result()  ← ⚠️ Mock数据
  │
  ├─ if completed segments > 0:
  │   └─ _merge_videos()             ← ✅ 真实实现 (ffmpeg concat)
  │
  └─ else:
      └─ _generate_placeholder_video() ← ⚠️ 占位视频 (ffmpeg纯色+正弦波)
```

### 2.4 Mock/占位触发条件 (6个)

| # | 条件 | 代码位置 | 触发 |
|---|------|---------|------|
| 1 | `self.api_key is None` | L112-115 | 无SEEDANCE_API_KEY环境变量 |
| 2 | HTTP POST抛异常 | L310-312 | DNS解析失败 (必触发) |
| 3 | API返回无task_id | L280-282 | 即使DNS通了但响应格式不符 |
| 4 | query_task抛异常 | L459-460 | DNS解析失败 |
| 5 | task状态=failed | L300-302 | API返回失败 |
| 6 | 轮询超时(5分钟) | L307-308 | API无响应 |

**当前状态**: 条件#2和#4**必触发** (DNS NXDOMAIN)，所有segment生成都会进入mock。

### 2.5 Mock数据清单

```python
# _mock_segment_result() — 每个segment的mock
{"url": "", "task_id": "mock_1_1718000000", "duration": 2.1,
 "width": 1080, "height": 1080, "format": "mp4",
 "status": "mock",
 "note": "Seedance API不可用或无API密钥，使用占位结果"}

# _mock_result() — 基础接口的mock
{"url": "", "task_id": "mock_1718000000", "duration": 5.0,
 "width": 1080, "height": 1080, "format": "mp4",
 "status": "pending"}

# _error_result() — 解析失败的mock
{"video_path": "", "total_duration": 0, "segments": [],
 "status": "parse_failed", "segments_completed": 0,
 "segments_total": 0, "error": "..."}

# _generate_placeholder_video() — 最终占位视频
# ffmpeg -f lavfi -i color=c=0x1a1a2e:s=1080x1920:d=15:r=30
#        -f lavfi -i sine=frequency=440:duration=15
#        → video.mp4 (纯深蓝背景 + 440Hz正弦波音频)
```

---

## 3. 即梦 (Jimeng) Provider

### 3.1 Endpoint验证

```
API_BASE = "https://api.jimeng.ai/v1"
```

| 测试 | 结果 |
|------|------|
| DNS解析 | ❌ **NXDOMAIN** — `api.jimeng.ai` 域名不存在 |
| HTTP连通 | ❌ 无法建立连接 |
| 实际归属 | `jimeng.ai` 域名不存在于公网DNS |

**注**: 即梦是字节跳动旗下产品，实际通过**火山引擎(Volcengine) ARK**平台提供API，非独立域名。

### 3.2 完整请求结构

#### POST — 提交视频生成任务
```
URL:    https://api.jimeng.ai/v1/video/generate   ← 虚假URL
Method: POST
Headers:
  Authorization: Bearer {self.api_key}
  Content-Type: application/json
Payload:
  {
    "prompt": "{中文正面描述}",
    "negative_prompt": "{中文负面提示词}",
    "duration": 2.1,
    "size": "1080x1920",
    "fps": 30,
    "style": "realistic",
    "motion_amplitude": "medium",
    "reference_image": "data:image/jpeg;base64,..."   // 可选
  }
```

#### POST — 提交图片生成任务
```
URL:    https://api.jimeng.ai/v1/image/generate    ← 虚假URL
Method: POST
Headers:
  Authorization: Bearer {self.api_key}
  Content-Type: application/json
Payload:
  {
    "prompt": "...",
    "negative_prompt": "...",
    "size": "1080x1920",
    "num_images": 1,
    "style": "photorealistic"
  }
```

#### GET — 查询任务状态
```
URL:    https://api.jimeng.ai/v1/task/{task_id}     ← 虚假URL
Method: GET
Headers:
  Authorization: Bearer {self.api_key}
```

#### POST — 上传图片
```
URL:    https://api.jimeng.ai/v1/upload             ← 虚假URL
Method: POST
Headers:
  Authorization: Bearer {self.api_key}
Body:   multipart/form-data { "file": (filename, bytes, mime) }
```

### 3.3 代码路径分析

```
generate_from_jimeng_txt()
  │
  ├─ _parse_jimeng_txt()            ← ✅ 真实实现 (正则解析)
  ├─ _match_reference_images()      ← ✅ 真实实现 (文件匹配)
  │
  ├─ for each segment:
  │   ├─ if self.api_key:
  │   │   └─ _generate_segment_with_polling()
  │   │       ├─ POST /video/generate  ← ❌ 虚假URL → 必抛异常
  │   │       ├─ poll query_task()     ← ❌ 虚假URL → 必抛异常
  │   │       └─ on any failure → _mock_segment_result()
  │   │
  │   └─ else:
  │       └─ _mock_segment_result()   ← ⚠️ Mock数据
  │
  ├─ if completed segments > 0:
  │   └─ _merge_videos()              ← ✅ 真实实现
  │
  └─ else:
      └─ _generate_placeholder_video() ← ⚠️ 占位视频
```

### 3.4 Mock/占位触发条件 (5个)

| # | 条件 | 代码位置 | 触发 |
|---|------|---------|------|
| 1 | `self.api_key is None` | generate_from_jimeng_txt | 无JIMENG_API_KEY |
| 2 | HTTP POST抛异常 | _generate_segment_with_polling | DNS解析失败 (必触发) |
| 3 | API返回无task_id | _generate_segment_with_polling | 响应格式不符 |
| 4 | task状态=failed | _generate_segment_with_polling | API返回失败 |
| 5 | 轮询超时(5分钟) | _generate_segment_with_polling | API无响应 |

**当前状态**: 条件#2**必触发** (DNS NXDOMAIN)，所有segment生成都会进入mock。

### 3.5 Mock数据清单

```python
# _mock_segment_result()
{"url": "", "task_id": "jimeng_mock_1_1718000000", "duration": 2.1,
 "width": 1080, "height": 1080, "format": "mp4",
 "status": "mock", "note": "即梦API不可用或无API密钥"}

# _mock_video_result()
{"url": "", "task_id": "jimeng_mock_1718000000", "duration": 5.0,
 "width": 1080, "height": 1080, "format": "mp4", "status": "pending"}

# _error_result()
{"video_path": "", "total_duration": 0, "segments": [],
 "status": "parse_failed", "segments_completed": 0, "segments_total": 0}
```

---

## 4. 对比分析

| 维度 | Seedance | Jimeng |
|------|----------|--------|
| Endpoint真实性 | ❌ 虚假 | ❌ 虚假 |
| DNS | NXDOMAIN | NXDOMAIN |
| 真实平台 | 字节跳动/火山引擎 | 字节跳动/火山引擎 |
| 实际API入口 | 火山引擎ARK (未集成) | 火山引擎ARK (未集成) |
| 代码架构 | ✅ 完整 (解析/调用/轮询/下载/合并) | ✅ 完整 |
| API调用尝试 | ✅ 真实HTTP POST | ✅ 真实HTTP POST |
| 降级策略 | ✅ Mock → 占位视频 | ✅ Mock → 占位视频 |
| 占位视频 | ✅ ffmpeg生成有效H.264 | ✅ ffmpeg生成有效H.264 |
| Pipeline集成 | ✅ 步骤11.5 | ✅ 步骤13.5 |
| 可切换 | ✅ factory.json + --provider | ✅ factory.json + --provider |

---

## 5. Pipeline 集成中的额外降级

两个Provider在pipeline中都有**双重降级保护**:

```python
# app/pipeline.py — _step_seedance_video() / _step_jimeng_video()

# 第1层: Provider实例检查
if isinstance(self.provider, SeedanceProvider):   # 检查类型
    ...
if seedance is None or not seedance.is_available():  # 检查可用性
    return {"status": "skipped"}                      # ← 直接跳过

# 第2层: Provider内部mock
# 即使通过了第1层，API调用失败也进入_mock_segment_result
```

---

## 6. 总判定

| 问题 | 答案 |
|------|------|
| 是否存在伪接口 | **是** — 两个Provider的API_BASE都是不存在的域名 |
| 是否存在占位Endpoint | **是** — `api.seedance.ai` 和 `api.jimeng.ai` 不存在于公网DNS |
| 是否存在Mock数据 | **是** — 3个mock方法 + 占位视频生成 |
| 是否能真实调用API | **否** — DNS解析在第一步就失败，从未到达真实API |
| 代码框架是否可复用 | **是** — 将API_BASE和payload格式替换为真实API后即可工作 |

### 要接入真实API需要:

1. **Seedance**: 替换 `API_BASE` 为火山引擎ARK的真实endpoint，适配AK/SK认证(非Bearer Token)，适配真实请求/响应格式
2. **Jimeng**: 替换 `API_BASE` 为火山引擎ARK的真实endpoint，适配AK/SK认证，适配真实请求/响应格式
3. 两者都需要阅读火山引擎官方API文档获取正确的endpoint、认证方式、payload schema

---

*审计完成。两个Provider代码架构完整，降级策略完善，但API Endpoint为未经验证的虚假域名。*
