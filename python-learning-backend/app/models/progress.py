from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, Float
from app.core.database import Base


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False, index=True)
    is_completed = Column(Boolean, default=False)   # 是否通关
    score = Column(Float, default=0.0)              # 得分（正确率或百分制）
    attempts = Column(Integer, default=0)           # 尝试次数
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)