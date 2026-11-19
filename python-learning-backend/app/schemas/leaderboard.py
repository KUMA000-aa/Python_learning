from pydantic import BaseModel


class ProgressRankItem(BaseModel):
    """闯关进度榜的一项：按通关数 → 星星 → 关卡总分排序"""

    rank: int
    user_id: int
    nickname: str
    avatar_url: str | None = None

    completed_levels: int     # 已通关关卡数
    total_levels: int         # 全部关卡数（分母）
    stars: int                # 星星总数
    score_sum: float          # 各关历史最高分之和
    is_me: bool = False


class CheckinRankItem(BaseModel):
    """打卡天数榜的一项：按有学习记录的天数排序"""

    rank: int
    user_id: int
    nickname: str
    avatar_url: str | None = None

    study_days: int           # 有作答记录的天数（= 打卡天数）
    answer_times: int         # 作答总次数
    is_me: bool = False


class GroupRankItem(BaseModel):
    """学习小组榜的一项：按组内成员得分总和排序"""

    rank: int
    group_name: str
    member_count: int
    total_score: float        # 组内所有成员各关最高分之和
    total_stars: int          # 组内星星总数
    is_me: bool = False       # 是否是我所在的小组


class LeaderboardOut(BaseModel):
    """
    三张榜单一次返回：切 tab 不用再发请求，秒切。
    `*_me` 是「我的排名」，即使排在 limit 之外也会带上。
    """

    total_users: int
    total_levels: int
    total_groups: int

    progress: list[ProgressRankItem] = []
    progress_me: ProgressRankItem | None = None

    checkin: list[CheckinRankItem] = []
    checkin_me: CheckinRankItem | None = None

    groups: list[GroupRankItem] = []
    groups_me: GroupRankItem | None = None
