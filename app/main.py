from fastapi import FastAPI

from app.core.config import settings
from app.core.database import engine
from app.routers import answers, auth, courses, levels, progress

app = FastAPI(title="Python Learning API")

app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(levels.router)
app.include_router(answers.router)
app.include_router(progress.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": settings.DATABASE_URL.split("://")[0],
    }
