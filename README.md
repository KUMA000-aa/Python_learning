# Python Learning 🐍

多邻国风格的 Python 编程学习微信小程序。

> 本仓库包含**前端（微信小程序）**和**后端（FastAPI）**两个独立项目，按子目录组织。

---

## 目录结构

```
Python-learning/
├── python-learning-miniapp/   ← 微信小程序前端（导入微信开发者工具的目录）
│   ├── app.js / app.json / app.wxss
│   ├── pages/                 # 3 个页面：首页 / 答题 / 结算
│   ├── utils/                 # request / auth / config
│   └── project.config.json
│
└── python-learning-backend/   ← FastAPI 后端服务
    ├── app/
    │   ├── main.py            # FastAPI 入口
    │   ├── core/              # 配置 / 数据库 / JWT / 依赖
    │   ├── models/            # ORM 模型
    │   ├── routers/           # 路由（auth / courses / levels / answers / progress）
    │   ├── schemas/           # Pydantic 出入参
    │   ├── init_db.py         # 建表脚本
    │   └── seed.py            # 演示数据
    ├── requirements.txt
    └── README.md
```

---

## 快速开始

### 1. 启动后端（必须先启动，前端才能跑）

```powershell
cd python-learning-backend

# 创建虚拟环境（Windows）
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 创建 .env 文件（首次运行必做）
# Windows PowerShell:
@"
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-me-to-a-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=10080
WX_APPID=
WX_SECRET=
"@ | Out-File -Encoding utf8 .env

# 建表 + 导入演示数据
python -m app.init_db
python -m app.seed

# 启动服务（端口 8001）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

看到 `Uvicorn running on http://0.0.0.0:8001` 即成功。浏览器访问 `http://127.0.0.1:8001/docs` 可在线调试所有接口。

### 2. 启动前端（微信小程序）

1. 下载并安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 打开开发者工具，点击 **「导入项目」**
3. **项目目录**选择 `python-learning-miniapp/`（⚠️ 注意是这个子目录，不是仓库根目录）
4. **AppID**：填你们自己的小程序 AppID，或选择「测试号」
5. 导入后，检查 `python-learning-miniapp/utils/config.js` 里的 `BASE_URL`：

| 场景 | BASE_URL 填什么 |
|------|----------------|
| 开发者工具模拟器里跑 | `http://127.0.0.1:8001` |
| 手机真机调试（手机和电脑连同一个 WiFi） | `http://电脑的局域网IP:8001` |

6. 在微信开发者工具里，点击右上角 **「详情 → 本地设置」**，勾选 **「不校验合法域名」**
7. 点击 **编译**，模拟器里就能看到首页了

---

## 演示流程（首次打开会经历什么）

1. **首次启动小程序** → `app.js` 自动调 `/auth/wx-login` 登录（没配 WX_APPID 时自动走 mock）
2. **首页** → 拉课程树 + 每个关卡的进度，合并成关卡地图
3. **点击某关卡** → 拉题目，逐题作答（每题立即返回判分 + 解析）
4. **答完全部题目** → 调结算接口，跳结果页展示得分和通关状态

---

## 后端接口一览

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/auth/wx-login` | 登录，返回 JWT | ❌ |
| POST | `/auth/mock-login` | 调试用假登录 | ❌ |
| GET  | `/health` | 健康检查 | ❌ |
| GET  | `/courses` | 课程/单元/关卡树 | ✅ |
| GET  | `/levels/{id}/questions` | 关卡题目（不含答案） | ✅ |
| POST | `/answers` | 上报单题作答，返回判分+解析 | ✅ |
| POST | `/progress/levels/{id}/complete` | 结算本关成绩 | ✅ |
| GET  | `/progress/levels/{id}` | 查询本关进度 | ✅ |

完整接口文档见 [python-learning-backend/API.md](python-learning-backend/API.md)。

---

## 常见问题

**Q: 前端打开后一直"网络请求失败"？**
A: 检查 3 件事：① 后端是否已在 8001 端口启动；② `config.js` 的 `BASE_URL` 是否正确；③ 微信开发者工具是否勾选了"不校验合法域名"。

**Q: 手机真机调试请求不到后端？**
A: 手机和电脑必须连**同一个 WiFi**，然后 `config.js` 里的 IP 改成电脑的局域网 IP（cmd 里跑 `ipconfig` 找 IPv4 地址）。另外电脑防火墙要放行 8001 端口。

**Q: 每次打开都新建用户，进度丢了？**
A: 把 `config.js` 里的 `USE_MOCK_LOGIN` 改成 `true`，`MOCK_CODE` 设成一个固定字符串（比如你的学号）。没配 WX_APPID 时，后端会用这个 code 当 openid，保证你每次都是同一个用户。

**Q: 怎么导入新的课程/题目？**
A: 直接改 `python-learning-backend/app/seed.py` 里的演示数据，然后重新运行 `python -m app.seed` 即可（会先清空再插入）。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | 微信原生小程序（无框架） |
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 鉴权 | JWT (python-jose) |
| 数据库 | SQLite（后续可平滑切换 MySQL） |
