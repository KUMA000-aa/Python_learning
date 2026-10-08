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

答完本关全部题目后调用，结算得分并落库。

- 计分规则：按 question_id 去重，取每题**最新一次**作答判定对错
- `score = 答对题数 / 总题数 × 100`（保留 2 位小数）
- `is_completed = true` 当且仅当全部答对

**请求体**：无（body 留空）

**响应 200**

```json
{
  "level_id": 1,
  "score": 100.0,
  "is_completed": true,
  "correct_count": 3,
  "total_count": 3,
  "attempts": 1
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| score | float | 得分 0-100 |
| is_completed | bool | 是否通关（全对） |
| correct_count | int | 答对题数（按题去重） |
| total_count | int | 本关总题数 |
| attempts | int | 本关累计挑战次数 |

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
  "attempts": 1
}
```

> 未产生进度时返回默认值：`id=null, is_completed=false, score=0, attempts=0`

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
