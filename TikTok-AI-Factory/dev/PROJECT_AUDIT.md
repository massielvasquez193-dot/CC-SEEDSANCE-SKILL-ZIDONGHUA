# PROJECT AUDIT — TikTok AI Video Factory

**审计日期**: 2026-06-10
**总文件数**: 37 (.py files)
**总代码行数**: ~7,400 lines

---

## 1. app/ — 应用核心模块 (8 files, 2,287 lines)

### app/__init__.py — 3 lines
| 项目 | 状态 |
|------|------|
| 行数 | 3 |
| Stub | ✅ 是 — 仅模块docstring |
| 业务逻辑 | ❌ 无 |
| 缺失 | 无 (__init__.py不需要逻辑) |

---

### app/scanner.py — 76 lines, 1 class, 6 methods
| 项目 | 状态 |
|------|------|
| 行数 | 76 |
| 业务逻辑 | ✅ 真实 — 完整的文件系统扫描 |
| AI集成 | N/A (纯文件IO) |
| 错误处理 | ⚠️ 部分 — 依赖Path.exists()，无try/except |
| 功能覆盖 | `scan_products()` / `scan_reference_videos()` / `scan_characters()` / `scan_all()` |
| 缺失 | 1. 无递归子目录扫描 2. 无文件大小/格式校验 3. 无重复文件检测 4. 无MIME类型检测(仅靠后缀) |

---

### app/product_extractor.py — 351 lines, 1 class, 15 methods
| 项目 | 状态 |
|------|------|
| 行数 | 351 |
| 业务逻辑 | ✅ 真实 — 完整产品信息提取 |
| AI集成 | ⚠️ **AI调用被注释**(L317: `# response = self.ai_client.analyze_image`) — 始终回退到模板推断 |
| 错误处理 | ✅ try/except (2处) |
| 真实逻辑 | 文件名解析(3种格式)、品类推断(10类关键词映射)、颜色推断(14色)、包装推断(9种)、材质推断(7种)、卖点生成、目标用户推断、规格推断 |
| 缺失 | 1. **AI视觉分析未实际连接** — `_ai_analyze()` 永远返回空dict 2. 无OCR集成读取包装文字 3. 无条形码/二维码识别 4. 颜色hex值为空(未做实际颜色提取) |

---

### app/video_analyzer.py — 647 lines, 1 class, 21 methods
| 项目 | 状态 |
|------|------|
| 行数 | 647 (最大单文件) |
| 业务逻辑 | ✅ 真实 — 最完整的模块 |
| AI集成 | ⚠️ **AI调用被注释**(L573: `# response = ai_client.chat(prompt)`) — 有回退逻辑 |
| 错误处理 | ✅ 全面 (11 try/except) |
| 真实逻辑 | ffprobe元数据提取、ffmpeg场景检测切镜(scene detect滤镜)、关键帧提取(3种模式)、软字幕提取(ffmpeg)、OCR硬字幕(tesseract)、音频提取+whisper转文字、镜头分类(基于时长)、运镜推断、转场推断、Hook/CTA分析、情绪曲线构建 |
| 缺失 | 1. **AI深度分析未实际连接** 2. scene detect sensitivity不可配置 3. OCR依赖tesseract外部安装 4. whisper转文字同样依赖外部安装 5. 无视频缩略图生成 6. 无音频波形分析 7. 无BGM检测 |

---

### app/character_extractor.py — 391 lines, 1 class, 9 methods
| 项目 | 状态 |
|------|------|
| 行数 | 391 |
| 业务逻辑 | ✅ 真实 — 完整人物特征提取 |
| AI集成 | ⚠️ **AI调用被注释**(L296: `# response = self.ai_client.analyze_image`) — 始终回退到默认值 |
| 错误处理 | ✅ try/except (2处) |
| 真实逻辑 | 年龄段映射(6档)、肤色映射(7种)、发型分类(12种)、发色(9种)、妆容(10种)、服装(14种)、体型(6种)、气质(10种)、文件名解析、默认值填充、一致性描述生成 |
| 缺失 | 1. **AI视觉分析未实际连接** 2. 无面部检测/关键点提取 3. 无服装颜色实际提取 4. 无年龄估计模型集成 5. default_character是硬编码常量，无法动态适配 |

