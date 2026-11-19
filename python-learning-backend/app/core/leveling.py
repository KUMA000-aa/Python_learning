"""
等级与经验规则（全站唯一口径）

设计要点：
1) 经验只来自「首次闯关」——同一关卡重复挑战不再给经验，避免刷分；
2) 经验 = 通关奖励（按星级）+ 探索奖励（本次答对题数），一次打得好更划算；
3) 等级由累计经验推导（不额外存 level 字段），避免两个字段不同步；
4) 头像框按等级解锁，解锁后永久持有，可随时切换。

曲线：need(lv) = 120 + 100×(lv-1) + 12×(lv-1)²
    Lv1→2 120、Lv2→3 232、Lv3→4 368、Lv4→5 528、Lv5→6 712、
    Lv6→7 920、Lv7→8 1152、Lv8→9 1408、Lv9→10 1688 …
前几级台阶温和（新手区不至于卡住），越往后每级跨度越大，
Lv10 之后基本要靠十几关才能升一级，等级才有分量。
"""

# ===== 升级曲线 =====
# need(level) = BASE_NEED + STEP × (level-1) + CURVE × (level-1)²
BASE_NEED = 120
STEP = 100
CURVE = 12

MAX_LEVEL = 30

# 旧曲线（一版线性）保留在迁移逻辑里：用来判断老玩家的原等级，
# 迁移时保证「等级不倒退」，不能删。
LEGACY_BASE_NEED = 80
LEGACY_STEP = 60

# ===== 经验产出 =====
# 首次闯关 = 通关奖励（50 + 星级 × 30）+ 探索奖励（答对题数 × 15）
BASE_REWARD = 50
STAR_BONUS = 30
EXPLORE_UNIT = 15

# 头像框：名字刻意避开段位名（不然「青铜段位」却拿到「白银环」会很乱），
# 改用材质/意象命名，解锁节奏跟段位错开，让每个段位里都有新东西可拿。
AVATAR_FRAMES = [
    {"id": "f1", "name": "素铁环", "min_level": 1, "accent": "#6E7B8B", "emoji": "🥉"},
    {"id": "f2", "name": "银纹环", "min_level": 2, "accent": "#9AA7B8", "emoji": "🥈"},
    {"id": "f3", "name": "金纹环", "min_level": 4, "accent": "#F5B400", "emoji": "🥇"},
    {"id": "f4", "name": "翡翠环", "min_level": 6, "accent": "#22B573", "emoji": "💎"},
    {"id": "f5", "name": "星轨环", "min_level": 9, "accent": "#7C6CFF", "emoji": "🌌"},
    {"id": "f6", "name": "传说之冠", "min_level": 12, "accent": "#FF5C8A", "emoji": "👑"},
    {"id": "f7", "name": "星耀环", "min_level": 16, "accent": "#00C2D1", "emoji": "✨"},
    {"id": "f8", "name": "赤霄环", "min_level": 22, "accent": "#D93A3A", "emoji": "🔥"},
]

DEFAULT_FRAME = AVATAR_FRAMES[0]["id"]

# ===== 段位 =====
# 每段固定 5 级，6 段 × 5 级 = 30 级，正好铺满 MAX_LEVEL。
# 段位内的小级用罗马数字「Ⅴ → Ⅰ」递减：Ⅴ 是刚进来，Ⅰ 是即将晋级，
# 这样「黑铁 Ⅰ」到「青铜 Ⅴ」的跨越感才成立。
TIERS = [
    {
        "id": "iron",
        "name": "黑铁",
        "start": 1,
        "end": 5,
        "color": "#6E7B8B",
        "light": "#EFF2F5",
        "desc": "刚起步，先把手感磨出来",
    },
    {
        "id": "bronze",
        "name": "青铜",
        "start": 6,
        "end": 10,
        "color": "#B87333",
        "light": "#FBF1E8",
        "desc": "基础成型，开始打出连击了",
    },
    {
        "id": "silver",
        "name": "白银",
        "start": 11,
        "end": 15,
        "color": "#7D8FA6",
        "light": "#EEF2F7",
        "desc": "稳定发挥，错题越来越少",
    },
    {
        "id": "gold",
        "name": "黄金",
        "start": 16,
        "end": 20,
        "color": "#E0A100",
        "light": "#FFF8E1",
        "desc": "手感火热，稳定性在线",
    },
    {
        "id": "diamond",
        "name": "钻石",
        "start": 21,
        "end": 25,
        "color": "#00A6B8",
        "light": "#E6F8FA",
        "desc": "高手区，基础题已经难不倒你",
    },
    {
        "id": "king",
        "name": "王者",
        "start": 26,
        "end": 30,
        "color": "#D93A3A",
        "light": "#FDECEC",
        "desc": "顶级选手，出题人都得让一让",
    },
]

# 段内小级：第 1 级（刚落段）→ 第 5 级（即将晋级）
TIER_ROMANS = ["Ⅴ", "Ⅳ", "Ⅲ", "Ⅱ", "Ⅰ"]

MAX_TIER_TITLE = "最强王者"


def _clamp_level(level: int) -> int:
    return min(max(int(level or 1), 1), MAX_LEVEL)


# ===== 曲线计算 =====
def need_for_next(level: int) -> int:
    """从 level 升到 level+1 需要的经验；已满级返回 0"""
    level = _clamp_level(level)
    if level >= MAX_LEVEL:
        return 0
    step = level - 1
    return BASE_NEED + STEP * step + CURVE * step * step


def cumulative_exp(level: int) -> int:
    """升到 level 总共需要的累计经验（Lv1 为 0）"""
    level = _clamp_level(level)
    total = 0
    for lv in range(1, level):
        total += need_for_next(lv)
    return total


