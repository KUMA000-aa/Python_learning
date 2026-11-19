from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(64), unique=True, index=True, nullable=False)  # 微信唯一标识
    nickname = Column(String(64), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    group_name = Column(String(32), nullable=True)   # 学习小组，用于小组排行榜；为空表示未分组
    exp = Column(Integer, default=0, nullable=False)          # 累计经验，等级由经验推导
    avatar_frame = Column(String(32), default="f1")           # 当前佩戴的头像框 id
    skin = Column(String(32), default="classic")              # 当前皮肤 id（配色主题）
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, default=datetime.utcnow)