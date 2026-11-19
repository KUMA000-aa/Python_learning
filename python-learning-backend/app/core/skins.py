"""
皮肤系统（全站唯一口径）

和「头像框」的区别：
    头像框只是头像周围的一圈装饰，改的是一张图；
    皮肤改的是整个界面的观感——页面底色、卡片质感、主色、顶部 hero 渐变、导航栏。

设计要点：
1) 皮肤只定义「色板令牌」，不写任何样式规则。前端把令牌转成 CSS 变量，
   各页面用 var(--sk-primary) 之类取值，所以加皮肤不用改页面；
2) 解锁条件只有两种：
   - level      达到指定等级（跟头像框同一套等级口径）
   - full_stars 所有关卡都拿到 3 星（成就类，给「技术流」一个专属款）
3) 每个皮肤都自带 dark 标记。深色皮肤要求页面所有文字/卡片都走变量，
   否则会出现「深底浅卡片里黑字」这种脏搭配。

色板令牌（tokens）字段说明：
    bg            页面底色
    glow          背景氛围光的颜色（半透明，铺在页面顶部）
    card          卡片底色
    border        卡片描边
    text          主要文字
    sub           次要文字
    muted         更淡的说明文字
    line          分割线
    track         进度条/进度槽底色
    primary       主色（按钮、进度、选中态）
    primary_dark  主色暗调（按钮立体投影）
    primary_soft  主色浅底（选中行、浅色标签）
    accent        强调色（星星、气泡、特殊标记）
    on_primary    主色上的文字色
    hero_from     顶部 hero 渐变起色
    hero_to       顶部 hero 渐变止色
    hero_text     hero 上的文字色
    hero_border   hero 描边（深色皮肤靠它做出霓虹边）
    nav           导航栏底色
    nav_text      导航栏文字（只接受 '#ffffff' / '#000000'，微信只认这两值）
"""

DEFAULT_SKIN = "classic"

# 稀有度：只影响前端标签配色与文案，不参与解锁判断
RARITIES = {
    "normal": {"name": "普通", "color": "#8A94A6", "light": "#F2F4F7"},
    "rare": {"name": "稀有", "color": "#1CB0F6", "light": "#E8F6FF"},
    "epic": {"name": "史诗", "color": "#A855F7", "light": "#F4EBFF"},
    "legend": {"name": "传说", "color": "#E0A100", "light": "#FFF7E0"},
    "limited": {"name": "限定", "color": "#FF5E93", "light": "#FFEDF3"},
}

