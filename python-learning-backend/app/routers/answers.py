import json
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.answer import AnswerRecord
from app.models.question import Question
from app.models.user import User
from app.schemas.answer import AnswerSubmitRequest, AnswerSubmitResponse

router = APIRouter(prefix="/answers", tags=["answers"])

# 这些题型都用选项字母判定
CHOICE_TYPES = {"single_choice", "choice", "multi_choice", "true_false"}


def _normalize(text) -> str:
    """文本归一化：换行统一、合并空白、去首尾、忽略大小写。"""
    if text is None:
        return ""
    s = str(text).replace("\r\n", "\n").replace("\r", "\n").strip()
    s = re.sub(r"\s+", " ", s)
    # 列表类答案里 "a, b" 与 "a,b" 视为相同，去掉逗号后的空格
    s = s.replace(", ", ",")
    return s.lower()


def _match_blank(expected, user) -> bool:
    """单个空位比对：正确答案可用 | 分隔多个可接受写法。"""
    user_norm = _normalize(user)
    if user_norm == "":
        return False
    return any(_normalize(alt) == user_norm for alt in str(expected).split("|"))


def _expected_answers(question: Question) -> list[str]:
    """代码补全的标准答案（按空位顺序）。"""
    raw = question.correct_answer or "[]"
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        data = raw
    if isinstance(data, list):
        return [str(x) for x in data]
    return [str(data)]


def _judge(question: Question, payload: AnswerSubmitRequest) -> tuple[bool, list[str] | None]:
    """按题型判分，返回 (是否正确, 代码补全的标准答案列表)。"""
    qtype = (question.question_type or "single_choice").lower()

    if qtype in CHOICE_TYPES:
        user = (payload.user_answer or "").strip().upper()
        correct = (question.correct_answer or "").strip().upper()
        return user == correct, None

    if qtype == "fill_blank":
        return _match_blank(question.correct_answer, payload.user_answer), None

    if qtype == "code_fill":
        expected = _expected_answers(question)
        user_answers = payload.user_answers
        if user_answers is None:
            # 兼容把多空答案以 JSON 数组放进 user_answer 的旧写法
            try:
                parsed = json.loads(payload.user_answer or "[]")
                user_answers = parsed if isinstance(parsed, list) else [str(parsed)]
            except (ValueError, TypeError):
                user_answers = [payload.user_answer or ""]
        if len(user_answers) != len(expected):
            return False, expected
        ok = all(_match_blank(e, u) for e, u in zip(expected, user_answers))
        return ok, expected

    # 未知题型：退回字母比对，避免直接判错
    user = (payload.user_answer or "").strip().upper()
    correct = (question.correct_answer or "").strip().upper()
    return user == correct, None


@router.post("", response_model=AnswerSubmitResponse)
def submit_answer(
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """答题上报：记录作答，返回是否正确与解析"""
    question = db.query(Question).filter(Question.id == payload.question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")

    is_correct, correct_answers = _judge(question, payload)

    qtype = (question.question_type or "single_choice").lower()
    if qtype == "code_fill" and payload.user_answers is not None:
        # 多空答案以 JSON 数组保存，便于错题本回看
        stored_answer = json.dumps(payload.user_answers, ensure_ascii=False)
    else:
        stored_answer = payload.user_answer or ""

    record = AnswerRecord(
        user_id=current_user.id,
        question_id=question.id,
        level_id=question.level_id,
        user_answer=stored_answer,
        is_correct=is_correct,
        duration_ms=payload.duration_ms,
    )
    db.add(record)
    db.commit()

    return AnswerSubmitResponse(
        question_id=question.id,
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        correct_answers=correct_answers,
        explanation=question.explanation,
    )
