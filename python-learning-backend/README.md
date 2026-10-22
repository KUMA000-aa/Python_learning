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
│   │   └── deps.py          # 依赖注入 get_current_user（从 token 取用户）
│   ├── models/              # ORM 模型
│   │   ├── user.py          # User（微信用户，openid 唯一）
│   │   ├── course.py        # Course / Unit / Level（课程 → 单元 → 关卡）
│   │   ├── question.py      # Question（题目，options 存 JSON）
│   │   ├── answer.py        # AnswerRecord（每次作答记录）
│   │   └── progress.py      # UserProgress（每关的通关状态）
│   ├── schemas/             # Pydantic 出入参
│   │   ├── auth.py          # WxLoginRequest / LoginResponse
│   │   ├── course.py        # CourseOut / UnitOut / LevelBrief
│   │   ├── question.py      # QuestionOut（不含答案）
│   │   ├── answer.py        # AnswerSubmitRequest / Response
│   │   └── progress.py      # ProgressOut / LevelCompleteResponse
│   └── routers/             # 路由
│       ├── auth.py          # POST /auth/wx-login, /auth/mock-login
│       ├── courses.py       # GET /courses
│       ├── levels.py        # GET /levels/{id}/questions
│       ├── answers.py       # POST /answers
│       └── progress.py      # GET+POST /progress/levels/{id}
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

## 数据库模型关系

```
User (1) ──── (N) AnswerRecord ──── (1) Question ──── (1) Level ──── (1) Unit ──── (1) Course
   │                                      │
   └────── (1) UserProgress ──────────────┘
            (user_id + level_id 联合唯一)
```

- 一个用户可以有多个答题记录（AnswerRecord），每题多次作答都会记录
- 结算时按 question_id 去重，取**最新一次**作答判定对错
- UserProgress 记录每关的通关状态、得分、尝试次数

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
