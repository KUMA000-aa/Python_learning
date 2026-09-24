from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
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
    """查某关卡进度"""
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
            is_completed=False,
            score=0.0,
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
    进度更新：根据该用户在本关的答题记录算得分与是否通关。
    前端在答完该关全部题目后调用。
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

    progress.score = score
    progress.is_completed = is_completed
    progress.attempts = (progress.attempts or 0) + 1
    db.commit()
    db.refresh(progress)

    return LevelCompleteResponse(
        level_id=level_id,
        score=score,
        is_completed=is_completed,
        correct_count=correct,
        total_count=total,
        attempts=progress.attempts,
    )
