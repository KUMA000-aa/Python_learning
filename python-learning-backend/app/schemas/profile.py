from datetime import datetime

from pydantic import BaseModel


class WrongQuestionOut(BaseModel):
    """错题：该用户在这道题上「最新一次作答」仍然是错的"""

    question_id: int
    level_id: int
    level_title: str
    stem: str
    options: list
    correct_answer: str
    explanation: str | None = None
    user_answer: str
    answered_at: datetime | None = None


class AvatarFrameOut(BaseModel):
    """头像框：等级达标即解锁，解锁后可切换佩戴"""

    id: str
    name: str
    min_level: int
    accent: str              # 主色，前端描边/发光直接用它
    emoji: str
    unlocked: bool
    equipped: bool
    levels_left: int         # 还差几级解锁，已解锁为 0


class FrameEquipIn(BaseModel):
    frame_id: str


class SkinOut(BaseModel):
    """
    皮肤：一整套配色令牌，前端转成 CSS 变量套到页面上。
    tokens 里全是颜色字符串，新增字段时前端不用改结构。
    """

    id: str
    name: str
    subtitle: str
    desc: str
    emoji: str
    dark: bool               # 深色皮肤：页面文字/卡片要反向处理
    tags: list[str] = []
    unlock_type: str         # level（等级解锁）/ full_stars（全满星解锁）
    min_level: int           # 等级解锁所需等级
    rarity: str              # normal / rare / epic / legend / limited
    rarity_name: str
    rarity_color: str
    rarity_light: str
    tokens: dict[str, str]   # 色板令牌
    unlocked: bool
    equipped: bool
    unlock_hint: str         # 已算好的一句话，如「Lv6 解锁 · 还差 3 级」
    levels_left: int = 0


class SkinEquipIn(BaseModel):
    skin_id: str


class ProfileStatsOut(BaseModel):
    """个人主页统计"""

    user_id: int
    nickname: str | None = None
    avatar_url: str | None = None

    # 关卡维度
    total_levels: int
    completed_levels: int
    progress_percent: float
    avg_score: float

    # 星级维度（每关最多 3 星）
    total_stars: int
    max_stars: int

    # 题目维度（按每题最新一次作答去重，与结算口径一致）
    total_questions: int
    answered_count: int
    correct_count: int
    wrong_count: int
    accuracy: float

    # 行为维度
    total_answer_times: int
    level_attempts: int
    study_days: int

    # ===== 等级维度 =====
    exp: int = 0
    level: int = 1
    level_title: str = ""
    exp_in_level: int = 0
    exp_need: int = 0
    exp_percent: float = 0.0
    exp_to_next: int = 0
    next_level_title: str = ""
    max_level: int = 30
    is_max_level: bool = False

    # ===== 段位 =====
    tier: str = "iron"
    tier_name: str = "黑铁"
    tier_color: str = ""
    tier_light: str = ""
    tier_desc: str = ""
    tier_index: int = 1
    tier_roman: str = ""
    tier_levels_left: int = 0
    next_tier_name: str = ""

    # ===== 头像框 =====
    avatar_frame: str = "f1"          # 当前佩戴的框 id
    avatar_frame_name: str = ""
    avatar_frame_accent: str = ""
    avatar_frame_emoji: str = ""
    frames: list[AvatarFrameOut] = [] # 全部框 + 解锁状态

    # ===== 皮肤 =====
    skin: str = "classic"             # 当前皮肤 id
    skin_name: str = ""
    skin_emoji: str = ""
    skin_dark: bool = False
    skin_tokens: dict[str, str] = {}  # 当前皮肤的色板，页面直接套
    skins: list[SkinOut] = []         # 全部皮肤 + 解锁状态
