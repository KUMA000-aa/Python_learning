from sqlalchemy import inspect, text

from app.core.database import Base, engine
from app.core.leveling import (
    cumulative_exp,
    explore_reward,
    exp_reward,
    legacy_level_from_exp,
)
from app.core.scoring import stars_from_percent
from app import models  # 这一行很关键，触发所有模型注册

# 迁移标记表：只放「一次性迁移是否跑过」这类键值，不放业务数据
META_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS app_meta (
    key VARCHAR(64) PRIMARY KEY,
    value VARCHAR(255)
)
"""


def init_db():
    Base.metadata.create_all(bind=engine)
    print("数据库表已创建")


# 表 -> {列名: 建列语句}
# 每次给模型加字段都要在这里登记，否则老库不会自动补列
COLUMN_MIGRATIONS = {
    "user_progress": {
        "stars": "INTEGER DEFAULT 0 NOT NULL",
        "best_score": "FLOAT DEFAULT 0 NOT NULL",
        "exp_awarded": "BOOLEAN DEFAULT 0 NOT NULL",
        "exp_gained": "INTEGER DEFAULT 0 NOT NULL",
    },
    "users": {
        "group_name": "VARCHAR(32)",
        "exp": "INTEGER DEFAULT 0 NOT NULL",
        "avatar_frame": "VARCHAR(32) DEFAULT 'f1'",
        "skin": "VARCHAR(32) DEFAULT 'classic'",
    },
}


def ensure_schema():
    """
    轻量迁移：给已存在的表补齐新增字段。
    create_all 只建「缺失的表」，不会改「已存在的表」，所以改用 ALTER TABLE 补列。
    可重复执行，字段已存在时自动跳过。
    """
    inspector = inspect(engine)
    added = []

    for table, columns in COLUMN_MIGRATIONS.items():
        if not inspector.has_table(table):
            continue
        existing = {col["name"] for col in inspector.get_columns(table)}
        for name, ddl in columns.items():
            if name in existing:
                continue
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
            added.append(f"{table}.{name}")

    if added:
        print("已补充字段: " + ", ".join(added))
        _backfill_stars()
        # 经验字段是本次新加的，老进度要按当时星级补发一次经验
        if any(name.startswith("user_progress.exp") for name in added):
            _backfill_exp()

    # 等级曲线换版（线性 → 二次递增）：老玩家的经验要补到「原等级在新曲线下的门槛」
    _migrate_leveling_v2()


def _ensure_meta():
    with engine.begin() as conn:
        conn.execute(text(META_TABLE_DDL))


def _migrate_leveling_v2():
    """
    等级曲线从线性（80 + 60×n）换成二次递增之后的一次性补偿。

    做两件事：
    1) 补发探索奖励：老版本只发通关奖励，按历史「答对过的题目数 × 15」补齐；
    2) 等级保底：把累计经验补到「原等级在本版曲线下的门槛」，保证改曲线不降级、
       已解锁的头像框不会突然被锁回去。

    用 app_meta 记标记，只跑一次。没有标记会重复补发，所以这一步必须幂等。
    """
    _ensure_meta()

    with engine.begin() as conn:
        done = conn.execute(
            text("SELECT value FROM app_meta WHERE key = 'leveling_v2'")
        ).fetchone()
        if done:
            return

        users = conn.execute(text("SELECT id, exp FROM users")).fetchall()
        bumped = 0
        gained_total = 0

        for row in users:
            uid = row.id
            old_exp = int(row.exp or 0)

            # 历史上答对过的题目数（按题去重，重复答对不重复计）
            n_correct = (
                conn.execute(
                    text(
                        "SELECT COUNT(DISTINCT question_id) FROM answer_records "
                        "WHERE user_id = :uid AND is_correct = 1"
                    ),
                    {"uid": uid},
                ).scalar()
                or 0
            )

            new_exp = old_exp + explore_reward(n_correct)

            # 等级保底：旧曲线算出的等级，不能在新曲线下掉下去
            lv_old = legacy_level_from_exp(old_exp)
            floor = cumulative_exp(lv_old)
            if new_exp < floor:
                new_exp = floor

            if new_exp != old_exp:
                conn.execute(
                    text("UPDATE users SET exp = :exp WHERE id = :uid"),
                    {"exp": new_exp, "uid": uid},
                )
                bumped += 1
                gained_total += new_exp - old_exp

        conn.execute(
            text("INSERT INTO app_meta (key, value) VALUES ('leveling_v2', '1')")
        )

    if bumped:
        print(f"等级曲线升级：{bumped} 位用户补发 {gained_total} 点经验（含探索奖励与等级保底）")


def _backfill_stars():
    """
    老数据没有星级，按已有的 score 反推一次。
    只在 stars 还是默认值 0 且确实挑战过（score > 0）的行上执行，不动新数据。
    """
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT id, score FROM user_progress WHERE stars = 0 AND score > 0")
        ).fetchall()
        for row in rows:
            stars = stars_from_percent(row.score)
            conn.execute(
                text(
                    "UPDATE user_progress SET stars = :stars, best_score = :best "
                    "WHERE id = :id"
                ),
                {"stars": stars, "best": float(row.score or 0), "id": row.id},
            )
    if rows:
        print(f"已回填 {len(rows)} 条历史进度的星级")


def _backfill_exp():
    """
    老玩家没有经验记录：按已通关卡的历史星级补发一次，并把 exp_awarded 置 1。
    只处理「挑战过但还没发过经验」的行，可重复执行不会重复发放。
    """
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, user_id, stars, attempts FROM user_progress "
                "WHERE exp_awarded = 0 AND attempts > 0"
            )
        ).fetchall()

        per_user: dict[int, int] = {}
        for row in rows:
            gain = exp_reward(int(row.stars or 0))
            conn.execute(
                text(
                    "UPDATE user_progress SET exp_awarded = 1, exp_gained = :gain "
                    "WHERE id = :id"
                ),
                {"gain": gain, "id": row.id},
            )
            per_user[row.user_id] = per_user.get(row.user_id, 0) + gain

        for user_id, gain in per_user.items():
            conn.execute(
                text("UPDATE users SET exp = COALESCE(exp, 0) + :gain WHERE id = :uid"),
                {"gain": gain, "uid": user_id},
            )

    if rows:
        print(f"已为 {len(per_user)} 位用户补发 {sum(per_user.values())} 点经验")


if __name__ == "__main__":
    init_db()
    ensure_schema()
