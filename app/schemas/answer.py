from pydantic import BaseModel


class AnswerSubmitRequest(BaseModel):
    """答题上报：前端提交单题作答"""
    question_id: int
    user_answer: str              # 用户选的选项字母，如 "A"
    duration_ms: int | None = None  # 作答耗时（毫秒）


class AnswerSubmitResponse(BaseModel):
    """答题上报后回包：是否正确 + 正确答案 + 解析"""
    question_id: int
    is_correct: bool
    correct_answer: str
    explanation: str | None = None
