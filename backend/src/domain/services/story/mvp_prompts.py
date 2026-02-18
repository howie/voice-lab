"""MVP prompt templates for Story Experience content generation.

Feature: 016-story-experience-mvp
These prompts are used for parent-input-based content generation,
supporting age-adaptive length and both story/song content types.
"""

# =============================================================================
# Age-based length guidelines
# =============================================================================

AGE_LENGTH_MAP = {
    # age_min, age_max: (min_chars, max_chars, description)
    (2, 4): (150, 300, "短篇"),
    (5, 8): (300, 500, "中篇"),
    (9, 12): (500, 800, "長篇"),
}


def get_length_guidance(age: int) -> str:
    """Return length guidance string based on child's age."""
    for (age_min, age_max), (min_chars, max_chars, desc) in AGE_LENGTH_MAP.items():
        if age_min <= age <= age_max:
            return f"{desc}（{min_chars}-{max_chars} 字）"
    return "中篇（300-500 字）"


def get_length_range(age: int) -> tuple[int, int]:
    """Return (min_chars, max_chars) for the given age."""
    for (age_min, age_max), (min_chars, max_chars, _) in AGE_LENGTH_MAP.items():
        if age_min <= age <= age_max:
            return (min_chars, max_chars)
    return (300, 500)


# =============================================================================
# System Prompt
# =============================================================================

MVP_STORY_SYSTEM_PROMPT = """\
你是一位專業的兒童故事創作者，擅長根據父母的需求為孩子量身打造繁體中文故事和兒歌。

## 核心規則（必須嚴格遵守）
1. 所有內容必須使用繁體中文（台灣用語）
2. 語言和詞彙必須符合目標年齡的理解能力
3. 內容必須安全、正面，禁止任何暴力、恐怖或不當內容
4. 自然融入父母指定的價值觀和情緒認知元素
5. 使用父母指定的喜愛角色作為故事主角
6. 嚴格遵守指定的字數範圍

## 輸出規則
- 直接輸出故事或兒歌的文字內容，不要加任何前綴說明或後記
- 不要輸出 JSON 格式，直接輸出純文字
- 故事使用自然的段落分隔
- 兒歌使用歌詞格式（段落、副歌標記）
"""

# =============================================================================
# Story Generation Prompt
# =============================================================================

MVP_STORY_GENERATE_PROMPT = """\
請根據以下需求創作一個適合 {age} 歲孩子的繁體中文故事：

- 教導內容：{educational_content}
- 價值觀：{values}
- 情緒認知：{emotions}
- 主角：{favorite_character}
- 目標長度：{length_guidance}

要求：
1. 以「{favorite_character}」作為故事主角，賦予其鮮明個性
2. 故事情節中自然融入「{educational_content}」的學習元素
3. 體現「{values}」的正面價值觀
4. 透過角色表現展示「{emotions}」的情緒認知
5. 使用適合 {age} 歲孩子的詞彙和句式
6. 故事需有完整的起承轉合
7. 字數控制在 {min_chars}-{max_chars} 字之間

請直接輸出故事內容，使用段落分隔。
"""

# =============================================================================
# Song Generation Prompt
# =============================================================================

MVP_SONG_GENERATE_PROMPT = """\
請根據以下需求創作一首適合 {age} 歲孩子的繁體中文兒歌：

- 教導內容：{educational_content}
- 價值觀：{values}
- 情緒認知：{emotions}
- 角色/主題：{favorite_character}
- 目標長度：{length_guidance}

要求：
1. 歌詞圍繞「{favorite_character}」展開
2. 融入「{educational_content}」的學習元素
3. 體現「{values}」的正面價值觀
4. 歌詞要有韻律感，適合孩子朗朗上口
5. 使用適合 {age} 歲孩子的詞彙
6. 包含明確的段落結構（至少2段 + 副歌）
7. 副歌要有重複句，便於孩子記憶
8. 字數控制在 {min_chars}-{max_chars} 字之間

請直接輸出歌詞，使用以下格式：
【第一段】
歌詞內容...

【副歌】
歌詞內容...

【第二段】
歌詞內容...
"""

# =============================================================================
# Story Branch Prompt
# =============================================================================

MVP_STORY_BRANCH_PROMPT = """\
以下是一段已經生成的故事：

---
{story_context}
---

請基於上述故事生成 3 個可能的故事走向選項，讓故事可以延伸。

要求：
1. 每個選項以一句簡短描述概括（15-30 字）
2. 三個選項要有明顯不同的方向
3. 所有選項都必須安全、正面
4. 與原始故事的角色和風格保持一致

請以 JSON 格式輸出：
```json
{{
  "branches": [
    {{"id": "1", "description": "走向描述一"}},
    {{"id": "2", "description": "走向描述二"}},
    {{"id": "3", "description": "走向描述三"}}
  ]
}}
```
"""

MVP_STORY_BRANCH_CONTINUE_PROMPT = """\
以下是一段已經生成的故事：

---
{story_context}
---

父母選擇了以下故事走向：「{selected_branch}」

請根據選定的走向，延續上述故事，生成後續段落。

要求：
1. 自然銜接上一段的情節
2. 依循選定的走向發展
3. 保持角色性格和故事風格的一致性
4. 新段落約 150-300 字
5. 內容安全、正面

請直接輸出延續的故事段落。
"""

# =============================================================================
# Q&A Prompt
# =============================================================================

MVP_STORY_QA_GENERATE_PROMPT = """\
以下是一段為 {age} 歲孩子創作的故事：

---
{story_context}
---

請根據故事內容生成 3 個適合 {age} 歲孩子的思考問題。

要求：
1. 問題與故事內容直接相關
2. 問題要能啟發思考，不是簡單的是非題
3. 問題措辭要適合 {age} 歲孩子理解
4. 問題涵蓋不同面向（角色感受、事件原因、價值觀反思）

請以 JSON 格式輸出：
```json
{{
  "questions": [
    {{"id": "1", "text": "問題一"}},
    {{"id": "2", "text": "問題二"}},
    {{"id": "3", "text": "問題三"}}
  ]
}}
```
"""

MVP_STORY_QA_ANSWER_PROMPT = """\
以下是一段為 {age} 歲孩子創作的故事：

---
{story_context}
---

孩子（或父母）提出了以下問題：「{question}」

請根據故事內容生成一個適合 {age} 歲孩子理解的回答。

要求：
1. 回答基於故事內容
2. 語言適合 {age} 歲孩子的理解能力
3. 回答溫暖、鼓勵性，激發進一步思考
4. 控制在 50-150 字之間

請直接輸出回答內容。
"""
