from app.core.database import Base, engine
from app import models  # 这一行很关键，触发所有模型注册

def init_db():
    Base.metadata.create_all(bind=engine)
    print("数据库表已创建")

if __name__ == "__main__":
    init_db()