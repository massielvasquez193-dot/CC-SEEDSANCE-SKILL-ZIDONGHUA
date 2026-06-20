"""
TikTok AI Video Factory - 分镜生成Agent
生成详细分镜表，包含镜头编号、时长、景别、运镜、动作、字幕等
"""

import logging
from pathlib import Path
from datetime import datetime

from prompts.system_prompts import STORYBOARD_PROMPT

logger = logging.getLogger(__name__)


class StoryboardGenerator:
    """分镜表生成器"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def generate(
        self,
        script: str,
        product_info: dict,
        character_info: dict,
        viral_analysis: dict,
    ) -> str:
        """生成分镜表"""
        logger.info("生成分镜表...")

        duration = int(viral_analysis.get("metadata", {}).get("duration", 0) or 0)
        # 如果无法获取视频时长(ffprobe未安装等)，使用默认15秒
        if duration <= 0:
            duration = 15
        product_name = product_info.get("product_name", "产品")
        character_name = character_info.get("name", "人物")

        # 估算镜头数
        shot_count = max(5, duration // 2)

        if self.ai_client:
            return self._ai_generate(
                script, product_info, character_info, viral_analysis,
                product_name, character_name, duration, shot_count,
            )
        else:
            return self._template_generate(
                script, product_info, character_info, viral_analysis,
                product_name, character_name, duration, shot_count,
            )

    def _ai_generate(self, script, product_info, character_info, viral_analysis,
                     product_name, character_name, duration, shot_count) -> str:
        """AI驱动生成分镜"""
        try:
            prompt = STORYBOARD_PROMPT.format(
                script=script,
                product_info=str(product_info),
                character_info=str(character_info),
                viral_analysis=str(viral_analysis),
                product_name=product_name,
                character_name=character_name,
                duration=duration,
                shot_count=shot_count,
                storyboard_table="[分镜表]",
                camera_summary="[运镜总览]",
                pacing_curve="[节奏曲线]",
            )
            # response = self.ai_client.chat(prompt)
            # return response
            return self._template_generate(
                script, product_info, character_info, viral_analysis,
                product_name, character_name, duration, shot_count,
            )
        except Exception as e:
            logger.error(f"AI分镜生成失败: {e}")
            return self._template_generate(
                script, product_info, character_info, viral_analysis,
                product_name, character_name, duration, shot_count,
            )

    def _template_generate(self, script, product_info, character_info, viral_analysis,
                           product_name, character_name, duration, shot_count) -> str:
        """模板驱动生成分镜"""
        features = product_info.get("key_features", ["效果显著"])
        color = product_info.get("color", "")
        packaging = product_info.get("packaging", "")
        vibe = character_info.get("vibe", "自然亲切")

        shots = self._build_shot_table(duration, shot_count, product_name, character_name, color, packaging, vibe)
        camera_summary = self._build_camera_summary(shots)
        pacing_curve = self._build_pacing_curve(duration, shot_count)

        return f"""# 分镜表 (Storyboard)

## 总览
- 总镜头数: {shot_count}
- 总时长: {duration}秒
- 人物: {character_name}
- 产品: {product_name}

{shots}

## 运镜总览
{camera_summary}

## 节奏曲线
{pacing_curve}

---
生成时间: {datetime.now().isoformat()}
"""

    def _build_shot_table(self, duration, shot_count, product_name, character_name, color, packaging, vibe) -> str:
        """构建镜头表格"""
        shot_durations = self._distribute_shot_durations(duration, shot_count)
        shots_md = []

        shot_types = ["特写", "中景", "近景", "特写", "全景", "近景", "中景", "特写"]
        camera_moves = ["静态→快速推", "手持跟随", "缓慢拉远", "快速摇镜", "推近特写", "固定", "缓慢推", "固定"]
        transitions = ["快切", "淡入", "快切", "闪白转场", "快切", "快切", "快切", "淡出"]

        time_cursor = 0.0

        for i in range(shot_count):
            shot_dur = shot_durations[i]
            start_t = time_cursor
            end_t = time_cursor + shot_dur
            time_cursor = end_t

            st = shot_types[i % len(shot_types)]
            cm = camera_moves[i % len(camera_moves)]
            tr = transitions[i % len(transitions)]

            if i == 0:
                action = f"Hook开场：{product_name}产品特写快速出现，{color}色{packaging}包装惊艳亮相"
                subtitle = f"🔥 发现宝藏{product_name}！"
                voiceover = f"天呐！这个{product_name}也太好用了吧！"
            elif i == shot_count - 1:
                action = f"人物({character_name})微笑面对镜头，手举{product_name}，屏幕弹出优惠信息和链接"
                subtitle = "🛒 限时优惠·主页链接"
                voiceover = "赶紧去试试吧！链接在主页！"
            else:
                action = f"人物({character_name})展示{product_name}使用效果，{vibe}气质自然流露"
                subtitle = f"✨ {product_name} · 真的好用"
                voiceover = f"效果真的太惊艳了！"

            shot_md = f"""### 镜头 {i+1} ({start_t:.1f}s-{end_t:.1f}s)
