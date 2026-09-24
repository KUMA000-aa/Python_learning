from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.answer import AnswerRecord
from app.models.question import Question
from app.models.user import User
from app.schemas.answer import AnswerSubmitRequest, AnswerSubmitResponse

router = APIRouter(prefix="/answers", tags=["answers"])


@router.post("", response_model=AnswerSubmitResponse)
def submit_answer(
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """答题上报：记录作答，返回是否正确与解析"""
    question = db.query(Question).filter(Question.id == payload.question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")

    is_correct = (
        payload.user_answer.strip().upper()
        == question.correct_answer.strip().upper()
    )

    record = AnswerRecord(
        user_id=current_user.id,
        question_id=question.id,
        level_id=question.level_id,
        user_answer=payload.user_answer,
        is_correct=is_correct,
        duration_ms=payload.duration_ms,
    )
    db.add(record)
    db.commit()

    return AnswerSubmitResponse(
        question_id=question.id,
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
    )
