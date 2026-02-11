"""Pre-built story templates for StoryPal.

Five default templates covering all story categories,
each with characters, scenes, and age-appropriate prompts.
"""

from uuid import UUID

from src.domain.entities.story import (
    SceneInfo,
    StoryCategory,
    StoryCharacter,
    StoryTemplate,
)

# Fixed UUIDs for default templates (reproducible across restarts)
_TEMPLATE_IDS = {
    "brave_rabbit": UUID("a1b2c3d4-1111-4000-8000-000000000001"),
    "space_explorer": UUID("a1b2c3d4-2222-4000-8000-000000000002"),
    "magic_kitchen": UUID("a1b2c3d4-3333-4000-8000-000000000003"),
    "ocean_adventure": UUID("a1b2c3d4-4444-4000-8000-000000000004"),
    "time_machine": UUID("a1b2c3d4-5555-4000-8000-000000000005"),
}


def get_default_templates() -> list[StoryTemplate]:
    """Return all pre-built story templates."""
    return [
        _brave_rabbit_template(),
        _space_explorer_template(),
        _magic_kitchen_template(),
        _ocean_adventure_template(),
        _time_machine_template(),
    ]


def _brave_rabbit_template() -> StoryTemplate:
    """勇敢小兔的森林冒險 - fairy tale forest adventure."""
    return StoryTemplate(
        id=_TEMPLATE_IDS["brave_rabbit"],
        name="勇敢小兔的森林冒險",
        description="小兔子棉花糖在神秘森林中展開一場勇敢的冒險，途中遇到各種有趣的動物朋友，一起克服困難、解決謎題。",
        category=StoryCategory.FAIRY_TALE,
        target_age_min=4,
        target_age_max=8,
        language="zh-TW",
        characters=[
            StoryCharacter(
                name="棉花糖",
                description="一隻勇敢又善良的小白兔，耳朵特別長，最喜歡吃胡蘿蔔，口頭禪是「沒問題的！」",
                voice_provider="azure",
                voice_id="zh-TW-HsiaoChenNeural",
                voice_settings={"pitch": "+10%", "rate": "+5%"},
                emotion="happy",
            ),
            StoryCharacter(
                name="松果爺爺",
                description="一隻年老的松鼠，住在最高的橡樹上，知道森林裡所有的祕密，說話慢悠悠的",
                voice_provider="azure",
                voice_id="zh-TW-YunJheNeural",
                voice_settings={"pitch": "-15%", "rate": "-10%"},
                emotion="neutral",
            ),
            StoryCharacter(
                name="小螢",
                description="一隻會發光的螢火蟲，個性活潑愛笑，負責在黑暗中照路，口頭禪是「亮晶晶～」",
                voice_provider="azure",
                voice_id="zh-TW-HsiaoChenNeural",
                voice_settings={"pitch": "+20%", "rate": "+10%"},
                emotion="excited",
            ),
            StoryCharacter(
                name="大熊呼嚕",
                description="一隻看起來很兇但其實很膽小的棕熊，最怕打雷，喜歡吃蜂蜜",
                voice_provider="azure",
                voice_id="zh-TW-YunJheNeural",
                voice_settings={"pitch": "-20%", "rate": "-5%"},
                emotion="neutral",
            ),
        ],
        scenes=[
            SceneInfo(
                name="兔子的家",
                description="一個溫馨的樹洞小屋，門口種了好多胡蘿蔔",
                bgm_prompt="Gentle morning music with birds chirping, soft flute melody, peaceful countryside",
                mood="warm",
            ),
            SceneInfo(
                name="神秘森林入口",
                description="高聳的大樹形成一道綠色的拱門，地上落葉沙沙作響",
                bgm_prompt="Mysterious forest ambience, gentle wind through trees, magical sparkle sounds",
                mood="mysterious",
            ),
            SceneInfo(
                name="螢火蟲洞穴",
                description="一個閃閃發光的洞穴，天花板上滿是螢火蟲，像星星一樣",
                bgm_prompt="Magical cave with echoing water drops, ethereal glowing sounds, wonder theme",
                mood="magical",
            ),
            SceneInfo(
                name="彩虹瀑布",
                description="一道巨大的瀑布，水花在陽光下形成美麗的彩虹",
                bgm_prompt="Majestic waterfall sounds, uplifting orchestral music, triumphant adventure theme",
                mood="triumphant",
            ),
        ],
        opening_prompt="棉花糖收到了松果爺爺的神秘信件，信上說森林深處有一顆許願星掉落了，需要勇敢的小動物去找到它。",
        system_prompt="這是一個關於勇氣和友誼的森林冒險故事。小兔子棉花糖要穿越神秘森林尋找許願星。途中會遇到需要幫助的動物朋友，需要解決各種謎題和挑戰。故事傳達勇氣、友誼和互助的價值觀。每個場景都有獨特的挑戰，角色之間會有有趣的互動和對話。",
        is_default=True,
    )


