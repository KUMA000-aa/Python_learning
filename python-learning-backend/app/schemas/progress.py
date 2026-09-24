from pydantic import BaseModel, ConfigDict


class ProgressOut(BaseModel):
    """某关卡的进度"""
    id: int | None = None
    user_id: int
    level_id: int
    is_completed: bool
    score: float
    attempts: int

    model_config = ConfigDict(from_attributes=True)


class LevelCompleteResponse(BaseModel):
    """通关上报回包：本关得分与是否通关"""
    level_id: int
    score: float
    is_completed: bool
    correct_count: int
    total_count: int
    attempts: int
