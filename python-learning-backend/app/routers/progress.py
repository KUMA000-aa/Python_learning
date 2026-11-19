from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.leveling import (
    first_clear_reward,
    frames_unlocked_between,
    level_from_exp,
    level_progress,
    tier_of,
    tier_up_between,
)
from app.core.scoring import calc_stars, stars_hint
from app.core.skins import skins_unlocked_between
from app.models.answer import AnswerRecord
from app.models.course import Level
from app.models.progress import UserProgress
from app.models.question import Question
from app.models.user import User
from app.schemas.progress import LevelCompleteResponse, ProgressOut

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/levels/{level_id}", response_model=ProgressOut)
def get_level_progress(
    level_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查某关卡进度（含星级）"""
    progress = (
        db.query(UserProgress)
        .filter(
            UserProgress.user_id == current_user.id,
            UserProgress.level_id == level_id,
        )
        .first()
    )
    if progress is None:
        # 没挑战过：返回零值，别写库（避免刷出大量空记录）
        progress = UserProgress(
            user_id=current_user.id,
            level_id=level_id,
            is_completed=False,
            score=0.0,
            stars=0,
            best_score=0.0,
            attempts=0,
        )
    return progress


@router.post("/levels/{level_id}/complete", response_model=LevelCompleteResponse)
def complete_level(
    level_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    进度更新：根据该用户在本关的答题记录算得分、是否通关与星级。
    前端在答完该关全部题目后调用。

    星级与通关状态「只升不降」：重玩时答差了不会丢掉已经拿到的星星。
    """
    level = db.query(Level).filter(Level.id == level_id).first()
    if level is None:
        raise HTTPException(status_code=404, detail="关卡不存在")

    total = (
        db.query(func.count(Question.id))
        .filter(Question.level_id == level_id)
        .scalar()
        or 0
    )

    # 按 question_id 去重，只统计每题的最新一次作答是否正确，防止重复提交导致分数 > 100
    # 思路：先取出本关所有答题记录，按 question_id 分组取最新一条，再算其中 is_correct=True 的题数
    all_records = (
        db.query(AnswerRecord)
        .filter(
            AnswerRecord.user_id == current_user.id,
            AnswerRecord.level_id == level_id,
        )
        .order_by(AnswerRecord.answered_at.desc())
        .all()
    )
    latest_by_qid = {}
    for rec in all_records:
        latest_by_qid.setdefault(rec.question_id, rec)
    correct = sum(1 for r in latest_by_qid.values() if r.is_correct)

    score = round((correct / total * 100), 2) if total else 0.0
    is_completed = total > 0 and correct >= total
    stars = calc_stars(correct, total)

    progress = (
        db.query(UserProgress)
        .filter(
            UserProgress.user_id == current_user.id,
            UserProgress.level_id == level_id,
        )
        .first()
    )
    if progress is None:
        progress = UserProgress(
            user_id=current_user.id,
            level_id=level_id,
        )
        db.add(progress)

    # 本次成绩
    progress.score = score
    progress.attempts = (progress.attempts or 0) + 1

    # 成就（历史最佳，只升不降）
    progress.is_completed = bool(progress.is_completed) or is_completed
    progress.stars = max(int(progress.stars or 0), stars)
    progress.best_score = max(float(progress.best_score or 0), score)

    best_stars = progress.stars
    best_score = progress.best_score

    # ===== 经验与等级 =====
    # 规则：只有「首次有效闯关」发经验：
    #   · 必须把本关每道题都答过（防半途结算白拿经验）
    #   · 至少答对 1 题（0 分不算闯关成功，可以重新打）
    # 同一关卡之后再来多少次都不再增加经验，避免刷分。
    prev_exp = int(current_user.exp or 0)
    prev_level = level_from_exp(prev_exp)
    exp_gained = 0
    exp_clear_bonus = 0
    exp_explore_bonus = 0
    exp_first_clear = False

    answered_all = total > 0 and len(latest_by_qid) >= total
    if not bool(progress.exp_awarded) and answered_all and correct > 0:
        # 首次闯关经验 = 通关奖励（按星级）+ 探索奖励（答对题数）
        exp_clear_bonus, exp_explore_bonus, exp_gained = first_clear_reward(
            stars, correct
        )
        progress.exp_awarded = True
        progress.exp_gained = exp_gained
        current_user.exp = prev_exp + exp_gained
        exp_first_clear = True

    exp_total = int(current_user.exp or 0)
    level = level_from_exp(exp_total)
    snapshot = level_progress(exp_total)
    frames_unlocked = frames_unlocked_between(prev_level, level)
    # 升级同时可能解锁皮肤（等级解锁款），结算页一起提示
    skins_unlocked = skins_unlocked_between(prev_level, level)
    tier_up = tier_up_between(prev_level, level)

    db.commit()
    db.refresh(progress)

    return LevelCompleteResponse(
        level_id=level_id,
        score=score,
        is_completed=is_completed,
        correct_count=correct,
        total_count=total,
        attempts=progress.attempts,
        stars=stars,
        best_stars=best_stars,
        best_score=best_score,
        level_completed=bool(progress.is_completed),
        stars_hint=stars_hint(correct, total, stars),
        exp_gained=exp_gained,
        exp_clear_bonus=exp_clear_bonus,
        exp_explore_bonus=exp_explore_bonus,
        exp_first_clear=exp_first_clear,
        exp_total=exp_total,
        level=level,
        level_title=snapshot["level_title"],
        prev_level=prev_level,
        level_up=level > prev_level,
        frames_unlocked=frames_unlocked,
        skins_unlocked=skins_unlocked,
        exp_in_level=snapshot["exp_in_level"],
        exp_need=snapshot["exp_need"],
        exp_percent=snapshot["exp_percent"],
        is_max_level=snapshot["is_max_level"],
        max_level=snapshot["max_level"],
        tier=snapshot["tier"],
        tier_name=snapshot["tier_name"],
        tier_color=snapshot["tier_color"],
        tier_light=snapshot["tier_light"],
        tier_desc=snapshot["tier_desc"],
        tier_index=snapshot["tier_index"],
        tier_roman=snapshot["tier_roman"],
        tier_levels_left=snapshot["tier_levels_left"],
        next_tier_name=snapshot["next_tier_name"],
        tier_up=bool(tier_up),
        prev_tier_name=tier_of(prev_level)["name"],
    )
