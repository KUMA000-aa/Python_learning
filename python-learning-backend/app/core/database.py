from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 专用，允许跨线程使用
)

# 创建会话工厂，每个请求用它开一个数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有数据表模型的基类，后面建表都继承它
Base = declarative_base()

# 依赖项：给每个请求提供一个数据库会话，用完自动关闭
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()