---

### app/task_manager.py — 167 lines, 2 classes, 12 methods
| 项目 | 状态 |
|------|------|
| 行数 | 167 |
| 业务逻辑 | ✅ 真实 — 完整的任务队列管理 |
| AI集成 | N/A |
| 错误处理 | ❌ 无 try/except |
| 真实逻辑 | Task类(状态机: pending→running→completed/failed)、2种配对模式(笛卡尔积/1对1)、任务JSON持久化、状态查询 |
| 缺失 | 1. 无并发控制 2. 无任务优先级 3. 无任务重试机制 4. 无任务依赖/编排 5. 无分布式任务队列集成(Celery/RQ) |

---

### app/pipeline.py — 366 lines, 1 class, 15 methods
| 项目 | 状态 |
|------|------|
| 行数 | 366 |
| 业务逻辑 | ✅ 真实 — 主流水线编排 |
| AI集成 | ✅ 通过ai_client/property传递到各模块 |
| 错误处理 | ⚠️ 顶层1个try/except包裹单任务，但内部步骤无独立异常保护 |
| 真实逻辑 | 16步全自动流水线、文件复制、产品/视频/人物信息提取调度、脚本→分镜→Prompt→字幕→总结链式调用、pairing_mode动态切换、provider集成 |
| 缺失 | 1. **单任务失败不阻塞后续任务** — 但部分步骤失败后任务直接标记failed，无断点续传 2. 无步骤级别的重试 3. 无中间产物缓存 4. 无并行任务执行 5. 无进度回调/WebSocket通知 |

---

### app/watcher.py — 566 lines, 6 classes, 30 methods
| 项目 | 状态 |
|------|------|
| 行数 | 566 |
| 业务逻辑 | ✅ 真实 — 完整的Watch Mode实现 |
| AI集成 | N/A — 纯文件监控+调度 |
| 错误处理 | ✅ 全面 (9 try/except) |
| 真实逻辑 | FileStateTracker(SHA256去重+JSON持久化)、InputScanner(新文件检测)、WatchTaskBuilder(事件→任务自动配对)、WatchMode(轮询/watchdog双模式、防抖冷却、事件缓冲、30s超时补齐)、回调机制(on_new_files/on_task_created/on_task_completed)、force_scan、状态查询 |
| 缺失 | 1. watchdog事件驱动模式已实现但未充分测试 2. 无文件删除事件处理 3. 无文件修改事件(仅新增) 4. 冷却时间固定不可动态调整 5. 无Webhook通知 |

---

## 2. agents/ — Agent模块 (10 files, 1,375 lines)

### agents/__init__.py — 3 lines
| 项目 | 状态 |
|------|------|
| Stub | ✅ 仅模块docstring |

---

### agents/viral_analyzer.py — 109 lines, 1 class, 4 methods
| 项目 | 状态 |
|------|------|
| 行数 | 109 |
| 业务逻辑 | ⚠️ **模板驱动为主** — `_ai_replicate()` 的AI调用被注释(L75)，始终执行 `_template_replicate()` |
| AI集成 | ❌ **未连接** — `self.ai_client.chat(prompt)` 被注释 |
| 错误处理 | ✅ try/except |
| 真实逻辑 | 5镜头固定拆解模板、替换规则(产品/品牌/人物/脚本4类)、节奏分析(Hook模式/高潮点/留存策略) |
| 缺失 | 1. **AI调用未实现** — 永远是固定模板输出 2. 镜头数量固定为5个，不随视频时长动态调整 3. 无真实视频帧分析 4. 替换逻辑为通用模板，非视频特定 |

---

