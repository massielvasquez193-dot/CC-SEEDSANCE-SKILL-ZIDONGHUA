"""
TikTok AI Video Factory - Video Replication Skill (P4)
完整实现 SKILL(2).md 全部逻辑

输出:
1. 视频摘要
2. 原视频拆解
3. 替换规则
4. 分镜头时间表
5. Storyboard 网格图提示词
6. 提示图生成方案
7. 通用视频生成提示词
8. Seedance 分段版
9. VEO3 完整版
10. 即梦/云镜版本
11. 口播/字幕时间轴
12. 反向提示词
13. 执行建议
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.video_analyzer import VideoAnalyzer
from app.product_extractor import ProductExtractor
from app.character_extractor import CharacterExtractor

logger = logging.getLogger(__name__)


class VideoReplicationSkill:
    """
    视频复刻技能

    将参考视频的创意结构和表演逻辑保留，
    替换产品、人物、品牌、Logo、包装文字，
    生成平台就绪的Prompt包。
    """

    # === 反向提示词清单 (来自SKILL.md) ===
    NEGATIVE_PROMPTS = [
        # 身份/肖像保护
        "original celebrity face", "original influencer identity",
        "original person likeness", "recognizable real person",
        "biometric facial features of source video",

        # 品牌保护
        "original brand logo", "original brand name text",
        "original packaging text", "original brand colors",
        "third-party trademarks", "copyrighted designs",
        "readable fake labels", "source video overlay text",

        # 产品一致性
        "product category drift", "wrong product color",
        "wrong product shape", "warped product geometry",
        "product morphing into different item",
        "inconsistent product across shots",

        # 人物一致性
        "mismatched wardrobe", "changing hairstyle",
        "inconsistent makeup", "different person each shot",
        "character inconsistency",

        # 质量/技术
        "extra fingers", "distorted hands", "deformed hands",
        "bad anatomy", "blurry", "low quality", "grainy",
        "overexposed", "underexposed", "harsh shadows",
        "over-smoothed skin", "AI plastic look",
        "flicker", "low-resolution artifacts",
        "watermark", "text artifacts", "unreadable text",

        # 场景/转场
        "sudden scene changes", "inconsistent lighting",
        "over-stylization", "cartoon rendering",
        "3D render", "illustration style",

        # 通用
        "cluttered background", "distracting elements",
        "nsfw", "violence", "gore",
    ]

    # === 默认人物 (来自SKILL.md) ===
    DEFAULT_CHARACTER_DESC = (
        "一位年轻成年女性美妆达人，干净自然妆容，长发，居家上衣，粉色美甲，"
        "在明亮卧室或浴室里对着手机前置镜头自然口播。表情真实、亲切、有种草感。"
        "动作和节奏参考原视频，但脸和身份完全不同于原视频人物。"
    )

    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.video_analyzer = VideoAnalyzer(ai_client)
        self.product_extractor = ProductExtractor(ai_client)
        self.character_extractor = CharacterExtractor(ai_client)

    # ================================================================
    # 主入口
    # ================================================================
    def execute(
        self,
        reference_video: Path,
        product_info: dict,
        character_info: dict = None,
        output_dir: Path = None,
    ) -> dict:
        """
        执行完整视频复刻工作流

        Args:
            reference_video: 参考视频路径
            product_info: 目标产品信息 (dict 或 Path -> product.json)
            character_info: 目标人物信息 (dict 或 Path -> character.json), None则用默认
            output_dir: 输出目录

        Returns:
            完整复刻包 dict，包含所有18个输出模块
        """
        if character_info is None:
            character_info = CharacterExtractor.default_character()

        if output_dir is None:
            output_dir = Path("./output/replication_output")

        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"=== Video Replication: {reference_video.name} ===")

        # Step 1: 视频分析
        video_analysis = self.video_analyzer.analyze_viral_elements(reference_video)
        shots = video_analysis.get("shot_analysis", {}).get("shots", [])
        metadata = video_analysis.get("metadata", {})

        # Step 2: 构建完整复刻包
        package = {
            "skill": "video_replication",
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "reference_video": str(reference_video),
            "metadata": metadata,
            "shots": shots,
        }

        # --- 模块1: 视频摘要 ---
        package["video_summary"] = self._module_video_summary(
            reference_video, metadata, shots, product_info, character_info
        )

        # --- 模块2: 原视频拆解 ---
        package["original_breakdown"] = self._module_original_breakdown(
            metadata, shots
        )

        # --- 模块3: 替换规则 ---
        package["replacement_rules"] = self._module_replacement_rules(
            product_info, character_info
        )

        # --- 模块3.5: 脚本生成 (基于视频分析的完整脚本) ---
        package["script"] = self._module_script_generation(
            shots, product_info, character_info, metadata, video_analysis
        )

        # --- 模块4: 分镜头时间表 ---
        package["shot_timing_table"] = self._module_shot_timing_table(
            shots, product_info, character_info, metadata
        )

        # --- 模块5: Storyboard 网格图提示词 ---
        package["storyboard_grid_prompt"] = self._module_storyboard_grid_prompt(
            shots, product_info, character_info
        )

        # --- 模块5.5: Storyboard 图生成 (PIL实际生成图片) ---
        storyboard_img_path = output_dir / "storyboard_grid.png"
        package["storyboard_grid_image"] = str(storyboard_img_path)
        self._module_storyboard_image(
            shots, product_info, character_info, storyboard_img_path
        )

        # --- 模块6: 提示图生成方案 ---
        package["prompt_image_plan"] = self._module_prompt_image_plan(
            shots, product_info, character_info
        )

        # --- 模块7: 通用视频生成提示词 ---
        package["general_video_prompt"] = self._module_general_video_prompt(
            shots, product_info, character_info, metadata
        )

        # --- 模块8: Seedance 分段版 ---
        package["seedance_segments"] = self._module_seedance_segments(
            shots, product_info, character_info, metadata
        )

        # --- 模块9: VEO3 完整版 ---
        package["veo3_prompt"] = self._module_veo3_prompt(
            shots, product_info, character_info, metadata
        )

        # --- 模块10: 即梦/云镜版本 ---
        package["jimeng_prompt"] = self._module_jimeng_prompt(
            shots, product_info, character_info, metadata
        )
        package["yunjing_prompt"] = self._module_yunjing_prompt(
            shots, product_info, character_info, metadata
        )

        # --- 模块11: 口播/字幕时间轴 ---
        package["voiceover_subtitle_timeline"] = self._module_voiceover_timeline(
            shots, product_info, character_info, metadata
        )

        # --- 模块12: 反向提示词 ---
        package["negative_prompts"] = self.NEGATIVE_PROMPTS

        # --- 模块13: 执行建议 ---
        package["execution_advice"] = self._module_execution_advice(
            shots, product_info, character_info
        )

        # 保存完整包
        self._save_package(package, output_dir)

        logger.info(f"Video Replication 完成 → {output_dir}")
        return package

    # ================================================================
    # 模块1: 视频摘要
    # ================================================================
    def _module_video_summary(self, video_path, metadata, shots, product, character) -> str:
        """视频摘要 - 用中文描述视频核心内容"""
        duration = metadata.get("duration", 0)
        product_name = product.get("product_name", "产品")
        brand = product.get("brand", "品牌")
        character_name = character.get("name", "人物")

        return f"""
