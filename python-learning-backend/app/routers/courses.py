from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseOut

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseOut])
def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """课程列表：按排序返回所有课程，含单元与关卡"""
    return (
        db.query(Course)
        .order_by(Course.order_index)
        .all()
    )
