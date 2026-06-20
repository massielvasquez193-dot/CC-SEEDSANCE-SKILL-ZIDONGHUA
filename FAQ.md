# 常见问题 FAQ — TikTok AI Factory Pro

---

## 安装与配置

### Q: 需要什么电脑配置？
**A**: Windows 10/11, 8GB内存以上。不需要独立显卡，所有AI计算在云端完成。

### Q: 必须安装Python吗？
**A**: 使用Setup.exe安装包会自动安装Python。手动安装需要Python 3.10+。

### Q: API密钥在哪里获取？
**A**: 
- OpenAI: https://platform.openai.com/api-keys
- ElevenLabs: https://elevenlabs.io/app/settings/api-keys
- 火山引擎(Seedance): https://console.volcengine.com/ark/

### Q: 最少需要配置几个API密钥？
**A**: 至少1个 — `OPENAI_API_KEY`。没有视频密钥时，系统会生成脚本/口播/字幕/分镜，仅跳过视频生成。

### Q: 支持Mac吗？
**A**: 当前仅支持Windows。Mac版本开发中。

---

## 素材

### Q: 产品图有什么要求？
**A**: JPG/PNG/WebP格式, 不超过20MB。建议白色背景, 产品主体清晰。手机拍的照片完全可以用。

### Q: 参考视频必须是TikTok视频吗？
**A**: 任何竖屏9:16的MP4/MOV视频都可以。系统会分析它的结构、节奏和爆款元素。你也可以用自己的视频作为参考。

### Q: 人物图必须是真人吗？
**A**: 建议放真人照片。系统会用GPT Image根据你的照片生成一致的数字人形象。不放人物图也可以使用系统内置的默认角色。

### Q: 可以一次处理多少个产品？
**A**: 没有限制。放入N组素材，系统自动生成N个视频。

---

## 生成

### Q: 生成一个视频要多久？
**A**: 约25-35分钟。GPT脚本~30秒, GPT Image关键帧~2分钟, Seedance视频~20-30分钟, 配音+合成~2分钟。

### Q: 为什么我的视频生成失败了？
**A**: 
1. 检查API密钥是否正确
2. 检查API余额是否充足
3. 查看 `logs/factory.log` 日志文件

### Q: 可以中途停止吗？
**A**: GUI模式下点击"停止"按钮。命令行模式按 Ctrl+C。已生成的中间文件会保留。

### Q: 视频可以自定义时长吗？
**A**: 编辑 `config/factory.json` 中的 `video.duration_seconds` 字段 (8/15/30/60秒)。

---

## 视频质量

### Q: 生成的视频看起来像真人吗？
**A**: 系统目标就是TikTok真人UGC标准。使用第一人称脚本、自然肤质、手机自拍角度、轻微镜头晃动。但最终效果取决于Seedance视频模型的能力。

### Q: 人物会变脸吗？
**A**: 不会。系统使用"人物圣经"(character.json)锁定人物特征。所有镜头强制引用同一个人物定义。禁止随机人物。

### Q: 产品颜色会变化吗？
**A**: 不会。产品特征同样被锁定。所有镜头强制引用同一产品定义。

### Q: 声音听起来像AI吗？
**A**: 使用ElevenLabs真人TTS引擎，支持8种情绪映射。效果接近真人。如果ElevenLabs不可用，系统会生成口播文本但跳过配音。

---

## 费用

### Q: 一个视频成本多少？
**A**: 约$5.69 (GPT脚本$0.02 + GPT Image关键帧$0.72 + Seedance视频$4.80 + ElevenLabs配音$0.15)。

### Q: 有免费额度吗？
**A**: 有。火山引擎新用户送500万tokens (约6个视频)。OpenAI新用户送$5额度。ElevenLabs每月免费10K字符。

### Q: 如何降低成本？
**A**: 
1. 使用Seedance快速版模型 (doubao-seedance-2-0-fast) — 价格更低
2. 减少关键帧数量 (config/factory.json中调整)
3. 使用GPT-4o-mini替代GPT-4.1 (脚本成本降低90%)

### Q: 可以只生成脚本不要视频吗？
**A**: 可以。不配置ARK_API_KEY即可。系统会生成完整的脚本/口播/字幕/分镜，跳过视频生成。

---

## 商业化

### Q: 生成的视频版权归谁？
**A**: 归你。MIT许可证。你可以自由使用、修改、商用。

### Q: 可以给客户交付什么？
**A**: 完整的output目录 (脚本+视频+字幕+分镜+评分报告)。客户可以直接使用。

### Q: 支持多语言吗？
**A**: 支持。脚本支持中英文, ElevenLabs配音支持29种语言, 字幕支持中英文。

### Q: 可以做TikTok以外的平台吗？
**A**: 视频是标准MP4格式, 可以发布到任何平台 (TikTok/Reels/Shorts/YouTube)。

---

## 故障排查

### Q: "ffmpeg未找到"
**A**: 下载安装: https://ffmpeg.org/download.html 并添加到系统PATH。

### Q: "Python不是内部命令"
**A**: 重新安装Python时勾选 "Add Python to PATH"。

### Q: "401 Unauthorized"
**A**: API密钥无效。检查.env文件中密钥是否正确。

### Q: "403 Forbidden"
**A**: API余额不足或服务未开通。检查对应平台账户状态。

### Q: "模块未找到"
**A**: 依赖未完整安装。运行: `pip install -r requirements.txt`

### Q: 如何查看详细日志？
**A**: 打开 `logs/factory.log` 文件。

---

*更多问题请联系技术支持。*