## 视频摘要

**参考视频**: {video_path.name}
**时长**: {duration:.1f}秒
**镜头数**: {len(shots)}个
**分辨率**: {metadata.get('width', 0)}x{metadata.get('height', 0)}

**核心内容**:
这是一个{product_name}的TikTok产品展示/测评视频。视频采用经典的"Hook-问题-解决方案-效果展示-CTA"结构，
通过快速剪辑和卡点BGM保持高完播率。

**复刻目标**:
- 将原产品替换为 {brand} {product_name}
- 将原人物替换为 {character_name}
- 保留视频结构和节奏
- 保留Hook/CTA模式
- 适配新产品卖点

**关键数据**:
- 平均镜头时长: {sum(s['duration'] for s in shots)/max(len(shots),1):.1f}秒
- 视频节奏: {'快' if duration <= 15 else '中' if duration <= 30 else '慢'}
- 结构模式: Hook → Problem → Solution → Effect → CTA
"""

    # ================================================================
    # 模块2: 原视频拆解
    # ================================================================
    def _module_original_breakdown(self, metadata, shots) -> dict:
        """原视频拆解 — 逐镜头分析"""
        breakdown = {
            "total_duration": metadata.get("duration", 0),
            "total_shots": len(shots),
            "fps": metadata.get("fps", 0),
            "resolution": f"{metadata.get('width', 0)}x{metadata.get('height', 0)}",
            "shot_list": [],
        }

        for shot in shots:
            breakdown["shot_list"].append({
                "shot_id": shot["shot_id"],
                "time_range": f"{shot['start_time']:.1f}s - {shot['end_time']:.1f}s",
                "duration": shot["duration"],
                "estimated_type": shot.get("shot_type", "中景"),
                "inferred_content": self._infer_shot_content(shot),
                "inferred_camera": self._infer_shot_camera(shot),
                "inferred_purpose": self._infer_shot_purpose(shot, len(shots)),
            })

        return breakdown

    def _infer_shot_content(self, shot: dict) -> str:
        """基于真实镜头数据的智能内容推断"""
        sid = shot["shot_id"]
        dur = shot.get("duration", 2.0)
        shot_type = shot.get("shot_type", "")

        # 基于镜头类型推断
        if "特写" in shot_type or "ECU" in shot_type.upper():
            if dur <= 1.5:
                return "快切特写，视觉冲击Hook/转场"
            else:
                return "产品细节特写，突出质感与卖点"
        elif "近景" in shot_type or "CU" in shot_type.upper():
            return "近景展示，人物与产品互动，传递使用体验"
        elif "全景" in shot_type or "WS" in shot_type.upper():
            return "全景/远景，展示整体场景与环境氛围"
        else:
            # 基于位置推断
            if sid == 1:
                return "开场Hook — 产品/视觉冲击快速抓住注意力"
            elif sid <= 3:
                return "场景铺设 — 人物引入/问题展示/情绪铺垫"
            elif sid <= 6:
                return "产品展示 — 核心卖点演示/效果呈现"
            else:
                return "转化引导 — 效果强化/信任建立/CTA推进"

    def _infer_shot_camera(self, shot: dict) -> str:
        """
        基于镜头持续时间和类型的运镜推断
        短镜头→快切，长镜头→稳定运镜
        """
        dur = shot.get("duration", 2.0)
        shot_type = shot.get("shot_type", "")

        if dur <= 0.8:
            return "快速切换 / 跳切"
        elif dur <= 1.5:
            if "特写" in shot_type:
                return "快速推近 (Fast Push-in)"
            return "手持微晃 (Handheld)"
        elif dur <= 3.0:
            return "平滑跟随 / 缓慢推拉"
        elif dur <= 5.0:
            return "固定机位 / 稳定摇镜"
        else:
            return "缓慢全景 / 长镜头环绕"

    def _infer_shot_purpose(self, shot: dict, total_shots: int) -> str:
        """
        基于镜头在视频中位置的叙事目的推断
        """
        sid = shot["shot_id"]
        dur = shot.get("duration", 2.0)
        ratio = sid / max(total_shots, 1)

        if ratio <= 0.15:
            purpose = "Hook — 前3秒抓住注意力，降低划走率"
        elif ratio <= 0.35:
            purpose = "共鸣建立 — 铺设痛点/场景，建立情感连接"
        elif ratio <= 0.65:
            purpose = "价值传递 — 产品展示/卖点讲解/效果证明"
        elif ratio <= 0.85:
            purpose = "信任强化 — 使用效果/社交证明/差异化卖点"
        else:
            purpose = "CTA — 引导行动，降低决策门槛"

        # 叠加时长分析
        if dur <= 1.0 and ratio > 0.5:
            purpose += " (快节奏高潮点)"
        elif dur >= 4.0:
            purpose += " (沉浸式展示)"

        return purpose

    # ================================================================
    # 模块3: 替换规则
    # ================================================================
    def _module_replacement_rules(self, product, character) -> dict:
        """替换规则 — 明确什么替换、什么保留"""
        return {
            "keep": [
                "参考视频的镜头结构和节奏",
                "运镜方式和镜头语言",
                "动作逻辑和表演节奏",
                "场景氛围和光线风格",
                "口播逻辑和情绪节奏",
                "CTA模式和转化路径",
                "转场方式和卡点节奏",
            ],
            "replace": {
                "product": {
                    "original": "[原视频产品]",
                    "target": f"{product.get('brand', '')} {product.get('product_name', '')}",
                    "rules": [
                        "产品外观替换为目标产品",
                        f"产品颜色保持: {product.get('color', '')}",
                        f"产品包装保持: {product.get('packaging', '')}",
                        f"产品材质保持: {product.get('material', '')}",
                        "产品展示角度/光线保持一致",
                    ],
                },
                "character": {
                    "original": "[原视频人物]",
                    "target": character.get("name", "新人物"),
                    "rules": [
                        f"年龄: {character.get('age_range', '')}",
                        f"发型: {character.get('hair_style', '')}",
                        f"妆容: {character.get('makeup', '')}",
                        f"服装: {character.get('clothing', '')}",
                        "保持原视频动作和表情节奏",
                        "不复制原人物面部/身份/生物特征",
                    ],
                },
                "brand": {
                    "rules": [
                        "移除所有原品牌Logo",
                        "移除所有原品牌色（除非属于目标产品）",
                        "移除所有原包装文字",
                        "替换为目标产品品牌元素",
                        "不出现第三方商标",
                    ],
                },
                "script": {
                    "rules": [
                        f"产品名替换: [原名] → {product.get('product_name', '')}",
                        f"品牌名替换: [原品牌] → {product.get('brand', '')}",
                        "保留Hook结构和情绪张力",
                        "强化新产品差异化卖点",
                        "增加转化话术",
                    ],
                },
            },
            "forbidden": [
                "禁止复制原视频人物身份/面部/生物特征",
                "禁止保留原品牌Logo/包装文字/商标",
                "禁止改变目标产品类别/颜色/形状",
                "禁止改变目标人物基本特征",
                "禁止使用原视频受版权保护的音乐",
                "禁止出现可读的第三方标签/水印",
            ],
        }

    # ================================================================
    # 模块3.5: 脚本生成
    # ================================================================
    def _module_script_generation(self, shots, product, character, metadata, video_analysis) -> str:
        """
        基于真实视频分析生成完整视频脚本
        保留爆款结构 → 替换产品/品牌/人物 → 提高转化率
        """
        product_name = product.get("product_name", "产品")
        product_brand = product.get("brand", "品牌")
        product_color = product.get("color", "")
        product_packaging = product.get("packaging", "")
        product_material = product.get("material", "")
        features = product.get("key_features", [])
        features_str = "、".join(features) if features else "效果显著、品质出众"
        target_audience = product.get("target_audience", "追求品质的消费者")

        char_name = character.get("name", "人物")
        char_age = character.get("age_range", "25-30岁")
        char_gender = character.get("gender", "female")
        char_vibe = character.get("vibe", "亲切自然")
        char_hair = character.get("hair_style", "长发")
        char_makeup = character.get("makeup", "自然妆容")
        char_clothing = character.get("clothing", "简约上衣")

        duration = metadata.get("duration", 15)
        total_shots = len(shots)

        # 基于视频分析确定结构数据
        structure = video_analysis.get("structure", {})
        pacing = video_analysis.get("pacing", {})
        hook_info = video_analysis.get("hook_analysis", {})
        cta_info = video_analysis.get("cta_analysis", {})

        # 计算各段时间分配
        if total_shots >= 5:
            hook_end = shots[0]["end_time"] if total_shots > 0 else min(3, duration)
            problem_start = shots[0]["end_time"] if total_shots > 0 else 3
            problem_end = shots[min(2, total_shots-1)]["end_time"] if total_shots > 2 else duration * 0.5
            product_start = problem_end
            product_end = shots[min(total_shots-2, total_shots-1)]["end_time"] if total_shots > 3 else duration - 5
            cta_start = max(product_end, duration - 5)
        else:
            hook_end = duration * 0.2
            problem_start = hook_end
            problem_end = duration * 0.5
            product_start = problem_end
            product_end = duration * 0.75
            cta_start = product_end

        # 构建口播 — 基于产品特征定制
        hook_lines = [
            f"天呐！这个{product_name}也太好用了吧！",
            f"姐妹们！我挖到宝了！{product_brand}新出的这个{product_name}绝了！",
            f"不是广！这个{product_name}真的让我惊了...",
            f"如果你也...那一定要看看这个{product_name}！",
        ]

        problem_lines = [
            f"你是不是也遇到过...之前试过好多产品都没用？",
            f"我以前也是，直到我发现了{product_brand}的这个{product_name}！",
            f"说真的，用过那么多{product.get('category', '产品')}，只有这个让我回购！",
        ]

        product_lines = [
            f"你看这个{features_str}，而且它是{product_color}色的{product_packaging}包装，{product_material}材质，质感绝了！",
            f"我使用了X天，效果真的肉眼可见！{features_str}名不虚传！",
            f"它的设计也很贴心，{product_packaging}包装方便携带，随时随地都能用！",
        ]

        cta_lines = [
            f"赶紧去试试吧！链接我放在主页了，现在下单还有限时优惠！",
            f"相信我，{target_audience}一定不要错过！主页有链接！",
            f"限时优惠进行中，错过等一年！快冲！",
        ]

        # 动态选取口播 (基于镜头位置)
        hook_text = hook_lines[hash(product_name) % len(hook_lines)]
        problem_text = problem_lines[hash(product_brand) % len(problem_lines)]
        product_text = product_lines[hash(features_str) % len(product_lines)]
        cta_text = cta_lines[hash(char_name) % len(cta_lines)]

        return f"""# 视频脚本