def _space_explorer_template() -> StoryTemplate:
    """星際小太空人 - science/adventure space exploration."""
    return StoryTemplate(
        id=_TEMPLATE_IDS["space_explorer"],
        name="星際小太空人",
        description="小太空人小星和機器人夥伴嗶嗶搭乘太空船探索太陽系，拜訪各個星球，學習有趣的太空知識。",
        category=StoryCategory.SCIENCE,
        target_age_min=5,
        target_age_max=10,
        language="zh-TW",
        characters=[
            StoryCharacter(
                name="小星",
                description="一位充滿好奇心的小太空人，戴著星星形狀的頭盔，口頭禪是「太酷了！」",
                voice_provider="azure",
                voice_id="zh-TW-HsiaoChenNeural",
                voice_settings={"pitch": "+5%", "rate": "+5%"},
                emotion="curious",
            ),
            StoryCharacter(
                name="嗶嗶",
                description="小星的機器人夥伴，圓滾滾的身體，會發出嗶嗶聲，知識豐富但偶爾會當機",
                voice_provider="azure",
                voice_id="zh-TW-YunJheNeural",
                voice_settings={"pitch": "+10%", "rate": "+15%"},
                emotion="neutral",
            ),
            StoryCharacter(
                name="月兔姐姐",
                description="住在月球上的太空站站長，溫柔又聰明，喜歡種月球花",
                voice_provider="azure",
                voice_id="zh-TW-HsiaoChenNeural",
                voice_settings={"pitch": "0%", "rate": "0%"},
                emotion="happy",
            ),
            StoryCharacter(
                name="火星小怪獸古力",
                description="住在火星上的友善小外星人，橘色的皮膚，三隻眼睛，很怕水",
                voice_provider="azure",
                voice_id="zh-TW-YunJheNeural",
                voice_settings={"pitch": "+25%", "rate": "+5%"},
                emotion="excited",
            ),
        ],
        scenes=[
            SceneInfo(
                name="太空站控制室",
                description="閃爍的螢幕和按鈕，窗外可以看到美麗的地球",
                bgm_prompt="Futuristic space station ambience, gentle electronic beeps, calm sci-fi background",
                mood="exciting",
            ),
            SceneInfo(
                name="月球表面",
                description="灰白色的月球表面，可以看到巨大的隕石坑和遠處的地球",
                bgm_prompt="Low gravity ethereal music, soft celestial tones, moonlight waltz",
                mood="wonder",
            ),
            SceneInfo(
                name="火星沙漠",
                description="紅色的沙漠一望無際，天空是橘紅色的，遠處有一座火山",
                bgm_prompt="Mars exploration theme, dramatic desert winds, adventurous orchestral music",
                mood="adventurous",
            ),
            SceneInfo(
                name="土星環",
                description="太空船穿過壯觀的土星環，冰晶和岩石碎片在周圍閃閃發光",
                bgm_prompt="Majestic space orchestra, sweeping cosmic strings, awe-inspiring celestial music",
                mood="majestic",
            ),
        ],
        opening_prompt="今天是小星第一次獨自駕駛太空船出任務！任務是去各個星球收集「星光種子」，集齊五顆就能種出一棵星光樹。",
        system_prompt="這是一個太空探索科普冒險故事。小太空人小星和機器人嗶嗶探索太陽系各星球。每到一個星球都會學到真實的太空知識（如重力、溫度、大氣等），但用有趣的方式呈現。融入科學好奇心和探索精神的價值觀。嗶嗶會適時提供科學小知識。",
        is_default=True,
    )