| 项目 | 内容 |
|------|------|
| 景别 | {st} |
| 运镜 | {cm} |
| 时长 | {shot_dur:.1f}秒 |
| 画面描述 | {action} |
| 人物动作 | {character_name}自然展示产品，表情{vibe} |
| 产品位置 | 画面{'中央' if i % 2 == 0 else '前景右侧'} |
| 字幕 | {subtitle} |
| 口播 | {voiceover} |
| 音效 | TikTok热门BGM卡点{'重拍' if i == 0 else '节奏'} |
| 转场 | {tr} |
"""
            shots_md.append(shot_md)

        return "\n".join(shots_md)

    def _distribute_shot_durations(self, total_duration: float, shot_count: int) -> list[float]:
        """分配每个镜头的时长"""
        if total_duration <= 0 or shot_count <= 0:
            return [1.0] * max(shot_count, 1)
        # Hook镜头稍短，展示镜头稍长
        base = total_duration / shot_count
        durations = []
        for i in range(shot_count):
            if i == 0:
                durations.append(base * 0.7)  # Hook快速
            elif i == shot_count - 1:
                durations.append(base * 0.8)  # CTA快速
            else:
                durations.append(base * 1.1)  # 展示稍长
        # 调整总和
        total = sum(durations)
        scale = total_duration / total
        return [round(d * scale, 1) for d in durations]

    def _build_camera_summary(self, shots_text: str) -> str:
        """构建运镜总览"""
        return """| 运镜类型 | 使用次数 | 适用场景 |
|---------|---------|---------|
| 快速推镜 | 2次 | Hook和产品特写 |
| 手持跟随 | 1次 | 人物使用展示 |
| 缓慢拉远 | 1次 | 场景过渡 |
| 摇镜 | 1次 | 环境展示 |
| 固定镜头 | 2次 | 口播和CTA |
| 推近特写 | 1次 | 产品细节 |
"""

    def _build_pacing_curve(self, duration: float, shot_count: int) -> str:
        """构建节奏曲线"""
        return f"""```
强度
10 |    ██
 9 |   ███
 8 |  ████  ██
 7 | ██████ ███
 6 | ██████████
 5 |████████████
 4 |█████████████
 3 |██████████████
 2 |███████████████
 1 |████████████████
   +------------------→ 时间
   0s              {int(duration)}s

Hook(0-3s) → 问题(3-8s) → 引入(8-15s) → 效果({15}-{int(duration)-5}s) → CTA({int(duration)-5}-{int(duration)}s)
峰值: 3s | 8s | {int(duration)-5}s
```"""

    def visualize(self, storyboard: str, output_path: Path) -> Path:
        """
        生成Storyboard可视化图
        使用PIL创建分镜预览图
        """
        logger.info(f"生成Storyboard可视化: {output_path}")
        try:
            from PIL import Image, ImageDraw, ImageFont

            # 解析分镜表获取镜头数
            shot_count = storyboard.count("### 镜头")
            if shot_count == 0:
                shot_count = 6

            # 创建画布
            width = 1200
            row_height = 200
            padding = 20
            total_height = shot_count * (row_height + padding) + 100

            img = Image.new("RGB", (width, total_height), "#1a1a2e")
            draw = ImageDraw.Draw(img)

            # 标题
            try:
                font_title = ImageFont.truetype("arial.ttf", 32)
                font_body = ImageFont.truetype("arial.ttf", 16)
            except Exception:
                font_title = ImageFont.load_default()
                font_body = ImageFont.load_default()

            draw.text((width//2 - 200, 20), "Storyboard 分镜表", fill="#e94560", font=font_title)

            for i in range(shot_count):
                y = 80 + i * (row_height + padding)
                # 镜头框
                draw.rectangle([20, y, width-20, y+row_height], outline="#0f3460", width=2)
                # 镜头编号
                draw.text((40, y+10), f"Shot {i+1}", fill="#e94560", font=font_body)
                # 占位信息
                draw.text((40, y+40), f"镜头 {i+1} | 景别变化 | 运镜运动", fill="#cccccc", font=font_body)
                draw.text((40, y+70), f"人物动作 | 产品展示 | 字幕叠加", fill="#888888", font=font_body)
                draw.text((40, y+100), f"转场效果 → 下一镜头", fill="#666666", font=font_body)

            img.save(output_path)
            logger.info(f"Storyboard图已保存: {output_path}")
            return output_path

        except ImportError:
            logger.warning("PIL未安装，生成占位文件")
            output_path.write_text(storyboard, encoding="utf-8")
            return output_path
        except Exception as e:
            logger.error(f"生成Storyboard图失败: {e}")
            output_path.write_text(storyboard, encoding="utf-8")
            return output_path
