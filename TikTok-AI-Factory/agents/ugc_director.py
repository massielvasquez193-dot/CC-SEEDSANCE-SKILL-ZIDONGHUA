"""
TikTok AI Video Factory - UGC Director
分析参考视频表演数据 → 生成 performance_script.json
所有镜头必须按照表演脚本执行

分析维度:
  情绪变化曲线 / 语速节奏 / 停顿时机 / 手势模式
  镜头运动轨迹 / 产品展示时机 / CTA结构
"""

import json
import logging
import re
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class UGCDirector:
    """UGC导演 — 分析爆款视频表演模式，生成可执行表演脚本"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def analyze(
        self,
        reference_video: Path,
        video_analysis: dict,
        master_script: str,
        character_info: dict,
        product_info: dict,
    ) -> dict:
        """
        分析参考视频 → 生成 performance_script.json

        Returns:
            {
                "emotion_curve": [...],
                "speech_pattern": {...},
                "gesture_map": [...],
                "camera_choreography": [...],
                "product_reveal_timing": {...},
                "cta_structure": {...},
                "shot_performance": [{...}, ...]
            }
        """
        shots = video_analysis.get("shot_analysis", {}).get("shots", [])
        metadata = video_analysis.get("metadata", {})
        duration = metadata.get("duration", 15)
        total_shots = len(shots)

        # ================================================================
        # 1. 情绪变化曲线
        # ================================================================
        emotion_curve = self._build_emotion_curve(shots, duration, total_shots)

        # ================================================================
        # 2. 语速/停顿/重音模式
        # ================================================================
        speech_pattern = self._analyze_speech_pattern(duration, total_shots)

        # ================================================================
        # 3. 手势映射
        # ================================================================
        gesture_map = self._build_gesture_map(total_shots, character_info)

        # ================================================================
        # 4. 镜头运动编排
        # ================================================================
        camera_choreography = self._build_camera_choreography(shots, total_shots)

        # ================================================================
        # 5. 产品展示时机
        # ================================================================
        product_reveal = self._analyze_product_reveal_timing(duration, total_shots)

        # ================================================================
        # 6. CTA结构
        # ================================================================
        cta_structure = self._build_cta_structure(duration, total_shots)

        # ================================================================
        # 7. 逐镜头表演指令
        # ================================================================
        shot_performance = []
        for i in range(total_shots):
            sp = self._build_shot_performance(
                i, total_shots, duration,
                emotion_curve, speech_pattern, gesture_map,
                camera_choreography, product_reveal, cta_structure,
                character_info, product_info,
            )
            shot_performance.append(sp)

        performance_script = {
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "reference_video": str(reference_video),
            "target": "TikTok UGC广告标准 — 真人感优先",
            "product": product_info.get("product_name", ""),
            "character": character_info.get("name", ""),
            "total_duration": duration,
            "total_shots": total_shots,
            "emotion_curve": emotion_curve,
            "speech_pattern": speech_pattern,
            "gesture_map": gesture_map,
            "camera_choreography": camera_choreography,
            "product_reveal_timing": product_reveal,
            "cta_structure": cta_structure,
            "shot_performance": shot_performance,
        }

        return performance_script

    # ================================================================
    # 1. 情绪变化曲线
    # ================================================================
    def _build_emotion_curve(self, shots: list, duration: float, total: int) -> list[dict]:
        """构建TikTok UGC标准情绪曲线"""
        curve = [
            {"time_ratio": 0.0, "emotion": "curiosity", "intensity": 8,
             "expression": "睁大眼睛/靠近镜头", "energy": "高"},
            {"time_ratio": 0.15, "emotion": "surprise", "intensity": 9,
             "expression": "惊讶/捂嘴/停顿", "energy": "极高"},
            {"time_ratio": 0.30, "emotion": "relatable", "intensity": 5,
             "expression": "点头/自然微笑/看向镜头", "energy": "中"},
            {"time_ratio": 0.45, "emotion": "trust", "intensity": 6,
             "expression": "认真/展示产品/眼神交流", "energy": "中高"},
            {"time_ratio": 0.60, "emotion": "excitement", "intensity": 8,
             "expression": "开心/快速展示/手势强调", "energy": "高"},
            {"time_ratio": 0.75, "emotion": "satisfaction", "intensity": 7,
             "expression": "满意点头/产品特写/自信微笑", "energy": "中高"},
            {"time_ratio": 0.85, "emotion": "trust+urgency", "intensity": 8,
             "expression": "真诚推荐/靠近镜头/手势引导", "energy": "高"},
            {"time_ratio": 0.95, "emotion": "warmth+cta", "intensity": 9,
             "expression": "温暖微笑/产品居中/手势指向链接", "energy": "极高"},
        ]

        # 为每个镜头映射情绪
        for i in range(total):
            ratio = i / max(total - 1, 1)
            closest = min(curve, key=lambda c: abs(c["time_ratio"] - ratio))
            closest["shot_id"] = i + 1
            closest["time_seconds"] = round(ratio * duration, 1)

        return curve

    # ================================================================
    # 2. 语速/停顿模式
    # ================================================================
    def _analyze_speech_pattern(self, duration: float, total_shots: int) -> dict:
        """分析语速、停顿、重音模式 — UGC标准"""
        return {
            "overall_tempo": "中快 (UGC自然语速，非播音腔)",
            "words_per_second": 3.5,
            "pause_pattern": [
                {"position": "hook_after", "duration_sec": 0.3, "purpose": "制造悬念"},
                {"position": "problem_after", "duration_sec": 0.4, "purpose": "让观众共鸣"},
                {"position": "solution_before", "duration_sec": 0.2, "purpose": "引出产品"},
                {"position": "proof_after", "duration_sec": 0.3, "purpose": "强化信任"},
                {"position": "cta_before", "duration_sec": 0.2, "purpose": "行动号召前停顿"},
            ],
            "emphasis_words": [
                "产品名 (加重+放慢)", "效果词 (提高音调)", "优惠词 (加快+兴奋)",
            ],
            "tone_profile": {
                "pitch_range": "自然中音区，非播音腔",
                "energy_level": "由高→中→高→极高",
                "naturalness": "必须有呼吸声、轻微口误感、真实说话节奏",
            },
            "forbidden": [
                "禁止AI配音腔", "禁止匀速朗读", "禁止无停顿",
                "禁止播音腔", "禁止无情感起伏", "禁止完美发音",
            ],
        }

    # ================================================================
    # 3. 手势映射
    # ================================================================
    def _build_gesture_map(self, total_shots: int, character: dict) -> list[dict]:
        """构建手势映射 — UGC真人习惯手势"""
        vibe = character.get("vibe", "亲切自然")
        gestures = [
            {"shot_id": 1, "gesture": "双手展示产品", "intensity": "high",
             "timing": "0-1s", "note": "产品快速靠近镜头"},
            {"shot_id": 2, "gesture": "单手比划/摊手", "intensity": "medium",
             "timing": "开头", "note": f"表达'你也有这个问题吧'的无奈感"},
            {"shot_id": 3, "gesture": "双手握产品/展示", "intensity": "medium",
             "timing": "全程", "note": "产品展示+手指指向关键部位"},
            {"shot_id": 4, "gesture": "快速手势切换", "intensity": "high",
             "timing": "对比展示时", "note": "Before/After手势强调变化"},
            {"shot_id": 5, "gesture": "点头+手势强调", "intensity": "medium",
             "timing": "说到效果时", "note": "真诚推荐感"},
            {"shot_id": 6, "gesture": "靠近镜头+手指方向", "intensity": "high",
             "timing": "CTA时", "note": "引导看向链接区域"},
        ]

        # 扩展到实际镜头数
        result = []
        for i in range(total_shots):
            template = gestures[i % len(gestures)]
            result.append({
                "shot_id": i + 1,
                "gesture": template["gesture"],
                "intensity": template["intensity"],
                "timing": template["timing"],
                "note": template["note"],
            })
        return result

    # ================================================================
    # 4. 镜头运动编排
    # ================================================================
    def _build_camera_choreography(self, shots: list, total: int) -> list[dict]:
        """镜头运动编排 — 模拟手机拍摄的自然晃动"""
        return [
            {"shot_id": 1, "camera": "手持快速推近产品",
             "phone_movement": "轻微上下晃动 (模拟真实手持)", "stability": "70% (不能太稳)"},
            {"shot_id": 2, "camera": "固定+微晃",
             "phone_movement": "自然呼吸式晃动", "stability": "80%"},
            {"shot_id": 3, "camera": "缓慢环绕产品",
             "phone_movement": "手腕转动+轻微移动", "stability": "75%"},
            {"shot_id": 4, "camera": "快速切换角度",
             "phone_movement": "快速转动手腕", "stability": "60% (制造动态感)"},
            {"shot_id": 5, "camera": "固定+推近",
             "phone_movement": "手臂伸直缓慢靠近", "stability": "85%"},
            {"shot_id": 6, "camera": "固定+微笑",
             "phone_movement": "稳定但保留微晃", "stability": "90%"},
        ]

    # ================================================================
    # 5. 产品展示时机
    # ================================================================
    def _analyze_product_reveal_timing(self, duration: float, total: int) -> dict:
        return {
            "first_appearance": "0-1s (Hook开场即展示 — UGC标准)",
            "full_reveal": f"{duration * 0.3:.0f}s (30%处完整展示)",
            "detail_shots": [
                {"time": f"{duration * 0.35:.0f}s", "focus": "包装/质感"},
                {"time": f"{duration * 0.50:.0f}s", "focus": "使用效果"},
                {"time": f"{duration * 0.65:.0f}s", "focus": "核心卖点"},
            ],
            "logo_visible": f"{duration * 0.85:.0f}s (CTA前品牌露出)",
            "holding_style": "自然手持 (非广告式摆拍)",
            "rule": "产品必须在全视频中出现≥80%的时长 (UGC铁律)",
        }

    # ================================================================
    # 6. CTA结构
    # ================================================================
    def _build_cta_structure(self, duration: float, total: int) -> dict:
        return {
            "type": "soft_cta + hard_cta 双层",
            "soft_cta": {
                "timing": f"{duration * 0.75:.0f}s-{duration * 0.85:.0f}s",
                "text": "我已经用了好几天了，效果真的明显",
                "tone": "自然推荐 (非推销感)",
                "gesture": "点头+展示产品+满意表情",
            },
            "hard_cta": {
                "timing": f"{duration * 0.88:.0f}s-{duration:.0f}s",
                "text": "赶紧去试试吧！链接在我主页，现在还有限时优惠！",
                "tone": "温暖紧迫 (非焦虑营销)",
                "gesture": "微笑+手指标注链接区域+产品居中",
                "visual": "产品居中+优惠信息弹出+主页链接指向",
            },
            "cta_rules": [
                "CTA必须由真人说出 (禁止AI配音CTA)",
                "CTA前必须有0.2s停顿 (制造紧迫前的呼吸感)",
                "CTA时产品必须在画面中",
                "CTA语气温暖>紧迫 (UGC风格)",
            ],
        }

    # ================================================================
    # 7. 逐镜头表演指令
    # ================================================================
    def _build_shot_performance(
        self, index: int, total: int, duration: float,
        emotion_curve: list, speech: dict, gestures: list,
        camera: list, product_reveal: dict, cta: dict,
        character: dict, product: dict,
    ) -> dict:
        """为单个镜头生成详细表演指令"""
        shot_id = index + 1
        ratio = index / max(total - 1, 1)
        shot_duration = duration / total
        start_t = index * shot_duration
        end_t = start_t + shot_duration

        is_hook = (index == 0)
        is_cta = (index == total - 1)

        # 找最接近的情绪
        closest_emotion = min(emotion_curve, key=lambda c: abs(c.get("time_ratio", 0) - ratio))

        return {
            "shot_id": shot_id,
            "time_range": f"{start_t:.1f}s-{end_t:.1f}s",
            "duration": round(shot_duration, 1),
            "role": "HOOK" if is_hook else "CTA" if is_cta else f"BEAT_{shot_id}",

            # 表演指令
            "emotion": {
                "type": closest_emotion.get("emotion", "neutral"),
                "intensity": closest_emotion.get("intensity", 5),
                "expression": closest_emotion.get("expression", "自然面对镜头"),
                "eye_contact": "直视镜头" if index % 2 == 0 else "看产品",
                "energy": closest_emotion.get("energy", "中"),
            },

            # 动作指令
            "action": {
                "primary_gesture": gestures[index % len(gestures)].get("gesture", ""),
                "body_position": "面对镜头" if index <= 1 else "45度侧身展示",
                "hand_movement": "自然手势" if index > 0 else "快速展示产品",
                "head_movement": "轻微歪头(亲切感)" if index == 2 else "正视",
            },

            # 口播指令
            "voice": {
                "speed": "快" if is_hook else "正常" if index <= total//2 else "稍慢(CTA前)",
                "pause_before": round(0.2 if index == 3 else 0, 1),
                "pause_after": round(0.3 if is_hook else 0.2 if is_cta else 0.1, 1),
                "emphasis": "产品名重读" if index == 1 else "效果词升调" if index == 3 else "自然语调",
                "breath": "开头深吸一口气(真实感)" if is_hook else "正常呼吸",
            },

            # 产品指令
            "product": {
                "visibility": "画面中央 80%面积" if is_hook or is_cta else "手持/前景 40%面积",
                "movement": "快速推近" if is_hook else "稳定展示" if index <= 3 else "缓慢旋转展示",
                "lighting": "柔光正面" if is_hook else "侧逆光45°" if index == 2 else "自然光+补光",
            },

            # UGC自然感
            "ugc_naturalness": {
                "camera_shake": "70%稳定+30%自然晃动 (模拟手机手持)" if index <= 2 else "85%稳定",
                "blink_rate": "正常眨眼 (每3-5秒一次)",
                "micro_expressions": "轻微嘴角上扬、偶尔看旁边(像在想词)" if index == 2 else "自然",
                "background_noise": "轻微环境音 (非完全静音)" if index <= 2 else "无",
            },
        }

    # ================================================================
    # 保存
    # ================================================================
    def save(self, performance_script: dict, output_dir: Path) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "performance_script.json"
        path.write_text(
            json.dumps(performance_script, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        logger.info(f"Performance script saved: {path}")
        return path