SKINS = [
    {
        "id": "classic",
        "name": "原野绿",
        "subtitle": "默认皮肤 · 一起从零开始",
        "desc": "最耐看的一套配色，绿白搭配不刺眼，长时间刷题也不累。",
        "emoji": "🌿",
        "rarity": "normal",
        "unlock_type": "level",
        "min_level": 1,
        "dark": False,
        "tags": ["护眼", "元气"],
        "tokens": {
            "bg": "#F7F7F9",
            "glow": "rgba(88, 204, 2, 0.10)",
            "card": "#FFFFFF",
            "border": "#EFF1F3",
            "text": "#3C3C3C",
            "sub": "#6E6E6E",
            "muted": "#A8A8A8",
            "line": "#F0F0F0",
            "track": "#EFEFEF",
            "primary": "#58CC02",
            "primary_dark": "#46A302",
            "primary_soft": "#EFF9E6",
            "accent": "#FFC800",
            "on_primary": "#FFFFFF",
            "hero_from": "#58CC02",
            "hero_to": "#37A000",
            "hero_text": "#FFFFFF",
            "hero_border": "rgba(255, 255, 255, 0.22)",
            "nav": "#4BB802",
            "nav_text": "#ffffff",
        },
    },
    {
        "id": "ocean",
        "name": "深海蓝",
        "subtitle": "Lv2 解锁 · 冷静专注",
        "desc": "蓝青渐变像下潜到海底，适合晚上安静地推关卡。",
        "emoji": "🌊",
        "rarity": "normal",
        "unlock_type": "level",
        "min_level": 2,
        "dark": False,
        "tags": ["专注", "清爽"],
        "tokens": {
            "bg": "#F0F6FC",
            "glow": "rgba(28, 176, 246, 0.12)",
            "card": "#FFFFFF",
            "border": "#E2EEF8",
            "text": "#1F2D3D",
            "sub": "#5B7285",
            "muted": "#93A6B6",
            "line": "#E8F0F7",
            "track": "#E6EFF7",
            "primary": "#1CB0F6",
            "primary_dark": "#1489C4",
            "primary_soft": "#E6F5FE",
            "accent": "#17C3B2",
            "on_primary": "#FFFFFF",
            "hero_from": "#2AA9F0",
            "hero_to": "#0A4F86",
            "hero_text": "#FFFFFF",
            "hero_border": "rgba(255, 255, 255, 0.22)",
            "nav": "#0F7FD0",
            "nav_text": "#ffffff",
        },
    },
    {
        "id": "sakura",
        "name": "樱花粉",
        "subtitle": "Lv4 解锁 · 温柔一点",
        "desc": "粉白配色配暖橙星星，答错题的时候也不会太有压力。",
        "emoji": "🌸",
        "rarity": "rare",
        "unlock_type": "level",
        "min_level": 4,
        "dark": False,
        "tags": ["温柔", "治愈"],
        "tokens": {
            "bg": "#FFF4F8",
            "glow": "rgba(255, 94, 147, 0.12)",
            "card": "#FFFFFF",
            "border": "#FBE4EC",
            "text": "#3E2A33",
            "sub": "#7A5B67",
            "muted": "#B294A0",
            "line": "#FBEAF0",
            "track": "#FBE6EE",
            "primary": "#FF5E93",
            "primary_dark": "#E13E76",
            "primary_soft": "#FFEAF1",
            "accent": "#FFB86B",
            "on_primary": "#FFFFFF",
            "hero_from": "#FF8FB0",
            "hero_to": "#E2467C",
            "hero_text": "#FFFFFF",
            "hero_border": "rgba(255, 255, 255, 0.28)",
            "nav": "#F0558A",
            "nav_text": "#ffffff",
        },
    },
    {
        "id": "parchment",
        "name": "羊皮卷",
        "subtitle": "Lv6 解锁 · 复古手稿",
        "desc": "牛皮纸底 + 棕墨主色，像在翻一本旧 Python 手册。",
        "emoji": "📜",
        "rarity": "rare",
        "unlock_type": "level",
        "min_level": 6,
        "dark": False,
        "tags": ["复古", "纸感"],
        "tokens": {
            "bg": "#F4EADA",
            "glow": "rgba(169, 116, 63, 0.14)",
            "card": "#FFFBF2",
            "border": "#EADFC8",
            "text": "#43331F",
            "sub": "#7A6448",
            "muted": "#A89577",
            "line": "#EDE2CC",
            "track": "#E8DCC5",
            "primary": "#B0722F",
            "primary_dark": "#8C5620",
            "primary_soft": "#F8EEDC",
            "accent": "#C0392B",
            "on_primary": "#FFF9EE",
            "hero_from": "#C68F55",
            "hero_to": "#7E5122",
            "hero_text": "#FFF8EA",
            "hero_border": "rgba(255, 248, 234, 0.28)",
            "nav": "#9A6226",
            "nav_text": "#ffffff",
        },
    },
    {
        "id": "aurora",
        "name": "极光",
        "subtitle": "限定 · 全部关卡 3 星通关",
        "desc": "紫到青的极光渐变。不是熬时间拿的，是把每一关都打到满分换来的。",
        "emoji": "🌌",
        "rarity": "limited",
        "unlock_type": "full_stars",
        "min_level": 1,
        "dark": False,
        "tags": ["限定", "满星"],
        "tokens": {
            "bg": "#F3F0FF",
            "glow": "rgba(124, 92, 255, 0.14)",
            "card": "#FFFFFF",
            "border": "#E7E2FB",
            "text": "#2C2545",
            "sub": "#635B85",
            "muted": "#9C95BC",
            "line": "#EDE9FB",
            "track": "#EAE5FA",
            "primary": "#7C5CFF",
            "primary_dark": "#5B3FD6",
            "primary_soft": "#F0EBFF",
            "accent": "#00D4C8",
            "on_primary": "#FFFFFF",
            "hero_from": "#8B5CF6",
            "hero_to": "#12B5C9",
            "hero_text": "#FFFFFF",
            "hero_border": "rgba(255, 255, 255, 0.26)",
            "nav": "#6D4BE8",
            "nav_text": "#ffffff",
        },
    },
    {
        "id": "cyber",
        "name": "赛博夜",
        "subtitle": "Lv9 解锁 · 深色 · 霓虹",
        "desc": "深底 + 电光蓝，夜间刷题专用。全程深色卡片，眼睛不容易干。",
        "emoji": "🌃",
        "rarity": "epic",
        "unlock_type": "level",
        "min_level": 9,
        "dark": True,
        "tags": ["深色", "夜间"],
        "tokens": {
            "bg": "#0D0F16",
            "glow": "rgba(0, 229, 255, 0.10)",
            "card": "#161A25",
            "border": "#242A3A",
            "text": "#E9EFFA",
            "sub": "#9AA6C0",
            "muted": "#6D7896",
            "line": "#232938",
            "track": "#1E2431",
            "primary": "#4C6FFF",
            "primary_dark": "#2F4EDC",
            "primary_soft": "#1A2340",
            "accent": "#00E5FF",
            "on_primary": "#FFFFFF",
            "hero_from": "#2A2168",
            "hero_to": "#0B0E18",
            "hero_text": "#EAF6FF",
            "hero_border": "rgba(0, 229, 255, 0.35)",
            "nav": "#10141F",
            "nav_text": "#ffffff",
        },
    },
    {
        "id": "royal",
        "name": "曜金",
        "subtitle": "Lv13 解锁 · 深色 · 黑金",
        "desc": "黑底描金边，段位越高越压得住。适合已经打到王者段的人。",
        "emoji": "👑",
        "rarity": "legend",
        "unlock_type": "level",
        "min_level": 13,
        "dark": True,
        "tags": ["深色", "尊贵"],
        "tokens": {
            "bg": "#100E0A",
            "glow": "rgba(232, 185, 58, 0.10)",
            "card": "#1A1712",
            "border": "#2A241A",
            "text": "#F5EEDC",
            "sub": "#B9AE93",
            "muted": "#877C63",
            "line": "#262117",
            "track": "#221D14",
            "primary": "#B5820A",
            "primary_dark": "#8A6104",
            "primary_soft": "#241E12",
            "accent": "#F2C14E",
            "on_primary": "#FFF6DF",
            "hero_from": "#3A2A12",
            "hero_to": "#14100A",
            "hero_text": "#F7EDD6",
            "hero_border": "rgba(242, 193, 78, 0.40)",
            "nav": "#100E0A",
            "nav_text": "#ffffff",
        },
    },
]


