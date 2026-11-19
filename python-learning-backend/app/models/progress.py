from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, Float
from app.core.database import Base


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False, index=True)
    is_completed = Column(Boolean, default=False)   # 是否通关
    score = Column(Float, default=0.0)              # 得分（正确率或百分制），记最近一次
    stars = Column(Integer, default=0)              # 星级 0~3，取历史最佳（只升不降）
    best_score = Column(Float, default=0.0)         # 历史最高分
    attempts = Column(Integer, default=0)           # 尝试次数
    exp_awarded = Column(Boolean, default=False)     # 本关经验是否已发放（只在首次闯关发一次）
    exp_gained = Column(Integer, default=0)          # 本关当时发放的经验值，用于展示与回滚核对
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)