# CHARACTER CONSISTENCY — 统一人物系统

**版本**: Character Canon v1
**规则**: 第一张人物图 → character.json (人物圣经) → 所有镜头必须引用 → 禁止随机

---

## 1. character.json 规范

第一张人物图生成后立即保存，全视频唯一人物定义。

```json
{
  "version": "character_canon_v1",
  "locked": true,
  "rule": "SAME PERSON across ALL shots. NO random characters.",

  "identity": {
    "name": "主角",
    "gender": "female",
    "age_range": "25-30",
    "race": "east_asian"
  },

  "appearance": {
    "hair":     { "style": "long straight", "color": "black", "length": "long" },
    "face":     { "shape": "oval", "skin_tone": "natural fair" },
    "body":     { "type": "slim", "height": "165-170cm" }
  },

  "makeup": {
    "style": "natural minimal",
    "detail": "light foundation, natural brows, nude lip"
  },

  "clothing": {
    "outfit": "casual cream top",
    "style": "casual"
  },

  "vibe": {
    "overall": "friendly natural",
    "energy": "warm approachable"
  },

  "forbidden": [
    "NO hair change", "NO outfit change", "NO makeup change",
    "NO face morphing", "NO age change", "NO skin tone change",
    "NO random Seedance character", "NO re-generation",
    "NO beauty filter or plastic skin"
  ]
}
```

---

## 2. 系统流程

```
STEP 2: GPT Image 生成第一张人物图
          ↓
        save_character_canon() → character.json (人物圣经 LOCKED)
          ↓
STEP 5: keyframe_generator → load_character_canon() → 每帧强制引用
          ↓     "SAME EXACT PERSON as character.json — NO variation"
STEP 6: seedance_generator → continuity anchor 注入
          ↓     "SAME PERSON: {name}, {hair}, {clothing}"
STEP 7: ARK API → 视频生成 (同一人物锚点)
```

---

## 3. 强制规则

| 规则 | 实施方式 |
|------|---------|
| 禁止重新随机人物 | `character.json` locked=true, load时无文件抛异常 |
| 所有镜头同一人 | keyframe prompt注入 "SAME EXACT PERSON as character.json" |
| 禁止换发型 | `forbidden` 列表 + continuity engine验证 |
| 禁止换服装 | `forbidden` 列表 + clothing锁定 |
| 禁止换妆容 | `forbidden` 列表 + makeup锁定 |
| 禁止美颜滤镜 | `forbidden` 列表 + UGC prompt: "natural skin, visible pores" |

---

## 4. API

```python
from agents.character_generator import CharacterGenerator

# 保存人物圣经 (STEP 2调用)
CharacterGenerator.save_character_canon(character_info, output_dir)
# → output_dir/character.json

# 加载人物圣经 (STEP 5/6调用)
canon = CharacterGenerator.load_character_canon(output_dir)
# → dict with identity/appearance/makeup/clothing/vibe/forbidden

# 无文件时:
# → FileNotFoundError("character.json not found. NO random characters allowed.")
```

---

## 5. 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `identity.gender` | string | male/female |
| `identity.age_range` | string | 年龄段 |
| `identity.race` | string | caucasian/east_asian/african_american/latin/middle_eastern/south_asian/southeast_asian |
| `appearance.hair.style` | string | 发型 |
| `appearance.hair.color` | string | 发色 |
| `appearance.face.shape` | string | 脸型 |
| `appearance.face.skin_tone` | string | 肤色 |
| `appearance.body.type` | string | 体型 |
| `appearance.body.height` | string | 身高 |
| `clothing.outfit` | string | 服装 |
| `makeup.style` | string | 妆容 |

---

*Character Consistency System ready. One person, one canon, across all shots.*
