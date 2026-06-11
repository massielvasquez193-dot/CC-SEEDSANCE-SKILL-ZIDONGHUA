"""
TikTok AI Video Factory - Character Consistency Module
生成人物一致性参考图 + 全镜头一致性锚点

输出:
  character_reference.png  — 人物参考图 (PIL生成/Codex生成)
  consistency_anchor.txt   — 全镜头人物一致性锚点文本

保证:
  发型一致 / 服装一致 / 年龄一致 / 肤色一致 / 妆容一致
"""

import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class CharacterConsistency:
    """人物一致性管理器"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def generate(
        self,
        character_info: dict,
        output_dir: Path,
    ) -> dict:
        """
        生成人物一致性参考图和锚点

        Returns:
            {
                "reference_image": "path/to/character_reference.png",
                "anchor_text": "path/to/consistency_anchor.txt",
                "consistency_rules": {...},
            }
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: 从人物信息提取特征
        rules = self._extract_consistency_rules(character_info)

        # Step 2: 生成一致性锚点文本
        anchor = self._build_anchor_text(rules, character_info)
        anchor_path = output_dir / "consistency_anchor.txt"
        anchor_path.write_text(anchor, encoding="utf-8")

        # Step 3: 生成人物参考图
        ref_path = output_dir / "character_reference.png"
        self._generate_reference_image(rules, character_info, ref_path)

        result = {
            "reference_image": str(ref_path),
            "anchor_text": str(anchor_path),
            "consistency_rules": rules,
        }

        logger.info(f"人物一致性: 参考图={ref_path.name}, 锚点={anchor_path.name}")
        return result

    # ================================================================
    # 特征提取
    # ================================================================
    def _extract_consistency_rules(self, character: dict) -> dict:
        """从人物信息提取一致性规则"""
        return {
            "identity": {
                "name": character.get("name", "主角"),
                "age_range": character.get("age_range", "25-30岁"),
                "gender": character.get("gender", "female"),
            },
            "appearance": {
                "hair_style": character.get("hair_style", "长直发"),
                "hair_color": character.get("hair_color", "黑色"),
                "hair_length": character.get("hair_style", "长发").split(" ")[0] if " " in str(character.get("hair_style", "")) else "长发",
                "face_shape": character.get("face_shape", "鹅蛋脸"),
                "skin_tone": character.get("skin_tone", "自然偏白"),
                "body_type": character.get("body_type", "苗条"),
                "height": character.get("height_estimate", "160-170cm"),
            },
            "makeup": {
                "style": character.get("makeup", "自然裸妆"),
                "detail": character.get("makeup_detail", "清透底妆、自然眉形、裸色唇釉"),
                "key_points": ["底妆轻薄", "眉毛自然", "唇色淡雅", "轻微腮红"],
            },
            "clothing": {
                "top": character.get("clothing", "简约白色上衣"),
                "style": character.get("clothing_style", "休闲日常"),
                "detail": character.get("clothing_detail", ""),
                "accessories": ["简约项链", "细手链"],
            },
            "vibe": {
                "overall": character.get("vibe", "亲切自然"),
                "expression": "自然微笑",
                "energy": "温暖、有种草感",
            },
            "forbidden": [
                "禁止改变发型/发色/发长",
                "禁止改变妆容风格",
                "禁止改变服装",
                "禁止改变年龄感",
                "禁止替换为不同人物",
                "禁止出现原视频人物面部特征",
                "禁止AI塑料感皮肤",
                "禁止面部变形/扭曲",
            ],
        }

    # ================================================================
    # 锚点文本
    # ================================================================
    def _build_anchor_text(self, rules: dict, character: dict) -> str:
        """构建全镜头人物一致性锚点文本"""
        a = rules["appearance"]
        m = rules["makeup"]
        c = rules["clothing"]
        v = rules["vibe"]
        i = rules["identity"]

        return f"""# CHARACTER CONSISTENCY ANCHOR — {i['name']}
# 所有镜头必须严格遵循此锚点。禁止任何偏离。

## IDENTITY
- Name: {i['name']}
- Age: {i['age_range']}
- Gender: {i['gender']}

## APPEARANCE (全镜头一致)
- Hair: {a['hair_style']} / {a['hair_color']} / {a['hair_length']}
- Face: {a['face_shape']}
- Skin: {a['skin_tone']}
- Body: {a['body_type']} / {a['height']}

## MAKEUP (全镜头一致)
- Style: {m['style']}
- Detail: {m['detail']}
- Key: {', '.join(m['key_points'])}

## CLOTHING (全镜头一致)
- Top: {c['top']}
- Style: {c['style']}
- Detail: {c['detail']}
- Accessories: {', '.join(c['accessories'])}

## VIBE (全镜头一致)
- Overall: {v['overall']}
- Expression: {v['expression']}
- Energy: {v['energy']}

## SEEDANCE CONTINUITY ANCHOR (每个镜头开头重复)
SAME PERSON: {i['name']}, {i['age_range']} {i['gender']},
{a['hair_style']} {a['hair_color']} hair, {a['face_shape']} face,
{m['style']}, wearing {c['top']},
{v['overall']} vibe, {v['expression']}.

## FORBIDDEN
{chr(10).join(f'- {f}' for f in rules['forbidden'])}

---
Generated: {datetime.now().isoformat()}
"""
    # ================================================================
    # 参考图生成
    # ================================================================
    def _generate_reference_image(self, rules: dict, character: dict, output_path: Path):
        """生成人物一致性参考图"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # 画布: 多姿态展示
            w, h = 1200, 1600
            img = Image.new("RGB", (w, h), "#faf8f5")
            draw = ImageDraw.Draw(img)

            try:
                font_title = ImageFont.truetype("arial.ttf", 36)
                font_body = ImageFont.truetype("arial.ttf", 20)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except Exception:
                font_title = ImageFont.load_default()
                font_body = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # 标题
            draw.text((40, 30), f"CHARACTER REFERENCE — {character.get('name', '主角')}", fill="#1a1a2e", font=font_title)

            # 4格姿态参考
            poses = [
                ("FRONT SPEAKING", "正面口播态", (40, 100)),
                ("SIDE DEMO", "侧面演示态", (620, 100)),
                ("HOLD PRODUCT", "手持产品态", (40, 800)),
                ("CTA SMILE", "CTA微笑态", (620, 800)),
            ]

            for label_en, label_cn, (px, py) in poses:
                # 姿态框
                draw.rectangle([px, py, px+540, py+640], fill="#f0ebe3", outline="#d4c5b5", width=2)
                draw.text((px+20, py+10), f"{label_en}", fill="#8b7355", font=font_body)
                draw.text((px+20, py+40), label_cn, fill="#a0896e", font=font_small)

                # 人物剪影
                cx, cy = px+270, py+220
                draw.ellipse([cx-60, cy-100, cx+60, cy+100], fill="#f5d5b8")
                draw.ellipse([cx-70, cy-110, cx-40, cy+80], fill="#3d2b1f")
                draw.ellipse([cx+40, cy-110, cx+70, cy+80], fill="#3d2b1f")
                draw.rectangle([cx-50, cy+95, cx+50, cy+350], fill="#f0ebe3")

                # 标签
                draw.text((px+20, py+580), f"Hair: {rules['appearance']['hair_style']}", fill="#6b5b4f", font=font_small)
                draw.text((px+20, py+600), f"Makeup: {rules['makeup']['style']}", fill="#6b5b4f", font=font_small)
                draw.text((px+20, py+620), f"Clothing: {rules['clothing']['top']}", fill="#6b5b4f", font=font_small)

            # 底部一致性规则
            y_bottom = 1480
            rules_text = "CONSISTENCY: Same person, same hair, same makeup, same clothing, same age, same skin tone — across ALL shots"
            draw.text((40, y_bottom), rules_text, fill="#e94560", font=font_small)
            draw.text((40, y_bottom+20), "FORBIDDEN: Hair change, makeup change, outfit change, face morphing, AI plastic skin, different person", fill="#8b7355", font=font_small)

            img.save(output_path, quality=95)
            logger.info(f"人物参考图: {output_path} ({w}x{h})")

        except ImportError:
            logger.warning("PIL 未安装，创建文本引用")
            output_path.with_suffix(".txt").write_text(
                f"CHARACTER REFERENCE: {character.get('name')}\n"
                f"Hair: {rules['appearance']['hair_style']}\n"
                f"Makeup: {rules['makeup']['style']}\n"
                f"Clothing: {rules['clothing']['top']}\n",
                encoding="utf-8",
            )
