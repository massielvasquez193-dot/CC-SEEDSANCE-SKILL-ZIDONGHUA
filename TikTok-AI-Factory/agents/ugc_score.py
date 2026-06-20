"""
TikTok AI Video Factory - UGC Score
对最终视频评分: AI感 / 真人感 / UGC感 / TikTok广告标准

评分维度:
  1. AI感 (越低越好) — 检测AI生成痕迹
  2. 真人感 (越高越好) — 检测真人UGC特征
  3. UGC感 (越高越好) — 检测UGC内容模式
  4. TikTok广告分 (越高越好) — 检测广告转化潜力

目标: 最终视频达到 TikTok真人UGC广告标准
      而不是AI生成视频标准
"""

import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class UGCScore:
    """UGC视频质量评分引擎"""

    # 评分权重
    WEIGHTS = {
        "ai_detection": 0.30,      # AI感检测 (负向)
        "human_realness": 0.30,    # 真人感 (正向)
        "ugc_authenticity": 0.25,  # UGC真实感 (正向)
        "ad_conversion": 0.15,     # 广告转化 (正向)
    }

    def __init__(self):
        pass

    def score(
        self,
        video_path: Path = None,
        master_script: str = "",
        performance_script: dict = None,
        continuity_report: dict = None,
        video_metadata: dict = None,
    ) -> dict:
        """
        综合评分

        Returns:
            {
                "total_score": 85,           # 总分 0-100
                "grade": "A",                # S/A/B/C/D/F
                "ai_detection": {...},       # AI感评分 (越低越好)
                "human_realness": {...},     # 真人感评分
                "ugc_authenticity": {...},   # UGC真实感评分
                "ad_conversion": {...},      # 广告转化评分
                "recommendations": [...],    # 改进建议
            }
        """
        # 1. AI感检测
        ai_score = self._score_ai_detection(video_metadata, master_script)

        # 2. 真人感
        human_score = self._score_human_realness(video_metadata, performance_script, master_script)

        # 3. UGC真实感
        ugc_score = self._score_ugc_authenticity(video_metadata, master_script, performance_script)

        # 4. 广告转化
        ad_score = self._score_ad_conversion(master_script, performance_script)

        # 加权总分
        total = (
            ai_score["score"] * self.WEIGHTS["ai_detection"]
            + human_score["score"] * self.WEIGHTS["human_realness"]
            + ugc_score["score"] * self.WEIGHTS["ugc_authenticity"]
            + ad_score["score"] * self.WEIGHTS["ad_conversion"]
        )

        grade = self._grade(total)

        report = {
            "total_score": round(total, 1),
            "grade": grade,
            "target_standard": "TikTok真人UGC广告",
            "scored_at": datetime.now().isoformat(),
            "ai_detection": ai_score,
            "human_realness": human_score,
            "ugc_authenticity": ugc_score,
            "ad_conversion": ad_score,
            "weights": self.WEIGHTS,
            "recommendations": self._generate_recommendations(
                ai_score, human_score, ugc_score, ad_score
            ),
            "pass_threshold": total >= 70,
        }

        return report

    # ================================================================
    # 1. AI感检测 (越低越好 — 分数越高=AI感越低)
    # ================================================================
    def _score_ai_detection(self, metadata: dict, script: str) -> dict:
        """检测AI生成痕迹"""
        deductions = []
        score = 100  # 从满分开始扣

        # 检查视频编码 (AI生成通常无ffmpeg本地编码标记)
        if metadata:
            encoder = metadata.get("tags", {}).get("encoder", "")
            if "Lavc" in str(encoder) or "Lavf" in str(encoder):
                deductions.append({"item": "local_ffmpeg_encode", "deduction": 20,
                                   "reason": "本地ffmpeg编码 ≠ AI平台生成"})
                score -= 20

            bitrate = metadata.get("bit_rate", 0)
            if isinstance(bitrate, str):
                bitrate = int(bitrate)
            if bitrate < 10000:
                deductions.append({"item": "ultra_low_bitrate", "deduction": 15,
                                   "reason": f"极低码率 {bitrate}bps — 占位视频特征"})
                score -= 15

        # 检查脚本AI痕迹
        ai_patterns = [
            "作为AI", "根据您的需求", "以下是为您", "请注意",
            "综上所述", "最后", "完美无瑕", "无与伦比",
        ]
        for pattern in ai_patterns:
            if pattern in script:
                deductions.append({"item": f"ai_script_pattern:{pattern}", "deduction": 5,
                                   "reason": f"AI生成文本特征: '{pattern}'"})
                score -= 5

        # 检查过度完美 — 真人说话有不完美
        if "```" in script:
            deductions.append({"item": "markdown_code_blocks", "deduction": 10,
                               "reason": "Markdown代码块 — 非UGC内容格式"})
            score -= 10

        return {
            "score": max(0, score),
            "label": "AI感" if score < 50 else "低AI感" if score < 75 else "真人内容",
            "deductions": deductions,
            "total_deductions": sum(d["deduction"] for d in deductions),
        }

    # ================================================================
    # 2. 真人感 (越高越好)
    # ================================================================
    def _score_human_realness(self, metadata: dict, performance: dict, script: str) -> dict:
        """检测真人UGC特征"""
        score = 50  # 基础分
        bonuses = []

        # 口播自然度
        if performance:
            emotion_curve = performance.get("emotion_curve", [])
            if len(emotion_curve) >= 4:
                bonuses.append({"item": "emotion_variety", "bonus": 10,
                                "reason": f"{len(emotion_curve)} 种情绪变化 — 真人特征"})
                score += 10

            speech = performance.get("speech_pattern", {})
            if speech.get("pause_pattern"):
                bonuses.append({"item": "natural_pauses", "bonus": 10,
                                "reason": "有自然停顿设计 — 非AI匀速朗读"})
                score += 10

            if speech.get("forbidden"):
                bonuses.append({"item": "ai_voice_avoidance", "bonus": 15,
                                "reason": "明确禁止AI配音腔 — 真人语音策略"})
                score += 15

        # 手势/动作
        if performance:
            gestures = performance.get("gesture_map", [])
            if len(gestures) >= 3:
                bonuses.append({"item": "gesture_variety", "bonus": 10,
                                "reason": f"{len(gestures)} 种手势变化 — 真人表现力"})
                score += 10

        # 检查镜头晃动 (模拟手持)
        if performance:
            choreo = performance.get("camera_choreography", [])
            for c in choreo:
                if "晃动" in str(c) or "shake" in str(c).lower():
                    bonuses.append({"item": "camera_shake_simulation", "bonus": 5,
                                    "reason": "模拟手机手持晃动 — UGC特征"})
                    score += 5
                    break

        return {
            "score": min(100, score),
            "label": "高真人感" if score >= 80 else "中等真人感" if score >= 60 else "低真人感",
            "bonuses": bonuses,
            "total_bonuses": sum(b["bonus"] for b in bonuses),
        }

    # ================================================================
    # 3. UGC真实感 (越高越好)
    # ================================================================
    def _score_ugc_authenticity(self, metadata: dict, script: str, performance: dict) -> dict:
        """检测UGC内容模式"""
        score = 50
        bonuses = []

        # Hook前3秒
        hook_keywords = ["天呐", "姐妹们", "你看", "绝了", "宝藏", "救命", "太上头"]
        for kw in hook_keywords:
            if kw in script[:500]:
                bonuses.append({"item": f"ugc_hook:{kw}", "bonus": 8,
                                "reason": f"UGC口语化Hook关键词: '{kw}'"})
                score += 8
                break

        # 口播风格
        ugc_voice_patterns = ["你是不是也", "说真的", "相信我", "我用了", "真的好"]
        found = [p for p in ugc_voice_patterns if p in script]
        if len(found) >= 2:
            bonuses.append({"item": "ugc_voice_tone", "bonus": 10,
                            "reason": f"UGC口播风格: {found}"})
            score += 10

        # CTA自然度
        ugc_cta = ["主页", "链接", "去看看", "试试"]
        cta_found = [c for c in ugc_cta if c in script[-1000:]]
        if cta_found:
            bonuses.append({"item": "ugc_cta_style", "bonus": 8,
                            "reason": f"UGC风格CTA: {cta_found}"})
            score += 8

        # 产品展示时机
        if performance:
            reveal = performance.get("product_reveal_timing", {})
            if reveal.get("first_appearance", "").startswith("0"):
                bonuses.append({"item": "instant_product_reveal", "bonus": 12,
                                "reason": "Hook即展示产品 — UGC标准操作"})
                score += 12

        # "不完美"特征 (UGC反而不该完美)
        if performance:
            for sp in performance.get("shot_performance", []):
                ugc_nat = sp.get("ugc_naturalness", {})
                if ugc_nat.get("camera_shake", "").startswith("70"):
                    bonuses.append({"item": "imperfect_camera", "bonus": 7,
                                    "reason": "70%稳定+30%晃动 — UGC真实手持感"})
                    score += 7
                    break

        return {
            "score": min(100, score),
            "label": "高UGC感" if score >= 80 else "中等UGC感" if score >= 60 else "低UGC感",
            "bonuses": bonuses,
            "total_bonuses": sum(b["bonus"] for b in bonuses),
        }

    # ================================================================
    # 4. TikTok广告转化 (越高越好)
    # ================================================================
    def _score_ad_conversion(self, script: str, performance: dict) -> dict:
        """检测广告转化潜力"""
        score = 50
        bonuses = []

        # Hook强度
        if len(script) > 0 and script[:200].count("!") >= 2:
            bonuses.append({"item": "strong_hook", "bonus": 10,
                            "reason": "Hook情绪强烈 — 降低划走率"})
            score += 10

        # 产品露出时长
        if "产品" in script or "product" in script.lower():
            bonuses.append({"item": "product_presence", "bonus": 8,
                            "reason": "产品持续出现在脚本中"})
            score += 8

        # Social proof
        if "用了" in script and ("天" in script or "效果" in script):
            bonuses.append({"item": "social_proof", "bonus": 10,
                            "reason": "使用天数+效果证明 — 社交信任"})
            score += 10

        # 紧迫感 CTA
        if "限时" in script or "优惠" in script or "错过" in script:
            bonuses.append({"item": "urgency_cta", "bonus": 10,
                            "reason": "限时+优惠 CTA — 紧迫感驱动转化"})
            score += 10

        # CTA低门槛
        if "链接" in script and "主页" in script:
            bonuses.append({"item": "low_barrier_cta", "bonus": 7,
                            "reason": "链接在主页 — 低门槛行动号召"})
            score += 7

        return {
            "score": min(100, score),
            "label": "高转化" if score >= 80 else "中等转化" if score >= 60 else "低转化",
            "bonuses": bonuses,
            "total_bonuses": sum(b["bonus"] for b in bonuses),
        }

    # ================================================================
    # 评级
    # ================================================================
    def _grade(self, score: float) -> str:
        if score >= 90:
            return "S (TikTok真人UGC广告标准 — 可直接投放)"
        elif score >= 80:
            return "A (接近真人UGC — 微调后投放)"
        elif score >= 70:
            return "B (可投放 — 需人工review)"
        elif score >= 60:
            return "C (AI痕迹明显 — 需要重拍)"
        elif score >= 40:
            return "D (明显AI生成 — 不建议投放)"
        else:
            return "F (完全不符合UGC标准)"

    def _generate_recommendations(self, ai, human, ugc, ad) -> list[str]:
        recs = []
        if ai["score"] < 70:
            recs.append(f"[AI感] {ai['label']}: 移除AI文本特征，使用真实口播录音替代TTS")
        if human["score"] < 70:
            recs.append(f"[真人感] {human['label']}: 增加手势变化、镜头微晃、情绪起伏")
        if ugc["score"] < 70:
            recs.append(f"[UGC感] {ugc['label']}: Hook口语化、产品即时展示、CTA自然推荐")
        if ad["score"] < 70:
            recs.append(f"[转化] {ad['label']}: 强化Hook情绪、增加Social Proof、紧迫感CTA")
        if not recs:
            recs.append("所有指标达标 — 达到TikTok真人UGC广告标准")
        return recs

    # ================================================================
    # 快速评分 (视频元数据)
    # ================================================================
    def quick_score_video(self, video_path: Path) -> dict:
        """基于视频元数据的快速AI感评分"""
        try:
            import subprocess, json
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", "-show_streams", str(video_path)],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return {"error": "ffprobe failed"}

            data = json.loads(result.stdout)
            video_stream = None
            for s in data.get("streams", []):
                if s.get("codec_type") == "video":
                    video_stream = s
                    break

            if not video_stream:
                return {"error": "no video stream"}

            bitrate = int(video_stream.get("bit_rate", 0)) / 1000
            encoder = video_stream.get("tags", {}).get("encoder", "")
            is_placeholder = "Lavc" in str(encoder) or "Lavf" in str(encoder)

            return {
                "is_placeholder": is_placeholder,
                "bitrate_kbps": round(bitrate, 1),
                "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
                "duration": video_stream.get("duration", "0"),
                "codec": video_stream.get("codec_name", ""),
                "ai_risk": "high" if is_placeholder else "low" if bitrate > 2000 else "medium",
            }
        except Exception as e:
            return {"error": str(e)}

    # ================================================================
    # 保存
    # ================================================================
    def save_report(self, report: dict, output_dir: Path) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "ugc_score_report.json"
        path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"UGC Score: {report['total_score']}/100 [{report['grade']}] → {path}")
        return path