## 基本信息
- 产品：{product_brand} {product_name}
- 品类：{product.get('category', '通用')}
- 人物：{char_name} ({char_age} {char_gender}, {char_vibe})
- 时长：{duration:.0f}秒
- 镜头数：{total_shots}个
- 节奏：{pacing.get('overall', '快节奏')}
- 结构模式：{structure.get('pattern', 'Hook→Problem→Solution→CTA')}

## 人物设定
- 姓名/代号：{char_name}
- 年龄：{char_age}
- 发型：{char_hair}
- 妆容：{char_makeup}
- 服装：{char_clothing}
- 气质：{char_vibe}
- 特征：{', '.join(character.get('distinctive_features', ['自然亲切']))}

## 产品设定
- 产品名：{product_name}
- 品牌：{product_brand}
- 颜色：{product_color}
- 包装：{product_packaging}
- 材质：{product_material}
- 核心卖点：{features_str}
- 目标用户：{target_audience}

---

## Hook (0-{hook_end:.0f}秒) — 开头黄金3秒

**[口播文案]**
"{hook_text}"

**[画面描述]**
产品{product_name}特写镜头。{product_color}色的{product_packaging}包装在柔光下展现质感。
快速推镜从产品包装到产品本身，深色/干净背景突出主体。
画面节奏紧凑，前0.5秒完成镜头切入。

**[字幕]**
🔥 {product_brand} {product_name} | 宝藏发现！

**[Hook分析]**
类型：{hook_info.get('type', '视觉冲击+好奇心')}
有效性：{hook_info.get('effectiveness', '高')}
关键：前3秒内完成产品惊艳亮相

---

## 问题/场景 ({problem_start:.0f}-{problem_end:.0f}秒)

**[口播文案]**
"{problem_text}"

**[画面描述]**
人物{char_name}中景/近景出镜。{char_hair}、{char_makeup}、{char_clothing}。
面对手机前置镜头（模拟自拍视角），展示真实使用场景。
自然光线（窗光或环形灯），温馨生活化环境，浅景深虚化背景。
人物表情{char_vibe}，真实不做作。

