# PHASE 2 REPORT — TikTok UGC Video Factory

**日期**: 2026-06-11
**升级**: AI Video Factory → TikTok UGC Video Factory
**优先级**: 真人感 > 视频质量 > 特效

---

## 1. 新增模块

### app/ugc_director.py ✅

| 功能 | 状态 |
|------|:---:|
| 语速分析 | ✅ 4种节奏: fast/normal/normal_fast/slow_building |
| 停顿位置 | ✅ 4个位置: after_hook/between_problem_agitate/before_solution/before_cta |
| 情绪变化 | ✅ 6种情绪: surprised/concerned/frustrated/excited/amazed/warm |
| 表情变化 | ✅ 逐镜头表情描述 (wide eyes/slight frown/bright smile...) |
| 手势动作 | ✅ 6种手势: hold_product_close/point_at_face/open_hands_shrug/hold_demo/point_result/point_link |
| 镜头晃动 | ✅ 25% shake (hook) / 15% shake (normal) |
| 产品出现时机 | ✅ 0s立即出现 / 35%/65%/85% 关键展示点 |
| CTA出现时机 | ✅ 70% soft CTA / 88% hard CTA |

输出: `performance_script.json`

```json
{
  "shot_01": {"role":"HOOK","emotion":"surprised_excited","gesture":"hold_product_close_to_camera","camera":"selfie_handheld_shaky","pace":"fast"},
  "shot_02": {"role":"PROBLEM","emotion":"concerned_relatable","gesture":"point_at_face_then_camera","camera":"selfie_closeup_stable","pace":"normal"},
  "shot_03": {"role":"AGITATE","emotion":"frustrated_empathetic","gesture":"open_hands_shrug","camera":"selfie_slight_shake","pace":"normal_fast"},
  "shot_04": {"role":"SOLUTION","emotion":"excited_discovery","gesture":"hold_product_demonstrate","camera":"handheld_product_focus","pace":"fast"},
  "shot_05": {"role":"RESULT","emotion":"amazed_satisfied","gesture":"point_at_result_before_after","camera":"selfie_stable_proud","pace":"normal"},
  "shot_06": {"role":"CTA","emotion":"warm_urgent","gesture":"point_down_to_link","camera":"selfie_smile_stable","pace":"slow_building"}
}
```

---

## 2. 升级模块

### agents/master_script_generator.py ✅

| 旧结构 | 新结构 (Phase 2) |
|--------|-----------------|
| Hook → Problem → Solution → Social Proof → CTA | **HOOK → PROBLEM → AGITATE → SOLUTION → RESULT → CTA** |

新增 AGITATE 段 — 放大痛点、强化情感共鸣
新增 RESULT 段 — 效果证明（Social Proof融入）
固定6段结构 — 禁止镜头独立编故事

### agents/voiceover_generator.py ✅

根据 `performance_script.json` 生成带表演标记的口播:

```
[Surprised Excited]
Guys... Look at this.

[pause 0.5] — let the reveal sink in

[Concerned Relatable]
I honestly didn't expect this to work so well.
[pause 0.3]

[Amazed]
Look at my skin after 7 days. The difference is real.
```

新增: 情绪标记 `[Excited]` `[Concerned]` `[Amazed]`, 停顿标记 `[pause 0.5]`, 重音规则

### agents/keyframe_generator.py ✅

| 旧 | 新 (Phase 2) |
|----|-------------|
| 通用prompt | **UGC特化prompt** |
| 无角色区分 | **6种角色专属prompt** (hook/problem/agitate/solution/result/cta) |
| 无风格约束 | **强制UGC Style后缀**: real American TikTok creator, natural skin, real home, handheld |

UGC Prompt规则:
- ✅ 真实美国TikTok达人
- ✅ 真实手机自拍
- ✅ 自然肤质 + 轻微瑕疵
- ✅ 自然光 + 真实家庭场景
- ✅ 手持镜头
- ❌ CGI / Plastic Skin / Beauty Filter / Commercial Studio / 3D Render

