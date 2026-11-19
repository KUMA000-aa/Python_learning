"""演示同学数据：给排行榜造一批有进度、有打卡记录的虚拟同学。

运行：python -m app.seed_leaderboard
可重复运行：每次先删掉 openid 以 `demo_` 开头的用户及其作答/进度记录，再重新生成。
不会动真实用户（openid 为 mock_xxx 的账号）。
"""
from datetime import datetime, timedelta

from app.core.database import Base, SessionLocal, engine
from app.core.scoring import calc_stars
from app.init_db import ensure_schema
from app import models  # noqa: F401  触发模型注册
from app.models.answer import AnswerRecord
from app.models.course import Level
from app.models.progress import UserProgress
from app.models.question import Question
from app.models.user import User

# (昵称, 学习小组, 打卡天数, 每关答对题数)
# 关卡按 order_index 排序，每关 3 题
DEMO_USERS = [
    ("阿伟", "变量小分队", 9, [3, 3]),
    ("木木", "循环冲锋队", 8, [3, 3]),
    ("小雨", "变量小分队", 7, [3, 2]),
    ("小北", "函数联盟", 7, [3, 1]),
    ("阿飞", "调试特工队", 6, [2, 3]),
    ("Kevin", "循环冲锋队", 6, [3, 2]),
    ("卷卷", "函数联盟", 5, [2, 1]),
    ("老陈", "变量小分队", 4, [2, 2]),
    ("阿紫", "循环冲锋队", 3, [1, 1]),
    ("桔子", "调试特工队", 2, [1, 1]),
    ("小满", "函数联盟", 2, [1, 1]),
    ("大熊", "调试特工队", 1, [0, 1]),
]


def _wrong_letter(correct: str) -> str:
    """随便挑一个不等于正确答案的选项，保证这条记录是错的"""
    return "A" if correct != "A" else "B"


def _clear_demo_users(db) -> int:
    demo_users = db.query(User).filter(User.openid.like("demo_%")).all()
    ids = [u.id for u in demo_users]
    if not ids:
        return 0
    db.query(AnswerRecord).filter(AnswerRecord.user_id.in_(ids)).delete(
        synchronize_session=False
    )
    db.query(UserProgress).filter(UserProgress.user_id.in_(ids)).delete(
        synchronize_session=False
    )
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return len(ids)


def seed_leaderboard():
    Base.metadata.create_all(bind=engine)
    # 老库可能还没有 users.group_name，先补列（幂等）
    ensure_schema()
    db = SessionLocal()

    removed = _clear_demo_users(db)

    levels = db.query(Level).order_by(Level.order_index).all()
    if not levels:
        print("还没有关卡，先跑 python -m app.seed")
        db.close()
        return

    questions_by_level = {
        level.id: db.query(Question)
        .filter(Question.level_id == level.id)
        .order_by(Question.order_index)
        .all()
        for level in levels
    }

    base_time = datetime.utcnow()

    for index, (nickname, group, days, level_correct) in enumerate(DEMO_USERS):
        user = User(
            openid=f"demo_{index + 1:02d}",
            nickname=nickname,
            group_name=group,
        )
        db.add(user)
        db.flush()  # 拿到 user.id

        # 造作答记录：先按各关答对题数生成，再打散到 days 个不同日期
        answers = []  # (question, level, is_correct)
        for level, correct_count in zip(levels, level_correct):
            for q_index, question in enumerate(questions_by_level[level.id]):
                answers.append((question, level, q_index < correct_count))

        # 作答数不足 days 时补几条复习记录，保证打卡天数正好等于 days
        if len(answers) < days:
            base_answers = list(answers)
            for i in range(days - len(answers)):
                answers.append(base_answers[i % len(base_answers)])

        for i, (question, level, is_correct) in enumerate(answers):
            day_offset = i % days
            moment = (base_time - timedelta(days=day_offset)).replace(
                hour=8 + (i % 10),
                minute=(i * 7) % 60,
                second=0,
                microsecond=0,
            )
            db.add(
                AnswerRecord(
                    user_id=user.id,
                    question_id=question.id,
                    level_id=level.id,
                    user_answer=(
                        question.correct_answer
                        if is_correct
                        else _wrong_letter(question.correct_answer)
                    ),
                    is_correct=is_correct,
                    duration_ms=2000 + (i * 300) % 6000,
                    answered_at=moment,
                )
            )

        # 造关卡进度：分数/星级按答对题数算，和历史最佳口径一致
        for level, correct_count in zip(levels, level_correct):
            total = len(questions_by_level[level.id])
            if total == 0:
                continue
            score = round(correct_count / total * 100, 2)
            db.add(
                UserProgress(
                    user_id=user.id,
                    level_id=level.id,
                    is_completed=correct_count >= total,
                    score=score,
                    stars=calc_stars(correct_count, total),
                    best_score=score,
                    attempts=1 + days // 4,
                )
            )

        db.commit()

    print(f"已清理 {removed} 个旧的演示同学，生成 {len(DEMO_USERS)} 位演示同学")
    db.close()


if __name__ == "__main__":
    seed_leaderboard()
