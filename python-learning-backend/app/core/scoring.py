"""
星级规则（全站唯一口径）

- 全部答对                  → ⭐⭐⭐ 3 星
- 正确率 ≥ 2/3 但未全对     → ⭐⭐   2 星
- 正确率 ≥ 1/3 但 < 2/3     → ⭐     1 星
- 正确率 < 1/3              → 0 星

全部用整数比较，避免 1/3、2/3 这种无限小数带来的浮点误差
（例如 1/3 = 0.3333...，用浮点算 3 * 0.3333 < 1 会误判成 0 星）。
"""

STARS_MAX = 3


def calc_stars(correct: int, total: int) -> int:
    """按答对题数算星级"""
    correct = max(int(correct or 0), 0)
    total = max(int(total or 0), 0)

    if total <= 0:
        return 0
    if correct >= total:
        return STARS_MAX
    # correct / total >= 2/3  ⇔  3 * correct >= 2 * total
    if correct * 3 >= total * 2:
        return 2
    # correct / total >= 1/3  ⇔  3 * correct >= total
    if correct * 3 >= total:
        return 1
    return 0


def stars_from_percent(percent: float) -> int:
    """
    按百分制得分反推星级，仅用于老数据回填。
    score 由 correct/total*100 四舍五入到两位小数，所以留一点容差。
    """
    value = float(percent or 0)
    if value >= 100 - 0.01:
        return STARS_MAX
    if value * 3 >= 200 - 0.05:
        return 2
    if value * 3 >= 100 - 0.05:
        return 1
    return 0


def stars_hint(correct: int, total: int, stars: int) -> str:
    """给前端的一句提示：离下一档星还差几题"""
    correct = max(int(correct or 0), 0)
    total = max(int(total or 0), 0)

    if total <= 0 or stars >= STARS_MAX:
        return ""

    # 下一档需要的答对题数（向上取整）
    if stars == 0:
        need = (total + 2) // 3                       # ceil(total / 3)
    elif stars == 1:
        need = (total * 2 + 2) // 3                   # ceil(total * 2 / 3)
    else:
        need = total

    gap = need - correct
    if gap <= 0:
        return ""
    return f"再答对 {gap} 题就能多拿 1 颗星"
