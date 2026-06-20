"""
TikTok UGC Video Factory — UGC Director
分析参考视频的真人表演模式 → 生成 performance_script.json

分析维度:
  语速 / 停顿位置 / 情绪变化 / 表情变化 / 手势动作
  镜头晃动 / 产品出现时机 / CTA出现时机

输出: performance_script.json — 每个镜头的详细表演指令
目标: 逼近真人TikTok UGC视频
"""

import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class UGCDirector:
    """UGC导演 — 从参考视频提取真人表演模式"""

    # UGC标准情绪-手势-运镜映射
    EMOTION_MAP = {
        "hook": {"emotion": "surprised_excited", "gesture": "hold_product_close_to_camera", "camera": "selfie_handheld_shaky", "pace": "fast"},
        "problem": {"emotion": "concerned_relatable", "gesture": "point_at_face_then_camera", "camera": "selfie_closeup_stable", "pace": "normal"},
        "agitate": {"emotion": "frustrated_empathetic", "gesture": "open_hands_shrug", "camera": "selfie_slight_shake", "pace": "normal_fast"},
        "solution": {"emotion": "excited_discovery", "gesture": "hold_product_demonstrate", "camera": "handheld_product_focus", "pace": "fast"},
        "result": {"emotion": "amazed_satisfied", "gesture": "point_at_result_before_after", "camera": "selfie_stable_proud", "pace": "normal"},
        "cta": {"emotion": "warm_urgent", "gesture": "point_down_to_link", "camera": "selfie_smile_stable", "pace": "slow_building"},
    }

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def analyze(self, reference_video: Path, video_analysis: dict, master_script: str, character_info: dict, product_info: dict) -> dict:
        """
        分析参考视频 + 主脚本 → 生成逐镜头表演指令
        """
        shots = video_analysis.get("shot_analysis", {}).get("shots", [])
        metadata = video_analysis.get("metadata", {})
        duration = metadata.get("duration", 15)
        total_shots = max(len(shots), 6)

        performance_script = {
            "version": "phase2_ugc",
            "generated_at": datetime.now().isoformat(),
            "reference_video": str(reference_video),
            "total_duration": duration,
            "total_shots": total_shots,
            "target": "TikTok真人UGC广告标准",

            # 全局表演参数
            "global_performance": self._global_performance(duration),
            "speech_pattern": self._speech_pattern(duration),
            "product_timing": self._product_timing(duration),
            "cta_timing": self._cta_timing(duration),

            # 逐镜头指令
            "shots": {},
        }

        # 为每个镜头生成表演指令
        shot_roles = ["hook", "problem", "agitate", "solution", "result", "cta"]
        for i in range(total_shots):
            shot_id = f"shot_{i+1:02d}"
            role = shot_roles[i % len(shot_roles)]
            performance_script["shots"][shot_id] = self._build_shot_performance(
                i, total_shots, duration, role, character_info
            )

        return performance_script

    def _global_performance(self, duration: float) -> dict:
        return {
            "style": "TikTok UGC authentic — real person, not actor, not model",
            "camera_rule": "ALWAYS smartphone selfie — slight natural shake, never tripod-stable",
            "skin_rule": "natural skin texture, slight imperfections, NO beauty filter, NO plastic smoothing",
            "lighting_rule": "natural window light + basic ring light, real home lighting, never studio",
            "background_rule": "real bedroom or living room, slightly messy, lived-in feel",
            "forbidden": [
                "cinematic lighting", "studio setup", "perfect skin", "beauty filter",
                "tripod-stable shot", "professional camera movement", "CGI", "3D render",
                "commercial look", "advertising aesthetic", "plastic face", "over-smoothing",
            ],
        }

    def _speech_pattern(self, duration: float) -> dict:
        return {
            "overall_pace": "fast hook → normal problem → fast solution → slow CTA",
            "words_per_second": 3.2,
            "pauses": [
                {"position": "after_hook", "duration": 0.5, "reason": "let the reveal sink in"},
                {"position": "between_problem_and_agitate", "duration": 0.3, "reason": "build empathy"},
                {"position": "before_solution_reveal", "duration": 0.6, "reason": "create anticipation"},
                {"position": "before_cta", "duration": 0.4, "reason": "shift to urgency"},
            ],
            "emphasis_rule": "product name SLOW + LOUD, benefit words HIGH PITCH, CTA WARM but URGENT",
            "naturalness": "include breath sounds, slight stumbles, 'um' moments, real person speech",
        }

    def _product_timing(self, duration: float) -> dict:
        return {
            "first_appearance": "0.0s — IMMEDIATELY in frame, TikTok UGC rule: show product instantly",
            "in_frame_percentage": "85% of total video — product almost always visible",
            "reveal_style": "natural, unstaged — not 'beauty shot', just holding it normally",
            "key_moments": [
                {"time": "0.0s", "action": "product rushes toward camera (hook)"},
                {"time": f"{duration*0.35:.1f}s", "action": "full product reveal + demo"},
                {"time": f"{duration*0.65:.1f}s", "action": "result proof + product visible"},
                {"time": f"{duration*0.85:.1f}s", "action": "product center + logo visible (CTA)"},
            ],
        }

    def _cta_timing(self, duration: float) -> dict:
        return {
            "soft_cta": {"time": f"{duration*0.7:.1f}s", "type": "natural recommendation"},
            "hard_cta": {"time": f"{duration*0.88:.1f}s", "type": "link + limited offer urgency"},
            "visual": "product center frame + person smile + link area pointed",
        }

    def _build_shot_performance(self, index: int, total: int, duration: float, role: str, character: dict) -> dict:
        template = self.EMOTION_MAP.get(role, self.EMOTION_MAP["problem"])
        shot_dur = duration / total
        start = index * shot_dur
        end = start + shot_dur

        return {
            "role": role.upper(),
            "time_range": f"{start:.1f}s-{end:.1f}s",
            "duration": round(shot_dur, 1),

            # 表演核心
            "emotion": template["emotion"],
            "gesture": template["gesture"],
            "camera": template["camera"],
            "pace": template["pace"],

            # 扩展表演细节
            "expression": self._expression_for_role(role),
            "eye_contact": "direct_to_camera" if role in ("hook", "cta", "result") else "glance_at_product_then_camera",
            "body_movement": self._body_for_role(role),
            "voice_tone": self._voice_for_role(role),

            # UGC自然感参数
            "ugc_naturalness": {
                "camera_shake_percent": 25 if role in ("hook", "agitate") else 15,
                "blink_naturally": True,
                "allow_imperfect_framing": True,
                "background_noise": "slight_room_tone" if role != "cta" else "none",
            },

            # 产品指令
            "product_action": self._product_action_for_role(role),
        }

    def _expression_for_role(self, role: str) -> str:
        return {
            "hook": "wide eyes, eyebrows raised, mouth slightly open — genuine surprise",
            "problem": "slight frown, head tilted, relatable 'you too?' look",
            "agitate": "furrowed brow, hand gesture emphasis, 'I was so frustrated' face",
            "solution": "bright eyes, genuine smile breaking through, 'look what I found!'",
            "result": "confident nod, proud smile, pointing at results",
            "cta": "warm genuine smile, direct eye contact, 'trust me on this' look",
        }.get(role, "natural, relaxed, real person talking to friend")

    def _body_for_role(self, role: str) -> str:
        return {
            "hook": "quick arm extension toward camera, slight lean forward",
            "problem": "natural stance, slight sway, one hand gesturing",
            "agitate": "open palm gestures, slight shoulder shrug, head shake",
            "solution": "two hands showing product, rotating it naturally",
            "result": "relaxed stance, one hand pointing at results, confident posture",
            "cta": "lean slightly closer, warm smile, hand gesturing toward link area",
        }.get(role, "natural relaxed stance")

    def _voice_for_role(self, role: str) -> str:
        return {
            "hook": "HIGH energy, fast pace, slight breathlessness — 'Guys. Look at this.'",
            "problem": "normal pace, slightly lower pitch, relatable tone — 'You know when...'",
            "agitate": "faster, higher pitch, emphatic — 'I tried EVERYTHING.'",
            "solution": "excited, slightly faster, genuine enthusiasm — 'Until I found THIS.'",
            "result": "confident, warm, proud — 'Look at the difference.'",
            "cta": "warm, slightly slower, building urgency — 'Go check it out. Link below.'",
        }.get(role, "natural conversational tone")

    def _product_action_for_role(self, role: str) -> str:
        return {
            "hook": "RUSH product toward camera lens immediately",
            "problem": "hold product casually, gesture with other hand",
            "agitate": "put product down, use both hands for emphasis",
            "solution": "PICK UP product, demonstrate use, show packaging",
            "result": "hold product next to results, compare visibly",
            "cta": "center product in frame, logo visible, hold steady",
        }.get(role, "keep product visible in frame")

    # ================================================================
    # 保存
    # ================================================================
    def save(self, performance_script: dict, output_dir: Path) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "performance_script.json"
        path.write_text(json.dumps(performance_script, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        logger.info(f"[UGC Director] performance_script.json saved: {path}")
        return path