### agents/seedance_generator.py ✅

格式已验证:
```
[REFERENCE IMAGE]  ← keyframe_01.png (GPT Image生成)
[POSITIVE PROMPT]  ← UGC风格描述
[NEGATIVE PROMPT]  ← 一致性保护负面词
[CONTINUITY ANCHOR] ← 人物+产品锚点
[CAMERA]           ← 模拟手机手持
[SEGMENT DURATION]  ← 时长
```

### app/pipeline.py ✅

Phase 2 流程 (7步):
```
STEP 1: UGC Director → performance_script.json
STEP 2: Character Consistency → character_reference.png + anchor
STEP 3: Voiceover (performance-driven) → voiceover.txt + subtitle.srt
STEP 4: Storyboard → storyboard.md + storyboard.png
STEP 5: GPT Image Keyframes → keyframe_01~06.png
STEP 6: Seedance (Keyframe-driven) → seedance_segment_01~06.txt
STEP 7: Video + FFmpeg Composite → video.mp4
```

---

## 3. 已有模块 (未修改)

| 模块 | 状态 |
|------|:---:|
| agents/character_consistency.py | ✅ 人物一致性参考图+锚点 |
| agents/continuity_engine.py | ✅ 人物/产品/场景锁定+验证 |
| agents/character_library.py | ✅ 多数字人管理+国家标签 |
| agents/ugc_score.py | ✅ AI感/真人感/UGC感/广告转化 4维评分 |

---

## 4. 测试验证

### 运行命令
```bash
python run_factory.py --max-tasks 1
```

### 生成文件 (15 files)

| 文件 | 大小 | 内容验证 |
|------|------|:---:|
| master_script.md | ✅ | HOOK→PROBLEM→AGITATE→SOLUTION→RESULT→CTA 6段结构 |
| voiceover.txt | ✅ | [Surprised Excited] [pause 0.5] 等表演标记 |
| subtitle.srt | ✅ | SRT格式 6段字幕 |
| performance_script.json | ✅ | 6 shot: emotion/gesture/camera/pace 完整 |
| storyboard.md | ✅ | 分镜表 |
| storyboard.png | ✅ | PIL可视化分镜图 |
| character_reference.png | ✅ | 4姿态人物参考图 |
| consistency_anchor.txt | ✅ | 人物一致性锚点文本 |
| product.json | ✅ | 产品结构化信息 |
| character.json | ✅ | 人物结构化信息 |
| viral_analysis.json | ✅ | 视频分析报告 |
| voiceover_result.json | ✅ | 口播结果汇总 |
| keyframes/ | ⏸️ | 需要 OPENAI_API_KEY (GPT Image) |
| seedance_segments/ | ⏸️ | 依赖 keyframes |
| video.mp4 | ⏸️ | 依赖 seedance_segments |

### GPT Image 防护

Step 5 正确拒绝占位图:
```
RuntimeError: GPT Image provider not available for keyframe 1.
Set OPENAI_API_KEY and use --provider openai. NO placeholders allowed.
```

### 完整运行 (with API keys)

```bash
OPENAI_API_KEY=sk-xxx SEEDANCE_API_KEY=ark-xxx \
python run_factory.py --max-tasks 1 --provider openai
```

---

## 5. Phase 2 关键指标

| 指标 | Phase 1 | Phase 2 |
|------|---------|---------|
| 脚本结构 | 5段 | **6段 (新增AGITATE)** |
| 表演指导 | 无 | **performance_script.json — 逐镜头情绪/手势/运镜** |
| 口播标记 | 无 | **[Emotion] + [pause N] 表演标记** |
| Keyframe风格 | 通用 | **UGC特化: real skin, real home, handheld, American creator** |
| 禁止规则 | 基础 | **全面: 禁止CGI/Plastic Skin/Beauty Filter/Commercial Studio/3D** |
| 真人感优先级 | 未定义 | **真人感 > 视频质量 > 特效** |
| 评分维度 | 4维 | **4维 (AI感/真人感/UGC感/广告转化)** |
