from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from app.core.database import Base


class AnswerRecord(Base):
    __tablename__ = "answer_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False, index=True)
    user_answer = Column(Text, nullable=False)      # 选择题存字母、填空存文本、代码补全存 JSON 数组
    is_correct = Column(Boolean, nullable=False)
    duration_ms = Column(Integer, nullable=True)   # 作答耗时（毫秒），后续做防作弊和数据分析
    answered_at = Column(DateTime, default=datetime.utcnow)