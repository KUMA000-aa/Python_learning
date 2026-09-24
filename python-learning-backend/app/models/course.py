from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)   # 排序用
    created_at = Column(DateTime, default=datetime.utcnow)

    units = relationship("Unit", back_populates="course", order_by="Unit.order_index")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    course = relationship("Course", back_populates="units")
    levels = relationship("Level", back_populates="unit", order_by="Level.order_index")


class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    title = Column(String(128), nullable=False)
    order_index = Column(Integer, default=0)

    unit = relationship("Unit", back_populates="levels")
    questions = relationship("Question", back_populates="level", order_by="Question.order_index")