### agents/script_generator.py — 167 lines, 1 class, 4 methods
| 项目 | 状态 |
|------|------|
| 行数 | 167 |
| 业务逻辑 | ⚠️ **模板驱动为主** — `_ai_generate()` 的AI调用被注释(L70)，始终回退到 `_template_generate()` |
| AI集成 | ❌ **未连接** |
| 错误处理 | ✅ try/except |
| 真实逻辑 | 完整脚本模板(Hook/问题/产品/效果/CTA五段式)、节奏说明、转化优化(卖点/信任/紧迫3策略)、口播+画面+字幕三轨 |
| 缺失 | 1. **AI调用未实现** 2. 无A/B脚本变体 3. 无多语言支持 4. 口播时长未与镜头时长同步计算 5. 无敏感词过滤 |

---

### agents/storyboard_generator.py — 268 lines, 1 class, 9 methods
| 项目 | 状态 |
|------|------|
| 行数 | 268 |
| 业务逻辑 | ⚠️ **模板驱动为主** — AI调用被注释(L66) |
| AI集成 | ❌ **未连接** |
| 错误处理 | ✅ try/except (3处) |
| 真实逻辑 | 镜头时长分配(Hook短/CTA短/展示长)、8种景别轮换、8种运镜轮换、8种转场轮换、PIL可视化(storyboard.png绘制)、字幕/口播/音效三轨分镜表 |
| 缺失 | 1. **AI调用未实现** 2. 分镜图仅用PIL绘框，无实际Keyframe画面 3. 镜头时长分配算法简单(按比例)，未考虑内容节奏 4. 转场仅标注类型，无实际转场效果参数 |

---

### agents/image_prompt_generator.py — 122 lines, 1 class, 4 methods
| 项目 | 状态 |
|------|------|
| 行数 | 122 |
| 业务逻辑 | ⚠️ 模板驱动 — AI调用被注释(L48) |
| AI集成 | ❌ **未连接** |
| 错误处理 | ✅ try/except |
| 真实逻辑 | 6种镜头场景描述模板、Midjourney/DALL-E/Stable Diffusion三格式Prompt输出、人物/产品一致性全局前缀 |
| 缺失 | 1. **AI调用未实现** 2. Prompt未针对具体产品/人物特征定制(使用通用描述) 3. 无negative prompt生成 4. 无seed/参数控制 |

---

### agents/seedance_generator.py — 107 lines, 1 class, 4 methods
| 项目 | 状态 |
|------|------|
| 行数 | 107 |
| 业务逻辑 | ⚠️ 模板驱动 |
| AI集成 | ❌ **未连接** |
| 错误处理 | ✅ try/except |
| 真实逻辑 | 8种运镜英文描述、每镜头独立positive+negative prompt、全局参数(帧率/分辨率/风格)、过渡效果配置 |
| 缺失 | 1. **AI调用未实现** 2. Prompt长度未针对Seedance平台优化(通常有长度限制) 3. 无motion_scale参数 |

---

### agents/veo3_generator.py — 123 lines, 1 class, 4 methods
| 项目 | 状态 |
|------|------|
| 行数 | 123 |
| 业务逻辑 | ⚠️ 模板驱动 |
| AI集成 | ❌ **未连接** |
| 错误处理 | ✅ try/except |
| 真实逻辑 | 4档时长适配(8s/15s/30s/60s)、场景密度自适应(compact/moderate/detailed/comprehensive)、完整视觉风格+音频方向+人物/产品一致性 |
| 缺失 | 1. **AI调用未实现** 2. 无VEO3特有的camera_control参数 3. 场景细节按固定模板展开，未基于实际分镜内容 |

---

### agents/jimeng_generator.py — 182 lines, 1 class, 7 methods
| 项目 | 状态 |
|------|------|
| 行数 | 182 |
| 业务逻辑 | ⚠️ 模板驱动 — 两个generate方法都回退到模板 |
| AI集成 | ❌ **未连接** |
| 错误处理 | ✅ try/except (2处) |
| 真实逻辑 | 即梦+云镜双版本、中文8镜头模板、全局参数(风格/色彩/光线/转场/BGM)、负面提示词 |
| 缺失 | 1. **AI调用未实现** 2. 即梦平台限制(通常5-15s)未在模板中明确 3. 云镜版本过于简化 |

