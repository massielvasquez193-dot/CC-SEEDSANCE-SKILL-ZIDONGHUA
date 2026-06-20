"""
TikTok AI Factory Pro — Demo Generator
========================================
Generates a complete 3-minute product demo package with:

  DEMO_PRODUCT     — Styled product card image
  DEMO_CHARACTER   — UGC character reference sheet
  DEMO_SCRIPT      — Full master script with Hook→CTA
  DEMO_STORYBOARD  — Visual storyboard grid
  DEMO_KEYFRAMES   — 6 keyframe images
  DEMO_SEEDANCE    — Seedance segment prompts
  DEMO_VOICEOVER   — Voiceover text with timing
  DEMO_SUBTITLES   — SRT subtitle file
  DEMO_VIDEO       — Composite demo video (FFmpeg)
  DEMO_SUMMARY     — Complete dashboard JSON

No API keys required — uses template generation + PIL styling.
"""

import json
import os
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DemoGenerator:
    """Generates a complete, visually impressive product demo."""

    # Demo product — a fictional skincare serum
    PRODUCT = {
        "name": "GlowRevive Serum",
        "brand": "GlowRevive",
        "category": "skincare",
        "color": "rose gold gradient",
        "packaging": "sleek glass dropper bottle with rose gold cap",
        "size": "30ml",
        "key_ingredients": ["Hyaluronic Acid", "Vitamin C", "Niacinamide"],
        "benefits": ["Instant glow", "Deep hydration", "Fades dark spots"],
        "price": "$39.99",
    }

    # Demo character — UGC creator persona
    CHARACTER = {
        "name": "Sophia",
        "gender": "female",
        "age_range": "25-30",
        "race": "east_asian",
        "hair": {"style": "long wavy", "color": "dark brown"},
        "face": {"skin_tone": "natural warm", "features": "friendly, relatable"},
        "clothing": {"outfit": "cream oversized knit sweater"},
        "makeup": {"style": "natural minimal, dewy finish"},
        "vibe": {"overall": "warm, trustworthy, girl-next-door"},
        "build": "slim",
    }

    # Demo style
    STYLE = "TikTok UGC"
    COUNTRY = "美国"

    # Script sections with timing
    SCRIPT_SECTIONS = [
        ("HOOK", "0-3s", "OMG! You guys HAVE to try this serum! 😱"),
        ("HOOK", "0-3s", "I've been using it for 3 days and look at my skin!"),
        ("PROBLEM", "3-8s", "I had these stubborn dark spots for MONTHS..."),
        ("PROBLEM", "3-8s", "Tried EVERYTHING — nothing worked. Until now."),
        ("SOLUTION", "8-18s", "This is GlowRevive Serum. Hyaluronic Acid + Vitamin C."),
        ("SOLUTION", "8-18s", "Look at the texture — so lightweight, absorbs instantly!"),
        ("SOCIAL_PROOF", "18-25s", "Day 1 vs Day 3. I'm not even wearing foundation here."),
        ("SOCIAL_PROOF", "18-25s", "My friends literally asked what I did to my skin!"),
        ("CTA", "25-30s", "Link in bio! Use code GLOW20 for 20% off! 🛒"),
        ("CTA", "25-30s", "Trust me — your skin will thank you! ✨"),
    ]

    def __init__(self):
        self.output_dir = PROJECT_ROOT / "output" / "demo"
        self._step = 0

    # ================================================================
    # Main entry
    # ================================================================

    def generate(self) -> Path:
        """Generate the complete demo package. Returns output directory."""
        start = datetime.now()

        print(f"\n{'='*60}")
        print(f"  TikTok AI Factory Pro — Demo Generator")
        print(f"  Product: {self.PRODUCT['name']}")
        print(f"  Character: {self.CHARACTER['name']}")
        print(f"  Style: {self.STYLE} | Country: {self.COUNTRY}")
        print(f"{'='*60}\n")

        # Clean output
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True)

        # Generate each asset
        self._gen_product()
        self._gen_character()
        script = self._gen_script()
        self._gen_storyboard(script)
        self._gen_keyframes()
        self._gen_seedance_prompts()
        self._gen_voiceover()
        self._gen_subtitles()
        self._gen_video()
        self._gen_summary()
        self._gen_sales_script()

        elapsed = (datetime.now() - start).total_seconds()

        print(f"\n{'='*60}")
        print(f"  ✅ Demo package generated!")
        print(f"  Output: {self.output_dir}")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Files: {len(list(self.output_dir.rglob('*')))}")
        print(f"{'='*60}\n")

        return self.output_dir

    # ================================================================
    # Asset generators
    # ================================================================

    def _gen_product(self):
        self._log("Product image card")
        path = self.output_dir / "DEMO_PRODUCT.png"
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.new("RGB", (1080, 1080), "#faf5f0")
            draw = ImageDraw.Draw(img)

            # Background gradient
            for i in range(1080):
                r = 250 - i // 10
                g = 245 - i // 12
                b = 240 - i // 10
                draw.line([(0, i), (1080, i)], fill=(max(r, 220), max(g, 210), max(b, 200)))

            # Product card
            margin = 80
            draw.rounded_rectangle([margin, 120, 1080 - margin, 960], radius=30,
                                   fill="white", outline="#e8b4b8", width=3)

            try:
                font_name = ImageFont.truetype("arial.ttf", 52)
                font_brand = ImageFont.truetype("arial.ttf", 36)
                font_desc = ImageFont.truetype("arial.ttf", 26)
                font_price = ImageFont.truetype("arial.ttf", 48)
                font_ingr = ImageFont.truetype("arial.ttf", 22)
            except Exception:
                font_name = font_brand = font_desc = font_price = font_ingr = ImageFont.load_default()

            # Product name
            draw.text((540, 220), self.PRODUCT["name"], fill="#b8465a", font=font_name, anchor="mt")
            draw.text((540, 290), self.PRODUCT["brand"], fill="#999999", font=font_brand, anchor="mt")

            # Product visualization (colored rectangle as placeholder)
            draw.rounded_rectangle([300, 360, 780, 640], radius=20,
                                   fill="#fce4e8", outline="#e8b4b8", width=2)
            draw.text((540, 430), "GlowRevive", fill="#b8465a", font=font_name, anchor="mt")
            draw.text((540, 500), "Serum", fill="#b8465a", font=font_desc, anchor="mt")
            draw.text((540, 570), "30ml / 1.0 fl oz", fill="#999999", font=font_ingr, anchor="mt")

            # Key ingredients
            y = 700
            for ing in self.PRODUCT["key_ingredients"]:
                draw.text((540, y), f"✦ {ing}", fill="#666666", font=font_ingr, anchor="mt")
                y += 40

            # Price
            draw.text((540, 870), self.PRODUCT["price"], fill="#b8465a", font=font_price, anchor="mt")

            # Footer
            draw.text((540, 1020), "TikTok AI Factory Pro — Demo", fill="#cccccc", font=font_ingr, anchor="mt")

            img.save(path)
            self._ok(f"  {path.name} (1080×1080)")
        except Exception as e:
            self._warn(f"  PIL unavailable: {e}")

    def _gen_character(self):
        self._log("Character reference sheet")
        path = self.output_dir / "DEMO_CHARACTER.png"
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.new("RGB", (1200, 1600), "#f8f6f4")
            draw = ImageDraw.Draw(img)

            try:
                f_title = ImageFont.truetype("arial.ttf", 44)
                f_body = ImageFont.truetype("arial.ttf", 26)
                f_small = ImageFont.truetype("arial.ttf", 20)
            except Exception:
                f_title = f_body = f_small = ImageFont.load_default()

            # Title bar
            draw.rectangle([0, 0, 1200, 100], fill="#2a1a3e")
            draw.text((600, 50), "CHARACTER CONSISTENCY SHEET", fill="#e94560", font=f_title, anchor="mt")
            draw.text((600, 82), f"Creator: {self.CHARACTER['name']} | Style: {self.STYLE}", fill="#8b949e", font=f_small, anchor="mt")

            # Pose frames
            poses = [
                ("NEUTRAL", "Front-facing, natural expression, eye contact"),
                ("SPEAKING", "Slightly turned, mouth open mid-sentence, animated"),
                ("DEMONSTRATING", "Holding product, both hands, showing to camera"),
                ("REACTION", "Surprised/amazed expression, hand near face"),
                ("BEFORE/AFTER", "Side profile, pointing at cheek/face area"),
                ("CTA POSE", "Warm smile, product centered, confident"),
            ]

            cols = 2
            cell_w = (1200 - 120) // cols
            cell_h = 240
            y_start = 130

            for i, (label, desc) in enumerate(poses):
                col = i % cols
                row = i // cols
                x = 40 + col * (cell_w + 40)
                y = y_start + row * (cell_h + 30)

                # Card background
                draw.rounded_rectangle([x, y, x + cell_w, y + cell_h], radius=12,
                                       fill="white", outline="#e0e0e0", width=2)
                # Label bar
                draw.rectangle([x + 4, y + 4, x + cell_w - 4, y + 44], fill="#e94560")
                draw.text((x + cell_w // 2, y + 24), label, fill="white", font=f_body, anchor="mt")
                # Description
                draw.text((x + cell_w // 2, y + cell_h // 2 + 10), desc, fill="#666666", font=f_small, anchor="mt")
                # Pose number
                draw.text((x + cell_w // 2, y + cell_h - 35), f"POSE {i+1}/6", fill="#cccccc", font=f_small, anchor="mt")

            # Character info box
            c = self.CHARACTER
            info_y = y_start + 3 * (cell_h + 30) + 50
            draw.rounded_rectangle([40, info_y, 1160, info_y + 240], radius=12,
                                   fill="white", outline="#e0e0e0", width=2)

            lines = [
                f"Name: {c['name']} | {c['gender']} | {c['age_range']} | {c['race']}",
                f"Hair: {c['hair']['style']} — {c['hair']['color']}",
                f"Face: {c['face']['skin_tone']} — {c['face']['features']}",
                f"Clothing: {c['clothing']['outfit']}",
                f"Makeup: {c['makeup']['style']}",
                f"Vibe: {c['vibe']['overall']}",
                "RULE: SAME PERSON in every shot. NO variation in hair, face, outfit, or build.",
            ]
            for j, line in enumerate(lines):
                color = "#e94560" if "RULE" in line else "#444444"
                font = f_body if j == 0 else f_small
                draw.text((80, info_y + 30 + j * 32), line, fill=color, font=font)

            # Bottom seal
            draw.text((600, 1550), "TikTok AI Factory Pro — Character Consistency Engine", fill="#cccccc", font=f_small, anchor="mt")

            img.save(path)
            self._ok(f"  {path.name} (1200×1600, 6 poses)")
        except Exception as e:
            self._warn(f"  PIL unavailable: {e}")

    def _gen_script(self) -> str:
        self._log("Master script")
        sections = {
            "Hook": ("0-3s", "Product reveal + creator reaction"),
            "Problem": ("3-8s", "Relatable skin concern"),
            "Solution": ("8-18s", "Product intro + texture demo"),
            "Social Proof": ("18-25s", "Before/after comparison"),
            "CTA": ("25-30s", "Link + discount code"),
        }

        lines = [
            f"# Master Script — {self.PRODUCT['name']}",
            f"## Demo Video | {self.STYLE} | {self.COUNTRY} | 30s",
            "",
        ]

        for section, (timing, visual) in sections.items():
            voiceover_lines = [s[2] for s in self.SCRIPT_SECTIONS if s[0] == section]
            subtitle_lines = [s[2][:40] for s in self.SCRIPT_SECTIONS if s[0] == section]

            lines.append(f"## {section} ({timing})")
            lines.append(f"[Visual]: {visual}")
            for vo in voiceover_lines:
                lines.append(f"[Voiceover]: {vo}")
            for sub in subtitle_lines:
                lines.append(f"[Subtitle]: {sub}")
            lines.append("")

        # Add production notes
        lines.append("---")
        lines.append(f"## Production Notes")
        lines.append(f"- Product: {self.PRODUCT['brand']} {self.PRODUCT['name']}")
        lines.append(f"- Character: {self.CHARACTER['name']} (consistent across all shots)")
        lines.append(f"- Camera: Handheld smartphone, natural window light")
        lines.append(f"- Style: {self.STYLE} — authentic, real person, natural skin")
        lines.append(f"- BGM: Trending TikTok beat, ducked under voiceover")
        lines.append(f"- Total duration: 30s")
        lines.append(f"- Generated by: TikTok AI Factory Pro v1.0.0")
        lines.append(f"- Generated at: {datetime.now().isoformat()}")

        script = "\n".join(lines)
        (self.output_dir / "DEMO_SCRIPT.md").write_text(script, encoding="utf-8")
        self._ok(f"  DEMO_SCRIPT.md ({len(script)} chars)")
        return script

    def _gen_storyboard(self, script: str):
        self._log("Storyboard grid")
        path = self.output_dir / "DEMO_STORYBOARD.png"
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.new("RGB", (1600, 1000), "#0d1117")
            draw = ImageDraw.Draw(img)

            try:
                f_title = ImageFont.truetype("arial.ttf", 38)
                f_shot = ImageFont.truetype("arial.ttf", 20)
                f_small = ImageFont.truetype("arial.ttf", 14)
            except Exception:
                f_title = f_shot = f_small = ImageFont.load_default()

            # Header
            draw.rectangle([0, 0, 1600, 70], fill="#1a1a2e")
            draw.text((800, 35), f"STORYBOARD — {self.PRODUCT['name']} — {self.STYLE} — 30s",
                      fill="#e94560", font=f_title, anchor="mt")

            # 5 shot panels
            shots = [
                ("SHOT 1 · HOOK", "0-3s", "Close-up · Push in",
                 "Product rushes toward camera.\nCreator surprised expression.\nGrab attention instantly."),
                ("SHOT 2 · PROBLEM", "3-8s", "Medium · Handheld",
                 "Creator frowns, relatable.\nPoints at problem area.\n'I had these spots for MONTHS.'"),
                ("SHOT 3 · SOLUTION", "8-18s", "Medium-close · Steady",
                 "Product demonstration.\nTexture shot on hand.\nHyaluronic Acid + Vitamin C."),
                ("SHOT 4 · PROOF", "18-25s", "Split screen · Steady",
                 "Before / After comparison.\nDay 1 vs Day 3.\nNo foundation. Real results."),
                ("SHOT 5 · CTA", "25-30s", "Medium · Slow pull",
                 "Warm smile, product centered.\n'Link in bio! Code GLOW20.'\nConfident, inviting."),
            ]

            panel_w = 290
            gap = 20
            start_x = (1600 - (5 * panel_w + 4 * gap)) // 2
            y = 100

            for i, (title, timing, camera, desc) in enumerate(shots):
                x = start_x + i * (panel_w + gap)

                # Panel background
                draw.rounded_rectangle([x, y, x + panel_w, y + 380], radius=10,
                                       fill="#161b22", outline="#30363d", width=2)
                # Shot number bar
                draw.rectangle([x + 5, y + 5, x + panel_w - 5, y + 48], fill="#e94560")
                draw.text((x + panel_w // 2, y + 28), title, fill="white", font=f_shot, anchor="mt")

                # Timing + Camera
                draw.text((x + 14, y + 66), f"⏱ {timing} | 🎥 {camera}", fill="#8b949e", font=f_small)

                # Visual placeholder
                draw.rounded_rectangle([x + 14, y + 96, x + panel_w - 14, y + 240], radius=6,
                                       fill="#0d1117", outline="#21262d")
                draw.text((x + panel_w // 2, y + 168), f"🎬 S{i+1}", fill="#30363d",
                          font=ImageFont.truetype("arial.ttf", 40) if "arial" in str(type(f_shot)) else f_shot, anchor="mt")

                # Description
                desc_y = y + 256
                for j, line in enumerate(desc.split("\n")):
                    draw.text((x + 14, desc_y + j * 22), line, fill="#c9d1d9", font=f_small)

                # Shot number at bottom
                draw.text((x + panel_w // 2, y + 355), f"Shot {i+1} of 5",
                          fill="#484f58", font=f_small, anchor="mt")

            # Footer
            draw.text((800, 960), "TikTok AI Factory Pro v1.0 — Demo Storyboard",
                      fill="#484f58", font=f_small, anchor="mt")

            img.save(path)
            self._ok(f"  {path.name} (1600×1000, 5 panels)")
        except Exception as e:
            self._warn(f"  PIL unavailable: {e}")

        # Also save text version
        md_path = self.output_dir / "DEMO_STORYBOARD.md"
        md_path.write_text(script, encoding="utf-8")

    def _gen_keyframes(self):
        self._log("Keyframe images")
        kf_dir = self.output_dir / "keyframes"
        kf_dir.mkdir(exist_ok=True)

        roles = ["HOOK", "PROBLEM", "SOLUTION", "SOCIAL_PROOF", "CTA", "END_CARD"]
        colors = ["#e94560", "#ff6b3d", "#238636", "#1f6feb", "#8b5cf6", "#e94560"]
        prompts = [
            "Product rushes to camera, creator surprised, natural light, smartphone selfie",
            "Creator frowns at skin, relatable frustration, real bathroom mirror",
            "Product demo on hand, texture shot, window light, clean composition",
            "Split screen before/after, genuine reaction, no makeup comparison",
            "Warm smile, product centered, hand gesture to link, confident",
            "Product + discount code overlay, clean background, shoppable CTA",
        ]

        for i, (role, color, prompt) in enumerate(zip(roles, colors, prompts)):
            path = kf_dir / f"keyframe_{i+1:02d}.png"
            try:
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new("RGB", (1080, 1920), "#0d1117")
                draw = ImageDraw.Draw(img)

                try:
                    f_role = ImageFont.truetype("arial.ttf", 56)
                    f_num = ImageFont.truetype("arial.ttf", 120)
                    f_prompt = ImageFont.truetype("arial.ttf", 22)
                    f_meta = ImageFont.truetype("arial.ttf", 18)
                except Exception:
                    f_role = f_num = f_prompt = f_meta = ImageFont.load_default()

                # Card
                draw.rounded_rectangle([40, 200, 1040, 1700], radius=24,
                                       fill="#161b22", outline=color, width=4)

                # Role bar
                draw.rectangle([44, 204, 1036, 290], fill=color)
                draw.text((540, 248), role, fill="white", font=f_role, anchor="mt")

                # Number
                draw.text((540, 500), f"{i+1:02d}", fill=color, font=f_num, anchor="mt")
                draw.text((540, 630), f"/ 6", fill="#484f58", font=f_role, anchor="mt")

                # Prompt lines
                prompt_lines = textwrap.wrap(prompt, width=40)
                y = 850
                for line in prompt_lines:
                    draw.text((540, y), line, fill="#c9d1d9", font=f_prompt, anchor="mt")
                    y += 38

                # Footer metadata
                draw.text((540, 1620), "TikTok UGC · Natural Skin · Smartphone · No AI Look", fill="#484f58", font=f_meta, anchor="mt")
                draw.text((540, 1660), "TikTok AI Factory Pro v1.0", fill="#30363d", font=f_meta, anchor="mt")

                img.save(path)
            except Exception:
                # Minimal fallback
                from PIL import Image as PILImage
                PILImage.new("RGB", (1080, 1920), color).save(path)

        # Index
        index = {
            "generated_at": datetime.now().isoformat(),
            "total_keyframes": 6,
            "generator": "Demo Mode — PIL Placeholders",
            "keyframes": [{"shot_id": i+1, "file": f"keyframe_{i+1:02d}.png", "role": r}
                          for i, r in enumerate(roles)],
        }
        (kf_dir / "keyframe_index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
        self._ok(f"  keyframes/ (6 PNGs + index)")

    def _gen_seedance_prompts(self):
        self._log("Seedance segment prompts")
        seg_dir = self.output_dir / "seedance_segments"
        seg_dir.mkdir(exist_ok=True)

        camera_moves = [
            "Handheld phone, quick push toward product, natural shake",
            "Steady phone selfie, subtle breathing movement",
            "Gentle wrist rotation around product, natural handheld",
            "Phone in one hand, slow arm extension, slight unsteadiness",
            "Stable selfie hold, warm smile, minimal movement",
            "Phone lowered then raised, casual reveal motion",
        ]

        for i in range(6):
            content = f"""# Seedance Segment {i+1:02d}/6 — {self.PRODUCT['name']}

[REFERENCE IMAGE]
keyframes/keyframe_{i+1:02d}.png

[POSITIVE PROMPT]
UGC-style smartphone video segment, {'2.0s' if i == 0 else '5.0s'} duration.
Camera: {camera_moves[i]}
Style: TikTok UGC authentic — real person, natural skin texture,
slight imperfections, smartphone camera quality.
Lighting: Natural window light, real home setting, NOT studio.
Character: {self.CHARACTER['name']}, {self.CHARACTER['gender']}, {self.CHARACTER['age_range']},
{self.CHARACTER['hair']['style']} {self.CHARACTER['hair']['color']} hair,
{self.CHARACTER['face']['skin_tone']} skin, {self.CHARACTER['clothing']['outfit']}.
Product: {self.PRODUCT['brand']} {self.PRODUCT['name']},
{self.PRODUCT['color']} {self.PRODUCT['packaging']}.
Vertical 9:16, 30fps.

[NEGATIVE PROMPT]
cinematic, studio lighting, perfect composition, plastic skin,
over-smoothed face, AI airbrushed, 3D render, CG animation,
cartoon, illustration, film look, professional camera,
watermark, text overlay, low quality, deformed hands,
hair change, outfit change, makeup change, different person,
product morphing, color change, packaging change

[CONTINUITY ANCHOR]
SAME PERSON: {self.CHARACTER['name']} — {self.CHARACTER['hair']['style']}
{self.CHARACTER['hair']['color']} hair, {self.CHARACTER['clothing']['outfit']},
{self.CHARACTER['makeup']['style']} makeup.
NO hair change. NO outfit change. NO face morphing.
SAME PRODUCT: {self.PRODUCT['brand']} {self.PRODUCT['name']}
{self.PRODUCT['color']} {self.PRODUCT['packaging']}.
NO color change. NO packaging change.

[CAMERA]
{camera_moves[i]}

[DURATION]
{'2.0' if i == 0 else '5.0'}s
"""
            (seg_dir / f"seedance_segment_{i+1:02d}.txt").write_text(content, encoding="utf-8")

        overview = {
            "generated_at": datetime.now().isoformat(),
            "total_segments": 6,
            "style": "TikTok UGC authentic",
            "rule": "EVERY segment MUST use its reference keyframe — NO text-only generation",
        }
        (seg_dir / "seedance_overview.json").write_text(json.dumps(overview, indent=2, ensure_ascii=False), encoding="utf-8")
        self._ok(f"  seedance_segments/ (6 prompts + overview)")

    def _gen_voiceover(self):
        self._log("Voiceover script")
        lines = [
            f"# Voiceover Script — {self.PRODUCT['name']} Demo",
            "",
            "| Time | Character | Text | Emotion |",
            "|------|-----------|------|---------|",
        ]
        timings = ["0:00", "0:03", "0:08", "0:13", "0:18", "0:22", "0:25", "0:28"]
        emotions = ["Excited", "Relatable", "Curious", "Amazed", "Confident", "Grateful", "Energetic", "Warm"]

        for i, (_, _, text) in enumerate(self.SCRIPT_SECTIONS):
            t = timings[min(i, len(timings)-1)]
            e = emotions[min(i, len(emotions)-1)]
            lines.append(f"| {t} | {self.CHARACTER['name']} | {text} | {e} |")

        lines.extend([
            "",
            "---",
            f"## TTS Settings",
            f"- Provider: ElevenLabs",
            f"- Voice: Female, 25-30, American English",
            f"- Style: TikTok Creator — warm, natural, conversational",
            f"- Speed: 1.0x",
            f"- Total duration: ~30s",
        ])

        vo_text = "\n".join(lines)
        (self.output_dir / "DEMO_VOICEOVER.md").write_text(vo_text, encoding="utf-8")

        # Plain text for TTS
        plain = " ".join(s[2] for s in self.SCRIPT_SECTIONS)
        (self.output_dir / "voiceover.txt").write_text(plain, encoding="utf-8")
        self._ok(f"  DEMO_VOICEOVER.md + voiceover.txt")

    def _gen_subtitles(self):
        self._log("Subtitles (SRT)")
        entries = []
        for i, (_, timing, text) in enumerate(self.SCRIPT_SECTIONS):
            start_sec = i * 3.2
            end_sec = (i + 1) * 3.2
            start_ts = f"00:00:{int(start_sec):02d},{int((start_sec%1)*1000):03d}"
            end_ts = f"00:00:{int(end_sec):02d},{int((end_sec%1)*1000):03d}"
            entries.append(f"{i+1}\n{start_ts} --> {end_ts}\n{text}\n")

        srt = "\n".join(entries)
        (self.output_dir / "DEMO_SUBTITLES.srt").write_text(srt, encoding="utf-8")
        self._ok(f"  DEMO_SUBTITLES.srt ({len(entries)} entries)")

    def _gen_video(self):
        self._log("Demo video")
        path = self.output_dir / "DEMO_VIDEO.mp4"
        try:
            # Generate video frames via PIL, then encode with FFmpeg
            from PIL import Image, ImageDraw, ImageFont

            frames_dir = self.output_dir / "_demo_frames"
            frames_dir.mkdir(exist_ok=True)

            try:
                f_title = ImageFont.truetype("arial.ttf", 72)
                f_sub = ImageFont.truetype("arial.ttf", 48)
                f_step = ImageFont.truetype("arial.ttf", 36)
                f_footer = ImageFont.truetype("arial.ttf", 24)
            except Exception:
                f_title = f_sub = f_step = f_footer = ImageFont.load_default()

            steps = [
                ("HOOK", "Product Reveal", "#e94560", 0, 3),
                ("PROBLEM", "Skin Concern — Relatable Pain Point", "#ff6b3d", 3, 8),
                ("SOLUTION", "Product Demo — Texture & Application", "#238636", 8, 18),
                ("SOCIAL PROOF", "Before / After — Real Results", "#1f6feb", 18, 25),
                ("CTA", "Link in Bio — Discount Code", "#8b5cf6", 25, 30),
            ]

            frame_count = 0
            # Generate 1 frame per second (30 frames for 30s video)
            for sec in range(30):
                t = float(sec)
                img = Image.new("RGB", (1080, 1920), "#0d1117")
                draw = ImageDraw.Draw(img)

                # Background accent
                current_step = None
                for label, desc, color, t_start, t_end in steps:
                    if t_start <= t < t_end:
                        current_step = (label, desc, color, t_start, t_end)
                        break

                if current_step:
                    label, desc, color, t_start, t_end = current_step
                    # Progress bar
                    progress = (t - t_start) / (t_end - t_start)
                    bar_w = int(1080 * progress)
                    draw.rectangle([0, 0, bar_w, 6], fill=color)

                    # Step label
                    draw.text((540, 200), label, fill=color, font=f_title, anchor="mt")
                    draw.text((540, 300), desc, fill="white", font=f_sub, anchor="mt")

                    # Step indicator dots
                    for i, (sl, _, sc, _, _) in enumerate(steps):
                        dot_x = 340 + i * 100
                        dot_color = sc if sl == label else "#30363d"
                        dot_size = 14 if sl == label else 8
                        draw.ellipse([dot_x - dot_size, 500 - dot_size,
                                      dot_x + dot_size, 500 + dot_size], fill=dot_color)

                # Always-visible title
                draw.text((540, 120), "TikTok AI Factory Pro", fill="#e94560", font=f_sub, anchor="mt")
                draw.text((540, 1800), "v1.0.0 — Demo Mode", fill="#484f58", font=f_footer, anchor="mt")

                # Product name at bottom
                draw.text((540, 1720), self.PRODUCT["name"], fill="#8b949e", font=f_footer, anchor="mt")

                # Frame counter in corner
                draw.text((1040, 20), f"{int(t//60):02d}:{int(t%60):02d}", fill="#30363d", font=f_footer, anchor="rt")

                frame_path = frames_dir / f"frame_{frame_count:04d}.png"
                img.save(frame_path)
                frame_count += 1

            self._ok(f"  {frame_count} frames rendered")

            # Encode with FFmpeg
            ffmpeg_path = "ffmpeg"
            # Try known Windows path
            import shutil
            found = shutil.which("ffmpeg")
            if not found:
                alt = Path("/c/Users/A/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe")
                if alt.exists():
                    ffmpeg_path = str(alt)

            result = subprocess.run([
                ffmpeg_path, "-y",
                "-framerate", "1",
                "-i", str(frames_dir / "frame_%04d.png"),
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                "-c:v", "libx264", "-crf", "23", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest", "-t", "30",
                str(path),
            ], capture_output=True, timeout=120)

            if path.exists() and path.stat().st_size > 1000:
                self._ok(f"  {path.name} ({path.stat().st_size/1024:.0f} KB, 30s, 1080×1920)")
            else:
                self._warn(f"  FFmpeg encode failed: {result.stderr.decode()[:200] if result.stderr else 'unknown'}")

            # Clean up frames
            shutil.rmtree(frames_dir, ignore_errors=True)

        except FileNotFoundError:
            self._warn("  FFmpeg not found — video requires FFmpeg")
        except Exception as e:
            self._warn(f"  Video generation failed: {e}")

    def _gen_summary(self):
        self._log("Demo summary dashboard")
        summary = {
            "demo_name": f"{self.PRODUCT['brand']} {self.PRODUCT['name']} Demo",
            "generated_at": datetime.now().isoformat(),
            "product": self.PRODUCT,
            "character": self.CHARACTER,
            "style": self.STYLE,
            "country": self.COUNTRY,
            "duration": "30s",
            "shots": 5,
            "keyframes": 6,
            "script_sections": ["Hook", "Problem", "Solution", "Social Proof", "CTA"],
            "assets_generated": {
                "DEMO_PRODUCT.png": "Product image card (1080×1080)",
                "DEMO_CHARACTER.png": "Character consistency sheet (1200×1600, 6 poses)",
                "DEMO_SCRIPT.md": "Full master script with timing",
                "DEMO_STORYBOARD.png": "Visual storyboard grid (1600×1000, 5 panels)",
                "keyframes/": "6 keyframe images (1080×1920 each)",
                "seedance_segments/": "6 Seedance segment prompts",
                "DEMO_VOICEOVER.md": "Voiceover script with TTS settings",
                "DEMO_SUBTITLES.srt": "SRT subtitles (8 entries, 30s)",
                "DEMO_VIDEO.mp4": "Composite demo video (1080×1920, 30s)",
                "DEMO_SUMMARY.json": "This file",
            },
            "pipeline_stats": {
                "total_assets": 10,
                "total_files": 0,  # filled below
                "generation_time_seconds": 0,
            },
        }
        summary["pipeline_stats"]["total_files"] = len(list(self.output_dir.rglob("*")))
        (self.output_dir / "DEMO_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._ok(f"  DEMO_SUMMARY.json")

    def _gen_sales_script(self):
        """Generate the narrated sales script for screen recording."""
        self._log("Sales script for screen recording")

        script = f"""# TikTok AI Factory Pro — 销售演示脚本

## 录屏说明

- **时长**: ~3 分钟
- **旁白**: 按脚本朗读
- **操作**: 按 [操作] 提示点击软件
- **语速**: 中等偏快，保持热情
- **背景音乐**: 轻快电子/Tech (可选)

---

## 第一部分: 开场 (0:00 — 0:30)

**[画面: 软件主界面 — 🎬 一键生成标签页]**

> "大家好！今天给大家演示 TikTok AI Factory Pro — 全自动 TikTok AI 视频生产工厂。"

> "你只需要上传 3 个素材：一张产品图、一张人物图、一段参考视频——点击一个按钮，就能自动生成一条 TikTok UGC 风格的带货视频。"

**[操作: 鼠标指向 3 个上传卡片]**

---

## 第二部分: 一键生成 (0:30 — 1:15)

**[操作: 点击上传产品图 → 选择 DEMO_PRODUCT.png]**

> "先上传产品图。这里是一瓶 GlowRevive Serum 精华液——玫瑰金渐变的玻璃滴管瓶，非常上镜。"

**[操作: 点击上传人物图 → 选择 DEMO_CHARACTER.png]**

> "再上传人物图。Sophia，25 到 30 岁的女性美妆创作者，自然妆容，奶油色毛衣。这个人物形象会在整个视频里保持一致。"

**[操作: 点击上传参考视频]**

> "最后上传一个爆款参考视频。AI 会自动分析它的节奏、镜头长度、转场方式——然后生成结构相同但产品和人物完全不同的新视频。"

**[操作: 选择国家=美国, 数量=1, 风格=TikTok UGC]**

> "选择目标国家、视频数量和风格。这里选美国、1 条、TikTok UGC 风格。"

**[操作: 鼠标悬停在「🚀 开始生成」按钮上]**

> "准备好之后，只需要点击这一个按钮。"

---

## 第三部分: 流水线展示 (1:15 — 2:00)

**[操作: 点击开始生成 — 展示进度条和 9 步指示器]**

> "看——9 个步骤自动执行。"

> "STEP 1: GPT 生成主脚本……Hook、Problem、Solution、Social Proof、CTA，标准的 TikTok 爆款结构。"

> "STEP 2: 人物分析……锁定性别、年龄、发型、肤色、服装。后续所有镜头保持完全一致。"

> "STEP 3: 分镜生成……每个镜头精确到秒，口播和字幕一一对应。"

> "STEP 4: GPT Image 生成关键帧……6 张真人感关键帧，自然光、手机拍摄、真实皮肤纹理。"

**[操作: 切换到 DEMO_STORYBOARD.png 展示]**

> "这是自动生成的 Storyboard——5 个镜头的完整分镜表。"

---

## 第四部分: 核心卖点 (2:00 — 2:30)

**[画面: 切换到 🏭 批量工厂标签页]**

> "如果你有 10 个产品、50 个产品——切换到批量工厂模式。"

> "把产品图、人物图、参考视频放入对应文件夹，自动扫描、自动匹配、自动生成。"

> "10 个产品 × 每产品 5 条视频 = 50 条视频，全自动完成。无人值守。"

**[画面: 切换到 👤 客户中心标签页]**

> "客户中心可以实时查看授权状态、使用统计、成本分析、视频记录。"

> "每一分 API 费用都清清楚楚——OpenAI、GPT Image、ElevenLabs、Seedance——全部可追踪。"

---

## 第五部分: 收尾 (2:30 — 3:00)

**[画面: 回到主界面，展示完整输出目录]**

> "最终输出：master_script.md（主脚本）、storyboard.png（分镜图）、keyframes（6 张关键帧）、Seedance 分段 Prompt、voiceover（口播）、subtitle.srt（字幕）——最后 FFmpeg 自动合成 video_final.mp4。"

> "整个流程不需要任何人工干预。从上传素材到成品视频，全程自动化。"

> "TikTok AI Factory Pro v1.0——让你的 TikTok 短视频生产进入工业化时代。"

**[画面: 软件 Logo + 联系方式]**

> "了解更多，请联系我们。谢谢观看！"

---

## 演示素材清单

| 素材 | 文件 | 说明 |
|------|------|------|
| 产品图 | `DEMO_PRODUCT.png` | 1080×1080 产品卡片 |
| 人物图 | `DEMO_CHARACTER.png` | 1200×1600 人物一致性表 |
| 参考视频 | `input/reference_videos/reference.mp4` | 示例参考视频 |
| 主脚本 | `DEMO_SCRIPT.md` | 5 段式完整脚本 |
| 分镜表 | `DEMO_STORYBOARD.png` | 1600×1000 可视化分镜 |
| 关键帧 | `keyframes/keyframe_*.png` | 6 张 1080×1920 关键帧 |
| Seedance | `seedance_segments/` | 6 个分段 Prompt |
| 口播 | `DEMO_VOICEOVER.md` | 带时间轴的 TTS 脚本 |
| 字幕 | `DEMO_SUBTITLES.srt` | 8 条 SRT 字幕 |
| 成品视频 | `DEMO_VIDEO.mp4` | 1080×1920 30s 演示视频 |

---

## 录屏技术要求

- 分辨率: 1920×1080 或更高
- 帧率: 30fps
- 音频: 清晰录制旁白
- 鼠标: 显示点击效果
- 推荐工具: OBS Studio (免费)

---

*生成时间: {datetime.now().isoformat()}*
*生成工具: tools/demo_generator.py*
"""
        path = PROJECT_ROOT / "DEMO_SALES_SCRIPT.md"
        path.write_text(script, encoding="utf-8")
        self._ok(f"  DEMO_SALES_SCRIPT.md ({len(script)} chars, ~3 min)")

    # ================================================================
    # Helpers
    # ================================================================

    def _step_num(self) -> str:
        self._step += 1
        return f"[{self._step}/10]"

    def _log(self, msg):
        print(f"  {self._step_num()} {msg}...", end=" ", flush=True)

    def _ok(self, detail=""):
        print(f"✅ {detail}")

    def _warn(self, detail=""):
        print(f"⚠️ {detail}")


if __name__ == "__main__":
    gen = DemoGenerator()
    output = gen.generate()

    print(f"\n📁 All demo assets: {output}")
    print(f"🎬 Demo video: {output / 'DEMO_VIDEO.mp4'}")
    print(f"📝 Sales script: {PROJECT_ROOT / 'DEMO_SALES_SCRIPT.md'}")