def _magic_kitchen_template() -> StoryTemplate:
    """小廚師的魔法廚房 - daily life magical cooking adventure."""
    return StoryTemplate(
        id=_TEMPLATE_IDS["magic_kitchen"],
        name="小廚師的魔法廚房",
        description="小廚師小圓在魔法廚房裡，食材會說話、鍋子會唱歌，每道料理都能帶來神奇的效果！",
        category=StoryCategory.DAILY_LIFE,
        target_age_min=3,
        target_age_max=7,
        language="zh-TW",
        characters=[
            StoryCharacter(
                name="小圓",
                description="一位戴著大廚師帽的小朋友，帽子老是歪歪的，熱愛做菜，口頭禪是「加點魔法調味料！」",
                voice_provider="azure",
                voice_id="zh-TW-HsiaoChenNeural",
                voice_settings={"pitch": "+10%", "rate": "+5%"},
                emotion="happy",
            ),
            StoryCharacter(
                name="胡蘿蔔先生",
                description="一根紳士般的胡蘿蔔，戴著單片眼鏡，說話很有禮貌，知道很多營養知識",
                voice_provider="azure",
                voice_id="zh-TW-YunJheNeural",
                voice_settings={"pitch": "+5%", "rate": "-5%"},
                emotion="neutral",
            ),
            StoryCharacter(
                name="鍋鍋",
                description="一個會唱歌的大鍋子，煮東西的時候會哼歌，脾氣很好但怕冷",
                voice_provider="azure",
                voice_id="zh-TW-YunJheNeural",
                voice_settings={"pitch": "-10%", "rate": "0%"},
                emotion="happy",
            ),
            StoryCharacter(
                name="糖糖",
                description="一顆愛撒嬌的方糖，甜甜的聲音，有時候會偷偷跳進料理裡",
                voice_provider="azure",
                voice_id="zh-TW-HsiaoChenNeural",
                voice_settings={"pitch": "+25%", "rate": "+10%"},
                emotion="excited",
            ),
        ],
        scenes=[
            SceneInfo(
                name="魔法廚房",
                description="色彩繽紛的廚房，鍋碗瓢盆都有眼睛和嘴巴，空氣中飄著香味",
                bgm_prompt="Playful kitchen sounds, cheerful xylophone melody, cooking show jingle, happy rhythm",
                mood="cheerful",
            ),
            SceneInfo(
                name="食材花園",
                description="後院的魔法花園，蔬菜水果長在彩虹色的土地上，會自己跳舞",
                bgm_prompt="Garden music with nature sounds, gentle guitar, playful woodwind melody",
                mood="playful",
            ),
            SceneInfo(
                name="調味料閣樓",
                description="充滿神秘瓶罐的閣樓，每個瓶子裡都有不同顏色的魔法粉末",
                bgm_prompt="Mysterious magical sounds, tinkling bells, enchanted music box melody",
                mood="mysterious",
            ),
            SceneInfo(
                name="美食派對",
                description="大家圍在桌旁品嚐小圓做的料理，桌上擺滿了色彩繽紛的美食",
                bgm_prompt="Celebration party music, cheerful brass fanfare, happy clapping rhythm",
                mood="celebration",
            ),
        ],
        opening_prompt="今天是魔法廚房的「美食挑戰日」！小圓要做出一道能讓大家都笑起來的料理，但是需要找到三種特別的魔法食材。",
        system_prompt="這是一個發生在魔法廚房的生活冒險故事。小廚師小圓要做出神奇料理，途中食材們會幫忙或搗蛋。故事融入基本的飲食知識和健康觀念（如蔬菜的營養、均衡飲食等），但用有趣好玩的方式呈現。強調創意、合作和不怕失敗的價值觀。",
        is_default=True,
    )


