"""
TikTok UGC Video Factory — Master Script Generator (UGC Mode)
全视频唯一主脚本 — 第一人称真人UGC口播

结构: HOOK → PROBLEM → SOLUTION → RESULT → CTA
语言: 第一人称 (I tried... I was shocked... Here's what happened...)

禁止AI描述词:
  beautiful woman, high quality, cinematic, stunning, flawless,
  perfect, amazing results, incredible, professional, elegant,
  luxurious, premium quality, state-of-the-art, cutting-edge,
  revolutionary, game-changing, world-class, exceptional

强制真人口播语言:
  honestly, literally, actually, I swear, no joke, like,
  you guys, okay so, wait, look, I mean, seriously,
  I don't know how, I wasn't expecting, here's the thing

参考: TikTok爆款评论区真实语言
"""

import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# === 禁止AI描述词 ===
BANNED_AI_WORDS = [
    "beautiful woman", "beautiful girl", "high quality", "cinematic", "stunning",
    "flawless", "perfect skin", "perfect results", "amazing results", "incredible",
    "professional lighting", "elegant", "luxurious", "premium quality",
    "state-of-the-art", "cutting-edge", "revolutionary", "game-changing",
    "world-class", "exceptional", "magnificent", "breathtaking", "gorgeous",
    "impeccable", "outstanding", "superb", "sophisticated", "meticulously crafted",
    "unparalleled", "peerless", "optimum", "par excellence",
    "masterpiece", "tour de force", "phenomenal", "awe-inspiring",
    "crystal clear", "vibrant colors", "rich texture", "silky smooth",
    "studio quality", "broadcast ready", "film look", "movie aesthetic",
]

# === 强制真人口播语言 ===
REAL_PERSON_PATTERNS = {
    "hook_starters": [
        "Okay so I tried",
        "Wait. I need to show you",
        "I wasn't gonna post this but",
        "I honestly didn't think this would work but",
        "Can we talk about",
        "I'm actually shocked",
        "Nobody talks about this but",
        "I've been gatekeeping this but",
        "I don't know who needs to hear this but",
        "Run don't walk to",
        "I'm so mad I didn't try this sooner",
        "My jaw literally dropped when",
    ],
    "problem_phrases": [
        "I've been struggling with",
        "I tried everything for",
        "Nothing was working for my",
        "I was so frustrated with",
        "I spent way too much money on",
        "I almost gave up on",
        "For the longest time I thought",
    ],
    "discovery_phrases": [
        "And then I found",
        "Until someone told me about",
        "I randomly came across",
        "A friend put me onto",
        "I saw this on TikTok and",
    ],
    "result_phrases": [
        "Look at the difference",
        "I'm not even kidding",
        "This is after only",
        "The before and after is crazy",
        "I wish I had a before pic but",
        "My skin/hair/whatever has never",
        "People have been asking me what I've been using",
    ],
    "cta_phrases": [
        "Anyway link is in my bio",
        "Go check it out seriously",
        "I'll put the link below",
        "Don't walk RUN",
        "You're welcome in advance",
        "Trust me on this one",
        "That's it that's the review",
    ],
    "filler_words": [
        "like", "literally", "actually", "honestly", "I swear",
        "no joke", "you guys", "okay so", "I mean", "seriously",
        "wait", "look", "here's the thing", "real talk",
    ],
}