---

### agents/subtitle_generator.py — 150 lines, 1 class, 10 methods
| 项目 | 状态 |
|------|------|
| 行数 | 150 |
| 业务逻辑 | ✅ **真实 — 纯算法实现，不需要AI** |
| AI集成 | ✅ 有AI路径但非必需 — 模板解析已足够 |
| 错误处理 | ✅ try/except |
| 真实逻辑 | 脚本正则解析提取字幕/口播、SRT格式生成(HH:MM:SS,mmm)、中文断句(≤20字/行)、双语支持框架、时间戳自动分配 |
| 缺失 | 1. 字幕时间与口播时长未精确对齐(按段数平均分配) 2. 无字幕位置/样式配置 3. 双语模式仅有框架无翻译集成 |

---

### agents/export_manager.py — 140 lines, 1 class, 5 methods
| 项目 | 状态 |
|------|------|
| 行数 | 140 |
| 业务逻辑 | ✅ **真实 — 数据聚合+格式化** |
| AI集成 | N/A |
| 错误处理 | ❌ 无 try/except |
| 真实逻辑 | summary.json聚合、生成时间计算、全任务汇总、ASCII Art可读报告 |
| 缺失 | 1. 无CSV/Excel导出 2. 无HTML报告 3. 无PDF导出 4. summary中generation_time字段为空(completed_at在mark_completed前设置) |

---

## 3. providers/ — AI Provider层 (11 files, 2,088 lines)

### providers/__init__.py — 146 lines, 0 classes, 6 functions
| 项目 | 状态 |
|------|------|
| 行数 | 146 |
| 业务逻辑 | ✅ 真实 — Provider注册中心+工厂方法 |
| 错误处理 | ✅ try/except (11处 — 每个import) |
| 真实逻辑 | 注册表模式、延迟导入自动注册、`create_provider()`工厂、`create_all_available()`批量创建 |
| 缺失 | 1. 无Provider健康检查(health check) 2. 无Provider优先级/权重 3. 无Provider fallback链 4. 自动注册在模块导入时执行，可能触发不必要的import |

---

### providers/base_provider.py — 301 lines, 1 class, 16 methods
| 项目 | 状态 |
|------|------|
| 行数 | 301 |
| 业务逻辑 | ✅ 真实 — 完整抽象基类 |
| 错误处理 | ✅ 每个抽象方法raise NotImplementedError |
| 真实逻辑 | 统一接口(generate_text/generate_image/generate_video/analyze_image/query_task)、懒加载client、能力标记(supports_text/image/video/vision)、`is_available()`、`get_capabilities()` |
| 缺失 | 1. 无streaming接口 2. 无batch接口 3. 无rate limiting 4. 无token计数 5. 无cost tracking 6. 无重试/退避策略 7. 无缓存层 |

---

### providers/openai_provider.py — 135 lines, 1 class, 7 methods
| 项目 | 状态 |
|------|------|
| 行数 | 135 |
| 业务逻辑 | ✅ **真实** — 完整OpenAI SDK集成 |
| API集成 | ✅ 实际调用 `client.chat.completions.create()` / `client.images.generate()` |
| 错误处理 | ❌ 无 try/except — 异常直接向上传播 |
| 真实逻辑 | GPT-4o文本生成、Vision图片分析(base64编码)、DALL-E 3图片生成(尺寸映射1024x1792)、negative prompt注入 |
| 缺失 | 1. 无streaming 2. 无function calling暴露 3. DALL-E仅支持3种固定尺寸 4. 无response_format=json_object参数 5. **无重试逻辑** — API错误直接崩溃 |

---

### providers/claude_provider.py — 132 lines, 1 class, 6 methods
| 项目 | 状态 |
|------|------|
| 行数 | 132 |
| 业务逻辑 | ✅ **真实** — 完整Anthropic SDK集成 |
| API集成 | ✅ 实际调用 `client.messages.create()` |
| 错误处理 | ❌ 无 try/except |
| 真实逻辑 | Claude文本生成(system prompt顶层参数)、Vision图片分析(base64/URL)、`generate_text_with_image()`图文混合 |
| 缺失 | 1. 无streaming 2. 无tool_use暴露 3. 无cache_control(Claude特有prompt caching) 4. **无重试逻辑** |