def _ocean_adventure_template() -> StoryTemplate:
    """海底探險隊 - science underwater exploration."""
    return StoryTemplate(
        id=_TEMPLATE_IDS["ocean_adventure"],
        name="海底探險隊",
        description="潛水小隊長小海帶領探險隊潛入深海，探索珊瑚礁、海底火山和神秘海溝，認識各種海洋生物。",
        category=StoryCategory.SCIENCE,
        target_age_min=5,
        target_age_max=9,
        language="zh-TW",
        characters=[
            StoryCharacter(
                name="小海",
                description="勇敢的潛水小隊長，戴著藍色潛水鏡，最喜歡海龜，口頭禪是「潛下去看看！」",
                voice_provider="azure",
                voice_id="zh-TW-HsiaoChenNeural",
                voice_settings={"pitch": "+5%", "rate": "+5%"},
                emotion="excited",
            ),
            StoryCharacter(
                name="泡泡",
                description="一隻聰明的海豚，會用泡泡排出各種形狀來溝通，是小海最好的朋友",
                voice_provider="azure",
                voice_id="zh-TW-HsiaoChenNeural",
                voice_settings={"pitch": "+15%", "rate": "+10%"},
                emotion="happy",
            ),
            StoryCharacter(
                name="珊瑚奶奶",
                description="一片活了一百年的珊瑚，知道海底所有的故事和祕密，說話溫柔緩慢",
                voice_provider="azure",
                voice_id="zh-TW-HsiaoChenNeural",
                voice_settings={"pitch": "-5%", "rate": "-15%"},
                emotion="neutral",
            ),
            StoryCharacter(
                name="墨墨",
                description="一隻害羞的小章魚，緊張時會噴墨汁，但其實很聰明，擅長解謎",
                voice_provider="azure",
                voice_id="zh-TW-YunJheNeural",
                voice_settings={"pitch": "+10%", "rate": "-5%"},
                emotion="neutral",
            ),
        ],
        scenes=[
            SceneInfo(
                name="海邊碼頭",
                description="陽光燦爛的碼頭，海風吹拂，潛水船停靠在旁邊",
                bgm_prompt="Ocean waves, seagull calls, cheerful sea shanty melody, sunny day ambience",
                mood="bright",
            ),
            SceneInfo(
                name="珊瑚礁花園",
                description="五彩繽紛的珊瑚礁，各種魚兒在其中游來游去，像水底的花園",
                bgm_prompt="Underwater tropical reef ambience, gentle bubbles, peaceful aquatic melody",
                mood="beautiful",
            ),
            SceneInfo(
                name="深海峽谷",
                description="越來越深的海底峽谷，光線漸暗，奇怪的發光生物開始出現",
                bgm_prompt="Deep ocean mystery theme, low rumbling, bioluminescent sparkle sounds, suspenseful",
                mood="mysterious",
            ),
            SceneInfo(
                name="海底火山",
                description="溫暖的海底火山口，氣泡從地面冒出，周圍有特殊的生物群落",
                bgm_prompt="Dramatic volcanic underwater sounds, rumbling bass, epic adventure crescendo",
                mood="dramatic",
            ),
        ],
        opening_prompt="珊瑚奶奶告訴小海，深海裡有一顆「海之心」寶石正在失去光芒，如果它完全熄滅，海洋的顏色就會消失。小海決定帶領探險隊去尋找讓海之心重新發光的方法。",
        system_prompt="這是一個海底探索科普冒險故事。小海帶領探險隊深入海洋尋找海之心。每到一個海域都會認識真實的海洋生物和海洋知識（如珊瑚礁生態、深海生物、海洋保育等）。融入環保意識和團隊合作的價值觀。泡泡和墨墨各有專長，需要大家合作才能完成任務。",
        is_default=True,
    )


