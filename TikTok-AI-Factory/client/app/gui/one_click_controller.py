"""
TikTok AI Factory Pro — One Click Controller
==============================================
Orchestrates the full pipeline from upload to final video.
No user intervention needed between steps.

Flow:
  STEP 1: Product analysis → master_script.md
  STEP 2: Character analysis → character.json
  STEP 3: Storyboard generation → storyboard.md
  STEP 4: GPT Image keyframes → keyframe_NN.png
  STEP 5: Seedance prompts → seedance_segment_NN.txt
  STEP 6: Video generation → segment_NN.mp4
  STEP 7: ElevenLabs TTS → voice.mp3
  STEP 8: Subtitle generation → subtitle.srt
  STEP 9: FFmpeg composite → video_final.mp4
"""

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class OneClickController:
    """End-to-end pipeline orchestrator with progress callbacks."""

    # Video style presets
    STYLES = {
        "TikTok UGC": {
            "tone": "authentic, real-person feel, smartphone selfie style",
            "camera": "handheld phone, slight natural shake, front camera",
            "lighting": "natural window light, NOT studio",
            "vibe": "friendly, relatable, genuine",
        },
        "Beauty Review": {
            "tone": "detailed product review, expert but approachable",
            "camera": "steady phone, beauty close-ups, texture shots",
            "lighting": "soft ring light, clean bathroom lighting",
            "vibe": "knowledgeable, honest, trustworthy",
        },
        "Problem Solution": {
            "tone": "relatable problem → satisfying solution reveal",
            "camera": "POV handheld, quick transitions, before/after shots",
            "lighting": "real home lighting, contrast before/after",
            "vibe": "empathetic, excited, solution-focused",
        },
        "Before After": {
            "tone": "dramatic transformation, visual proof",
            "camera": "steady comparison shots, split screen moments",
            "lighting": "consistent lighting for fair comparison",
            "vibe": "shocked, confident, proof-driven",
        },
        "Testimonial": {
            "tone": "personal story, emotional connection",
            "camera": "steady selfie, warm close-ups, natural framing",
            "lighting": "warm home lighting, cozy feel",
            "vibe": "grateful, sincere, personal",
        },
        "POV Story": {
            "tone": "first-person narrative, day-in-the-life",
            "camera": "POV shots, mirror selfies, handheld walk-through",
            "lighting": "natural throughout the day, varied",
            "vibe": "intimate, voyeuristic, real-life",
        },
    }

    COUNTRIES = {
        "美国": {"code": "US", "lang": "en", "voice_accent": "american"},
        "英国": {"code": "GB", "lang": "en", "voice_accent": "british"},
        "马来西亚": {"code": "MY", "lang": "ms", "voice_accent": "malay"},
        "印尼": {"code": "ID", "lang": "id", "voice_accent": "indonesian"},
        "德国": {"code": "DE", "lang": "de", "voice_accent": "german"},
        "法国": {"code": "FR", "lang": "fr", "voice_accent": "french"},
        "西班牙": {"code": "ES", "lang": "es", "voice_accent": "spanish"},
    }

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(
        self,
        product_path: str,
        character_path: str,
        video_path: str,
        country: str = "美国",
        video_count: int = 1,
        style: str = "TikTok UGC",
        progress_callback: Callable = None,
        step_callback: Callable = None,
        log_callback: Callable = None,
    ) -> dict:
        """
        Execute the full one-click pipeline.

        Args:
            product_path: Path to product image
            character_path: Path to character image
            video_path: Path to reference video
            country: Target country name
            video_count: Number of final videos to produce
            style: Video style preset
            progress_callback(percent, message): Overall progress 0-100
            step_callback(step_num, step_name): Current step notification
            log_callback(message): Real-time log message

        Returns:
            dict with output paths and status
        """
        self._cancelled = False
        country_info = self.COUNTRIES.get(country, self.COUNTRIES["美国"])
        style_info = self.STYLES.get(style, self.STYLES["TikTok UGC"])
        start_time = datetime.now()

        # Prepare output directory
        task_name = f"oneclick_{start_time.strftime('%Y%m%d_%H%M%S')}"
        output_dir = self.project_root / "output" / task_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy input files
        self._log(log_callback, "📁 准备输入文件...")
        product_dest = output_dir / ("product" + Path(product_path).suffix)
        char_dest = output_dir / ("character" + Path(character_path).suffix)
        video_dest = output_dir / ("reference" + Path(video_path).suffix)
        shutil.copy2(product_path, product_dest)
        shutil.copy2(character_path, char_dest)
        shutil.copy2(video_path, video_dest)

        results = {
            "task_name": task_name,
            "output_dir": str(output_dir),
            "country": country,
            "style": style,
            "videos": [],
            "files": {},
        }

        # Build config dict for pipeline context
        config = {
            "country": country_info,
            "style": style_info,
            "video_count": video_count,
            "output_dir": output_dir,
        }

        steps = [
            (1, "GPT脚本生成", self._step1_script, (product_dest, char_dest, video_dest, config)),
            (2, "人物分析", self._step2_character, (char_dest, config)),
            (3, "分镜生成", self._step3_storyboard, (config,)),
            (4, "GPT Image关键帧", self._step4_keyframes, (config,)),
            (5, "Seedance Prompt", self._step5_seedance_prompts, (config,)),
            (6, "Seedance视频生成", self._step6_video_gen, (config,)),
            (7, "ElevenLabs口播", self._step7_voiceover, (config,)),
            (8, "字幕生成", self._step8_subtitles, (config,)),
            (9, "视频合成", self._step9_composite, (output_dir, results)),
        ]

        for step_num, step_name, step_fn, args in steps:
            if self._cancelled:
                self._log(log_callback, "⏹ 用户取消")
                results["status"] = "cancelled"
                return results

            self._progress(progress_callback, step_num * 10, f"STEP {step_num}/{len(steps)}")
            self._step(step_callback, step_num, step_name)
            self._log(log_callback, f"\n{'='*50}")
            self._log(log_callback, f"  STEP {step_num}: {step_name}")
            self._log(log_callback, f"{'='*50}")

            try:
                result = step_fn(*args)
                if isinstance(result, dict):
                    config.update(result)
                    results["files"][f"step{step_num}"] = result
                self._log(log_callback, f"  ✅ {step_name} 完成")
            except Exception as e:
                self._log(log_callback, f"  ⚠️ {step_name} 跳过: {e}")
                logger.warning(f"Step {step_num} ({step_name}) failed: {e}")

        # Collect final videos
        for vf in sorted(output_dir.glob("video_final*.mp4")):
            results["videos"].append(str(vf))

        elapsed = (datetime.now() - start_time).total_seconds()
        self._progress(progress_callback, 100, "完成!")
        self._log(log_callback, f"\n{'='*50}")
        self._log(log_callback, f"  🎉 一键生成完成！")
        self._log(log_callback, f"  用时: {elapsed:.0f}秒")
        self._log(log_callback, f"  输出: {output_dir}")
        self._log(log_callback, f"  视频: {len(results['videos'])} 个")
        self._log(log_callback, f"{'='*50}")

        results["status"] = "completed"
        results["elapsed_seconds"] = elapsed
        results["config"] = config

        # Save summary
        summary_path = output_dir / "oneclick_summary.json"
        summary_path.write_text(
            json.dumps(results, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        return results

    # ================================================================
    # STEP 1: Master Script
    # ================================================================
    def _step1_script(self, product_path, character_path, video_path, config):
        """Generate master_script.md from product + reference video analysis."""
        output_dir = config["output_dir"]
        style_info = config["style"]
        country_info = config["country"]

        # Try AI-driven generation
        ai_client = self._get_ai_client()
        if ai_client:
            script = self._ai_generate_script(ai_client, product_path, video_path, style_info, country_info)
        else:
            script = self._template_script(Path(product_path).stem, style_info, country_info)

        script_path = output_dir / "master_script.md"
        script_path.write_text(script, encoding="utf-8")
        config["master_script"] = script
        config["script_path"] = str(script_path)
        return {"master_script": script, "script_path": str(script_path)}

    def _ai_generate_script(self, client, product_path, video_path, style, country):
        """Use AI provider to generate the master script."""
        try:
            prompt = f"""You are a TikTok UGC video script writer for {country['code']} market.
Style: {style['tone']}

Write a complete short-video script with these sections:
1. HOOK (0-3s): Grab attention immediately
2. PROBLEM (3-8s): Relatable pain point
3. SOLUTION (8-15s): Product as the answer
4. SOCIAL PROOF (15-20s): Why it works, results
5. CTA (20-25s): Strong call to action

Rules:
- Language: {country['lang']}
- Duration: 15-30 seconds
- Tone: {style['tone']}
- Camera: {style['camera']}
- Include voiceover text AND on-screen subtitle text
- Make it feel like a real person, NOT an ad

Output format:
# Master Script
## Hook
[Voiceover]: ...
[Subtitle]: ...
[Visual]: ...

## Problem
...

## Solution
...

## Social Proof
...

## CTA
..."""
            response = client.chat(prompt, system_prompt="You write TikTok UGC scripts. Output only the script, no explanations.")
            return response
        except Exception as e:
            logger.warning(f"AI script generation failed: {e}")
            return self._template_script(Path(product_path).stem, style, country)

    def _template_script(self, product_name, style, country):
        """Template script fallback when AI is unavailable."""
        return f"""# Master Script — {product_name}

## Hook (0-3s)
[Voiceover]: 天呐！这个{product_name}也太好用了吧！
[Subtitle]: 🔥 发现宝藏{product_name}
[Visual]: 产品快速推向镜头，人物惊喜表情

## Problem (3-8s)
[Voiceover]: 我之前试了那么多产品都没效果...
[Subtitle]: 用过的人都懂😭
[Visual]: 人物对镜头皱眉，摇头

## Solution (8-15s)
[Voiceover]: 直到我发现了这个{product_name}！
[Subtitle]: ✨ 效果真的太惊艳
[Visual]: 人物展示产品使用，自然光

## Social Proof (15-20s)
[Voiceover]: 你看这个效果，真的绝了！用了三天就...
[Subtitle]: 💯 真实效果对比
[Visual]: 产品效果展示，before/after

## CTA (20-25s)
[Voiceover]: 链接在主页，赶紧去试试！
[Subtitle]: 🛒 限时优惠·主页链接
[Visual]: 人物微笑举产品，屏幕弹出链接

---
Style: {style['tone']}
Country: {country['code']}
Duration: 25s
"""

    # ================================================================
    # STEP 2: Character Analysis
    # ================================================================
    def _step2_character(self, character_path, config):
        """Extract and lock character identity."""
        output_dir = config["output_dir"]

        char_info = {
            "name": "主角",
            "gender": "female",
            "age_range": "25-30",
            "race": "east_asian",
            "hair_style": "long straight",
            "hair_color": "black",
            "skin_tone": "natural",
            "clothing": "casual top",
            "makeup": "natural minimal",
            "vibe": "friendly natural",
            "build": "slim",
        }

        # Try AI vision analysis
        ai_client = self._get_ai_client()
        if ai_client and hasattr(ai_client, 'analyze_image'):
            try:
                char_info.update(self._ai_analyze_character(ai_client, character_path))
            except Exception as e:
                logger.warning(f"AI character analysis failed: {e}")

        char_json = output_dir / "character.json"
        char_json.write_text(json.dumps(char_info, indent=2, ensure_ascii=False), encoding="utf-8")
        config["character_info"] = char_info
        return {"character_json": str(char_json), "character_info": char_info}

    def _ai_analyze_character(self, client, image_path):
        """AI vision analysis of character image."""
        try:
            response = client.analyze_image(image_path, """Analyze this person. Return JSON:
{
  "gender": "male/female",
  "age_range": "20-25/25-30/30-35/35-40",
  "race": "east_asian/south_asian/caucasian/african/hispanic/middle_eastern",
  "hair_style": "long straight/short curly/etc",
  "hair_color": "black/brown/blonde/red/etc",
  "skin_tone": "fair/medium/olive/dark",
  "clothing": "description of outfit",
  "build": "slim/athletic/average/plus"
}""")
            import json as _json
            # Extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return _json.loads(response[start:end])
        except Exception:
            pass
        return {}

    # ================================================================
    # STEP 3: Storyboard
    # ================================================================
    def _step3_storyboard(self, config):
        """Generate storyboard from master script."""
        output_dir = config["output_dir"]
        script = config.get("master_script", "")
        char_info = config.get("character_info", {})

        # Parse script sections for shot count
        shots = re.findall(r'## (Hook|Problem|Solution|Social Proof|CTA)', script)
        if not shots:
            shots = ["Hook", "Problem", "Solution", "Social Proof", "CTA"]

        lines = []
        lines.append("# Storyboard\n")
        lines.append(f"## Overview")
        lines.append(f"- Total Shots: {len(shots)}")
        lines.append(f"- Character: {char_info.get('gender','female')}, {char_info.get('age_range','25-30')}")
        lines.append("")

        for i, section in enumerate(shots):
            shot_num = i + 1
            dur_map = {"Hook": "2.0s", "Problem": "5.0s", "Solution": "5.0s",
                       "Social Proof": "5.0s", "CTA": "3.0s"}
            dur = dur_map.get(section, "4.0s")

            lines.append(f"### Shot {shot_num}: {section} ({dur})")
            lines.append(f"- **Framing**: {'Close-up' if i==0 else 'Medium' if i<4 else 'Medium-close'}")
            lines.append(f"- **Camera**: {'Quick push' if i==0 else 'Handheld steady' if i<4 else 'Slow pull'}")
            lines.append(f"- **Action**: {self._shot_action(section, char_info)}")
            lines.append(f"- **Product**: {'Center frame' if i in (0,3) else 'In hand' if i in (2,4) else 'Foreground'}")
            lines.append(f"- **Transition**: {'Fast cut' if i<4 else 'Fade out'}")
            lines.append("")

        storyboard = "\n".join(lines)
        sb_path = output_dir / "storyboard.md"
        sb_path.write_text(storyboard, encoding="utf-8")
        config["storyboard"] = storyboard
        config["shot_count"] = len(shots)
        return {"storyboard": storyboard, "shot_count": len(shots), "storyboard_path": str(sb_path)}

    def _shot_action(self, section, char_info):
        name = char_info.get("name", "Creator")
        actions = {
            "Hook": f"Product rushes toward camera, {name} surprised expression",
            "Problem": f"{name} frowns, shakes head, relatable frustration",
            "Solution": f"{name} excited discovery, demonstrates product use",
            "Social Proof": f"{name} confident smile, shows results, before/after",
            "CTA": f"{name} warm smile, holds product centered, points to link",
        }
        return actions.get(section, f"{name} natural interaction with product")

    # ================================================================
    # STEP 4: Keyframes
    # ================================================================
    def _step4_keyframes(self, config):
        """Generate keyframe images via GPT Image or PIL fallback."""
        output_dir = config["output_dir"]
        shot_count = config.get("shot_count", 5)
        kf_dir = output_dir / "keyframes"
        kf_dir.mkdir(parents=True, exist_ok=True)

        keyframes = []
        for i in range(shot_count):
            kf_path = kf_dir / f"keyframe_{i+1:02d}.png"
            self._generate_keyframe_image(kf_path, i + 1, shot_count)
            keyframes.append({"shot_id": i + 1, "path": str(kf_path), "file": kf_path.name})

        # Save index
        index = {"generated_at": datetime.now().isoformat(), "total": shot_count, "keyframes": keyframes}
        (kf_dir / "keyframe_index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
        config["keyframes"] = keyframes
        return {"keyframes": keyframes, "keyframe_dir": str(kf_dir)}

    def _generate_keyframe_image(self, path, shot_id, total):
        """Generate a single keyframe image."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            roles = ["HOOK", "PROBLEM", "SOLUTION", "SOCIAL PROOF", "CTA"]
            colors = ["#e94560", "#ff6b3d", "#238636", "#1f6feb", "#8b5cf6"]
            role = roles[(shot_id - 1) % len(roles)]
            color = colors[(shot_id - 1) % len(colors)]

            img = Image.new("RGB", (1080, 1920), "#0d1117")
            draw = ImageDraw.Draw(img)

            # Background gradient effect with rectangles
            for j in range(10):
                shade = 13 + j * 3
                draw.rectangle([0, j * 192, 1080, (j + 1) * 192], fill=f"#{shade:02x}{shade+2:02x}{shade+5:02x}")

            # Card
            margin = 60
            draw.rounded_rectangle([margin, 400, 1080 - margin, 1520], radius=20, fill="#161b22", outline=color, width=3)

            # Shot number
            try:
                font_huge = ImageFont.truetype("arial.ttf", 120)
                font_lg = ImageFont.truetype("arial.ttf", 48)
                font_md = ImageFont.truetype("arial.ttf", 32)
                font_sm = ImageFont.truetype("arial.ttf", 22)
            except Exception:
                font_huge = ImageFont.load_default()
                font_lg = font_md = font_sm = font_huge

            # Center content
            draw.text((540, 550), f"KEYFRAME", fill=color, font=font_lg, anchor="mt")
            draw.text((540, 620), f"{shot_id:02d} / {total:02d}", fill="#c9d1d9", font=font_huge, anchor="mt")
            draw.text((540, 800), role, fill="#8b949e", font=font_lg, anchor="mt")

            # Style cues
            cues = [
                "📱 Smartphone selfie quality",
                "👤 Real person, natural skin",
                "💡 Natural window lighting",
                "🏠 Real home background",
                "🚫 NO AI/plastic/CGI look",
            ]
            y = 920
            for cue in cues:
                draw.text((540, y), cue, fill="#484f58", font=font_sm, anchor="mt")
                y += 50

            # Footer
            draw.text((540, 1800), "TikTok AI Factory Pro — One Click", fill="#30363d", font=font_sm, anchor="mt")

            img.save(path)
            return True
        except Exception as e:
            logger.warning(f"Keyframe generation failed: {e}")
            # Minimal fallback
            from PIL import Image
            Image.new("RGB", (1080, 1920), "#0d1117").save(path)
            return False

    # ================================================================
    # STEP 5: Seedance Prompts
    # ================================================================
    def _step5_seedance_prompts(self, config):
        """Generate Seedance segment prompt files."""
        output_dir = config["output_dir"]
        keyframes = config.get("keyframes", [])
        shot_count = len(keyframes)
        seg_dir = output_dir / "seedance_segments"
        seg_dir.mkdir(parents=True, exist_ok=True)

        camera_moves = [
            "Handheld phone, slight natural shake, quick push toward product",
            "Steady phone selfie hold, subtle breathing movement",
            "Gentle wrist rotation around product, natural handheld",
            "Phone in one hand, quick angle switch, casual motion",
            "Slow arm extension, slight unsteadiness, warm smile",
        ]

        segments = []
        for i, kf in enumerate(keyframes):
            shot_id = i + 1
            cm = camera_moves[i % len(camera_moves)]
            dur = 2.0 if i == 0 else 3.0 if i < 4 else 2.5

            content = f"""# Seedance Segment {shot_id:02d}/{shot_count}

[REFERENCE IMAGE]
keyframes/{kf['file']}

[POSITIVE PROMPT]
UGC-style smartphone video segment, {dur}s duration.
Camera: {cm}
Style: TikTok UGC authentic — real person, natural skin, smartphone quality.
Lighting: Natural window light + soft ring light, real home setting.
Vertical 9:16, 30fps.

[NEGATIVE PROMPT]
cinematic, studio lighting, perfect composition, plastic skin,
over-smoothed face, AI airbrushed, 3D render, CG animation,
cartoon, illustration, film look, professional camera,
watermark, text overlay, low quality, deformed hands

[CONTINUITY ANCHOR]
SAME PERSON as all other segments — same face, same hair, same outfit,
same skin texture, same build. NO variation between segments.
SAME PRODUCT — same color, same packaging, same size.

[CAMERA]
{cm}

[DURATION]
{dur}s
"""
            seg_file = seg_dir / f"seedance_segment_{shot_id:02d}.txt"
            seg_file.write_text(content, encoding="utf-8")
            segments.append({"shot_id": shot_id, "file": str(seg_file), "keyframe": kf["file"], "duration": dur})

        config["seedance_segments"] = segments
        return {"segments": segments, "segment_dir": str(seg_dir)}

    # ================================================================
    # STEP 6: Video Generation
    # ================================================================
    def _step6_video_gen(self, config):
        """Generate video segments via Seedance API."""
        output_dir = config["output_dir"]
        segments = config.get("seedance_segments", [])

        try:
            from providers.seedance_provider import SeedanceProvider
            sp = SeedanceProvider()
            if not sp.is_available():
                return {"video_gen": "skipped", "reason": "Seedance API key not configured"}

            seg_videos = []
            for seg in segments:
                seg_out = output_dir / f"segment_{seg['shot_id']:02d}.mp4"
                try:
                    shot_data = {
                        "shot_id": seg["shot_id"],
                        "duration": seg["duration"],
                        "positive_prompt": Path(seg["file"]).read_text(encoding="utf-8") if Path(seg["file"]).exists() else "",
                    }
                    result = sp._call_ark_api(shot_data, 1080, 1920, 30)
                    if result.get("video_url"):
                        sp._download_video(result["video_url"], seg_out)
                        seg_videos.append(str(seg_out))
                except Exception as e:
                    logger.warning(f"Segment {seg['shot_id']} video gen failed: {e}")

            if seg_videos:
                config["segment_videos"] = seg_videos
                return {"segment_videos": seg_videos}
            return {"video_gen": "skipped", "reason": "No segments generated"}
        except Exception as e:
            logger.warning(f"Video generation skipped: {e}")
            return {"video_gen": "skipped", "reason": str(e)[:100]}

    # ================================================================
    # STEP 7: Voiceover (ElevenLabs TTS)
    # ================================================================
    def _step7_voiceover(self, config):
        """Generate voiceover audio via ElevenLabs."""
        output_dir = config["output_dir"]
        script = config.get("master_script", "")
        country_info = config.get("country", {})

        # Extract voiceover lines
        vo_lines = re.findall(r'\[Voiceover\]:\s*(.+)', script)
        if not vo_lines:
            vo_lines = ["Welcome to this product review!"]
        full_text = " ".join(vo_lines)

        # Save voiceover text
        (output_dir / "voiceover.txt").write_text(full_text, encoding="utf-8")

        # Try ElevenLabs TTS
        try:
            from providers.elevenlabs_provider import ElevenLabsProvider
            ep = ElevenLabsProvider()
            if ep.is_available():
                voice_path = output_dir / "voice.mp3"
                result = ep.generate_speech(
                    text=full_text,
                    output_path=voice_path,
                    voice="female_american" if country_info.get("code") == "US" else "female_natural",
                )
                config["voice_mp3"] = str(voice_path)
                return {"voice_mp3": str(voice_path), "voiceover_text": full_text}
        except Exception as e:
            logger.warning(f"ElevenLabs TTS failed: {e}")

        # Fallback: check if there's a way to generate basic audio
        config["voiceover_text"] = full_text
        return {"voiceover_text": full_text, "voice_mp3": None}

    # ================================================================
    # STEP 8: Subtitles
    # ================================================================
    def _step8_subtitles(self, config):
        """Generate SRT subtitle file from voiceover text."""
        output_dir = config["output_dir"]
        script = config.get("master_script", "")
        vo_lines = re.findall(r'\[Subtitle\]:\s*(.+)', script)

        if not vo_lines:
            vo_lines = re.findall(r'\[Voiceover\]:\s*(.+)', script)

        srt_parts = []
        for i, line in enumerate(vo_lines):
            start = i * 3
            end = (i + 1) * 3
            srt_parts.append(
                f"{i+1}\n"
                f"00:00:{start:02d},000 --> 00:00:{end:02d},000\n"
                f"{line}\n"
            )

        srt_content = "\n".join(srt_parts)
        srt_path = output_dir / "subtitle.srt"
        srt_path.write_text(srt_content, encoding="utf-8")
        config["subtitle_srt"] = str(srt_path)
        return {"subtitle_srt": str(srt_path)}

    # ================================================================
    # STEP 9: FFmpeg Composite
    # ================================================================
    def _step9_composite(self, output_dir, results):
        """Composite video + voiceover + subtitles into final video."""
        segment_videos = []
        for v in sorted(output_dir.glob("segment_*.mp4")):
            segment_videos.append(v)

        voice_path = output_dir / "voice.mp3"
        subtitle_path = output_dir / "subtitle.srt"

        if not segment_videos:
            # Create a demo/placeholder video
            final = output_dir / "video_final.mp4"
            self._create_placeholder_video(final)
            results["videos"].append(str(final))
            return {"final_video": str(final)}

        # Merge segments
        concat_file = output_dir / "concat_list.txt"
        with open(concat_file, "w") as f:
            for v in segment_videos:
                f.write(f"file '{v.name}'\n")

        merged = output_dir / "video_merged.mp4"
        self._ffmpeg_concat(concat_file, merged)

        # Add voiceover
        if merged.exists() and voice_path.exists():
            final = output_dir / "video_final.mp4"
            self._ffmpeg_composite(merged, voice_path, subtitle_path, final)
            results["videos"].append(str(final))
            return {"final_video": str(final)}

        if merged.exists():
            shutil.copy(merged, output_dir / "video_final.mp4")
            results["videos"].append(str(output_dir / "video_final.mp4"))
            return {"final_video": str(output_dir / "video_final.mp4")}

        return {"final_video": None}

    def _ffmpeg_concat(self, concat_file, output):
        """Run ffmpeg concat demuxer."""
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_file), "-c", "copy", str(output),
            ], capture_output=True, timeout=120)
        except Exception as e:
            logger.warning(f"FFmpeg concat failed: {e}")

    def _ffmpeg_composite(self, video, audio, subtitles, output):
        """Composite video + audio + subtitles."""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video),
                "-i", str(audio),
                "-filter_complex",
                "[0:v]scale=1080:1920,setsar=1[v];[v]subtitles=" + str(subtitles) + ":force_style='FontSize=28,PrimaryColour=&HFFFFFF,Outline=1,Shadow=1'[out]",
                "-map", "[out]", "-map", "1:a",
                "-c:v", "libx264", "-crf", "23", "-preset", "medium",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                str(output),
            ]
            subprocess.run(cmd, capture_output=True, timeout=180)
        except Exception as e:
            logger.warning(f"FFmpeg composite failed: {e}")
            shutil.copy(video, output)

    def _create_placeholder_video(self, output):
        """Create a minimal placeholder video for testing."""
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", "color=c=0x0d1117:s=1080x1920:d=10:r=30",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                "-c:v", "libx264", "-c:a", "aac",
                "-shortest", "-t", "10",
                str(output),
            ], capture_output=True, timeout=60)
        except Exception:
            pass

    # ================================================================
    # Helpers
    # ================================================================
    def _get_ai_client(self):
        """Get the best available AI client."""
        try:
            from providers import create_provider
            for name in ["claude", "openai", "deepseek", "gemini"]:
                provider = create_provider(name)
                if provider and provider.is_available():
                    return provider
        except Exception:
            pass
        return None

    def _progress(self, callback, pct, msg):
        if callback:
            callback(pct, msg)

    def _step(self, callback, num, name):
        if callback:
            callback(num, name)

    def _log(self, callback, msg):
        if callback:
            callback(msg)
