---
name: video-replication
description: Create complete video-replication packages and Codex-generated prompt images from a reference video plus a target product and optional new character setting. Use when the user says "执行【视频复刻】", "视频复刻", "复刻这个视频", "生成提示图", "生成storyboard图", or asks to preserve a reference video's shot structure, pacing, camera movement, actions, voiceover logic, scene mood, and CTA style while replacing the product, person, brand, logo, packaging text, and identity for Seedance, VEO3, 即梦, 云镜, or similar video generation tools. When the exact command is "执行【视频复刻】", run the full workflow by default, including all text outputs and actual Codex prompt image generation when image generation tools are available, so the user can directly use the generated images and segmented prompts in Seedance.
---

# Video Replication

## Overview

Use this skill to turn a reference video into a clean, legally safer remake plan: preserve the reusable creative structure and performance logic, but replace the product, person, brand identity, logo, packaging text, and exact face/identity. Produce platform-ready prompt variants, timing tables, and optional prompt images that help the user generate a new video with consistent product and character continuity.

## Full Command Behavior

Treat `执行【视频复刻】` as the master command. When the user says this exact command, execute every module in this skill unless the user explicitly limits the scope.

Full execution includes:

- Video summary
- Original video breakdown
- Replacement rules
- Shot-by-shot timing table
- Storyboard grid prompt
- Prompt image generation plan
- Prompt image generation prompts
- Actual Codex-generated prompt images, when image generation tools are available
- General video generation prompt
- Seedance segmented version
- VEO3 complete version
- 即梦/云镜 version
- Voiceover/subtitle timeline
- Negative prompts
- Execution advice

If required inputs are missing, ask only for the missing essentials before running the full workflow. If the user provides enough information to proceed, do not ask whether to include optional sections; include all sections by default. Do not stop after writing prompt text when visual assets are requested or when the exact master command is used; generate the visual assets too.

## Input Handling

Ask for missing essentials only when they are necessary to proceed. If a reference video, target product, or product image is missing, request it. If the new character setting is missing, use the default below.

Default new character:

```text
一位年轻成年女性美妆达人，干净自然妆容，长发，居家上衣，粉色美甲，在明亮卧室或浴室里对着手机前置镜头自然口播。表情真实、亲切、有种草感。动作和节奏参考原视频，但脸和身份完全不同于原视频人物。
```

When the user provides a product only as text, extract and preserve product name, category, color, form factor, packaging, use case, visible materials, and distinguishing details. Keep the product category accurate; do not morph it into a related category.

## Workflow

1. Inspect or infer the reference video's duration, scene sequence, shot count, pacing, framing, camera movement, character actions, voiceover logic, on-screen text style, product beats, emotional arc, and CTA.
2. Separate reusable structure from protected or unwanted specifics. Preserve structure, rhythm, camera language, action types, scene mood, script logic, and CTA pattern. Replace original person, face, identity, brand, logo, package copy, and product design details.
3. Build replacement rules for product and character consistency. State what must stay consistent across all shots: product category, color, shape, material, packaging style, character age range, wardrobe, hair, makeup, and scene.
4. Generate a shot-by-shot timing table. Include timestamp, duration, framing, camera movement, action, product placement, voiceover/subtitle, transition, and replacement notes.
5. Generate image and video prompts. Include a storyboard grid prompt, prompt-image generation prompts, a general video generation prompt, and tool-specific versions for Seedance, VEO3, and 即梦/云镜.
6. When the user says `执行【视频复刻】`, asks to generate prompt images, or when visual planning would materially help, create actual prompt images using Codex image generation. Prefer a storyboard grid, keyframe sheet, product replacement reference sheet, and/or character consistency reference sheet depending on the request.
7. Add negative prompts and execution advice that prevent identity copying, brand carryover, product drift, text artifacts, hand/product deformation, continuity loss, and over-stylization.

## Replacement Rules

Always include these constraints in the generated package unless the user explicitly changes them:

- Keep the reference video's shot structure, rhythm, camera movement, action logic, scene mood, voiceover logic, and CTA style.
- Replace every original product with the target product.
- Replace the original person with the specified new person or the default new character.
- Do not copy the original real person's identity, face, likeness, or distinctive biometric traits.
- Do not keep original brand logos, packaging text, trademarks, product shape, or exact industrial design unless those belong to the user's target product.
- Keep the target product visually accurate and in the correct category throughout the video.
- Keep the new character consistent across the full video.
- Avoid copyrighted music, visible third-party marks, readable fake labels, and exact source-video overlays unless the user owns or provides them.

## Default Output