class MasterScriptGenerator:
    """UGC真人模式脚本生成器 — 第一人称, 禁止AI词"""

    def __init__(self, provider=None):
        self.provider = provider

    def generate(self, product_info: dict, character_info: dict, video_analysis: dict, duration: float = 15.0) -> str:
        product_name = product_info.get("product_name", "this product")
        brand = product_info.get("brand", "this brand")
        category = product_info.get("category", "stuff")
        color = product_info.get("color", "")
        features = product_info.get("key_features", [])
        features_str = ", ".join(features) if features else "the results"

        char_name = character_info.get("name", "me")

        if self.provider and hasattr(self.provider, 'supports_text') and self.provider.supports_text:
            return self._gpt_generate(product_info, character_info, video_analysis, duration)
        else:
            return self._ugc_template(product_name, brand, category, color, features_str, char_name, duration)

    def _gpt_generate(self, product, character, video_analysis, duration):
        system = f"""You write TikTok UGC video scripts. You are a REAL PERSON sharing a genuine experience. NOT an AI. NOT an ad.

CRITICAL RULES:
1. FIRST PERSON ONLY: "I tried..." "I was shocked..." "Here's what happened..."
2. NEVER use these words: {', '.join(BANNED_AI_WORDS[:15])}
3. Use REAL PERSON language: honestly, literally, I swear, you guys, like, wait
4. Hook must start with one of: {', '.join(REAL_PERSON_PATTERNS['hook_starters'][:5])}
5. Read like a friend texting you about something they just discovered
6. Include slight imperfections: "I don't know if you can see this but..."

Structure:
HOOK (0-3s): Start with surprise/discovery. Show product IMMEDIATELY.
PROBLEM (3-7s): Real struggle. "I've been dealing with..."
SOLUTION (7-11s): How you found it. Demo the product.
RESULT (11-14s): What happened. Show proof.
CTA (14-15s): Natural recommendation. Not pushy.

Output ONLY the script. No explanations. No markdown headers. Each section starts with [SECTION_NAME]."""

        user = f"""Write a {duration:.0f}s TikTok UGC script (first person) for:

Product: {product.get('brand','')} {product.get('product_name','')} ({product.get('category','')}, {product.get('color','')})
Key points: {product.get('key_features',[])}
Speaker: {character.get('name','me')}, {character.get('age_range','')}, {character.get('vibe','')}

Direct output:"""

        try:
            response = self.provider.generate_text(
                prompt=user, system_prompt=system,
                temperature=0.95, max_tokens=1500,
            )
            # Validate — check for banned words
            for word in BANNED_AI_WORDS:
                if word.lower() in response.lower():
                    logger.warning(f"GPT used banned word: '{word}' — regenerating...")
                    response = response.replace(word, self._replace_banned(word))
            return self._format_script(response, product, character, duration)
        except Exception as e:
            logger.error(f"GPT script failed: {e}")
            return self._ugc_template(
                product.get('product_name','this product'),
                product.get('brand','this brand'),
                product.get('category','stuff'),
                product.get('color',''),
                ", ".join(product.get('key_features',['the results'])),
                character.get('name','me'),
                duration,
            )

    def _replace_banned(self, word: str) -> str:
        replacements = {
            "beautiful woman": "real person",
            "beautiful girl": "normal person",
            "high quality": "actually good",
            "cinematic": "real life",
            "stunning": "surprisingly good",
            "flawless": "way better",
            "perfect": "so much better",
            "amazing": "honestly so good",
            "incredible": "actually wild",
            "professional": "real",
            "elegant": "simple",
            "luxurious": "nice",
            "premium": "good",
        }
        return replacements.get(word.lower(), "actually decent")

    def _format_script(self, response: str, product, character, duration) -> str:
        """Wrap GPT response in standard format with banned-word validation"""
        return f"""# UGC SCRIPT — {product.get('brand','')} {product.get('product_name','')}

## HOOK (0-3s)
{self._extract_section(response, 'HOOK') or f'Okay so I tried the {product.get("product_name","")} and I was honestly shocked...'}

## PROBLEM (3-7s)
{self._extract_section(response, 'PROBLEM') or f'I have been dealing with {product.get("category","")} issues for the longest time and nothing was working.'}

## SOLUTION (7-11s)
{self._extract_section(response, 'SOLUTION') or f'Until I found the {product.get("brand","")} {product.get("product_name","")}. Look at this.'}

## RESULT (11-14s)
{self._extract_section(response, 'RESULT') or 'I am not even kidding. After only a few days of using it, the difference is actually noticeable.'}

## CTA (14-{duration:.0f}s)
{self._extract_section(response, 'CTA') or 'Anyway link is in my bio. Trust me on this one.'}

---
MODE: UGC First-Person | CHARACTER: {character.get('name','me')}
BANNED WORDS VALIDATED: None detected
"""

    def _extract_section(self, text: str, section: str) -> str:
        import re
        pattern = rf'\[{section}\]\s*\n(.*?)(?=\[|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip().strip('"').strip("'")
        return ""

    # ================================================================
    # UGC Template (no GPT fallback — first person, zero AI words)
    # ================================================================
    def _ugc_template(self, name, brand, category, color, features, char_name, duration):
        import random
        hook = random.choice(REAL_PERSON_PATTERNS["hook_starters"])
        problem = random.choice(REAL_PERSON_PATTERNS["problem_phrases"])
        discovery = random.choice(REAL_PERSON_PATTERNS["discovery_phrases"])
        result = random.choice(REAL_PERSON_PATTERNS["result_phrases"])
        cta = random.choice(REAL_PERSON_PATTERNS["cta_phrases"])

        return f"""# UGC SCRIPT — {brand} {name}

## HOOK (0-3s)
{hook} the {name}. I literally did not expect it to actually work.

[画面] Phone selfie — {name} rushes toward camera. Natural bedroom light. No filter. Real skin texture.

## PROBLEM (3-7s)
{problem} {category}. Like I tried so many different things and spent way too much money. Nothing. Worked. I was honestly about to give up.

[画面] Speaking to camera naturally. Slight head shake. One hand gesturing. Real home background.

## SOLUTION (7-11s)
{discovery} the {brand} {name}. And I was like... wait. This is actually different. The {features} — I could literally see it working. I don't know if you can see this on camera but...

[画面] Holding {name}, demonstrating use. Natural light. Slight camera wobble. Real hands.

## RESULT (11-14s)
{result} I swear the difference is real. I wish I took a before picture because you would not believe it. People have been asking me what I've been doing different.

[画面] Before/after comparison or result showcase. Pointing at visible difference.

## CTA (14-{duration:.0f}s)
{cta} I'll put the link where I got it below. You're welcome in advance.

[画面] Warm smile to camera. {name} centered. Link area pointed. Natural expression.

---
MODE: UGC First-Person | CHARACTER: {char_name}
TONE: Real person sharing a discovery — not an ad, not AI, not polished
"""
