from fastapi import FastAPI

from app.core.config import settings
from app.core.database import engine
from app.init_db import ensure_schema
from app.routers import (
    answers,
    auth,
    courses,
    leaderboard,
    levels,
    profile,
    progress,
)

# 启动时自动补齐新增字段（幂等，可安全重复执行；老库升级不用手动跑迁移）
ensure_schema()

app = FastAPI(title="Python Learning API")

app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(levels.router)
app.include_router(answers.router)
app.include_router(progress.router)
app.include_router(profile.router)
app.include_router(leaderboard.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": settings.DATABASE_URL.split("://")[0],
    }
