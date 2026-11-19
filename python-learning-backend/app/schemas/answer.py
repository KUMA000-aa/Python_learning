from pydantic import BaseModel


class AnswerSubmitRequest(BaseModel):
    """答题上报：前端提交单题作答。

    选择题 / 判断题 / 填空题用 user_answer（字符串）；
    代码补全（多空）用 user_answers（按空位顺序的数组）。
    """
    question_id: int
    user_answer: str | None = None       # 选项字母 / 填空文本
    user_answers: list[str] | None = None  # 代码补全：按空位顺序的答案
    duration_ms: int | None = None       # 作答耗时（毫秒）


class AnswerSubmitResponse(BaseModel):
    """答题上报后回包：是否正确 + 正确答案 + 解析"""
    question_id: int
    is_correct: bool
    correct_answer: str
    correct_answers: list[str] | None = None  # 代码补全的标准答案，便于前端逐空展示
    explanation: str | None = None