def level_from_exp(exp: int) -> int:
    """累计经验推导等级，不依赖数据库字段"""
    exp = max(int(exp or 0), 0)
    level = 1
    while level < MAX_LEVEL and exp >= need_for_next(level):
        exp -= need_for_next(level)
        level += 1
    return level


def tier_of(level: int) -> dict:
    """
    等级所属段位 + 段内小级。
    index 为段内第几级（1 = 刚进段），roman 是对应的罗马数字。
    """
    level = _clamp_level(level)
    tier = TIERS[0]
    for item in TIERS:
        if level >= item["start"]:
            tier = item
    index = min(max(level - tier["start"] + 1, 1), 5)
    return {
        **tier,
        "index": index,
        "roman": TIER_ROMANS[index - 1],
        "is_final": level >= MAX_LEVEL,
    }


def level_title(level: int) -> str:
    """等级称号：段位 + 段内小级，如「青铜 Ⅲ」；满级特判为「最强王者」"""
    level = _clamp_level(level)
    if level >= MAX_LEVEL:
        return MAX_TIER_TITLE
    tier = tier_of(level)
    return f"{tier['name']} {tier['roman']}"


def _next_tier_name(tier_id: str) -> str:
    """下一段的名字；已是最后一段返回空串"""
    for i, item in enumerate(TIERS):
        if item["id"] == tier_id and i + 1 < len(TIERS):
            return TIERS[i + 1]["name"]
    return ""


def tier_up_between(old_level: int, new_level: int) -> dict | None:
    """本次是否跨段；跨段返回新段位信息，否则返回 None"""
    old_tier = tier_of(old_level)
    new_tier = tier_of(new_level)
    return new_tier if old_tier["id"] != new_tier["id"] else None


def level_progress(exp: int) -> dict:
    """
    经验明细：当前等级、本级已得/所需、进度百分比。
    前端直接用这几个字段渲染经验条，不用自己算。
    """
    exp = max(int(exp or 0), 0)
    level = level_from_exp(exp)
    floor = cumulative_exp(level)
    need = need_for_next(level)
    maxed = need == 0
    # 满级后多出来的经验不再显示，避免前端出现「99999 / 0 EXP」这种怪数
    in_level = 0 if maxed else max(exp - floor, 0)
    tier = tier_of(level)

    return {
        "exp": exp,
        "level": level,
        "level_title": level_title(level),
        # ===== 段位 =====
        "tier": tier["id"],
        "tier_name": tier["name"],
        "tier_color": tier["color"],
        "tier_light": tier["light"],
        "tier_desc": tier["desc"],
        "tier_index": tier["index"],
        "tier_roman": tier["roman"],
        "tier_levels_left": max(tier["end"] - level, 0),  # 还差几级晋级下一段
        "next_tier_name": _next_tier_name(tier["id"]),
        "exp_in_level": in_level,
        "exp_need": need,
        "exp_percent": (100.0 if maxed else round(in_level / need * 100, 2)),
        "exp_to_next": max(need - in_level, 0),
        "next_level_title": "已满级" if maxed else level_title(level + 1),
        "total_exp_for_level": floor,
        "is_max_level": maxed,
        "max_level": MAX_LEVEL,
    }


# ===== 经验产出 =====
def exp_reward(stars: int) -> int:
    """首次通关奖励：0 星 50，1 星 80，2 星 110，3 星 140"""
    stars = min(max(int(stars or 0), 0), 3)
    return BASE_REWARD + stars * STAR_BONUS


def explore_reward(correct: int) -> int:
    """探索奖励：首次通关时每答对一题 +15"""
    return EXPLORE_UNIT * max(int(correct or 0), 0)


def first_clear_reward(stars: int, correct: int) -> tuple[int, int, int]:
    """
    首次闯关的总经验，返回 (通关奖励, 探索奖励, 合计)。
    拆开返回是为了让结算页能解释「这 185 是怎么来的」。
    """
    clear_bonus = exp_reward(stars)
    explore_bonus = explore_reward(correct)
    return clear_bonus, explore_bonus, clear_bonus + explore_bonus


# ===== 头像框 =====
def find_frame(frame_id: str | None) -> dict | None:
    for frame in AVATAR_FRAMES:
        if frame["id"] == frame_id:
            return frame
    return None


def frames_state(level: int, equipped: str | None = None) -> list[dict]:
    """
    全部头像框 + 是否已解锁。
    前端用它渲染「已解锁/还差几级」两种状态，不用再写判断逻辑。
    """
    level = _clamp_level(level)
    current = equipped or DEFAULT_FRAME
    result = []
    for frame in AVATAR_FRAMES:
        result.append(
            {
                **frame,
                "unlocked": level >= frame["min_level"],
                "equipped": frame["id"] == current,
                "levels_left": max(frame["min_level"] - level, 0),
            }
        )
    return result


def frames_unlocked_between(old_level: int, new_level: int) -> list[dict]:
    """本次升级新解锁的头像框（老等级 < min_level <= 新等级）"""
    old_level = _clamp_level(old_level)
    new_level = _clamp_level(new_level)
    return [
        frame
        for frame in AVATAR_FRAMES
        if old_level < frame["min_level"] <= new_level
    ]


# ===== 迁移辅助 =====
def legacy_level_from_exp(exp: int) -> int:
    """
    按「上一版」线性曲线（80 + 60×(lv-1)）算等级。
    只给迁移用：改曲线时保证老玩家等级不倒退。
    """
    exp = max(int(exp or 0), 0)
    level = 1
    while level < 100:
        need = LEGACY_BASE_NEED + (level - 1) * LEGACY_STEP
        if exp < need:
            break
        exp -= need
        level += 1
    return level
