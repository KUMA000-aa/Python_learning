# python-learning-backend

Python 学习小程序的后端服务 —— **FastAPI + SQLite**。

已跑通完整链路：**登录 → 课程列表 → 关卡题目 → 答题上报 → 进度更新**。

## 技术栈

- Python 3.12 + FastAPI
- SQLAlchemy 2.x + SQLite（后续可平滑切换 MySQL）
- JWT 鉴权（python-jose）
- 微信登录（jscode2session），未配置密钥时自动降级为 mock 模式

## 目录结构

```
python-learning-backend/
├── app/
│   ├── main.py              # FastAPI 入口（include 所有路由）
│   ├── init_db.py           # 建表脚本（首次运行必跑）
│   ├── seed.py              # 演示数据（1 课程 / 1 单元 / 2 关卡 / 6 题）
│   ├── core/
│   │   ├── config.py        # 配置（读 .env）
│   │   ├── database.py      # SQLAlchemy 引擎 + 会话
│   │   ├── security.py      # JWT 签发 / 校验
│   │   ├── scoring.py       # 星级规则（全站唯一口径）
│   │   ├── leveling.py      # 经验/等级/头像框规则（全站唯一口径）
│   │   ├── skins.py         # 皮肤色板与解锁规则（全站唯一口径）
│   │   └── deps.py          # 依赖注入 get_current_user（从 token 取用户）
│   ├── models/              # ORM 模型
│   │   ├── user.py          # User（微信用户，openid 唯一）
│   │   ├── course.py        # Course / Unit / Level（课程 → 单元 → 关卡）
│   │   ├── question.py      # Question（题目，options 存 JSON）
│   │   ├── answer.py        # AnswerRecord（每次作答记录）
│   │   └── progress.py      # UserProgress（每关的通关状态、星级、经验发放标记）
│   ├── schemas/             # Pydantic 出入参
│   │   ├── auth.py          # WxLoginRequest / LoginResponse
│   │   ├── course.py        # CourseOut / UnitOut / LevelBrief
│   │   ├── question.py      # QuestionOut（不含答案）
│   │   ├── answer.py        # AnswerSubmitRequest / Response
│   │   ├── progress.py      # ProgressOut / LevelCompleteResponse
│   │   ├── profile.py       # ProfileStatsOut / WrongQuestionOut / AvatarFrameOut / SkinOut
│   │   └── leaderboard.py   # 排行榜出参
│   └── routers/             # 路由
│       ├── auth.py          # POST /auth/wx-login, /auth/mock-login
│       ├── courses.py       # GET /courses
│       ├── levels.py        # GET /levels/{id}/questions
│       ├── answers.py       # POST /answers
│       ├── progress.py      # GET+POST /progress/levels/{id}（含经验发放）
│       ├── profile.py       # /profile/stats、/wrong-questions、/frames、/frame、/skins、/skin
│       └── leaderboard.py   # GET /leaderboard（三张榜）
├── requirements.txt
├── .env                     # 本地配置，gitignore 不入库
├── app.db                   # SQLite 数据库，首次 seed 后生成
└── README.md
```

## 快速开始

### Windows PowerShell

```powershell
# 1. 进入后端目录
cd python-learning-backend

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 .env（首次必做）
@"
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-this-to-a-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=10080
WX_APPID=
WX_SECRET=
"@ | Out-File -Encoding utf8 .env

# 5. 建表 + 导入演示数据
python -m app.init_db
python -m app.seed

# 6. 启动服务（端口 8001，让手机也能访问用 0.0.0.0）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### macOS / Linux（bash / zsh）

```bash
cd python-learning-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cat > .env << EOF
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-this-to-a-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=10080
WX_APPID=
WX_SECRET=
EOF

python -m app.init_db
python -m app.seed
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

启动成功后会看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

浏览器打开 **http://127.0.0.1:8001/docs** → FastAPI 自动生成的 Swagger 页面，可直接在线调试所有接口。

## .env 配置说明

| 字段 | 说明 | 必须填 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接串，默认 SQLite | ✅ |
| `SECRET_KEY` | JWT 签名密钥，改成随机字符串 | ✅ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | token 有效期，默认 10080（7 天） | ❌ |
| `WX_APPID` | 微信小程序 AppID，留空走 mock 模式 | ❌ |
| `WX_SECRET` | 微信小程序 Secret，留空走 mock 模式 | ❌ |

