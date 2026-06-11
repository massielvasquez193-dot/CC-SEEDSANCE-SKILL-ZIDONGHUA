# UGC SCRIPT ENGINE — TikTok真人第一人称脚本引擎

**版本**: UGC Mode v1.0
**升级日期**: 2026-06-11

---

## 1. 核心规则

### 1.1 第一人称强制

所有脚本必须以第一人称书写:

```
"I tried this and was honestly shocked..."
"I've been dealing with this for months..."
"I don't know who needs to hear this but..."
"Run don't walk to get this..."
```

**禁止**: 第三人称、广告文案、产品说明书式描述

### 1.2 固定5段结构

```
HOOK (0-3s)     → 开场钩子, 产品立即出现
PROBLEM (3-7s)  → 真实痛点, 第一人称经历
SOLUTION (7-11s) → 发现产品, 自然演示
RESULT (11-14s)  → 效果证明, Before/After
CTA (14-15s)     → 自然推荐, 不pushy
```

---

## 2. 禁止AI描述词 (68个)

| 类别 | 禁止词 |
|------|--------|
| 外貌 | beautiful woman, beautiful girl, gorgeous, stunning |
| 质量 | high quality, premium quality, state-of-the-art, cutting-edge, world-class, exceptional |
| 电影 | cinematic, film look, movie aesthetic, professional lighting |
| 完美 | flawless, perfect, impeccable, outstanding, superb, magnificent |
| 奢侈 | luxurious, elegant, sophisticated, meticulously crafted |
| 技术 | revolutionary, game-changing, unparalleled, peerless, optimum |
| 质感 | crystal clear, vibrant colors, rich texture, silky smooth, breathtaking |
| 广播 | studio quality, broadcast ready, professional grade |

**替换规则**: `cinematic` → `real life` / `high quality` → `actually good` / `stunning` → `surprisingly good`

---

## 3. 强制真人口播语言

### 3.1 Hook开头 (12种)

```
Okay so I tried...
Wait. I need to show you...
I wasn't gonna post this but...
I honestly didn't think this would work but...
Can we talk about...
I'm actually shocked...
Nobody talks about this but...
I've been gatekeeping this but...
I don't know who needs to hear this but...
Run don't walk to...
I'm so mad I didn't try this sooner...
My jaw literally dropped when...
```

### 3.2 痛点表达 (7种)

```
I've been struggling with...
I tried everything for...
Nothing was working for my...
I was so frustrated with...
I spent way too much money on...
I almost gave up on...
For the longest time I thought...
```

### 3.3 发现产品 (5种)

```
And then I found...
Until someone told me about...
I randomly came across...
A friend put me onto...
I saw this on TikTok and...
```

### 3.4 效果证明 (7种)

```
Look at the difference...
I'm not even kidding...
This is after only...
The before and after is crazy...
I wish I had a before pic but...
My skin/whatever has never...
People have been asking me what I've been using...
```

### 3.5 CTA (7种)

```
Anyway link is in my bio...
Go check it out seriously...
I'll put the link below...
Don't walk RUN...
You're welcome in advance...
Trust me on this one...
That's it that's the review...
```

### 3.6 口语填充词 (12种)

```
like, literally, actually, honestly, I swear,
no joke, you guys, okay so, I mean, seriously,
wait, look, here's the thing, real talk
```

---

## 4. 参考TikTok爆款评论区真实语言

### 高频真实评论模式

| 模式 | 示例 |
|------|------|
| 震惊发现 | "I'm actually shocked this worked" |
| 对比失望 | "I tried everything and nothing worked until this" |
| 朋友推荐 | "My friend put me onto this and I'm so glad" |
| 意外效果 | "I wasn't expecting it to actually do anything but" |
| 持续使用 | "I've been using this for 3 weeks and" |
| 价格惊喜 | "For the price I was not expecting much but" |
| 否定开头 | "I was so skeptical but I'm not even kidding" |
| 催促行动 | "I need y'all to run to get this" |

---

## 5. 示例脚本

### 示例: 护肤品精华液 (15秒)

```
[HOOK]
Okay so I tried this serum and I was honestly shocked.

[PROBLEM]
I've been dealing with texture issues for months.
Tried so many products. Spent way too much.
Nothing was actually working. I almost gave up.

[SOLUTION]
Until my friend put me onto this.
And I was like... wait.
After only a few days — look.

[RESULT]
I'm not even kidding.
My skin has literally never looked like this.
People have been asking what I'm using.

[CTA]
Anyway I'll put the link below.
Trust me on this one.
```

### 验证

```
Banned words found: NONE
First person: YES (I, I've, my, me)
UGC tone: YES (literally, honestly, like, anyway)
Structure: HOOK → PROBLEM → SOLUTION → RESULT → CTA
```

---

## 6. 集成

```python
from agents.master_script_generator import MasterScriptGenerator

gen = MasterScriptGenerator(provider=openai_provider)
script = gen.generate(product_info, character_info, video_analysis, duration=15)
# → 自动: 第一人称 + 零AI词 + 随机UGC短语 + GPT-5.5增强
```

**无GPT降级**: 模板使用随机UGC短语组合, 同样保证第一人称+零AI词

---

*UGC Script Engine ready. Target: TikTok real-person review standard — not AI-generated content.*
