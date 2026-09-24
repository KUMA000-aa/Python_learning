"""演示数据填充：课程 / 单元 / 关卡 / 题目。

运行：python -m app.seed
多次运行会先清空旧的演示数据再插入，方便反复调试。
"""
import json

from app.core.database import Base, SessionLocal, engine
from app import models  # noqa: F401  触发模型注册
from app.models.course import Course, Level, Unit
from app.models.question import Question


def _q(stem: str, options: list[str], correct: str, explanation: str, idx: int) -> dict:
    return {
        "stem": stem,
        "options": options,
        "correct_answer": correct,
        "explanation": explanation,
        "order_index": idx,
    }


# 演示题目数据
LEVEL_1_QUESTIONS = [
    _q(
        "下列哪个是合法的 Python 变量名？",
        ["2name", "my_var", "class", "my-var"],
        "B",
        "变量名不能以数字开头，不能用关键字(class)，不能含连字符。",
        0,
    ),
    _q(
        "print(type(3.14)) 的输出是？",
        ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'bool'>"],
        "B",
        "3.14 是浮点数，type() 返回 float 类型。",
        1,
    ),
    _q(
        "表达式 7 // 2 的结果是？",
        ["3.5", "3", "4", "1"],
        "B",
        "// 是整除运算，向下取整，7//2 = 3。",
        2,
    ),
]

LEVEL_2_QUESTIONS = [
    _q(
        "len('hello') 的结果是？",
        ["4", "5", "6", "hello"],
        "B",
        "'hello' 有 5 个字符，len() 返回 5。",
        0,
    ),
    _q(
        "'py' + 'thon' 的结果是？",
        ["'py thon'", "'python'", "'pyton'", "报错"],
        "B",
        "字符串用 + 拼接，'py' + 'thon' = 'python'。",
        1,
    ),
    _q(
        "下列哪个能把字符串 '10' 转成整数？",
        ["str('10')", "int('10')", "float('10')", "list('10')"],
        "B",
        "int('10') 将字符串转为整数 10。",
        2,
    ),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 清空旧的演示数据（顺序：题目 → 关卡 → 单元 → 课程）
    db.query(Question).delete()
    db.query(Level).delete()
    db.query(Unit).delete()
    db.query(Course).delete()
    db.commit()

    course = Course(
        title="Python 入门",
        description="从零开始学 Python 的第一门课",
        order_index=0,
    )
    db.add(course)
    db.flush()

    unit = Unit(
        course_id=course.id,
        title="基础语法",
        description="变量、类型、运算符",
        order_index=0,
    )
    db.add(unit)
    db.flush()

    # 关卡 1
    level1 = Level(
        unit_id=unit.id,
        title="变量与 print",
        order_index=0,
    )
    db.add(level1)
    db.flush()
    for q in LEVEL_1_QUESTIONS:
        db.add(
            Question(
                level_id=level1.id,
                question_type="single_choice",
                stem=q["stem"],
                options=json.dumps(q["options"], ensure_ascii=False),
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                order_index=q["order_index"],
            )
        )

    # 关卡 2
    level2 = Level(
        unit_id=unit.id,
        title="数据类型与字符串",
        order_index=1,
    )
    db.add(level2)
    db.flush()
    for q in LEVEL_2_QUESTIONS:
        db.add(
            Question(
                level_id=level2.id,
                question_type="single_choice",
                stem=q["stem"],
                options=json.dumps(q["options"], ensure_ascii=False),
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                order_index=q["order_index"],
            )
        )

    db.commit()
    print("演示数据已填充：1 课程 / 1 单元 / 2 关卡 / 6 题")
    db.close()


if __name__ == "__main__":
    seed()
