# python-learning-backend

多邻国风格的 Python 学习微信小程序 —— 后端服务（demo 阶段）。

已跑通最小链路：**微信登录 → 课程列表 → 关卡题目 → 答题上报 → 进度更新**。

## 技术栈

- Python 3 + FastAPI
- SQLAlchemy 2.x + SQLite（后续可平滑切换 MySQL）
- JWT 鉴权（python-jose）
- 微信登录（jscode2session），未配置密钥时自动降级为 mock 模式

## 快速开始

```powershell
# 1. 克隆仓库（本仓库可能包含多个项目，后端在本目录下）
git clone https://github.com/KUMA000-aa/Python_learning.git
cd Python_learning/python-learning-backend

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量：复制下面的内容保存为 .env（放在本目录）
```

`.env` 模板：

```ini
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-this-to-a-random-string-later
ACCESS_TOKEN_EXPIRE_MINUTES=10080
WX_APPID=
WX_SECRET=
```

```powershell
# 5. 建表并导入演示数据（1 门课程 / 1 个单元 / 2 个关卡 / 6 道题）
venv\Scripts\python.exe -m app.init_db
venv\Scripts\python.exe -m app.seed

# 6. 启动服务
venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

浏览器打开 **http://127.0.0.1:8001/docs** 即可调试所有接口。

## 接口一览

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/auth/wx-login` | 微信登录，返回 JWT | 否 |
| GET  | `/health` | 健康检查 | 否 |
| GET  | `/courses` | 课程/单元/关卡树 | 是 |
| GET  | `/levels/{level_id}/questions` | 关卡题目（不含答案） | 是 |
| POST | `/answers` | 上报单题作答，返回判分+解析 | 是 |
| POST | `/progress/levels/{level_id}/complete` | 结算本关成绩并落库 | 是 |
| GET  | `/progress/levels/{level_id}` | 查询本关进度 | 是 |

带鉴权的接口需在请求头携带 `Authorization: Bearer <token>`；Swagger 页面里点右上角 Authorize 粘贴 token 即可。

## 演示流程（Swagger）

1. `POST /auth/wx-login`，body 任意填（如 `{"code": "test123"}`），复制返回的 `token` 并 Authorize
2. `GET /courses` 记下关卡 `id`（演示数据为 1、2）
3. `GET /levels/1/questions` 查看题目
4. `POST /answers` 依次答 3 道题（演示关答案均为 `B`）
5. `POST /progress/levels/1/complete` 结算 → 返回 `score=100, is_completed=true`
6. `GET /progress/levels/1` 查询确认

> 注意：答题和结算必须用**同一个 token**（同一次登录）完成，进度按用户隔离。

## 微信真实登录

- `WX_APPID` / `WX_SECRET` 留空时走 mock 模式：code 直接当 openid 用，方便前后端联调
- 填上真实小程序的 AppID + Secret 后自动切换为官方 `jscode2session`，无需改代码

## 目录结构

```
python-learning-backend/
├── app/
│   ├── main.py          # FastAPI 入口
│   ├── config.py        # 配置（读 .env）
│   ├── database.py      # SQLAlchemy 会话
│   ├── security.py      # JWT 签发/校验
│   ├── deps.py          # 依赖注入（get_current_user）
│   ├── seed.py          # 演示数据
│   ├── models/          # ORM 模型（user/course/question/progress/answer）
│   ├── schemas/         # Pydantic 出入参
│   └── routers/         # 路由（auth/courses/levels/answers/progress）
├── requirements.txt
└── .env                 # 本地配置，不入库
```

## Git 推送提示（内网环境）

直连 GitHub 不通时，推送需挂本机代理（端口以实际梯子为准）：

```powershell
$env:HTTPS_PROXY='http://127.0.0.1:<端口>'; git push
```