# ===== 查询 =====
def find_skin(skin_id: str | None) -> dict | None:
    for skin in SKINS:
        if skin["id"] == skin_id:
            return skin
    return None


def default_skin() -> dict:
    return find_skin(DEFAULT_SKIN) or SKINS[0]


def rarity_of(skin: dict) -> dict:
    return RARITIES.get(skin.get("rarity", "normal"), RARITIES["normal"])


# ===== 解锁判断 =====
def is_unlocked(skin: dict, level: int, total_stars: int = 0, max_stars: int = 0) -> bool:
    """
    两种解锁条件共用同一个入口，避免各处各写一份判断。
    full_stars 需要 max_stars > 0（一关都没有时不算解锁，不然新用户白拿限定皮肤）。
    """
    if skin.get("unlock_type") == "full_stars":
        return max_stars > 0 and total_stars >= max_stars
    return int(level) >= int(skin.get("min_level", 1))


def unlock_hint(skin: dict, level: int, total_stars: int = 0, max_stars: int = 0) -> str:
    """一句话说明怎么解锁，直接给前端显示，前端不再拼字符串"""
    if skin.get("unlock_type") == "full_stars":
        if max_stars <= 0:
            return "通关任意关卡后开始计算"
        return f"已获 {total_stars}/{max_stars} 星"
    left = max(int(skin.get("min_level", 1)) - int(level), 0)
    if left <= 0:
        return "已解锁"
    return f"Lv{skin['min_level']} 解锁 · 还差 {left} 级"