---

### providers/gemini_provider.py — 122 lines, 1 class, 6 methods
| 项目 | 状态 |
|------|------|
| 行数 | 122 |
| 业务逻辑 | ✅ **真实** — 完整Gemini SDK集成 |
| API集成 | ✅ 实际调用 `model.generate_content()` |
| 错误处理 | ❌ 无 try/except |
| 真实逻辑 | Gemini文本生成(system_instruction)、Vision图片分析、Imagen图片生成 |
| 缺失 | 1. 无streaming 2. Imagen生成返回base64但无本地保存逻辑 3. **无重试逻辑** 4. 无safety_settings暴露 |

---

### providers/deepseek_provider.py — 122 lines, 1 class, 5 methods
| 项目 | 状态 |
|------|------|
| 行数 | 122 |
| 业务逻辑 | ✅ **真实** — 完整OpenAI兼容SDK集成 |
| API集成 | ✅ 实际调用 `client.chat.completions.create()` |
| 错误处理 | ❌ 无 try/except (除JSON解析) |
| 真实逻辑 | DeepSeek文本生成、R1推理模式(`deepseek-reasoner`)、JSON结构化输出(自动清理markdown标记) |
| 缺失 | 1. **无重试逻辑** 2. JSON解析失败时返回raw_text而非重试 3. 无streaming |

---

### providers/seedance_provider.py — 189 lines, 1 class, 8 methods
| 项目 | 状态 |
|------|------|
| 行数 | 189 |
| 业务逻辑 | ⚠️ **部分真实** — HTTP API框架完整，但使用推测的API endpoint |
| API集成 | ⚠️ 真实HTTP调用，但API URL可能不准确 (`https://api.seedance.ai/v1`) |
| 错误处理 | ✅ try/except + mock_result降级 |
| 真实逻辑 | 文生视频/图生视频双模式、分段生成(`generate_segments`)、base64图片编码、速率限制(delay)、任务查询 |
| 缺失 | 1. **API endpoint未验证** — 需要实际Seedance API文档 2. 无认证token刷新 3. 图生视频的图片上传方式未验证(直接base64 vs 先上传获取URL) |

---

### providers/veo3_provider.py — 148 lines, 1 class, 7 methods
| 项目 | 状态 |
|------|------|
| 行数 | 148 |
| 业务逻辑 | ⚠️ **部分真实** — 框架完整，API endpoint推测 |
| API集成 | ⚠️ 推测的API URL (`https://api.veo3.google.com/v1`) |
| 错误处理 | ✅ try/except + mock_result |
| 真实逻辑 | 4档时长适配、多时长批量生成、aspect_ratio自动判断、camera_control/motion_intensity参数 |
| 缺失 | 1. **API endpoint未验证** — VEO3目前通过Google Cloud Vertex AI提供，非独立REST API 2. 无GCP认证(service account) 3. 无bucket上传逻辑 |

---

### providers/jimeng_provider.py — 190 lines, 1 class, 9 methods
| 项目 | 状态 |
|------|------|
| 行数 | 190 |
| 业务逻辑 | ⚠️ **部分真实** — 框架完整，API endpoint推测 |
| API集成 | ⚠️ 推测的API URL (`https://api.jimeng.ai/v1`) |
| 错误处理 | ✅ 3 try/except + mock降级 |
| 真实逻辑 | 视频生成+图片生成双能力、逐镜生成(`generate_shot_by_shot`)、中文prompt优化、motion_amplitude参数 |
| 缺失 | 1. **API endpoint未验证** 2. 即梦实际通过字节跳动火山引擎提供 3. 无AK/SK认证方式 |

---

