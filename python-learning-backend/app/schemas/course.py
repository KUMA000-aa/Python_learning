from pydantic import BaseModel, ConfigDict


class LevelBrief(BaseModel):
    """关卡摘要：课程列表里只暴露必要字段"""
    id: int
    title: str
    order_index: int

    model_config = ConfigDict(from_attributes=True)


class UnitOut(BaseModel):
    id: int
    title: str
    description: str | None = None
    order_index: int
    levels: list[LevelBrief] = []

    model_config = ConfigDict(from_attributes=True)


class CourseOut(BaseModel):
    id: int
    title: str
    description: str | None = None
    order_index: int
    units: list[UnitOut] = []

    model_config = ConfigDict(from_attributes=True)
