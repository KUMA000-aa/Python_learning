from pydantic import BaseModel, ConfigDict


class ProgressOut(BaseModel):
    """某关卡的进度"""

    id: int | None = None
    user_id: int
    level_id: int
    is_completed: bool
    score: float          # 最近一次得分
    stars: int            # 历史最佳星级 0~3
    best_score: float     # 历史最高分
    attempts: int

    model_config = ConfigDict(from_attributes=True)


class LevelCompleteResponse(BaseModel):
    """通关上报回包：本次得分、星级及历史最佳"""

    level_id: int
    score: float              # 本次得分
    is_completed: bool        # 本次是否全对
    correct_count: int
    total_count: int
    attempts: int

    # 星级：3 全对 / 2 正确率≥2/3 / 1 正确率≥1/3 / 0 不足 1/3
    stars: int                # 本次获得
    best_stars: int           # 历史最佳（只升不降）
    best_score: float         # 历史最高分
    level_completed: bool     # 该关是否已通关过（含之前）
    stars_hint: str = ""      # 「再答对 N 题就能多拿 1 颗星」

    # ===== 经验与等级 =====
    exp_gained: int = 0       # 本次获得的经验，重复闯关为 0
    exp_clear_bonus: int = 0  # 其中：通关奖励（50 + 星级 × 30）
    exp_explore_bonus: int = 0  # 其中：探索奖励（答对题数 × 15）
    exp_first_clear: bool = False  # 本次是不是「首次闯关」（决定是否发经验）
    exp_total: int = 0        # 结算后的累计经验
    level: int = 1            # 结算后的等级
    level_title: str = ""     # 等级称号，如「学徒」
    prev_level: int = 1       # 结算前的等级
    level_up: bool = False    # 本次是否升级
    frames_unlocked: list = []  # 本次升级新解锁的头像框
    skins_unlocked: list = []   # 本次升级新解锁的皮肤（等级解锁款）
    exp_in_level: int = 0     # 当前等级内已累计经验
    exp_need: int = 0         # 升到下一级所需经验
    exp_percent: float = 0.0  # 当前等级进度百分比
    is_max_level: bool = False  # 是否已满级
    max_level: int = 30       # 等级上限

    # ===== 段位（每段 5 级：黑铁 / 青铜 / 白银 / 黄金 / 钻石 / 王者）=====
    tier: str = "iron"        # 段位 id
    tier_name: str = "黑铁"    # 段位名
    tier_color: str = ""      # 段位主色
    tier_light: str = ""      # 段位浅色底
    tier_desc: str = ""       # 段位一句话
    tier_index: int = 1       # 段内第几级（1-5）
    tier_roman: str = ""      # 段内小级罗马数字（Ⅴ→Ⅰ）
    tier_levels_left: int = 0 # 还差几级晋级下一段
    next_tier_name: str = ""  # 下一段位名
    tier_up: bool = False     # 本次是否跨段
    prev_tier_name: str = ""  # 跨段前的段位名
