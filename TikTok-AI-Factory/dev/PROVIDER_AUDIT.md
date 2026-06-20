# PROVIDER AUDIT — Text Providers

**审计日期**: 2026-06-10
**审计范围**: 4个Text Provider + BaseProvider

---

## 审计维度

| 维度 | 说明 |
|------|------|
| API调用 | 是否通过SDK/HTTP真正调用远程API |
| stream | 是否支持流式输出 |
| temperature | 是否支持temperature参数 |
| max_tokens | 是否支持max_tokens参数 |
| system_prompt | 是否支持系统提示词 |

---

## 1. openai_provider.py — 135 lines

### API调用: ✅ 真实

```python
# L39: 实际SDK调用
response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    temperature=temperature,
    max_tokens=max_tokens,
    **kwargs,
)
```

- SDK: `openai.OpenAI` (官方SDK)
- 调用方式: 同步 `client.chat.completions.create()`
- DALL-E: 同步 `client.images.generate()`

### stream: ❌ 不支持

`_generate_text_impl` 始终调用非stream模式。`**kwargs` 可以传递 `stream=True` 给底层SDK，但返回值类型会变成 `Stream` 对象而非 `str`，导致 `response.choices[0].message.content` 崩溃。

```python
# 当前代码 — 假设非stream响应
return response.choices[0].message.content
```

### temperature: ✅ 支持

```python
def _generate_text_impl(self, prompt, system_prompt, temperature, max_tokens, **kwargs):
    response = self.client.chat.completions.create(
        ...
        temperature=temperature,  # L42
        ...
    )
```

### max_tokens: ✅ 支持

```python
max_tokens=max_tokens,  # L43
```

### system_prompt: ✅ 支持

```python
if system_prompt:
    messages.append({"role": "system", "content": system_prompt})  # L36
```

### 其他发现
- **无重试逻辑**: API错误直接向上传播
- **无速率限制**: 无rate limit handling
- **无token计数**: 不追踪token消耗
- **DALL-E**: size仅支持3种固定尺寸(1024x1024/1024x1792/1792x1024)，自定义width/height会被映射

---

## 2. claude_provider.py — 132 lines

### API调用: ✅ 真实

```python
# L53: 实际SDK调用
response = self.client.messages.create(**create_kwargs)
```

- SDK: `anthropic.Anthropic` (官方SDK)
- 调用方式: 同步 `client.messages.create()`
- System prompt: Claude特有，通过顶层 `system` 参数而非messages中 (L50-51)

```python
if system_prompt:
    create_kwargs["system"] = system_prompt  # L50-51
```

### stream: ❌ 不支持

`_generate_text_impl` 调用 `messages.create()` 不带 `stream=True`。如果通过 `**kwargs` 传入 `stream=True`，`response` 会变成 `Stream` 对象，`response.content[0].text` 会失败。

```python
response = self.client.messages.create(**create_kwargs)
return response.content[0].text  # stream模式下content是迭代器
```

### temperature: ✅ 支持

```python
create_kwargs = {
    "temperature": temperature,  # L47
    ...
}
```

### max_tokens: ✅ 支持

```python
create_kwargs = {
    "max_tokens": max_tokens,  # L46 (Claude参数名是max_tokens)
    ...
}
```

### system_prompt: ✅ 支持 (Claude原生方式)

```python
# L35-51: 正确的Claude system prompt处理
kwargs.pop("system_prompt", None)  # 避免重复
if system_prompt:
    create_kwargs["system"] = system_prompt  # Claude的system在顶层
```

**注意**: L36 `kwargs.pop("system_prompt", None)` 是防御性代码 — 如果调用者通过kwargs传了system_prompt，会被移除以避免与messages参数冲突。

### 其他发现
- **Claude特有功能**: `generate_text_with_image()` 图文混合输入 (L74-102)
- **无重试逻辑**
- **无streaming**
- **无prompt caching利用** (Claude的cache_control)

---

## 3. deepseek_provider.py — 122 lines

### API调用: ✅ 真实

```python
# L40: 通过OpenAI兼容接口调用
response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    temperature=temperature,
    max_tokens=max_tokens,
    **kwargs,
)
```

- SDK: `openai.OpenAI` (使用DeepSeek兼容端点)
- Base URL: `https://api.deepseek.com/v1`
- 调用方式: 同步，与OpenAI完全兼容

### stream: ❌ 不支持

与OpenAI Provider相同问题 — 假设非stream响应结构。

### temperature: ✅ 支持

```python
temperature=temperature,  # L43
```

### max_tokens: ✅ 支持

```python
max_tokens=max_tokens,  # L44
```

### system_prompt: ✅ 支持

```python
if system_prompt:
    messages.append({"role": "system", "content": system_prompt})  # L37
```

### DeepSeek特有功能
- **R1推理模式** (`generate_with_reasoning`, L52-78): 调用 `deepseek-reasoner` 模型，返回 `{reasoning, answer}`  结构
- **JSON结构化输出** (`generate_json`, L84-122): 自动处理markdown代码块清理和JSON解析
- **温度默认0.3**: `generate_json` 使用较低temperature以获得稳定JSON输出

