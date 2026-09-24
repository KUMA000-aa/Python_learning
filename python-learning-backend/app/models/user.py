from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(64), unique=True, index=True, nullable=False)  # 微信唯一标识
    nickname = Column(String(64), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, default=datetime.utcnow)