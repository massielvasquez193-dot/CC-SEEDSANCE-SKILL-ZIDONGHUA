"""
TikTok AI Video Factory - Continuity Engine
保证全视频一致性: 人物/产品/服装/妆容/背景

作为所有生成模块的中间件:
  - 在每个Keyframe生成时注入一致性锚点
  - 在每个Seedance Prompt前验证参数
  - 生成 continuity_report.json
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ContinuityEngine:
    """
    一致性引擎

    职责:
      1. 提取并锁定人物特征 (只提取一次，全局复用)
      2. 提取并锁定产品特征 (只提取一次，全局复用)
      3. 验证每帧是否偏离锁定值
      4. 注入一致性锚点到所有Prompt
      5. 生成 continuity_report.json
    """

    def __init__(self):
        self._character_lock: Optional[dict] = None
        self._product_lock: Optional[dict] = None
        self._scene_lock: Optional[dict] = None
        self._violations: list[dict] = []

    # ================================================================
    # 锁定
    # ================================================================
    def lock_character(self, character_info: dict) -> dict:
        """
        锁定人物特征 — 全视频只调用一次
        之后所有镜头必须引用此锁定值
        """
        self._character_lock = {
            "name": character_info.get("name", "主角"),
            "age_range": character_info.get("age_range", ""),
            "gender": character_info.get("gender", ""),
            "hair": {
                "style": character_info.get("hair_style", ""),
                "color": character_info.get("hair_color", ""),
            },
            "face": {
                "shape": character_info.get("face_shape", ""),
                "skin_tone": character_info.get("skin_tone", ""),
            },
            "makeup": {
                "style": character_info.get("makeup", ""),
                "detail": character_info.get("makeup_detail", ""),
            },
            "clothing": {
                "outfit": character_info.get("clothing", ""),
                "style": character_info.get("clothing_style", ""),
            },
            "body": {
                "type": character_info.get("body_type", ""),
                "height": character_info.get("height_estimate", ""),
            },
            "vibe": character_info.get("vibe", ""),
        }
        logger.info(f"[Continuity] 人物已锁定: {self._character_lock['name']}")
        return self._character_lock

    def lock_product(self, product_info: dict) -> dict:
        """
        锁定产品特征 — 全视频只调用一次
        """
        self._product_lock = {
            "name": product_info.get("product_name", ""),
            "brand": product_info.get("brand", ""),
            "category": product_info.get("category", ""),
            "color": product_info.get("color", ""),
            "packaging": product_info.get("packaging", ""),
            "material": product_info.get("material", ""),
            "size": product_info.get("size", ""),
            "features": product_info.get("key_features", []),
        }
        logger.info(f"[Continuity] 产品已锁定: {self._product_lock['brand']} {self._product_lock['name']}")
        return self._product_lock

    def lock_scene(self, scene_info: dict = None) -> dict:
        """锁定场景 — 全视频统一背景和光线"""
        self._scene_lock = {
            "background": scene_info.get("background", "clean modern interior") if scene_info else "clean modern interior",
            "lighting": {
                "key_light": "soft key light 45-degree left",
                "rim_light": "warm rim light from behind",
                "color_temp": "warm (3200K-4500K)",
                "intensity": "medium-soft",
            },
            "depth_of_field": "shallow (f/2.8)",
            "camera_angle": "eye-level, front-facing",
            "environment": "minimal props, uncluttered background",
        }
        logger.info("[Continuity] 场景已锁定")
        return self._scene_lock

    # ================================================================
    # 验证
    # ================================================================
    def validate_keyframe(self, shot_id: int, prompt: str, reference: dict = None) -> dict:
        """
        验证单个Keyframe是否偏离锁定值

        Returns:
            {"pass": True/False, "violations": [...], "corrected_prompt": "..."}
        """
        violations = []

        if self._character_lock:
            # 检查人物描述是否包含锁定特征
            char_name = self._character_lock["name"]
            char_hair = self._character_lock["hair"]["style"]
            char_clothing = self._character_lock["clothing"]["outfit"]

            if char_name and char_name not in prompt:
                violations.append({
                    "type": "character_name_missing",
                    "shot_id": shot_id,
                    "expected": char_name,
                    "severity": "high",
                })

            # 检查是否有"换发型/换服装"关键词
            dangerous = ["different hair", "new outfit", "changed clothes",
                         "different person", "new look", "makeup change"]
            for d in dangerous:
                if d.lower() in prompt.lower():
                    violations.append({
                        "type": "character_change_detected",
                        "shot_id": shot_id,
                        "keyword": d,
                        "severity": "critical",
                    })

        if self._product_lock:
            prod_color = self._product_lock["color"]
            prod_brand = self._product_lock["brand"]

            dangerous_prod = ["different color", "new packaging", "replaced product",
                              "different product", "changed brand", "wrong color"]
            for d in dangerous_prod:
                if d.lower() in prompt.lower():
                    violations.append({
                        "type": "product_change_detected",
                        "shot_id": shot_id,
                        "keyword": d,
                        "severity": "critical",
                    })

        return {
            "pass": len([v for v in violations if v["severity"] == "critical"]) == 0,
            "violations": violations,
            "corrected_prompt": prompt,  # 如有violations在此注入纠正
        }

    def validate_seedance_segment(self, shot_id: int, segment_text: str) -> dict:
        """验证Seedance分段是否包含所有必要锚点"""
        checks = {
            "has_reference_image": "[REFERENCE IMAGE]" in segment_text,
            "has_positive_prompt": "[POSITIVE PROMPT]" in segment_text,
            "has_negative_prompt": "[NEGATIVE PROMPT]" in segment_text,
            "has_continuity_anchor": "[CONTINUITY ANCHOR]" in segment_text,
            "has_camera": "[CAMERA]" in segment_text,
            "has_duration": "[SEGMENT DURATION]" in segment_text,
        }

        missing = [k for k, v in checks.items() if not v]

        return {
            "pass": len(missing) == 0,
            "missing_tags": missing,
            "all_checks": checks,
        }

    # ================================================================
    # 锚点生成
    # ================================================================
    def get_character_anchor(self) -> str:
        """生成人物一致性锚点 (注入到所有Prompt)"""
        if not self._character_lock:
            return "CHARACTER NOT LOCKED"

        c = self._character_lock
        return (
            f"SAME PERSON across ALL shots: {c['name']}, {c['age_range']} {c['gender']}, "
            f"{c['hair']['style']} {c['hair']['color']} hair, {c['face']['shape']} face, "
            f"{c['face']['skin_tone']} skin, {c['makeup']['style']}, "
            f"wearing {c['clothing']['outfit']} ({c['clothing']['style']}). "
            f"NO hair change, NO outfit change, NO makeup change, NO different person, NO face morphing."
        )

    def get_product_anchor(self) -> str:
        """生成产品一致性锚点"""
        if not self._product_lock:
            return "PRODUCT NOT LOCKED"

        p = self._product_lock
        return (
            f"SAME PRODUCT across ALL shots: {p['brand']} {p['name']}, "
            f"{p['color']} color, {p['packaging']} packaging, {p['material']} material. "
            f"NO color change, NO packaging change, NO brand change, NO product morphing."
        )

    def get_scene_anchor(self) -> str:
        """生成场景一致性锚点"""
        if not self._scene_lock:
            return "SCENE NOT LOCKED"

        s = self._scene_lock
        return (
            f"SAME SCENE across ALL shots: {s['background']}, "
            f"{s['lighting']['key_light']}, {s['camera_angle']}. "
            f"NO background change, NO lighting change, NO environment change."
        )

    # ================================================================
    # 报告
    # ================================================================
    def generate_report(self, output_dir: Path) -> Path:
        """生成 continuity_report.json"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        report = {
            "generated_at": datetime.now().isoformat(),
            "character_locked": self._character_lock is not None,
            "product_locked": self._product_lock is not None,
            "scene_locked": self._scene_lock is not None,
            "total_violations": len(self._violations),
            "violations": self._violations,
            "character_lock": self._character_lock,
            "product_lock": self._product_lock,
            "scene_lock": self._scene_lock,
            "character_anchor": self.get_character_anchor() if self._character_lock else None,
            "product_anchor": self.get_product_anchor() if self._product_lock else None,
            "scene_anchor": self.get_scene_anchor() if self._scene_lock else None,
        }

        path = output_dir / "continuity_report.json"
        path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"[Continuity] Report: {path} ({len(self._violations)} violations)")
        return path

    def reset(self):
        """重置所有锁定 — 用于新任务"""
        self._character_lock = None
        self._product_lock = None
        self._scene_lock = None
        self._violations = []