def _time_machine_template() -> StoryTemplate:
    """時光機器之旅 - fairy tale/science time travel adventure."""
    return StoryTemplate(
        id=_TEMPLATE_IDS["time_machine"],
        name="時光機器之旅",
        description="小發明家阿奇意外啟動了爺爺的時光機器，和貓咪夥伴喵喵穿越到不同的時代，展開一場跨越時空的大冒險。",
        category=StoryCategory.FAIRY_TALE,
        target_age_min=5,
        target_age_max=10,
        language="zh-TW",
        characters=[
            StoryCharacter(
                name="阿奇",
                description="一位愛發明東西的小男孩，戴著圓圓的眼鏡，口袋裡總是裝滿小工具，口頭禪是「讓我想想辦法！」",
                voice_provider="azure",
                voice_id="zh-TW-YunJheNeural",
                voice_settings={"pitch": "+15%", "rate": "+5%"},
                emotion="curious",
            ),
            StoryCharacter(
                name="喵喵",
                description="阿奇的貓咪夥伴，穿越時空後突然會說話了，愛吐槽但很忠心，口頭禪是「喵的！」",
                voice_provider="azure",
                voice_id="zh-TW-HsiaoChenNeural",
                voice_settings={"pitch": "+20%", "rate": "+10%"},
                emotion="neutral",
            ),
            StoryCharacter(
                name="鐘伯伯",
                description="時光機器裡的 AI 管家，是個老式懷錶的形象，對每個時代都很熟悉，說話像念古文",
                voice_provider="azure",
                voice_id="zh-TW-YunJheNeural",
                voice_settings={"pitch": "-10%", "rate": "-10%"},
                emotion="neutral",
            ),
            StoryCharacter(
                name="小恐龍嘟嘟",
                description="在恐龍時代認識的友善小三角龍，意外跟著一起穿越了，對現代世界很好奇",
                voice_provider="azure",
                voice_id="zh-TW-YunJheNeural",
                voice_settings={"pitch": "+20%", "rate": "0%"},
                emotion="excited",
            ),
        ],
        scenes=[
            SceneInfo(
                name="阿奇的閣樓",
                description="堆滿了爺爺舊發明的閣樓，角落裡有一台被布蓋住的神秘機器",
                bgm_prompt="Curious tinkering sounds, music box melody, grandfather clock ticking, cozy attic",
                mood="curious",
            ),
            SceneInfo(
                name="恐龍時代",
                description="巨大的蕨類植物和高聳的樹木，遠處傳來恐龍的叫聲",
                bgm_prompt="Prehistoric jungle ambience, dinosaur roars in distance, tribal drums, epic adventure",
                mood="exciting",
            ),
            SceneInfo(
                name="古代城堡",
                description="一座中世紀的石頭城堡，旗幟飄揚，騎士在訓練場上練劍",
                bgm_prompt="Medieval castle atmosphere, trumpets, horse hooves, noble court music",
                mood="grand",
            ),
            SceneInfo(
                name="未來城市",
                description="飛行車在透明的管道中穿梭，到處都是全息投影，機器人在路上走動",
                bgm_prompt="Futuristic cityscape sounds, electronic synth melody, flying cars whooshing, cyberpunk",
                mood="wonder",
            ),
        ],
        opening_prompt="阿奇在爺爺的閣樓裡發現了一台奇怪的機器，上面寫著「時光旅行器 - 請小心使用」。好奇的阿奇忍不住按了一個大紅按鈕……",
        system_prompt="這是一個穿越時空的冒險故事，融合童話和科普元素。阿奇和夥伴們穿越到不同時代（恐龍時代、古代、未來），每個時代都會學到有趣的歷史和科學知識。故事傳達好奇心、解決問題的能力和珍惜當下的價值觀。鐘伯伯會提供歷史知識，喵喵負責吐槽和搞笑。他們的目標是修好時光機回到現代。",
        is_default=True,
    )
