# REAL API MODE — Seedance & 即梦 Provider

**更新日期**: 2026-06-10
**变更**: 移除所有 Mock/Placeholder/Fake 逻辑，替换为真实火山引擎 ARK API

---

## 变更摘要

| 项目 | 旧 (MOCK) | 新 (REAL) |
|------|-----------|-----------|
| API Base | `https://api.seedance.ai/v1` (不存在) | `https://ark.cn-beijing.volces.com/api/v3` |
| API Base | `https://api.jimeng.ai/v1` (不存在) | `https://ark.cn-beijing.volces.com/api/v3` |
| 认证 | `Bearer {api_key}` (推测) | `Bearer {api_key}` (ARK控制台创建) |
| 创建任务 | `POST /generate` (虚假) | `POST /contents/generations/tasks` |
| 查询任务 | `GET /task/{task_id}` (虚假) | `GET /contents/generations/tasks/{task_id}` |
| Payload格式 | `{mode, prompt, ...}` (推测) | `{model, content, parameters}` (ARK文档) |
| 图片传入 | `reference_image: base64` | `content[{type: image_url, image_url: {url: ...}}]` |
| 任务状态 | `completed/processing/failed` | `queued/running/succeeded/failed/expired/cancelled` |
| Mock降级 | 3个mock方法 + 占位视频 | **全部移除** — API失败即抛异常 |
| 空API Key | 默默切换到mock | **抛 RuntimeError** — 强制配置 |
| Segment失败 | 继续下一个 → 占位视频 | **抛异常** — 阻止不完整输出 |

---

## 移除的内容

### Seedance Provider — 已删除

```python
# 已删除的方法:
_mock_segment_result()          # 返回空url + mock task_id
_mock_result()                  # 返回空url + pending状态
_error_result()                 # 返回空video_path
_generate_placeholder_video()   # ffmpeg生成纯色+440Hz占位视频

# 已删除的逻辑:
if self.api_key: ... else: _mock_segment_result()     # 无key时返回mock
except Exception: return self._mock_result()           # API失败时返回mock
if not task_id: return self._mock_segment_result()    # 无task_id时返回mock
if not completed: _generate_placeholder_video()        # 无可用片段时生成占位

# 已删除的跳过逻辑 (pipeline):
if seedance is None or not seedance.is_available():
    return {"status": "skipped"}   # ← 现在直接抛异常
```

### Jimeng Provider — 已删除

```python
# 已删除的方法:
_mock_segment_result()
_mock_video_result()
_error_result()
_generate_placeholder_video()

# 已删除的逻辑:
if self.api_key: ... else: ...
except Exception: return self._mock_video_result()
if not completed: _generate_placeholder_video()
```

---

## 真实API请求

### Seedance

```
POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
Authorization: Bearer {SEEDANCE_API_KEY}
Content-Type: application/json

{
  "model": "doubao-seedance-2-0-260128",
  "content": [
    {
      "type": "text",
      "text": "Cinematic product video segment, 2.1 seconds. Camera: Fast push-in..."
    },
    {
      "type": "image_url",
      "image_url": {"url": "data:image/jpeg;base64,..."}
    }
  ],
  "parameters": {
    "duration": 5,
    "resolution": "1080p",
    "fps": 24,
    "generate_audio": true,
    "negative_prompt": "blurry, distorted face, extra fingers..."
  }
}
```

### 即梦 (Jimeng)

```
POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
Authorization: Bearer {JIMENG_API_KEY}
Content-Type: application/json

{
  "model": "jimeng-video-3-0-1080p",
  "content": [
    {
      "type": "text",
      "text": "特写镜头：金色包装的精华液产品，光线从侧面打在..."
    }
  ],
  "parameters": {
    "duration": 5,
    "resolution": "1080p",
    "fps": 24,
    "generate_audio": true,
    "negative_prompt": "模糊, 变形, 多余的手指..."
  }
}
```

### 任务查询 (两者相同)

```
GET https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{task_id}
Authorization: Bearer {api_key}

Response (succeeded):
{
  "id": "task_xxx",
  "status": "succeeded",
  "video_url": "https://...",
  ...
}
```

---

## 可用模型

| Provider | Model ID | 说明 |
|----------|----------|------|
| Seedance | `doubao-seedance-2-0-260128` | Seedance 2.0 标准版 |
| Seedance | `doubao-seedance-2-0-fast-260128` | Seedance 2.0 快速版 |
| Seedance | `doubao-seedance-1-5-pro` | Seedance 1.5 Pro (旧版) |
| Jimeng | `jimeng-video-3-0-1080p` | 即梦视频3.0 1080P |
| Jimeng | `jimeng-video-3-0-720p` | 即梦视频3.0 720P |
| Jimeng | `jimeng-video-3-0-pro` | 即梦视频3.0 Pro |

---

## 如何获取API Key

1. 注册火山引擎账号: https://console.volcengine.com
2. 完成实名认证
3. 进入 ARK 方舟平台: https://console.volcengine.com/ark
4. 创建 API Key: https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
5. 开通模型: 在「模型开通管理」→「视觉模型」tab 开通 Seedance/即梦 模型
6. 确保账户余额 ≥ 200元 或领取免费试用额度

### 配置

```bash
# .env
SEEDANCE_API_KEY=your-ark-api-key-here
JIMENG_API_KEY=your-ark-api-key-here
```

---

## 错误处理策略

| 场景 | 行为 |
|------|------|
| 无 API Key | `RuntimeError("SEEDANCE_API_KEY not set...")` |
| API 返回无 task_id | `RuntimeError("ARK API 返回异常: 无 task_id...")` |
| 任务失败 (failed/expired/cancelled) | `RuntimeError("ARK 任务 xxx failed: ...")` |
| 任务超时 (10分钟) | `TimeoutError("ARK 任务 xxx 超时...")` |
| succeeded 但无 video_url | `RuntimeError("ARK 任务 xxx succeeded 但无 video_url...")` |
| 视频下载失败 | `requests.HTTPError` (原始异常) |
| ffmpeg 合并失败 | `RuntimeError("视频合并失败: ...")` |

**无任何 Mock / Fallback / Placeholder。失败即停止。**

---

## 验证命令

```bash
# 验证 API 连通性
curl -H "Authorization: Bearer $SEEDANCE_API_KEY" \
  https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/ping

# 运行
SEEDANCE_API_KEY=your-key python run_factory.py --provider seedance

# 或
JIMENG_API_KEY=your-key python run_factory.py --provider jimeng
```