**WX_APPID/WX_SECRET 留空时**：登录接口用 code 当 openid，方便本地联调。
**填上后**：自动走官方 `jscode2session` 换取真实 openid，无需改代码。

## 接口一览

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/auth/wx-login` | 微信登录，返回 JWT | ❌ |
| POST | `/auth/mock-login` | 调试用假登录（传昵称即可） | ❌ |
| GET  | `/health` | 健康检查 | ❌ |
| GET  | `/courses` | 课程 / 单元 / 关卡树 | ✅ |
| GET  | `/levels/{level_id}/questions` | 关卡题目（**不含答案**，防作弊） | ✅ |
| POST | `/answers` | 上报单题作答，返回判分 + 解析 | ✅ |
| POST | `/progress/levels/{level_id}/complete` | 结算本关成绩并落库 | ✅ |
| GET  | `/progress/levels/{level_id}` | 查询当前用户在某关的进度 | ✅ |
| GET  | `/profile/stats` | 个人统计 + 等级经验 + 头像框状态 | ✅ |
| GET  | `/profile/wrong-questions` | 当前错题列表 | ✅ |
| GET  | `/profile/frames` | 全部头像框与解锁状态 | ✅ |
| POST | `/profile/frame` | 切换佩戴头像框（校验等级） | ✅ |
| GET  | `/profile/skins` | 全部皮肤与解锁状态（含色板令牌） | ✅ |
| POST | `/profile/skin` | 换皮肤（校验等级或满星） | ✅ |
| GET  | `/leaderboard` | 闯关进度 / 打卡天数 / 小组总分三张榜 | ✅ |

带鉴权的接口需在请求头携带：
```
Authorization: Bearer <token>
```
Swagger 页面里点右上角 **Authorize** 粘贴 token 即可自动带。

完整接口文档（含请求/响应示例）见 [API.md](./API.md)。

## 演示流程（Swagger 页面里手动走一遍）

```
1. POST /auth/wx-login        body: {"code": "anything"}
   → 复制返回的 token → 点 Authorize 粘贴

2. GET  /courses              → 记下 level 的 id（演示数据是 1、2）

3. GET  /levels/1/questions   → 看题目

4. POST /answers × 3 题      body: {"question_id": 1, "user_answer": "B"}
                              演示数据答案全是 B

5. POST /progress/levels/1/complete  → 结算 → score=100, is_completed=true