### 其他发现
- **无重试逻辑**
- **无streaming**
- **JSON解析失败降级**: 返回 `{"raw_text": text}` 而非抛出异常

---

## 4. gemini_provider.py — 122 lines

### API调用: ✅ 真实

```python
# L44-48: 实际SDK调用
model = self.client.GenerativeModel(**model_kwargs)
response = model.generate_content(
    prompt,
    generation_config=generation_config,
)
```

- SDK: `google.generativeai` (官方SDK)
- 调用方式: 同步 `model.generate_content()`
- System prompt: Gemini特有，通过 `system_instruction` 模型构造参数 (L42)

```python
if system_prompt:
    model_kwargs["system_instruction"] = system_prompt  # L42
```

### stream: ❌ 不支持

`_generate_text_impl` 调用 `generate_content()` 不带 `stream=True`。

### temperature: ✅ 支持

```python
generation_config = {
    "temperature": temperature,  # L34
    "max_output_tokens": max_tokens,  # L36 — Gemini参数名不同
}
```

### max_tokens: ✅ 支持

```python
"max_output_tokens": max_tokens,  # L36
```

**注意**: Gemini SDK参数名是 `max_output_tokens` 而非 `max_tokens`，当前实现正确。

### system_prompt: ✅ 支持 (Gemini原生方式)

```python
# L40-42
model_kwargs = {"model_name": self.model}
if system_prompt:
    model_kwargs["system_instruction"] = system_prompt
```

**⚠️ 潜在问题**: 每次调用 `_generate_text_impl` 都通过 `self.client.GenerativeModel(**model_kwargs)` 创建新的模型实例 (L44)。这在system_prompt不变时浪费资源。应考虑缓存model实例。

### 其他发现
- **Gemini特有**: Imagen图片生成 (`_generate_image_impl`)，输出base64数据而非URL
- **每次新建model实例**: `GenerativeModel(...)` 在每次text generation调用中都重新创建 — 低效
- **无重试逻辑**
- **无streaming**
- **无safety_settings暴露**: Gemini的safety filtering无法配置
- **`_analyze_image_impl` 未传system_prompt**: L58直接 `self.client.GenerativeModel(self.model)` 无system_instruction

---

## 5. base_provider.py — 301 lines (接口定义)

### generate_text 接口

| 参数 | 类型 | 默认值 | 是否传递到子类 |
|------|------|--------|---------------|
| prompt | str | (必填) | ✅ |
| system_prompt | str \| None | None | ✅ |
| temperature | float | 0.7 | ✅ |
| max_tokens | int | 4096 | ✅ |
| **kwargs | dict | — | ✅ 透传 |

### stream: ❌ 未定义

`generate_text()` 返回类型固定为 `str`，无stream接口。如需添加：

```python
# 缺少的接口
def generate_text_stream(
    self,
    prompt: str,
    system_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    **kwargs,
) -> Iterator[str]:
    ...
```

---

## 总结矩阵

| 维度 | OpenAI | Claude | DeepSeek | Gemini |
|------|--------|--------|----------|--------|
| **API调用** | ✅ SDK | ✅ SDK | ✅ SDK | ✅ SDK |
| **stream** | ❌ | ❌ | ❌ | ❌ |
| **temperature** | ✅ | ✅ | ✅ | ✅ |
| **max_tokens** | ✅ | ✅ | ✅ | ✅ (命名: max_output_tokens) |
| **system_prompt** | ✅ messages[0] | ✅ 顶层system参数 | ✅ messages[0] | ✅ system_instruction |
| **重试逻辑** | ❌ | ❌ | ❌ | ❌ |
| **速率限制** | ❌ | ❌ | ❌ | ❌ |
| **token计数** | ❌ | ❌ | ❌ | ❌ |
| **特有优势** | DALL-E图片生成 | 图文混合输入 | R1推理+JSON输出 | Imagen图片生成 |

### 关键发现

**全部4个Provider都真正调用API** — 使用官方SDK进行实际远程调用，不是stub/模板。

**stream全缺** — 4个Provider的 `_generate_text_impl` 都返回 `str`，不支持流式输出。如果通过 `**kwargs` 传入 `stream=True`，返回值类型变化会导致 `response.choices[0].message.content` 崩溃。

**system_prompt处理方式各不同**:
- OpenAI/DeepSeek: `messages.append({"role": "system", ...})`
- Claude: `create_kwargs["system"] = system_prompt` (顶层参数)
- Gemini: `model_kwargs["system_instruction"] = system_prompt` (模型构造参数)

**max_tokens命名差异**: Gemini使用 `max_output_tokens`，其他使用 `max_tokens`

**共同缺失**:
1. 无stream接口 (需要单独的 `generate_text_stream()` 方法)
2. 无重试/退避 (网络错误直接崩溃)
3. 无速率限制 (可能429)
4. 无token使用量统计
5. 无请求日志/追踪
6. 无超时控制 (依赖SDK默认值)

---

*审计完成。4个Text Provider均真实调用API，temperature/max_tokens/system_prompt全部支持，stream全部不支持。*