Respond in Chinese by default when the user writes in Chinese. Use this structure unless the user requests a shorter or different format:

1. 视频摘要
2. 原视频拆解
3. 替换规则
4. 分镜头时间表
5. Storyboard 网格图提示词
6. Codex 直接生成的 Storyboard 网格图
7. Codex 直接生成的分镜提示图/关键帧图
8. 产品替换参考图
9. 人物一致性参考图
10. 提示图生成方案
11. 提示图生成提示词
12. 通用视频生成提示词
13. Seedance 分段版
14. VEO3 完整版
15. 即梦/云镜版本
16. 口播/字幕时间轴
17. 反向提示词
18. 执行建议

For short user requests, include a concise first pass and state what inputs are still needed to make it exact. If the user says `执行【视频复刻】`, generate the complete package and actual prompt images when possible instead of stopping at text prompts. In the final response, show or link the generated images before the Seedance prompt sections so the user can use them directly.

## Prompt Guidance

Storyboard grid prompt:

- Ask for a multi-panel grid with one panel per shot or beat.
- Each panel should show framing, scene, pose, product placement, camera angle, lighting, and subtitle/voiceover cue.
- Do not ask for the original person's face or exact source product unless it is the target product.

Prompt image generation:

- Use Codex image generation when the user requests "生成提示图", "生成 storyboard 图", "生成关键帧图", "出图", "提示图资产", or any direct visual output. Also use it by default when the user says `执行【视频复刻】`.
- Default prompt image set: one storyboard grid showing all core shots, one shot-by-shot keyframe sheet, one product replacement reference sheet, and one character consistency reference sheet. Generate fewer images only if the user explicitly limits the scope or the available image generation tool cannot produce all assets.
- Make prompt images production-useful: clean composition, visible shot labels, consistent target product, consistent new character, clear camera angles, clear action beats, no source-video face, no original logos, no readable third-party packaging text.
- For storyboard grids, use 4, 6, 8, or 9 panels depending on the reference video's shot count. Each panel should show one keyframe, not decorative mood art.
- For product replacement sheets, show the target product from several useful angles and in-hand/in-scene usage, while keeping category, color, shape, material, packaging, and scale faithful to the user-provided product.
- For character consistency sheets, show the same new character across neutral, speaking, demonstrating, holding product, and CTA poses. Keep wardrobe, hair, makeup, age range, and scene consistent.
- If source or target images are available as files, use them as visual references when the image generation tool supports references. If not, convert their visual details into explicit prompt text.

Codex-generated image deliverables:

- `storyboard_grid`: A single grid image that visualizes the full video structure for planning. Use this as the top-level Seedance visual reference.
- `seedance_keyframes`: A shot-by-shot keyframe sheet. Each panel should correspond to one Seedance segment and match the shot timing table.
- `product_replacement_reference`: A product accuracy sheet showing the target product alone, in hand, and in scene.
- `character_consistency_reference`: A character sheet showing the same new person across speaking, demonstrating, holding product, and CTA poses.

When generating these images, write one concise image-generation prompt per deliverable, then invoke the image generation tool for the deliverables that are in scope. After generation, label each image clearly in the response and pair it with the exact Seedance segment or usage note.

Seedance direct-use packaging:

- For each Seedance segment, include: segment number, timestamp, duration, reference image to use, image-to-video prompt, camera movement, action, product requirement, character continuity anchor, subtitle/voiceover cue, and negative prompt.
- Make the generated keyframe sheet and segment prompts match one-to-one. If there are 6 Seedance segments, the keyframe sheet should have 6 panels and the Seedance section should have 6 segment prompts.
- Keep prompts ready to paste into Seedance: short, visual, action-forward, and free of analysis notes.

Seedance version:

- Split into short segments when the video has multiple shots or product actions.
- Put continuity anchors at the start of each segment: same person, same wardrobe, same product, same setting, same lighting.
- Include timing, camera movement, action, and product interaction per segment.

VEO3 version:

- Provide one coherent full-video prompt with duration, scene progression, character, target product, camera grammar, narration/subtitle timing, and CTA.
- Include a separate negative prompt.

即梦/云镜 version:

- Use direct, visual Chinese prompts with clear shot order.
- Keep each shot concise and concrete.
- Repeat product and character consistency constraints.

## Negative Prompt Checklist

Include negatives for: original celebrity/influencer identity, original face, original logo, original packaging text, original brand colors when not part of target product, product category drift, extra fingers, distorted hands, unreadable labels, random text, mismatched wardrobe, inconsistent character, inconsistent product, sudden scene changes, over-smoothed skin, AI plastic look, flicker, warped product geometry, and low-resolution artifacts.