### providers/runway_provider.py — 231 lines, 1 class, 10 methods
| 项目 | 状态 |
|------|------|
| 行数 | 231 |
| 业务逻辑 | ⚠️ **部分真实** — 框架完整 |
| API集成 | ⚠️ 推测的API URL (`https://api.runwayml.com/v1`) |
| 错误处理 | ✅ 5 try/except + mock降级 |
| 真实逻辑 | 文生视频+图生视频双模式、导演模式(多关键帧控制)、图片上传(base64 fallback)、motion_bucket_id参数 |
| 缺失 | 1. **API endpoint未验证** 2. Runway实际API使用不同endpoint结构 3. 导演模式关键帧position参数未验证 |

---

### providers/kling_provider.py — 227 lines, 1 class, 10 methods
| 项目 | 状态 |
|------|------|
| 行数 | 227 |
| 业务逻辑 | ⚠️ **部分真实** — 框架完整 |
| API集成 | ⚠️ 推测的API URL (`https://api.kling.ai/v1`) |
| 错误处理 | ✅ 3 try/except + mock降级 |
| 真实逻辑 | 11种运镜控制(`CAMERA_MOVEMENTS`字典)、std/pro双模式、`generate_with_camera()`便捷方法 |
| 缺失 | 1. **API endpoint未验证** 2. 可灵实际使用快手开放平台API 3. 运镜参数名(如`camera_control`)未经实际测试 |

---

## 4. skills/ — 技能模块 (2 files, 962 lines)

### skills/__init__.py — 3 lines
| 项目 | 状态 |
|------|------|
| Stub | ✅ 仅模块docstring |

---

### skills/video_replication.py — 958 lines, 1 class, 22 methods
| 项目 | 状态 |
|------|------|
| 行数 | 958 (项目最大文件) |
| 业务逻辑 | ✅ **真实** — 完整Video Replication实现 |
| AI集成 | ❌ **无AI调用** — 全部基于规则和模板生成 |
| 错误处理 | ⚠️ 1个try/except(仅包级save) |
| 真实逻辑 | 13个完整模块: 视频摘要/原视频拆解/替换规则/分镜时间表/Storyboard网格提示词/提示图生成方案/通用视频Prompt/Seedance分段版/VEO3完整版/即梦版/云镜版/口播字幕时间轴/反向提示词(52条)/执行建议 |
| 缺失 | 1. **无AI调用** — 所有内容基于模板生成，非基于实际视频分析 2. 代码量过大(958行单体类)应拆分 3. Storyboard网格/提示图生成方案仅生成Prompt文本，无实际图片生成调用 4. 替换规则中的镜头类型/运镜为固定轮询，非基于实际视频内容 5. 无Codex/图片生成工具的实际集成(按SKILL.md要求应生成storyboard_grid/seedance_keyframes/product_replacement_reference/character_consistency_reference四类图) |

---

## 5. workflows/ — 工作流模块 (2 files, 241 lines)

### workflows/__init__.py — 3 lines
| 项目 | 状态 |
|------|------|
| Stub | ✅ 仅模块docstring |

---

### workflows/factory_workflow.py — 237 lines, 1 class, 10 methods
| 项目 | 状态 |
|------|------|
| 行数 | 237 |
| 业务逻辑 | ✅ 真实 — 完整工作流调度 |
| AI集成 | ✅ 通过provider参数集成 |
| 错误处理 | ❌ 无 try/except |
| 真实逻辑 | 5种工作流模式(full_auto/script_only/storyboard_only/prompt_only/single_task)、动态Provider切换(`switch_provider()`)、所有Agent的provider引用更新、可用Provider查询 |
| 缺失 | 1. 无工作流DAG/编排引擎 2. Provider切换后未验证新Provider可用性 3. 无工作流版本管理 4. 无工作流回滚 |

---

## 6. 其他文件

### config/settings.py — 76 lines, 0 classes, 0 functions
| 项目 | 状态 |
|------|------|
| 类型 | 配置常量模块 |
| 真实逻辑 | ✅ 路径/Duration/Provider/AI模型全部可配置 |
| 缺失 | 1. 无YAML/TOML配置加载 2. 无环境变量验证(schema) 3. 无配置热更新 |