6. GET  /progress/levels/1   → 确认进度
```

⚠️ 答题和结算必须用**同一个 token**（同一次登录），进度按用户隔离。

## 等级与经验规则

规则集中在 `app/core/leveling.py`，前后端都以此为准：

| 项目 | 规则 |
|---|---|
| 经验来源 | **首次有效闯关**：本关每道题都答完且至少答对 1 题 |
| 通关奖励 | `50 + 星级 × 30` → 0★ 50 / 1★ 80 / 2★ 110 / 3★ 140 |
| 探索奖励 | `答对题数 × 15`，3 题全对再加 45 |
| 一关满分 | 140 + 45 = **185 EXP** |
| 重复闯关 | 经验 +0；`user_progress.exp_awarded` 标记后永不再发 |
| 0 分 | 不发经验，可以重新挑战 |
| 升级曲线 | `need(lv) = 120 + 100×(lv-1) + 12×(lv-1)²` → 120 / 232 / 368 / 528 / 712 / 920 …，上限 **Lv30** |
| 累计门槛 | Lv2 120 · Lv3 352 · Lv4 720 · Lv6 1960 · Lv9 5440 · Lv12 11440 |
| 等级存储 | 只存 `users.exp`，等级由 `level_from_exp()` 推导，避免两处不同步 |
| 段位 | 每段 5 级：黑铁 1-5 / 青铜 6-10 / 白银 11-15 / 黄金 16-20 / 钻石 21-25 / 王者 26-30 |
| 段内小级 | 罗马数字 Ⅴ→Ⅰ 递减，称号形如「青铜 Ⅲ」；满级 Lv30 为「最强王者」 |
| 跨段 | `tier_up_between()` 判断是否换段，前端据此把「升级」换成「晋级」 |
| 头像框 | Lv1 素铁 / Lv2 银纹 / Lv4 金纹 / Lv6 翡翠 / Lv9 星轨 / Lv12 传说 / Lv16 星耀 / Lv22 赤霄（名字刻意不撞段位名） |

## 皮肤系统

皮肤规则集中在 `app/core/skins.py`，一套皮肤 = 20 个色板令牌，**不含任何样式规则**：

- 页面根节点挂 `style="--sk-primary:#58CC02; ..."`，WXSS 里写 `var(--sk-primary, 兜底值)`；
- 加皮肤只改后端 `SKINS` 列表，前端一行不用动；
- 深色皮肤带 `dark=true`，前端据此给根节点加 `sk-dark`，卡片/正文/分割线一起反向。

| 皮肤 | id | 稀有度 | 解锁 | 深色 |
|---|---|---|---|---|
| 原野绿 | `classic` | 普通 | Lv1（默认） | 否 |
| 深海蓝 | `ocean` | 普通 | Lv2 | 否 |
| 樱花粉 | `sakura` | 稀有 | Lv4 | 否 |
| 羊皮卷 | `parchment` | 稀有 | Lv6 | 否 |
| 极光 | `aurora` | 限定 | **全部关卡 3 星** | 否 |
| 赛博夜 | `cyber` | 史诗 | Lv9 | 是 |
| 曜金 | `royal` | 传说 | Lv13 | 是 |

- 解锁判断统一走 `is_unlocked(skin, level, total_stars, max_stars)`：`unlock_type=level` 看等级，`full_stars` 看星星是否拿满（一关都没有时不算解锁）
- `skins_state()` 会把「已解锁 / 使用中 / 还差几级」都算好给前端，前端不写判断逻辑
- 换皮肤 `POST /profile/skin` 后端校验，改前端参数拿不到没解锁的皮肤
- 升级时 `skins_unlocked_between()` 会算出本次新解锁的皮肤，结算页跟着头像框一起提示
- 只落 `users.skin` 一个字段，成绩、经验、头像框都不受影响

老库升级：`ensure_schema()` 会自动补 `users.skin`（默认 `classic`），已有用户不受影响。

### 曲线换版怎么处理老数据

`leveling_v2` 是一次性迁移（标记存在 `app_meta` 表，只跑一次）：

1. **补发探索奖励**：老版本只发通关奖励，按历史「答对过的题目数 × 15」补齐；
2. **等级保底**：把累计经验补到「原等级在新曲线下的门槛」，保证换曲线**不降级**、已解锁头像框不会被锁回去。

老库升级：`ensure_schema()` 会自动补 `users.exp`、`users.avatar_frame`、`user_progress.exp_awarded`、`user_progress.exp_gained` 四列，并按历史星级为老玩家补发经验。

## 数据库模型关系

```
User (1) ──── (N) AnswerRecord ──── (1) Question ──── (1) Level ──── (1) Unit ──── (1) Course
   │                                      │
   └────── (1) UserProgress ──────────────┘
            (user_id + level_id 联合唯一)
```

- 一个用户可以有多个答题记录（AnswerRecord），每题多次作答都会记录
- 结算时按 question_id 去重，取**最新一次**作答判定对错
- UserProgress 记录每关的通关状态、得分、尝试次数、星级，以及经验是否已发放
- User.exp 累计经验，等级由经验推导；User.avatar_frame 记录当前佩戴的头像框

## 常见问题

**Q: 启动报 "Address already in use"？**
A: 8001 端口被占了，先关旧进程或换端口：`python -m uvicorn app.main:app --port 8002`

**Q: 手机号请求不到后端？**
A: ① 用 `--host 0.0.0.0` 启动（不是 127.0.0.1）；② 手机和电脑连同一个 WiFi；③ Windows 防火墙放行 8001 端口：
```powershell
New-NetFirewallRule -DisplayName "Python Learning API" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow
```

**Q: 想清空数据重新 seed？**
A: 直接删 `app.db`，再跑 `python -m app.init_db` + `python -m app.seed`。
或者 seed 脚本本身就会先清空旧数据。

**Q: 想加新的课程/关卡/题目？**
A: 改 `seed.py` 里的演示数据结构（课程 → 单元 → 关卡 → 题目），然后 `python -m app.seed`。
生产环境建议建个管理后台直接操作数据库。

**Q: 想切到 MySQL？**
A: 把 `.env` 的 `DATABASE_URL` 改成 `mysql+pymysql://user:pass@localhost:3306/dbname`，装好 `pip install pymysql` 即可，代码不用改。

## Git 推送提示（内网环境）

直连 GitHub 不通时，推送前挂代理：

```powershell
$env:HTTPS_PROXY='http://127.0.0.1:<你的梯子端口>'
git push
```