**[字幕]**
❌ 试过N种方法都不管用？→ ✅ 终于找到解决方案！

---

## 产品展示/效果 ({product_start:.0f}-{product_end:.0f}秒)

**[口播文案]**
"{product_text}"

**[画面描述]**
人物手持{product_name}，展示产品细节和使用方法。
近景+特写镜头交替：产品特写→人物使用→效果展示→产品卖点。
{product_color}色{product_packaging}在侧逆光下展现{product_material}质感。
可能包含Before/After对比画面。

**[字幕]**
✨ {features_str}
💎 {product_brand} {product_name} | {product_color}色{product_packaging}

---

## CTA ({cta_start:.0f}-{duration:.0f}秒)

**[口播文案]**
"{cta_text}"

**[画面描述]**
人物{char_name}微笑面对镜头，手持{product_name}。
产品{product_name}在画面中央/前景，Logo清晰可见。
白色/干净明亮背景，正面柔光。
屏幕叠加优惠信息/链接提示/限时标签动画。

**[字幕]**
🛒 限时优惠，错过等一年 | 👇 主页链接

**[CTA分析]**
类型：{cta_info.get('type', 'link_in_bio + 限时紧迫')}
策略：限时优惠 + 社交证明 + 低门槛行动

---

## 节奏与情绪

| 时间段 | 情绪 | 强度 | 镜头节奏 |
|--------|------|------|----------|
| 0-{hook_end:.0f}s | 好奇心/惊喜 | 8/10 | 极快 |
| {hook_end:.0f}-{problem_end:.0f}s | 共鸣/信任 | 5/10 | 正常 |
| {problem_end:.0f}-{product_end:.0f}s | 兴奋/信任 | 7/10 | 快 |
| {product_end:.0f}-{duration:.0f}s | 信任/紧迫 | 8/10 | 正常→快 |

## 转化优化
- **卖点强化**: Hook阶段直接展示最佳效果，中间用{features_str}具体说明
- **信任背书**: 真实使用场景 + Before/After对比 + 产品细节实拍
- **紧迫感**: 限时优惠 + 社交证明（"我也在用"）+ 低门槛（"链接在主页"）

## 一致性要求
- 人物{char_name}全视频保持同一发型、妆容、服装、年龄感
- 产品{product_brand} {product_name}全视频保持同一颜色、包装、品牌元素
- 禁止出现原视频人物、品牌、Logo
"""
    # ================================================================
    # 模块4: 分镜头时间表
    # ================================================================
    def _module_shot_timing_table(self, shots, product, character, metadata) -> list[dict]:
        """分镜头时间表 — 逐镜头详细编排"""
        product_name = product.get("product_name", "产品")
        product_brand = product.get("brand", "品牌")
        character_name = character.get("name", "人物")
        char_vibe = character.get("vibe", "亲切")

        table = []
        # 镜头类型序列
        framing = ["特写/ECU", "中景/MS", "近景/CU", "特写/ECU", "中景/MS", "近景/CU", "全景/WS", "特写/ECU"]
        camera_moves = ["快速推镜", "手持跟随", "缓慢拉远", "快速摇镜", "推近特写", "固定机位", "缓慢环绕", "固定+变焦推"]
        transitions = ["硬切", "硬切", "硬切", "闪白转场", "硬切", "硬切", "硬切", "淡出"]

        voiceover_lines = [
            f"天呐！这个{product_name}也太好用了吧！",
            f"你是不是也遇到过这个问题？",
            f"直到我发现了{product_brand}的这个{product_name}！",
            f"你看这个质感和效果，真的太惊艳了！",
            f"用了之后完全是两个样子！",
            f"而且它的设计也很贴心...",
            f"我已经用了X天了，效果真的明显！",
            f"赶紧去试试吧！链接在主页，现在还有限时优惠！",
        ]

        subtitle_lines = [
            f"🔥 宝藏{product_name}！",
            f"❌ 试过N种方法？",
            f"✅ {product_brand} {product_name}",
            f"✨ 效果太惊艳",
            f"💯 真实测评对比",
            f"💎 {product_name}细节",
            f"📸 X天使用效果",
            "🛒 限时优惠·主页",
        ]

        for i, shot in enumerate(shots):
            idx = i % len(framing)
            table.append({
                "shot_id": shot["shot_id"],
                "timestamp": f"{shot['start_time']:.1f}s - {shot['end_time']:.1f}s",
                "duration_sec": shot["duration"],
                "framing": framing[idx],
                "camera_movement": camera_moves[idx],
                "action": self._build_shot_action(i, len(shots), product_name, character_name),
                "product_placement": "画面中央" if i % 2 == 0 else "前景右侧/手持展示",
                "character_action": f"{character_name}自然展示，表情{char_vibe}" if i > 0 else "产品特写为主",
                "voiceover": voiceover_lines[i % len(voiceover_lines)],
                "subtitle": subtitle_lines[i % len(subtitle_lines)],
                "transition": transitions[idx],
                "replacement_note": f"产品→{product_name}，人物→{character_name}，品牌→{product_brand}",
            })

        return table

    def _build_shot_action(self, index: int, total: int, product_name: str, character_name: str) -> str:
        if index == 0:
            return f"产品{product_name}特写快速出现，光线闪烁突出质感，Hook开场"
        elif index == total - 1:
            return f"人物微笑面对镜头，手持{product_name}，屏幕弹出优惠信息和CTA按钮"
        elif index <= total * 0.3:
            return f"人物({character_name})面对镜头展示使用场景，自然光线，真实环境"
        elif index <= total * 0.7:
            return f"产品{product_name}细节展示，人物演示使用方法，镜头聚焦产品卖点"
        else:
            return f"使用前后对比效果展示，快速切换突出变化，情绪高潮"

    # ================================================================
    # 模块5: Storyboard 网格图提示词
    # ================================================================
    def _module_storyboard_grid_prompt(self, shots, product, character) -> str:
        """Storyboard网格图提示词 (给Codex/DALL-E等图片生成工具)"""
        product_name = product.get("product_name", "产品")
        product_brand = product.get("brand", "品牌")
        product_color = product.get("color", "")
        product_packaging = product.get("packaging", "")
        char_desc = self._build_character_visual_desc(character)

        panels = min(len(shots), 9)
        grid_layout = {4: "2x2", 6: "2x3", 8: "2x4", 9: "3x3"}.get(panels, f"{panels}-panel")

        prompt = f"""A {grid_layout} storyboard grid for a TikTok-style product video. Each panel is a keyframe.

CHARACTER (consistent across ALL panels):
{char_desc}

