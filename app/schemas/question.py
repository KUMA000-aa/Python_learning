import json

from pydantic import BaseModel, ConfigDict, field_validator


class QuestionOut(BaseModel):
    """
    返回给前端的题目：不含 correct_answer，防止前端拿到答案。
    options 在库里以 JSON 字符串存储，这里转成 list。
    """
    id: int
    level_id: int
    question_type: str
    stem: str
    options: list
    order_index: int

    @field_validator("options", mode="before")
    @classmethod
    def parse_options(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)