def _public(skin: dict, level: int, equipped: str, total_stars: int, max_stars: int) -> dict:
    rarity = rarity_of(skin)
    unlocked = is_unlocked(skin, level, total_stars, max_stars)
    return {
        "id": skin["id"],
        "name": skin["name"],
        "subtitle": skin["subtitle"],
        "desc": skin["desc"],
        "emoji": skin["emoji"],
        "dark": bool(skin["dark"]),
        "tags": list(skin["tags"]),
        "unlock_type": skin["unlock_type"],
        "min_level": int(skin["min_level"]),
        "rarity": skin["rarity"],
        "rarity_name": rarity["name"],
        "rarity_color": rarity["color"],
        "rarity_light": rarity["light"],
        "tokens": dict(skin["tokens"]),
        "unlocked": unlocked,
        "equipped": skin["id"] == equipped,
        "unlock_hint": unlock_hint(skin, level, total_stars, max_stars),
        "levels_left": max(int(skin["min_level"]) - int(level), 0)
        if skin["unlock_type"] == "level"
        else 0,
    }


def skins_state(
    level: int,
    equipped: str | None = None,
    total_stars: int = 0,
    max_stars: int = 0,
) -> list[dict]:
    """
    全部皮肤 + 解锁/佩戴状态。
    equipped 传空或传了不存在的 id 时，回落到默认皮肤，
    这样即使数据库里存了个已下线的皮肤 id，页面也不会没有主色可用。
    """
    current = equipped if find_skin(equipped) else DEFAULT_SKIN
    return [
        _public(skin, level, current, total_stars, max_stars)
        for skin in SKINS
    ]


def equipped_skin(equipped: str | None) -> dict:
    """当前佩戴的皮肤（带解锁信息），给 /profile/stats 用"""
    return find_skin(equipped) or default_skin()


def skin_payload(
    level: int,
    equipped: str | None,
    total_stars: int = 0,
    max_stars: int = 0,
) -> dict:
    """当前皮肤的精简结构：前端一进页面就能先套色，不用等全量列表"""
    skin = equipped_skin(equipped)
    rarity = rarity_of(skin)
    return {
        "id": skin["id"],
        "name": skin["name"],
        "emoji": skin["emoji"],
        "dark": bool(skin["dark"]),
        "rarity": skin["rarity"],
        "rarity_name": rarity["name"],
        "tokens": dict(skin["tokens"]),
    }


def skins_unlocked_between(
    old_level: int,
    new_level: int,
    total_stars: int = 0,
    max_stars: int = 0,
) -> list[dict]:
    """本次升级新解锁的皮肤（按等级解锁的那些）"""
    result = []
    for skin in SKINS:
        if skin["unlock_type"] != "level":
            continue
        if int(old_level) < int(skin["min_level"]) <= int(new_level):
            result.append(
                {
                    "id": skin["id"],
                    "name": skin["name"],
                    "emoji": skin["emoji"],
                    "rarity": skin["rarity"],
                    "light": rarity_of(skin)["light"],
                }
            )
    return result
