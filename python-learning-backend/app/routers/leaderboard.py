from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.answer import AnswerRecord
from app.models.course import Level
from app.models.progress import UserProgress
from app.models.user import User
from app.schemas.leaderboard import (
    CheckinRankItem,
    GroupRankItem,
    LeaderboardOut,
    ProgressRankItem,
)

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

# 没有小组的用户归到这里，保证「小组榜」能覆盖所有人
UNGROUPED = "未分组"


def _display_name(user: User) -> str:
    """微信登录拿不到昵称时给个可读的兜底名字"""
    name = (user.nickname or "").strip()
    return name or f"学习者 {user.id}"


def _group_of(user: User) -> str:
    return (user.group_name or "").strip() or UNGROUPED


def _progress_agg(db: Session) -> dict[int, dict]:
    """按用户聚合关卡进度：通关数 / 星星 / 各关最高分之和"""
    agg: dict[int, dict] = {}
    for row in db.query(UserProgress).all():
        item = agg.setdefault(
            row.user_id,
            {"completed": 0, "stars": 0, "score": 0.0},
        )
        if row.is_completed:
            item["completed"] += 1
        item["stars"] += int(row.stars or 0)
        item["score"] += float(row.best_score or 0)
    return agg


def _checkin_agg(db: Session) -> dict[int, dict]:
    """
    按用户聚合打卡数据。
    打卡天数 = 有作答记录的 UTC 日期数，和 /profile/stats 的 study_days 口径一致。
    """
    rows = (
        db.query(
            AnswerRecord.user_id.label("user_id"),
            func.count(func.distinct(func.date(AnswerRecord.answered_at))).label("days"),
            func.count(AnswerRecord.id).label("times"),
        )
        .group_by(AnswerRecord.user_id)
        .all()
    )
    return {
        r.user_id: {"days": int(r.days or 0), "times": int(r.times or 0)}
        for r in rows
    }


@router.get("", response_model=LeaderboardOut)
def get_leaderboard(
    limit: int = Query(20, ge=1, le=100, description="每张榜单返回多少名"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    排行榜总接口：一次返回三张榜（闯关进度 / 每日打卡 / 学习小组）。

    排序规则：
    - 闯关进度：通关数 → 星星数 → 各关最高分之和
    - 每日打卡：打卡天数 → 作答次数
    - 学习小组：组内成员各关最高分之和 → 组内星星数

    并列时按用户 ID / 小组名兜底，保证多次请求顺序稳定。
    """
    users = db.query(User).order_by(User.id).all()
    total_levels = db.query(func.count(Level.id)).scalar() or 0
    progress_agg = _progress_agg(db)
    checkin_agg = _checkin_agg(db)

    my_group = _group_of(current_user)

    # ---------- 1. 闯关进度榜 ----------
    progress_rows = []
    for user in users:
        stat = progress_agg.get(user.id, {"completed": 0, "stars": 0, "score": 0.0})
        progress_rows.append(
            {
                "user_id": user.id,
                "nickname": _display_name(user),
                "avatar_url": user.avatar_url,
                "completed_levels": stat["completed"],
                "total_levels": total_levels,
                "stars": stat["stars"],
                "score_sum": round(stat["score"], 2),
            }
        )
    progress_rows.sort(
        key=lambda r: (
            -r["completed_levels"],
            -r["stars"],
            -r["score_sum"],
            r["user_id"],
        )
    )

    # ---------- 2. 打卡天数榜 ----------
    checkin_rows = []
    for user in users:
        stat = checkin_agg.get(user.id, {"days": 0, "times": 0})
        checkin_rows.append(
            {
                "user_id": user.id,
                "nickname": _display_name(user),
                "avatar_url": user.avatar_url,
                "study_days": stat["days"],
                "answer_times": stat["times"],
            }
        )
    checkin_rows.sort(key=lambda r: (-r["study_days"], -r["answer_times"], r["user_id"]))

    # ---------- 3. 学习小组榜 ----------
    group_map: dict[str, dict] = {}
    for user in users:
        name = _group_of(user)
        stat = progress_agg.get(user.id, {"completed": 0, "stars": 0, "score": 0.0})
        group = group_map.setdefault(
            name,
            {"group_name": name, "member_count": 0, "total_score": 0.0, "total_stars": 0},
        )
        group["member_count"] += 1
        group["total_score"] += stat["score"]
        group["total_stars"] += stat["stars"]

    group_rows = [
        {**g, "total_score": round(g["total_score"], 2)}
        for g in group_map.values()
    ]
    group_rows.sort(key=lambda g: (-g["total_score"], -g["total_stars"], g["group_name"]))

    # ---------- 组装：加名次 + 找「我的排名」 ----------
    def rank_items(rows, builder):
        items = []
        for index, row in enumerate(rows, start=1):
            items.append(builder(row, index))
        return items

    progress_items = rank_items(
        progress_rows,
        lambda row, rank: ProgressRankItem(
            rank=rank,
            **row,
            is_me=row["user_id"] == current_user.id,
        ),
    )
    checkin_items = rank_items(
        checkin_rows,
        lambda row, rank: CheckinRankItem(
            rank=rank,
            **row,
            is_me=row["user_id"] == current_user.id,
        ),
    )
    group_items = rank_items(
        group_rows,
        lambda row, rank: GroupRankItem(
            rank=rank,
            **row,
            is_me=row["group_name"] == my_group,
        ),
    )

    def pick_me(items):
        for item in items:
            if item.is_me:
                return item
        return None

    return LeaderboardOut(
        total_users=len(users),
        total_levels=total_levels,
        total_groups=len(group_rows),
        progress=progress_items[:limit],
        progress_me=pick_me(progress_items),
        checkin=checkin_items[:limit],
        checkin_me=pick_me(checkin_items),
        groups=group_items[:limit],
        groups_me=pick_me(group_items),
    )
