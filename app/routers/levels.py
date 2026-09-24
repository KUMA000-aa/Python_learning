from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.course import Level
from app.models.question import Question
from app.models.user import User
from app.schemas.question import QuestionOut

router = APIRouter(prefix="/levels", tags=["levels"])


@router.get("/{level_id}/questions", response_model=list[QuestionOut])
def get_level_questions(
    level_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取某关卡下所有题目，不含正确答案"""
    level = db.query(Level).filter(Level.id == level_id).first()
    if level is None:
        raise HTTPException(status_code=404, detail="关卡不存在")

    return (
        db.query(Question)
        .filter(Question.level_id == level_id)
        .order_by(Question.order_index)
        .all()
    )
