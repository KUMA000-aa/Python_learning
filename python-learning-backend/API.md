# API 接口文档

多邻国风格 Python 学习微信小程序 · 后端接口

- Base URL：`http://127.0.0.1:8001`（本地开发）
- 交互式调试：http://127.0.0.1:8001/docs
- 认证方式：`Authorization: Bearer <token>`（登录接口返回）
- 数据格式：请求/响应均为 `application/json`

---

## 目录

| # | 接口 | 说明 | 鉴权 |
|---|------|------|------|
| 1 | [POST /auth/wx-login](#1-post-authwx-login) | 微信登录 | 否 |
| 2 | [POST /auth/mock-login](#2-post-authmock-login) | Mock 登录（调试用） | 否 |
| 3 | [GET /health](#3-get-health) | 健康检查 | 否 |
| 4 | [GET /courses](#4-get-courses) | 课程/单元/关卡树 | ✅ |
| 5 | [GET /levels/{level_id}/questions](#5-get-levelslevel_idquestions) | 关卡题目 | ✅ |
| 6 | [POST /answers](#6-post-answers) | 答题上报 | ✅ |
| 7 | [POST /progress/levels/{level_id}/complete](#7-post-progresslevelslevel_idcomplete) | 结算本关 | ✅ |
| 8 | [GET /progress/levels/{level_id}](#8-get-progresslevelslevel_id) | 查询本关进度 | ✅ |
| 9 | [GET /profile/stats](#9-get-profilestats) | 个人统计（通关数/正确率/学习天数） | ✅ |
| 10 | [GET /profile/wrong-questions](#10-get-profilewrong-questions) | 错题列表 | ✅ |
| 11 | [GET /leaderboard](#11-get-leaderboard) | 排行榜（闯关/打卡/小组三张榜） | ✅ |
| 12 | [GET /profile/frames](#12-get-profileframes) | 头像框列表（解锁状态） | ✅ |
| 13 | [POST /profile/frame](#13-post-profileframe) | 切换佩戴头像框 | ✅ |
| 14 | [GET /profile/skins](#14-get-profileskins) | 皮肤列表（解锁状态） | ✅ |
| 15 | [POST /profile/skin](#15-post-profileskin) | 换皮肤 | ✅ |

通用错误码：`401` 未带 token 或 token 失效 · `404` 资源不存在 · `422` 参数校验失败

---

## 1. `POST /auth/wx-login`

微信小程序登录。前端 `wx.login()` 拿到 `code` 后调用，后端换 openid 并签发 JWT。

- `.env` 未配置 `WX_APPID`/`WX_SECRET` 时自动降级 mock：直接用 code 当 openid（方便本地联调）
- 配置后走微信官方 `jscode2session`

**请求体**

```json
{
  "code": "string  // wx.login() 返回的临时凭证"
}
```

**响应 200**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": 1,
  "nickname": null,
  "avatar_url": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| token | string | JWT，有效期默认 7 天（`ACCESS_TOKEN_EXPIRE_MINUTES`） |
| user_id | int | 用户 ID |
| nickname | string \| null | 昵称（新用户为 null） |
| avatar_url | string \| null | 头像 |

**错误**：`400` 微信换 openid 失败（返回 errmsg）

---

## 2. `POST /auth/mock-login`

调试用的假登录，只传昵称即可创建/复用用户，不走微信。

**请求体**

```json
{ "nickname": "小明" }
```

**响应 200**：同 wx-login。

---

## 3. `GET /health`

健康检查。

**响应 200**

```json
{ "status": "ok", "database": "sqlite" }
```

---

## 4. `GET /courses`

课程列表：返回所有课程，内嵌单元与关卡（用于首页地图）。

**请求头**：`Authorization: Bearer <token>`

**响应 200**（数组）

```json
[
  {
    "id": 1,
    "title": "Python 入门",
    "description": "从零开始学 Python",
    "order_index": 1,
    "units": [
      {
        "id": 1,
        "title": "基础语法",
        "description": "变量、数据类型",
        "order_index": 1,
        "levels": [
          { "id": 1, "title": "第1关：变量", "order_index": 1 },
          { "id": 2, "title": "第2关：字符串", "order_index": 2 }
        ]
      }
    ]
  }
]
```

---

## 5. `GET /levels/{level_id}/questions`

获取某关卡全部题目。**不返回正确答案**，防止作弊。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| level_id | int | 关卡 ID |

**响应 200**（数组）

```json
[
  {
    "id": 1,
    "level_id": 1,
    "question_type": "choice",
    "stem": "下列哪个是合法的 Python 变量名？",
    "options": ["2name", "my_var", "class", "my-var"],
    "order_index": 1
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| question_type | string | 题型，目前为 `choice` |
| stem | string | 题干 |
| options | string[] | 选项数组（顺序即 A/B/C/D） |

**错误**：`404` 关卡不存在

---

## 6. `POST /answers`

上报单题作答，立即返回判分结果与解析。

**请求体**

```json
{
  "question_id": 1,
  "user_answer": "B",
  "duration_ms": 1500
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question_id | int | ✅ | 题目 ID |
| user_answer | string | ✅ | 选项字母，如 `"A"`、`"B"`（大小写不敏感） |
| duration_ms | int | 否 | 作答耗时（毫秒） |

**响应 200**

```json
{
  "question_id": 1,
  "is_correct": true,
  "correct_answer": "B",
  "explanation": "变量名不能以数字开头，不能用关键字(class)，不能含连字符。"
}
```

**错误**：`404` 题目不存在

---

## 7. `POST /progress/levels/{level_id}/complete`

答完本关全部题目后调用，结算得分、星级并落库。

- 计分规则：按 question_id 去重，取每题**最新一次**作答判定对错
- `score = 答对题数 / 总题数 × 100`（保留 2 位小数）
- `is_completed = true` 当且仅当本次全部答对

**星级规则**（后端唯一实现：`app/core/scoring.py`）

| 本次正确率 | 星级 |
|---|---|
| 全部答对 | ⭐⭐⭐ 3 |
| ≥ 2/3 但未全对 | ⭐⭐ 2 |
| ≥ 1/3 但 < 2/3 | ⭐ 1 |
| < 1/3 | 0 |

> 判定全部用整数比较（`correct * 3 >= total * 2` 等），避免 1/3、2/3 的浮点误差。
> 星级与通关状态**只升不降**：重玩答差了不会丢掉已拿到的星星，`best_stars` / `best_score` 记历史最佳。

**请求体**：无（body 留空）

**响应 200**

```json
{
  "level_id": 1,
  "score": 100.0,
  "is_completed": true,
  "correct_count": 3,
  "total_count": 3,
  "attempts": 1,
  "stars": 3,
  "best_stars": 3,
  "best_score": 100.0,
  "level_completed": true,
  "stars_hint": "",
  "exp_gained": 185,
  "exp_clear_bonus": 140,
  "exp_explore_bonus": 45,
  "exp_first_clear": true,
  "exp_total": 185,
  "level": 2,
  "level_title": "学徒",
  "prev_level": 1,
  "level_up": true,
  "frames_unlocked": [
    { "id": "f2", "name": "银纹环", "min_level": 2, "accent": "#9AA7B8", "emoji": "🥈" }
  ],
  "exp_in_level": 65,
  "exp_need": 232,
  "exp_percent": 28.02,
  "is_max_level": false,
  "max_level": 30,
  "tier": "iron",
  "tier_name": "黑铁",
  "tier_color": "#6E7B8B",
  "tier_light": "#EFF2F5",
  "tier_desc": "刚起步，先把手感磨出来",
  "tier_index": 2,
  "tier_roman": "Ⅳ",
  "tier_levels_left": 3,
  "next_tier_name": "青铜",
  "tier_up": false,
  "prev_tier_name": "黑铁"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| score | float | 本次得分 0-100 |
| is_completed | bool | 本次是否全对 |
| correct_count | int | 答对题数（按题去重） |
| total_count | int | 本关总题数 |
| attempts | int | 本关累计挑战次数 |
| stars | int | **本次**获得星级 0-3 |
| best_stars | int | 历史最佳星级（只升不降） |
| best_score | float | 历史最高分 |
| level_completed | bool | 该关是否已通关过（含之前） |
| stars_hint | string | 「再答对 N 题就能多拿 1 颗星」，满星时为空 |
| exp_gained | int | 本次获得的经验；重复闯关或未答完时为 0 |
| exp_clear_bonus | int | 其中：通关奖励（`50 + 星级 × 30`） |
| exp_explore_bonus | int | 其中：探索奖励（`答对题数 × 15`） |
| exp_first_clear | bool | 本次是否为「首次有效闯关」（决定是否发经验） |
| exp_total | int | 结算后的累计经验 |
| level | int | 结算后的等级 |
| level_title | string | 等级称号：段位 + 段内小级，如「黑铁 Ⅳ」；满级为「最强王者」 |
| prev_level | int | 结算前的等级 |
| level_up | bool | 本次是否升级 |
| frames_unlocked | array | 本次升级新解锁的头像框（结构同头像框列表） |
| skins_unlocked | array | 本次升级新解锁的皮肤（仅等级解锁款，含 id/name/emoji/rarity/light） |
| exp_in_level | int | 当前等级内已累计经验 |
| exp_need | int | 当前等级升到下一级所需经验 |
| exp_percent | float | 当前等级进度百分比，前端直接用来画经验条 |
| is_max_level / max_level | bool / int | 是否已满级 / 等级上限（30） |
| tier / tier_name | string | 段位 id / 段位名（iron/黑铁、bronze/青铜…） |
| tier_color / tier_light | string | 段位主色 / 浅色底，前端直接用 |
| tier_desc | string | 段位一句话文案 |
| tier_index / tier_roman | int / string | 段内第几级（1-5）/ 对应罗马数字（Ⅴ→Ⅰ） |
| tier_levels_left / next_tier_name | int / string | 还差几级晋级 / 下一段位名 |
| tier_up / prev_tier_name | bool / string | 本次是否跨段 / 跨段前的段位名 |

**经验规则**（后端唯一实现：`app/core/leveling.py`）

| 项目 | 规则 |
|---|---|
| 发放条件 | **首次**把本关每道题都答完，且至少答对 1 题 |
| 通关奖励 | `50 + 星级 × 30` → 0★ 50 / 1★ 80 / 2★ 110 / 3★ 140 |
| 探索奖励 | `答对题数 × 15` → 3 题全对 45 |
| 一关满分 | 140 + 45 = **185 EXP**（3 星全对） |
| 重复闯关 | 经验 +0（`exp_awarded` 标记为真后永不再发），星级与最高分照旧只升不降 |
| 0 分 | 不发经验，`exp_awarded` 保持为假，可以重打 |
| 升级曲线 | `need(lv) = 120 + 100×(lv-1) + 12×(lv-1)²`，上限 **Lv30** |
| 前几级门槛 | 120 / 232 / 368 / 528 / 712 / 920 / 1152 / 1408 … |
| 累计门槛 | Lv2 120 · Lv3 352 · Lv4 720 · Lv6 1960 · Lv9 5440 · Lv12 11440 |
| 段位 | 每段 5 级：黑铁 Lv1-5 / 青铜 6-10 / 白银 11-15 / 黄金 16-20 / 钻石 21-25 / 王者 26-30 |
| 段内小级 | Ⅴ → Ⅰ 递减（Ⅴ 刚进段、Ⅰ 即将晋级），满级 Lv30 显示「最强王者」 |
| 跨段 | 结算 `tier_up = true`，前端横幅由「升级」改为「晋级！黑铁 → 青铜」 |
| 头像框 | Lv1 素铁环 / Lv2 银纹环 / Lv4 金纹环 / Lv6 翡翠环 / Lv9 星轨环 / Lv12 传说之冠 / Lv16 星耀环 / Lv22 赤霄环 |

**错误**：`404` 关卡不存在

---

## 8. `GET /progress/levels/{level_id}`

查询当前用户在某关卡的进度。

**响应 200**

```json
{
  "id": 1,
  "user_id": 2,
  "level_id": 1,
  "is_completed": true,
  "score": 100.0,
  "stars": 3,
  "best_score": 100.0,
  "attempts": 1
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| score | float | 最近一次得分 |
| stars | int | 历史最佳星级 0-3（关卡地图上的星星） |
| best_score | float | 历史最高分 |

> 未产生进度时返回默认值：`id=null, is_completed=false, score=0, stars=0, best_score=0, attempts=0`

---

## 9. `GET /profile/stats`

个人主页统计。题目维度的数据**按每题最新一次作答去重**，与结算接口口径一致。

**响应 200**

```json
{
  "user_id": 1,
  "nickname": null,
  "avatar_url": null,
  "total_levels": 2,
  "completed_levels": 1,
  "progress_percent": 50.0,
  "avg_score": 100.0,
  "total_stars": 3,
  "max_stars": 6,
  "total_questions": 6,
  "answered_count": 3,
  "correct_count": 2,
  "wrong_count": 1,
  "accuracy": 66.67,
  "total_answer_times": 5,
  "level_attempts": 2,
  "study_days": 1,
  "exp": 280,
  "level": 3,
  "level_title": "黑铁 Ⅲ",
  "exp_in_level": 18,
  "exp_need": 368,
  "exp_percent": 4.89,
  "exp_to_next": 350,
  "next_level_title": "黑铁 Ⅱ",
  "max_level": 30,
  "is_max_level": false,
  "tier": "iron",
  "tier_name": "黑铁",
  "tier_color": "#6E7B8B",
  "tier_light": "#EFF2F5",
  "tier_desc": "刚起步，先把手感磨出来",
  "tier_index": 3,
  "tier_roman": "Ⅲ",
  "tier_levels_left": 2,
  "next_tier_name": "青铜",
  "avatar_frame": "f2",
  "avatar_frame_name": "银纹环",
  "avatar_frame_accent": "#9AA7B8",
  "avatar_frame_emoji": "🥈",
  "skin": "ocean",
  "skin_name": "深海蓝",
  "skin_emoji": "🌊",
  "skin_dark": false,
  "skin_tokens": {
    "bg": "#F0F6FC", "glow": "rgba(28, 176, 246, 0.12)", "card": "#FFFFFF",
    "border": "#E2EEF8", "text": "#1F2D3D", "sub": "#5B7285", "muted": "#93A6B6",
    "line": "#E8F0F7", "track": "#E6EFF7", "primary": "#1CB0F6", "primary_dark": "#1489C4",
    "primary_soft": "#E6F5FE", "accent": "#17C3B2", "on_primary": "#FFFFFF",
    "hero_from": "#2AA9F0", "hero_to": "#0A4F86", "hero_text": "#FFFFFF",
    "hero_border": "rgba(255, 255, 255, 0.22)", "nav": "#0F7FD0", "nav_text": "#ffffff"
  },
  "skins": [
    { "id": "classic", "name": "原野绿", "dark": false, "rarity": "normal",
      "unlocked": true, "equipped": false, "unlock_hint": "已解锁", "min_level": 1 }
  ],
  "frames": [
    { "id": "f1", "name": "素铁环", "min_level": 1, "accent": "#6E7B8B", "emoji": "🥉",
      "unlocked": true, "equipped": false, "levels_left": 0 },
    { "id": "f2", "name": "银纹环", "min_level": 2, "accent": "#9AA7B8", "emoji": "🥈",
      "unlocked": true, "equipped": true, "levels_left": 0 },
    { "id": "f6", "name": "传说之冠", "min_level": 12, "accent": "#FF5C8A", "emoji": "👑",
      "unlocked": false, "equipped": false, "levels_left": 5 }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| total_levels / completed_levels | int | 全部关卡数 / 已通关数 |
| progress_percent | float | 通关比例 0-100 |
| avg_score | float | 已挑战关卡的平均分（按各关历史最高分，无挑战时为 0） |
| total_stars | int | 已获得星星总数 |
| max_stars | int | 星星上限 = 关卡数 × 3（限定皮肤按它判断是否满星） |
| total_questions | int | 题库总题数 |
| answered_count | int | 已作答题数（按题去重） |
| correct_count | int | 最新作答为正确的题数 |
| wrong_count | int | 当前错题数 = answered − correct |
| accuracy | float | 正确率 = correct / answered × 100，**以已作答题为分母** |
| total_answer_times | int | 答题总次数（含重复作答） |
| level_attempts | int | 关卡挑战总次数 |
| study_days | int | 有作答记录的天数（按 UTC 日期去重） |
| exp / level | int | 累计经验 / 由经验推导的等级（等级不单独落库） |
| level_title | string | 等级称号（段位 + 小级，如「黑铁 Ⅲ」） |
| tier / tier_name / tier_color | string | 段位 id、名称、主色 |
| tier_index / tier_roman | int / string | 段内第几级 / 罗马数字 |
| tier_levels_left / next_tier_name | int / string | 还差几级晋级 / 下一段位名 |
| tier_desc / tier_light | string | 段位一句话 / 浅色底 |
| exp_in_level / exp_need | int | 本级已得经验 / 升级所需经验 |
| exp_percent | float | 本级进度百分比 |
| exp_to_next / next_level_title | int / string | 还差多少经验升级 / 下一级称号 |
| max_level / is_max_level | int / bool | 等级上限（30）/ 是否已满级 |
| avatar_frame | string | 当前佩戴的头像框 id |
| avatar_frame_name / accent / emoji | string | 当前头像框的名称、主色、角标 emoji |
| skin / skin_name / skin_emoji | string | 当前皮肤 id、名称、emoji |
| skin_dark | bool | 是否深色皮肤（前端据此决定文字/卡片是否反向） |
| skin_tokens | object | 当前皮肤的 20 个色板令牌，前端转成 CSS 变量套到页面根节点 |
| skins | array | 全部皮肤 + 解锁状态（结构同 `GET /profile/skins`） |
| frames | array | 全部头像框及解锁状态（`unlocked` / `equipped` / `levels_left`） |

---

## 10. `GET /profile/wrong-questions`

错题列表。**每题只看最新一次作答**，仍答错的才算错题；答对后自动移出列表。
返回结果包含 `correct_answer` 与 `explanation`（复习场景，允许看答案）。

**响应 200**（数组，按作答时间倒序）

```json
[
  {
    "question_id": 5,
    "level_id": 2,
    "level_title": "数据类型与字符串",
    "stem": "'py' + 'thon' 的结果是？",
    "options": ["'py thon'", "'python'", "'pyton'", "报错"],
    "correct_answer": "B",
    "explanation": "字符串用 + 拼接，'py' + 'thon' = 'python'。",
    "user_answer": "D",
    "answered_at": "2026-11-02T14:34:48.502400"
  }
]
```

> 订正方式：对同一 `question_id` 再调一次 `POST /answers` 并答对，该题即从错题列表消失。
> `answered_at` 为 **UTC** 时间，前端展示需要 +8 小时。

---

## 11. `GET /leaderboard`

排行榜总接口：**一次返回三张榜**，前端切 tab 不需要重新请求。

- `?limit=20`（1~100，默认 20）：每张榜返回多少名
- `*_me` 字段是「我的排名」，即使排在 `limit` 之外也会带上
- 并列时按用户 ID / 小组名兜底，保证多次请求顺序稳定

**三张榜的排序口径**

| 榜 | 主指标 | 并列时依次比较 |
|---|---|---|
| 闯关进度 `progress` | 已通关关卡数 | 星星数 → 各关最高分之和 → 用户 ID |
| 每日打卡 `checkin` | 打卡天数（有作答记录的 UTC 日期数） | 作答次数 → 用户 ID |
| 学习小组 `groups` | 组成员的各关最高分之和 | 组内星星数 → 小组名 |

> 没有填 `group_name` 的用户统一归到 `未分组`，保证小组榜覆盖所有人。

**响应 200**（节选）

```json
{
  "total_users": 15,
  "total_levels": 2,
  "total_groups": 5,
  "progress": [
    {
      "rank": 1,
      "user_id": 4,
      "nickname": "阿伟",
      "avatar_url": null,
      "completed_levels": 2,
      "total_levels": 2,
      "stars": 6,
      "score_sum": 200.0,
      "is_me": false
    }
  ],
  "progress_me": { "rank": 3, "user_id": 1, "nickname": "学习者 1", "completed_levels": 1, "total_levels": 2, "stars": 5, "score_sum": 166.67, "is_me": true },
  "checkin": [
    { "rank": 1, "user_id": 4, "nickname": "阿伟", "avatar_url": null, "study_days": 9, "answer_times": 9, "is_me": false }
  ],
  "checkin_me": null,
  "groups": [
    { "rank": 1, "group_name": "变量小分队", "member_count": 3, "total_score": 500.01, "total_stars": 15, "is_me": false }
  ],
  "groups_me": { "rank": 4, "group_name": "未分组", "member_count": 2, "total_score": 166.67, "total_stars": 5, "is_me": true }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| total_users / total_levels / total_groups | int | 参与排名的用户数 / 关卡总数 / 小组数 |
| progress[].completed_levels | int | 已通关关卡数（主指标） |
| progress[].stars / score_sum | int / float | 星星总数 / 各关最高分之和（并列时用） |
| checkin[].study_days | int | 打卡天数（主指标） |
| checkin[].answer_times | int | 作答总次数（并列时用） |
| groups[].total_score | float | 组内成员各关最高分之和（主指标） |
| groups[].total_stars | int | 组内星星总数（并列时用） |
| is_me | bool | 是否是当前用户 / 当前用户所在小组 |

> 演示数据：`python -m app.seed_leaderboard` 会生成 12 位演示同学（4 个小组，含进度与打卡记录），
> 可重复执行，只会清理 `openid` 以 `demo_` 开头的账号。

---

## 12. `GET /profile/frames`

全部头像框与解锁状态，结构与 `/profile/stats` 里的 `frames` 一致。

**响应 200**

```json
[
  { "id": "f1", "name": "素铁环", "min_level": 1, "accent": "#6E7B8B", "emoji": "🥉",
    "unlocked": true, "equipped": true, "levels_left": 0 },
  { "id": "f4", "name": "翡翠环", "min_level": 4, "accent": "#22B573", "emoji": "💎",
    "unlocked": false, "equipped": false, "levels_left": 1 }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id / name | string | 头像框标识与名称 |
| min_level | int | 解锁所需等级 |
| accent / emoji | string | 主色、角标 emoji，前端直接用 |
| unlocked | bool | 当前等级是否已解锁 |
| equipped | bool | 是否正在佩戴 |
| levels_left | int | 还差几级解锁，已解锁为 0 |

---

## 13. `POST /profile/frame`

切换佩戴的头像框。**后端会校验等级**，不能靠改前端参数提前用上高级框。

**请求体**

```json
{ "frame_id": "f2" }
```

**响应 200**：返回更新后的头像框列表（结构同 `GET /profile/frames`），其中 `equipped=true` 为刚戴上的那个。

**错误**

| 状态码 | 说明 |
|---|---|
| 404 | 头像框不存在 |
| 403 | 等级不足，`detail` 形如「达到 Lv4 才能解锁「翡翠环」」 |

---

## 14. `GET /profile/skins`

全部皮肤与解锁状态。前端「皮肤图鉴」页直接渲染这个列表，不用自己判断解锁条件。

**响应 200**

```json
[
  {
    "id": "ocean",
    "name": "深海蓝",
    "subtitle": "Lv2 解锁 · 冷静专注",
    "desc": "蓝青渐变像下潜到海底，适合晚上安静地推关卡。",
    "emoji": "🌊",
    "dark": false,
    "tags": ["专注", "清爽"],
    "unlock_type": "level",
    "min_level": 2,
    "rarity": "normal",
    "rarity_name": "普通",
    "rarity_color": "#8A94A6",
    "rarity_light": "#F2F4F7",
    "tokens": {
      "bg": "#F0F6FC", "glow": "rgba(28, 176, 246, 0.12)", "card": "#FFFFFF",
      "border": "#E2EEF8", "text": "#1F2D3D", "sub": "#5B7285", "muted": "#93A6B6",
      "line": "#E8F0F7", "track": "#E6EFF7", "primary": "#1CB0F6",
      "primary_dark": "#1489C4", "primary_soft": "#E6F5FE", "accent": "#17C3B2",
      "on_primary": "#FFFFFF", "hero_from": "#2AA9F0", "hero_to": "#0A4F86",
      "hero_text": "#FFFFFF", "hero_border": "rgba(255, 255, 255, 0.22)",
      "nav": "#0F7FD0", "nav_text": "#ffffff"
    },
    "unlocked": true,
    "equipped": false,
    "unlock_hint": "已解锁",
    "levels_left": 0
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id / name / emoji | string | 皮肤标识、名称、图标 |
| subtitle / desc | string | 一句话副标题 / 图鉴里的描述 |
| dark | bool | 深色皮肤（卡片与文字一起反向） |
| tags | array | 风格标签，前端显示成小圆角标签 |
| unlock_type | string | `level`（等级解锁）/ `full_stars`（全部关卡 3 星） |
| min_level | int | 等级解锁所需等级（`full_stars` 时仍返回，供排序用） |
| rarity / rarity_name / rarity_color / rarity_light | string | 稀有度 id、中文名、主色、浅底 |
| tokens | object | 20 个色板令牌（见下方说明） |
| unlocked | bool | 当前是否已解锁（后端按等级与星星算好） |
| equipped | bool | 是否正在使用 |
| unlock_hint | string | 已算好的一句话，如「Lv6 解锁 · 还差 3 级」「已获 4/6 星」 |
| levels_left | int | 等级款还差几级；成就款恒为 0 |

**色板令牌（tokens）**

| 令牌 | 用途 |
|---|---|
| `bg` / `glow` | 页面底色 / 顶部氛围光（半透明） |
| `card` / `border` / `line` | 卡片底、卡片描边、分割线 |
| `text` / `sub` / `muted` | 正文、次要文字、更淡的说明文字 |
| `track` | 进度条槽底色 |
| `primary` / `primary_dark` / `primary_soft` / `on_primary` | 主色、主色暗调（立体投影）、主色浅底、主色上的文字 |
| `accent` | 强调色（星星、气泡、特殊标记） |
| `hero_from` / `hero_to` / `hero_text` / `hero_border` | 顶部 hero 渐变起止色、hero 文字、hero 描边 |
| `nav` / `nav_text` | 导航栏底色与文字（`nav_text` 只有 `#ffffff` / `#000000`） |

---

## 15. `POST /profile/skin`

换皮肤。**后端校验解锁状态**，前端改参数也拿不到没解锁的皮肤。

**请求体**

```json
{ "skin_id": "ocean" }
```

**响应 200**：返回更新后的皮肤列表（结构同 `GET /profile/skins`），其中 `equipped=true` 为刚换上的那套。

**错误**

| 状态码 | 说明 |
|---|---|
| 404 | 皮肤不存在 |
| 403 | 未解锁。等级款：`达到 Lv6 才能解锁「羊皮卷」`；限定款：`「极光」需要全部关卡 3 星通关（当前 4/6 星）` |

**皮肤一览（`app/core/skins.py`）**

| 皮肤 | 稀有度 | 解锁 | 深色 |
|---|---|---|---|
| 原野绿 `classic` | 普通 | Lv1（默认） | 否 |
| 深海蓝 `ocean` | 普通 | Lv2 | 否 |
| 樱花粉 `sakura` | 稀有 | Lv4 | 否 |
| 羊皮卷 `parchment` | 稀有 | Lv6 | 否 |
| 极光 `aurora` | 限定 | 全部关卡 3 星 | 否 |
| 赛博夜 `cyber` | 史诗 | Lv9 | 是 |
| 曜金 `royal` | 传说 | Lv13 | 是 |

---

## 完整调用时序

```
前端                          后端
  │ wx.login()                  │
  │ ────code────▶ POST /auth/wx-login
  │ ◀──token────  │
  │                             │
  │ GET /courses (Bearer)       │
  │ ◀──课程树───  │
  │                             │
  │ GET /levels/1/questions     │
  │ ◀──题目(无答案)─            │
  │                             │
  │ POST /answers × N 题        │
  │ ◀──判分+解析──              │
  │                             │
  │ POST /progress/levels/1/complete
  │ ◀──score/通关──             │
  │                             │
  │ GET /progress/levels/1      │
  │ ◀──进度────   │
```

⚠️ **注意**：答题与结算必须使用**同一个 token**（同一次登录），进度按用户隔离。
