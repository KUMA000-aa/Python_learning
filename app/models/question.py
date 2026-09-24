from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)
    question_type = Column(String(32), default="single_choice")  # 题型：单选
    stem = Column(Text, nullable=False)                # 题干
    options = Column(Text, nullable=False)             # 选项，用 JSON 字符串存
    correct_answer = Column(String(16), nullable=False) # 正确答案，比如 "A"
    explanation = Column(Text, nullable=True)          # 解析
    order_index = Column(Integer, default=0)

    level = relationship("Level", back_populates="questions")