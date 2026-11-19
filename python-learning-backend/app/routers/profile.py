import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.leveling import (
    DEFAULT_FRAME,
    find_frame,
    frames_state,
    level_progress,
)
from app.core.scoring import STARS_MAX
from app.core.skins import (
    find_skin as find_skin_by_id,
    is_unlocked,
    skin_payload,
    skins_state,
)
from app.models.answer import AnswerRecord
from app.models.course import Level
from app.models.progress import UserProgress
from app.models.question import Question
from app.models.user import User
from app.schemas.profile import (
    AvatarFrameOut,
    FrameEquipIn,
    ProfileStatsOut,
    SkinEquipIn,
    SkinOut,
    WrongQuestionOut,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def _latest_records(db: Session, user_id: int) -> list[AnswerRecord]:
    """取该用户全部作答记录，按时间倒序（最新的在前）"""
    return (
        db.query(AnswerRecord)
        .filter(AnswerRecord.user_id == user_id)
        # 同一秒内的多条记录靠 id 兜底排序，保证「最新」稳定
        .order_by(AnswerRecord.answered_at.desc(), AnswerRecord.id.desc())
        .all()
    )


def _latest_by_question(records: list[AnswerRecord]) -> dict[int, AnswerRecord]:
    """按 question_id 去重，只保留最新一次作答（与结算接口口径一致）"""
    latest: dict[int, AnswerRecord] = {}
    for record in records:  # records 已按时间倒序，首次出现即最新
        latest.setdefault(record.question_id, record)
    return latest


def _star_totals(db: Session, user_id: int) -> tuple[int, int]:
    """
    星星口径：total = 该用户历史最佳星级之和，max = 关卡数 × 3。
    皮肤里的「限定款」要按满星判断，所以单独抽出来，personal 页和皮肤页共用。
    """
    total = (
        db.query(func.coalesce(func.sum(UserProgress.stars), 0))
        .filter(UserProgress.user_id == user_id)
        .scalar()
        or 0
    )
    level_count = db.query(func.count(Level.id)).scalar() or 0
    return int(total), level_count * STARS_MAX


@router.get("/stats", response_model=ProfileStatsOut)
def get_profile_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """个人主页统计：关卡进度、正确率、平均分、学习天数"""
    total_levels = db.query(func.count(Level.id)).scalar() or 0
    total_questions = db.query(func.count(Question.id)).scalar() or 0

    progress_rows = (
        db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()
    )
    attempted_levels = [p for p in progress_rows if (p.attempts or 0) > 0]
    completed_levels = sum(1 for p in progress_rows if p.is_completed)
    level_attempts = sum((p.attempts or 0) for p in progress_rows)
    avg_score = (
        round(
            sum(float(p.best_score or p.score or 0) for p in attempted_levels)
            / len(attempted_levels),
            2,
        )
        if attempted_levels
        else 0.0
    )

    records = _latest_records(db, current_user.id)
    latest = _latest_by_question(records)

    answered_count = len(latest)
    correct_count = sum(1 for r in latest.values() if r.is_correct)
    wrong_count = answered_count - correct_count

    study_days = len({r.answered_at.date() for r in records if r.answered_at})

    total_stars = sum(int(p.stars or 0) for p in progress_rows)

    # 等级与头像框：等级由累计经验推导，不额外落库
    snapshot = level_progress(current_user.exp or 0)
    level = snapshot["level"]
    equipped = find_frame(current_user.avatar_frame) or find_frame(DEFAULT_FRAME)

    max_stars = total_levels * STARS_MAX
    # 皮肤：只返回当前这套的色板 + 全量列表（前端拿 tokens 直接套 CSS 变量）
    skin = skin_payload(level, current_user.skin, total_stars, max_stars)

    return ProfileStatsOut(
        user_id=current_user.id,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        total_levels=total_levels,
        completed_levels=completed_levels,
        progress_percent=round(completed_levels / total_levels * 100, 2) if total_levels else 0.0,
        avg_score=avg_score,
        total_stars=total_stars,
        max_stars=max_stars,
        total_questions=total_questions,
        answered_count=answered_count,
        correct_count=correct_count,
        wrong_count=wrong_count,
        accuracy=round(correct_count / answered_count * 100, 2) if answered_count else 0.0,
        total_answer_times=len(records),
        level_attempts=level_attempts,
        study_days=study_days,
        exp=snapshot["exp"],
        level=level,
        level_title=snapshot["level_title"],
        exp_in_level=snapshot["exp_in_level"],
        exp_need=snapshot["exp_need"],
        exp_percent=snapshot["exp_percent"],
        exp_to_next=snapshot["exp_to_next"],
        next_level_title=snapshot["next_level_title"],
        max_level=snapshot["max_level"],
        is_max_level=snapshot["is_max_level"],
        tier=snapshot["tier"],
        tier_name=snapshot["tier_name"],
        tier_color=snapshot["tier_color"],
        tier_light=snapshot["tier_light"],
        tier_desc=snapshot["tier_desc"],
        tier_index=snapshot["tier_index"],
        tier_roman=snapshot["tier_roman"],
        tier_levels_left=snapshot["tier_levels_left"],
        next_tier_name=snapshot["next_tier_name"],
        avatar_frame=equipped["id"],
        avatar_frame_name=equipped["name"],
        avatar_frame_accent=equipped["accent"],
        avatar_frame_emoji=equipped["emoji"],
        frames=frames_state(level, equipped["id"]),
        skin=skin["id"],
        skin_name=skin["name"],
        skin_emoji=skin["emoji"],
        skin_dark=skin["dark"],
        skin_tokens=skin["tokens"],
        skins=skins_state(level, skin["id"], total_stars, max_stars),
    )


@router.get("/wrong-questions", response_model=list[WrongQuestionOut])
def list_wrong_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    错题列表：每题只看最新一次作答，仍答错的才算错题。
    答对后这道题会自动从列表里消失（说明已订正）。
    """
    rows = (
        db.query(AnswerRecord, Question, Level)
        .join(Question, Question.id == AnswerRecord.question_id)
        .join(Level, Level.id == Question.level_id)
        .filter(AnswerRecord.user_id == current_user.id)
        .order_by(AnswerRecord.answered_at.desc(), AnswerRecord.id.desc())
        .all()
    )

    seen: set[int] = set()
    result: list[WrongQuestionOut] = []

    for record, question, level in rows:
        if question.id in seen:
            continue
        seen.add(question.id)

        if record.is_correct:
            continue

        try:
            options = json.loads(question.options) if isinstance(question.options, str) else question.options
        except (TypeError, ValueError):
            options = []

        result.append(
            WrongQuestionOut(
                question_id=question.id,
                level_id=level.id,
                level_title=level.title,
                stem=question.stem,
                options=options or [],
                correct_answer=question.correct_answer,
                explanation=question.explanation,
                user_answer=record.user_answer,
                answered_at=record.answered_at,
            )
        )

    return result


@router.get("/frames", response_model=list[AvatarFrameOut])
def list_frames(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """全部头像框：返回解锁状态与当前佩戴的那一个"""
    snapshot = level_progress(current_user.exp or 0)
    return frames_state(snapshot["level"], current_user.avatar_frame)


@router.post("/frame", response_model=list[AvatarFrameOut])
def equip_frame(
    payload: FrameEquipIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    切换头像框。只能佩戴已解锁的框——等级不够时后端拒绝，
    避免前端改参数就能提前用上高级框。
    """
    snapshot = level_progress(current_user.exp or 0)
    level = snapshot["level"]

    frame = find_frame(payload.frame_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="头像框不存在")
    if level < frame["min_level"]:
        raise HTTPException(
            status_code=403,
            detail=f"达到 Lv{frame['min_level']} 才能解锁「{frame['name']}」",
        )

    current_user.avatar_frame = frame["id"]
    db.commit()

    return frames_state(level, frame["id"])


@router.get("/skins", response_model=list[SkinOut])
def list_skins(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """全部皮肤：解锁状态、当前佩戴、解锁提示都在里面，前端不做判断"""
    snapshot = level_progress(current_user.exp or 0)
    total_stars, max_stars = _star_totals(db, current_user.id)
    return skins_state(snapshot["level"], current_user.skin, total_stars, max_stars)


@router.post("/skin", response_model=list[SkinOut])
def equip_skin(
    payload: SkinEquipIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    换皮肤。只校验「有没有解锁」：
    · 等级解锁款——等级不够返回 403；
    · 满星限定款——星星不够返回 403，并说清还差几颗星。
    校验放在后端，前端改参数也拿不到没解锁的皮肤。
    """
    snapshot = level_progress(current_user.exp or 0)
    level = snapshot["level"]
    total_stars, max_stars = _star_totals(db, current_user.id)

    skin = find_skin_by_id(payload.skin_id)
    if skin is None:
        raise HTTPException(status_code=404, detail="皮肤不存在")

    if not is_unlocked(skin, level, total_stars, max_stars):
        if skin["unlock_type"] == "full_stars":
            raise HTTPException(
                status_code=403,
                detail=f"「{skin['name']}」需要全部关卡 3 星通关（当前 {total_stars}/{max_stars} 星）",
            )
        raise HTTPException(
            status_code=403,
            detail=f"达到 Lv{skin['min_level']} 才能解锁「{skin['name']}」",
        )

    current_user.skin = skin["id"]
    db.commit()

    return skins_state(level, skin["id"], total_stars, max_stars)