PRODUCT (consistent across ALL panels):
{product_brand} {product_name}, {product_color} color, {product_packaging} packaging. Accurate to the target product in every panel.

STYLE:
Photorealistic, cinematic lighting, vertical 9:16 composition, warm color grading.
Clean modern aesthetic. Each panel labeled with shot number.

CONTENT PER PANEL:
"""
        for i, shot in enumerate(shots[:panels]):
            framing = ["ECU", "MS", "CU", "ECU", "MS", "CU", "WS", "ECU"][i % 8]
            prompt += f"Panel {i+1}: Shot {shot['shot_id']} ({framing}) — product showcase, natural pose, clean background\n"

        prompt += f"""
NEGATIVE: {', '.join(self.NEGATIVE_PROMPTS[:10])}
NO original logos. NO original person face. NO readable third-party text.
"""
        return prompt

    def _build_character_visual_desc(self, character: dict) -> str:
        c = character
        return (
            f"{c.get('age_range', '25-30岁')} {c.get('gender', 'female')}, "
            f"{c.get('skin_tone', '自然肤色')}, "
            f"{c.get('hair_style', '长发')} {c.get('hair_color', '黑色')}, "
            f"{c.get('makeup', '自然妆容')}, "
            f"wearing {c.get('clothing', '简约上衣')}, "
            f"{c.get('body_type', '苗条')} build, "
            f"{c.get('vibe', '亲切自然')} vibe, "
            f"{c.get('expression', '自然微笑')}"
        )

    # ================================================================
    # 模块5.5: Storyboard 图生成 (PIL实际生成图片)
    # ================================================================
    def _module_storyboard_image(self, shots, product, character, output_path: Path):
        """
        使用PIL生成实际Storyboard网格图
        输出: storyboard_grid.png — 可直接用于Seedance参考
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            logger.warning("PIL未安装，跳过Storyboard图片生成。安装: pip install Pillow")
            # 创建占位文本文件
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.with_suffix(".txt").write_text(
                f"Storyboard Grid — {len(shots)} shots\n"
                f"Product: {product.get('product_name', 'N/A')}\n"
                f"Character: {character.get('name', 'N/A')}\n"
                f"(PIL not available — install Pillow for image generation)\n"
            )
            return

        product_name = product.get("product_name", "产品")
        product_color = product.get("color", "")
        char_name = character.get("name", "人物")

        n_shots = min(len(shots), 8)
        # 网格布局
        if n_shots <= 2:
            cols, rows = n_shots, 1
        elif n_shots <= 4:
            cols, rows = 2, 2
        elif n_shots <= 6:
            cols, rows = 3, 2
        else:
            cols, rows = 4, 2

        # 画布 — 9:16竖屏比例
        cell_w, cell_h = 540, 960
        padding = 40
        header_h = 120
        footer_h = 60

        canvas_w = cols * cell_w + (cols + 1) * padding
        canvas_h = rows * cell_h + (rows + 1) * padding + header_h + footer_h

        # 配色
        bg_color = "#0d1117"
        cell_bg = "#161b22"
        border_color = "#30363d"
        accent_color = "#e94560"
        text_color = "#c9d1d9"
        dim_color = "#8b949e"

        img = Image.new("RGB", (canvas_w, canvas_h), bg_color)
        draw = ImageDraw.Draw(img)

        # 字体
        try:
            font_title = ImageFont.truetype("arial.ttf", 36)
            font_shot = ImageFont.truetype("arial.ttf", 28)
            font_body = ImageFont.truetype("arial.ttf", 20)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            font_title = ImageFont.load_default()
            font_shot = ImageFont.load_default()
            font_body = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # 标题
        title = f"STORYBOARD — {product_name}"
        draw.text((padding, 20), title, fill=accent_color, font=font_title)
        draw.text((padding, 65), f"Character: {char_name} | Shots: {n_shots} | 9:16 Vertical", fill=dim_color, font=font_small)
        draw.line([(padding, 110), (canvas_w - padding, 110)], fill=border_color, width=1)

        # 运镜标签
        camera_labels = [
            "ECU Push-in", "MS Handheld", "CU Pull-out", "ECU Whip Pan",
            "MS Dolly", "CU Static", "WS Orbit", "ECU Zoom",
        ]
        # 景别标签
        framing_labels = [
            "EXTREME CLOSE-UP", "MEDIUM SHOT", "CLOSE-UP", "EXTREME CLOSE-UP",
            "MEDIUM SHOT", "CLOSE-UP", "WIDE SHOT", "EXTREME CLOSE-UP",
        ]

        for i in range(n_shots):
            row = i // cols
            col = i % cols

            x = padding + col * (cell_w + padding)
            y = header_h + padding + row * (cell_h + padding)

            shot = shots[i] if i < len(shots) else None
            shot_id = shot["shot_id"] if shot else i + 1

            # 单元格背景
            draw.rectangle([x, y, x + cell_w, y + cell_h], fill=cell_bg, outline=border_color, width=2)

            # 镜头编号角标
            badge_w, badge_h = 50, 50
            draw.rectangle([x, y, x + badge_w, y + badge_h], fill=accent_color)
            draw.text((x + 12, y + 8), f"S{shot_id}", fill="white", font=font_shot)

            # 景别标签
            fl = framing_labels[i % len(framing_labels)]
            draw.text((x + 60, y + 14), fl, fill=dim_color, font=font_small)

            # 运镜
            cm = camera_labels[i % len(camera_labels)]
            draw.text((x + 20, y + cell_h - 130), cm, fill=accent_color, font=font_body)

            # 画面描述 (简化)
            if i == 0:
                desc = f"Product reveal\n{product_name}\n{product_color}"
            elif i == n_shots - 1:
                desc = f"CTA Finale\n{char_name} + product\nLink overlay"
            else:
                desc = f"Shot {shot_id}\n{char_name}\ndemonstrating"

            for li, line in enumerate(desc.split("\n")):
                draw.text((x + 20, y + cell_h - 100 + li * 24), line, fill=text_color, font=font_body)

            # 时间戳
            if shot:
                ts = f"{shot['start_time']:.1f}s - {shot['end_time']:.1f}s"
                draw.text((x + 20, y + cell_h - 30), ts, fill=dim_color, font=font_small)

            # 预览框 (占位矩形表示画面)
            preview_margin = 60
            preview_x = x + preview_margin
            preview_y = y + 80
            preview_w = cell_w - 2 * preview_margin
            preview_h = cell_h - 240
            draw.rectangle(
                [preview_x, preview_y, preview_x + preview_w, preview_y + preview_h],
                fill="#21262d", outline="#30363d", width=1
            )
            # 交叉线表示取景
            cx, cy = preview_x + preview_w // 2, preview_y + preview_h // 2
            draw.line([(cx - 30, cy), (cx + 30, cy)], fill=border_color, width=1)
            draw.line([(cx, cy - 40), (cx, cy + 40)], fill=border_color, width=1)
            # 9:16比例指示
            aspect_w, aspect_h = 40, 71
            draw.rectangle(
                [cx - aspect_w//2, cy - aspect_h//2, cx + aspect_w//2, cy + aspect_h//2],
                outline=dim_color, width=1
            )

        # 底部信息
        footer_y = canvas_h - footer_h + 10
        draw.line([(padding, footer_y - 5), (canvas_w - padding, footer_y - 5)], fill=border_color, width=1)
        draw.text((padding, footer_y),
                  f"Seedance Reference | Product: {product_name} | Consistent character & product across all shots",
                  fill=dim_color, font=font_small)

        # 保存
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, quality=95)
        logger.info(f"Storyboard grid image saved: {output_path} ({canvas_w}x{canvas_h})")

    # ================================================================
    # 模块6: 提示图生成方案
    # ================================================================
    def _module_prompt_image_plan(self, shots, product, character) -> dict:
        """提示图生成方案 — 4类图的规定"""
        return {
            "deliverables": [
                {
                    "name": "storyboard_grid",
                    "description": "多面板网格图，每个面板一个关键帧",
                    "panels": min(len(shots), 9),
                    "usage": "Seedance顶层视觉参考，整体规划用",
                },
                {
                    "name": "seedance_keyframes",
                    "description": "逐镜关键帧表，每个面板对应一个Seedance分段",
                    "panels": len(shots),
                    "usage": "与Seedance分段Prompt 1对1匹配使用",
                },
                {
                    "name": "product_replacement_reference",
                    "description": "产品精度参考图：单独产品、手持产品、场景中产品",
                    "angles": ["正面", "45度", "手持", "使用中"],
                    "usage": "确保所有镜头中产品保持一致",
                },
                {
                    "name": "character_consistency_reference",
                    "description": "人物一致性参考图：口播姿态、演示姿态、手持产品、CTA姿态",
                    "poses": ["正面口播", "侧面演示", "手持产品", "CTA微笑"],
                    "usage": "确保所有镜头中人物保持一致",
                },
            ],
            "image_generation_priority": [
                "seedance_keyframes (最高优先级)",
                "storyboard_grid",
                "product_replacement_reference",
                "character_consistency_reference",
            ],
            "output_format": "PNG, 9:16 vertical, 4K quality",
            "style": "Photorealistic, cinematic, consistent lighting across all images",
        }

    # ================================================================
    # 模块7: 通用视频生成提示词
    # ================================================================
    def _module_general_video_prompt(self, shots, product, character, metadata) -> str:
        """通用视频生成提示词"""
        product_name = product.get("product_name", "产品")
        brand = product.get("brand", "品牌")
        duration = metadata.get("duration", 15)
        char_desc = self._build_character_visual_desc(character)
        features = product.get("key_features", [])
        features_str = "、".join(features) if features else "效果显著"

        return f"""# 通用视频生成提示词

## 视频概览
- 时长: {duration:.0f}秒
- 格式: 9:16竖屏 (1080x1920)
- 风格: 超写实电影感 / TikTok产品展示
- FPS: 30

## 完整场景描述

一个{duration:.0f}秒的TikTok产品展示视频，展示 **{brand} {product_name}**。

### 开场Hook (0-3s)
产品特写，快速推镜，{product_name}在柔光下展现出{product.get('color', '')}色的{product.get('packaging', '')}包装质感。深色背景突出产品。节奏快速，视觉冲击力强。

### 问题引入 (3-8s)
人物({character.get('name', '')})中景出镜，面对镜头展示使用场景。{char_desc}。自然光线，温馨真实的环境。建立情感共鸣。

### 产品展示 (8-{duration-5:.0f}s)
人物手持{product_name}，展示核心卖点: **{features_str}**。近景+特写交替，展示产品细节和使用效果。侧逆光勾勒质感。

### CTA引导 ({duration-5:.0f}-{duration:.0f}s)
人物微笑面对镜头，{product_name}居中展示。干净明亮的背景。弹出优惠信息和链接引导。温暖自信的结尾。

## 视觉风格
- 色调: 暖色为主，电影级调色
- 光线: 柔光+逆光轮廓
- 景深: 浅景深突出主体
- 运镜: 平滑稳定，关键节点推镜加强
- 字幕: 现代无衬线字体，弹入动画

## 音频
- BGM: TikTok热门电子/流行卡点音乐
- 口播: 热情自信的中文女声/男声
- 音效: 转场轻音效 + 文字弹出音效

## 人物一致性
{self.character_extractor.generate_consistency_description(character)[:300]}

## 产品一致性
{self.product_extractor.generate_consistency_description(product)}
"""

    # ================================================================
    # 模块8: Seedance 分段版
    # ================================================================
    def _module_seedance_segments(self, shots, product, character, metadata) -> list[dict]:
        """Seedance分段版 — 每个镜头独立Prompt"""
        product_name = product.get("product_name", "产品")
        product_color = product.get("color", "")
        char_name = character.get("name", "人物")
        char_hair = character.get("hair_style", "长发")
        char_clothing = character.get("clothing", "简约上衣")
        char_vibe = character.get("vibe", "亲切自然")

        segments = []

        camera_moves_en = [
            "Fast push-in from medium to extreme close-up, smooth and energetic",
            "Smooth handheld follow with subtle natural bounce",
            "Slow pull-out reveal, starting from detail expanding to full scene",
            "Quick whip pan, dynamic energy transition",
            "Steady dolly push-in, cinematic smooth motion",
            "Locked-off tripod, stable confident framing",
            "Slow orbiting arc around subject, gentle parallax",
            "Fixed with slow zoom in on product detail",
        ]

        for i, shot in enumerate(shots):
            cm = camera_moves_en[i % len(camera_moves_en)]
            is_first = (i == 0)
            is_last = (i == len(shots) - 1)

            # 正面Prompt
            positive = (
                f"Shot {shot['shot_id']}: "
                f"Cinematic product video segment, {shot['duration']:.1f} seconds. "
                f"Camera: {cm}. "
                f"Subject: {char_name}, {char_hair}, {char_clothing}, {char_vibe} expression. "
                f"Product: {product_name}, {product_color} color, centered and clear. "
                f"Lighting: Soft key light from 45-degree left, warm rim light from behind, "
                f"clean modern background. "
                f"Action: {'Eye-catching product reveal, dynamic opening hook' if is_first else 'Natural confident CTA, warm smile, product proudly displayed' if is_last else 'Natural product demonstration, genuine interaction'}. "
                f"Mood: Professional yet approachable, high-energy social media feel. "
                f"Color: Warm teal and orange grade, slightly boosted saturation. "
                f"9:16 vertical framing, 30fps, photorealistic."
            )

            # 负面Prompt
            negative = (
                "original person face, original logo, original brand, "
                "deformed hands, extra fingers, bad anatomy, "
                "blurry, low quality, grainy, watermark, text artifacts, "
                "product morphing, inconsistent character, inconsistent product, "
                "over-smoothed skin, AI plastic look, flicker, warped geometry, "
                "cartoon, 3D render, illustration, over-stylized"
            )

            segments.append({
                "segment": shot["shot_id"],
                "timestamp": f"{shot['start_time']:.1f}s - {shot['end_time']:.1f}s",
                "duration_sec": shot["duration"],
                "reference_image": f"keyframe_{shot['shot_id']:03d}.jpg",
                "positive_prompt": positive,
                "negative_prompt": negative,
                "camera_movement": cm,
                "subtitle_cue": f"Shot {shot['shot_id']} subtitle overlay",
                "continuity_anchor": (
                    f"SAME person ({char_name}, {char_hair}, {char_clothing}), "
                    f"SAME product ({product_name}, {product_color}), "
                    f"SAME lighting, SAME setting"
                ),
            })

        return segments

    # ================================================================
    # 模块9: VEO3 完整版
    # ================================================================
    def _module_veo3_prompt(self, shots, product, character, metadata) -> dict:
        """VEO3完整版 — 一个完整视频Prompt + 独立Negative Prompt"""
        product_name = product.get("product_name", "产品")
        brand = product.get("brand", "品牌")
        duration = metadata.get("duration", 15)
        char_name = character.get("name", "人物")

        # 构建场景序列
        scene_sequence = ""
        for i, shot in enumerate(shots):
            scene_sequence += (
                f"  [{shot['start_time']:.1f}s-{shot['end_time']:.1f}s] "
                f"Shot {shot['shot_id']}: "
            )
            if i == 0:
                scene_sequence += f"ECU product reveal, fast push-in, {product_name} glows under soft light\n"
            elif i == len(shots) - 1:
                scene_sequence += f"MS {char_name} smiles warmly, {product_name} centered, CTA text overlay, clean white bg\n"
            else:
                scene_sequence += f"MS/CU {char_name} demonstrates {product_name}, natural light, lifestyle setting\n"

        positive = f"""A {duration:.0f}-second TikTok-style product showcase video for {brand} {product_name}.

Vertical 9:16 (1080x1920), 30fps, hyper-realistic cinematic quality.

SCENE SEQUENCE:
{scene_sequence}

VISUAL STYLE:
- Color grading: Warm teal and orange, cinematic look
- Lighting: Soft key + rim light, depth and dimension
- Depth of field: Shallow for product shots, moderate for person
- Text overlays: Bold modern sans-serif, pop-in animation style
- Transitions: Hard cuts with occasional whip pan for energy

AUDIO:
- Background: Upbeat trending TikTok electronic/pop
- Voiceover: Enthusiastic confident Chinese female voice
- Sound FX: Subtle whoosh transitions, click for text pop-ins

CHARACTER: {char_name}, consistent appearance throughout.
PRODUCT: {brand} {product_name}, accurate and consistent in every scene.
"""

        negative = "original celebrity face, original influencer identity, original logo, original packaging text, original brand colors, product category drift, extra fingers, distorted hands, deformed anatomy, unreadable labels, random text artifacts, mismatched wardrobe, inconsistent character, inconsistent product, sudden scene changes, over-smoothed skin, AI plastic look, flicker, warped product geometry, low-resolution artifacts, watermark, cartoon, 3D render, illustration"

        return {
            "duration": duration,
            "format": "9:16 vertical, 30fps, 1080x1920",
            "positive_prompt": positive,
            "negative_prompt": negative,
        }

    # ================================================================
    # 模块10: 即梦/云镜版本
    # ================================================================
    def _module_jimeng_prompt(self, shots, product, character, metadata) -> str:
        """即梦版本 — 直接中文视觉描述"""
        product_name = product.get("product_name", "产品")
        brand = product.get("brand", "品牌")
        product_color = product.get("color", "")
        char_name = character.get("name", "人物")

        shot_descs = []
        for i, shot in enumerate(shots):
            if i == 0:
                desc = (f"镜头{shot['shot_id']}({shot['start_time']:.0f}-{shot['end_time']:.0f}秒): "
                        f"产品特写，快速推镜，{product_color}色{product_name}在柔光下闪耀，"
                        f"深色背景突出质感，字幕弹出")
            elif i == len(shots) - 1:
                desc = (f"镜头{shot['shot_id']}({shot['start_time']:.0f}-{shot['end_time']:.0f}秒): "
                        f"人物微笑面对镜头，{product_name}画面中央，白色干净背景，CTA文字")
            else:
                desc = (f"镜头{shot['shot_id']}({shot['start_time']:.0f}-{shot['end_time']:.0f}秒): "
                        f"中景/近景，{char_name}展示{product_name}，自然光线，"
                        f"温馨场景，产品清晰可见")
            shot_descs.append(desc)

        return f"""# 即梦视频生成 Prompt

## 项目信息
- 产品: {brand} {product_name}
- 风格: 超写实电影感 / TikTok竖屏
- 分辨率: 1080x1920 (9:16)

## 人物一致性
{character.get('age_range', '')} {character.get('gender', '')}，
{character.get('hair_style', '')} {character.get('hair_color', '')}，
{character.get('makeup', '')}，{character.get('clothing', '')}。
所有镜头同一人物。

## 产品一致性
{product_color}色{product.get('packaging', '')}包装的{product_name}。
所有镜头同一产品，同一包装，同一颜色。

## 镜头序列
{chr(10).join(shot_descs)}

## 全局参数
- 视频风格: 写实
- 色彩: 暖色调，电影级调色
- 光线: 柔光+逆光
- 转场: 硬切
- BGM: 快节奏卡点电子

## 负面提示词
原视频人物面孔, 原品牌Logo, 原包装文字, 多余手指, 畸形手部,
模糊, 低画质, 水印, 产品变形, 人物不一致, 产品不一致,
过度磨皮, AI塑料感, 闪烁, 几何扭曲
"""

    def _module_yunjing_prompt(self, shots, product, character, metadata) -> str:
        """云镜版本"""
        product_name = product.get("product_name", "产品")
        brand = product.get("brand", "品牌")

        return f"""# 云镜视频生成 Prompt

一段{brand}{product_name}的TikTok产品展示视频，{metadata.get('duration', 15):.0f}秒，9:16竖屏。

## 视觉风格
超写实电影感，暖色调调色，柔光+自然光，浅景深，画面干净高级。

## 镜头序列
{self._build_jimeng_shot_sequence(shots, product, character)}

## 人物
{character.get('name', '人物')}，{character.get('age_range', '')}，
{character.get('hair_style', '')}，{character.get('clothing', '')}，
贯穿全视频保持一致。

## 产品
{brand}{product_name}，{product.get('color', '')}色，
{product.get('packaging', '')}包装，所有镜头保持一致。

## 全局参数
写实风格、暖色调、快节奏卡点、硬切转场
"""

    def _build_jimeng_shot_sequence(self, shots, product, character) -> str:
        lines = []
        for i, shot in enumerate(shots):
            if i == 0:
                lines.append(f"镜头{shot['shot_id']}: Hook开场，产品特写推镜")
            elif i == len(shots) - 1:
                lines.append(f"镜头{shot['shot_id']}: CTA结尾，人物微笑展示产品")
            else:
                lines.append(f"镜头{shot['shot_id']}: 人物自然展示产品")
        return "\n".join(lines)

    # ================================================================
    # 模块11: 口播/字幕时间轴
    # ================================================================
    def _module_voiceover_timeline(self, shots, product, character, metadata) -> dict:
        """口播/字幕时间轴"""
        product_name = product.get("product_name", "产品")
        brand = product.get("brand", "品牌")

        voiceover_lines = [
            f"天呐！这个{product_name}也太好用了吧！",
            f"你是不是也遇到过...之前试过好多产品都没用",
            f"直到我发现了{brand}的这个{product_name}",
            f"你看这个质感和效果",
            f"用了之后真的太惊艳了",
            f"而且它的设计也很贴心",
            f"我已经用了好几天了，效果真的明显",
            "赶紧去试试吧！链接在主页，现在还有限时优惠！",
        ]

        subtitle_lines = [
            f"🔥 发现宝藏{product_name}！",
            f"❌ 试过N种方法？都不管用？",
            f"✅ 终于找到{product_name}",
            f"✨ 效果太惊艳了",
            f"💯 真实测评对比",
            f"💎 {brand}品质保证",
            f"📸 效果持续在线",
            "🛒 限时优惠·错过等一年",
        ]

        timeline = []
        for i, shot in enumerate(shots):
            idx = i % len(voiceover_lines)
            timeline.append({
                "shot_id": shot["shot_id"],
                "time_range": f"{shot['start_time']:.1f}s - {shot['end_time']:.1f}s",
                "voiceover": voiceover_lines[idx],
                "subtitle": subtitle_lines[idx],
                "voice_tone": "热情自信" if i < 3 else "真诚推荐" if i < len(shots) - 1 else "温暖引导",
                "speaking_speed": "快速" if i == 0 else "正常" if i < len(shots) - 2 else "稍慢",
            })

        return {
            "language": "中文",
            "voice_tone_overall": "热情、自信、有种草感",
            "total_segments": len(timeline),
            "segments": timeline,
        }

    # ================================================================
    # 模块13: 执行建议
    # ================================================================
    def _module_execution_advice(self, shots, product, character) -> str:
        product_name = product.get("product_name", "产品")
        brand = product.get("brand", "品牌")
        char_name = character.get("name", "人物")

        return f"""
## 执行建议

### Seedance 使用流程
1. 将 Keyframe 图片上传到 Seedance
2. 每个分段使用对应的 positive_prompt + negative_prompt
3. 确保每个分段开头包含 continuity_anchor
4. 共 {len(shots)} 个分段，按顺序生成后拼接

### VEO3 使用
1. 直接使用完整 positive_prompt
2. 附带 negative_prompt
3. 期望生成完整的 {len(shots)} 镜头视频

### 即梦/云镜 使用
1. 逐镜头生成后拼接
2. 每个镜头保持人物/产品一致性描述

### 质量检查清单
- [ ] 产品 {brand} {product_name} 在所有镜头中保持一致
- [ ] 人物 {char_name} 在所有镜头中保持一致
- [ ] 无原视频人物面部/身份
- [ ] 无原品牌Logo/包装文字
- [ ] 产品类别/颜色/形状正确
- [ ] 镜头节奏符合参考视频
- [ ] Hook在3秒内抓住注意力
- [ ] CTA清晰可行动
- [ ] 字幕时间轴与口播同步
- [ ] BGM节奏匹配视频卡点

### 注意事项
- 使用 Seedance 时，分段越多控制越精确，但拼接越复杂
- VEO3 适合生成完整视频，但单个镜头的精细控制不如 Seedance
- 始终保持 negative_prompt 中包含原视频人物和品牌的排除项
- 如果生成结果中出现产品变形，加强 negative_prompt 中的 "warped product geometry"
- 如果人物不一致，在每段 positive_prompt 开头重复人物描述
"""

    # ================================================================
    # 保存
    # ================================================================
    def _save_package(self, package: dict, output_dir: Path):
        """保存完整复刻包"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存完整JSON
        json_path = output_dir / "replication_package.json"
        # 移除过大的二进制数据后保存
        saveable = {}
        for k, v in package.items():
            try:
                json.dumps({k: v}, ensure_ascii=False)
                saveable[k] = v
            except (TypeError, ValueError):
                saveable[k] = str(v)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(saveable, f, ensure_ascii=False, indent=2)
        logger.info(f"复刻包已保存: {json_path}")

        # 保存各模块为独立文件
        text_exports = {
            "01_video_summary.md": package.get("video_summary", ""),
            "02_original_breakdown.json": package.get("original_breakdown", {}),
            "03_replacement_rules.json": package.get("replacement_rules", {}),
            "03_script.md": package.get("script", ""),
            "04_shot_timing_table.json": package.get("shot_timing_table", []),
            "05_storyboard_grid_prompt.txt": package.get("storyboard_grid_prompt", ""),
            "06_prompt_image_plan.json": package.get("prompt_image_plan", {}),
            "07_general_video_prompt.md": package.get("general_video_prompt", ""),
            "08_seedance_segments.json": package.get("seedance_segments", []),
            "09_veo3_prompt.json": package.get("veo3_prompt", {}),
            "10_jimeng_prompt.txt": package.get("jimeng_prompt", ""),
            "10_yunjing_prompt.txt": package.get("yunjing_prompt", ""),
            "11_voiceover_timeline.json": package.get("voiceover_subtitle_timeline", {}),
            "12_negative_prompts.txt": "\n".join(self.NEGATIVE_PROMPTS),
            "13_execution_advice.md": package.get("execution_advice", ""),
        }

        for filename, content in text_exports.items():
            filepath = output_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                if isinstance(content, (dict, list)):
                    json.dump(content, f, ensure_ascii=False, indent=2)
                else:
                    f.write(str(content))

        logger.info(f"全部模块已导出到: {output_dir}")