### config/api_keys.py — 70 lines, 1 class, 11 methods
| 项目 | 状态 |
|------|------|
| 真实逻辑 | ✅ 从环境变量读取所有API密钥 |
| 缺失 | 1. 无.env文件自动加载 2. 无密钥轮换 3. 无密钥加密存储 |

### prompts/system_prompts.py — 367 lines, 0 classes, 0 functions
| 项目 | 状态 |
|------|------|
| 类型 | 纯数据文件 — Prompt模板 |
| 真实逻辑 | ✅ 10套完整提示词模板 (VIRAL_ANALYZER/SCRIPT_GENERATOR/STORYBOARD/IMAGE_PROMPT/SEEDANCE/VEO3/JIMENG/SUBTITLE/YUNJING) |
| 缺失 | 1. 所有Prompt使用Python f-string格式 — 调用者需.format()，非直接可用 2. 无英文版本 3. 无token长度估算 4. 无Prompt版本管理 |

### run_factory.py — 429 lines, 0 classes, 11 functions
| 项目 | 状态 |
|------|------|
| 真实逻辑 | ✅ CLI入口+Watch Mode+Provider集成+5种运行模式 |
| 错误处理 | ✅ try/except (2处，KeyboardInterrupt + main) |
| 缺失 | 1. 无配置文件指定(仅CLI参数) 2. 无daemon模式 3. 无systemd/service集成 4. Windows GBK编码处理(safe_print)可能在某些终端仍有问题 |

---

## 7. 总体评估

### 代码量分布

| 目录 | 文件数 | 总行数 | 占比 |
|------|--------|--------|------|
| app/ | 8 | 2,287 | 31% |
| providers/ | 11 | 2,088 | 28% |
| agents/ | 10 | 1,375 | 19% |
| skills/ | 2 | 962 | 13% |
| config/ | 2 | 146 | 2% |
| workflows/ | 2 | 241 | 3% |
| prompts/ | 1 | 367 | 5% |
| 根目录 | 1 | 429 | 6% |

### 真实业务逻辑 vs Stub/模板

| 分类 | 数量 | 说明 |
|------|------|------|
| ✅ **完整真实逻辑** | 22 files | scanner, task_manager, pipeline, watcher, export_manager, subtitle_generator, 所有11个provider(含4个真实SDK集成), settings, api_keys, factory_workflow, video_replication, run_factory |
| ⚠️ **模板驱动(有AI路径但未连接)** | 6 files | viral_analyzer, script_generator, storyboard_generator, image_prompt_generator, seedance_generator, veo3_generator, jimeng_generator, product_extractor(部分), character_extractor(部分), video_analyzer(部分) |
| ❌ **纯Stub** | 5 files | 全部 __init__.py (预期行为) |

### 关键缺失汇总

1. **AI集成缺口** (P0 — 核心功能受阻):
   - 6个Agent文件的AI调用全部被注释，始终执行模板回退
   - 3个app分析器(product/character/video)的AI视觉分析未连接
   - 5个视频生成Provider的API endpoint未经验证

2. **错误处理缺口** (P1):
   - OpenAI/Claude/Gemini/DeepSeek 4个Provider无重试逻辑
   - pipeline单任务执行仅1层try/except
   - task_manager无异常处理

3. **生产化缺口** (P1):
   - 无streaming接口
   - 无并发任务执行
   - 无断点续传
   - 无速率限制/令牌桶
   - 无成本追踪
   - 无健康检查

4. **SKILL.md合规性** (P1):
   - video_replication.py生成了所有13个模块的文本描述，但未生成实际图片(Codex storyboard_grid/seedance_keyframes/product_replacement_reference/character_consistency_reference)
   - Seedance分段Prompt中reference_image指向不存在的keyframe文件

5. **测试** (P2):
   - 项目无任何单元测试
   - 无集成测试
   - 无CI/CD配置

---

*审计完成。项目已建立完整架构和模板逻辑，核心缺口是AI API调用被注释和视频生成Provider的endpoint未验证。*
