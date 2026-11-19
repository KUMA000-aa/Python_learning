# Python Learning 🐍

多邻国风格的 Python 编程学习微信小程序。

> 本仓库包含**前端（微信小程序）**和**后端（FastAPI）**两个独立项目，按子目录组织。
>
> 当前版本：**1.1.1**

---

## 目录结构

```
Python-learning/
├── python-learning-miniapp/   ← 微信小程序前端（导入微信开发者工具的目录）
│   ├── app.js / app.json / app.wxss
│   ├── pages/                 # 学习 / 排行 / 错题 / 我的 / 皮肤 / 答题 / 结算
│   ├── components/tabbar/     # 自定义底部导航
│   ├── utils/                 # request / auth / config / skin / audio / combo-copy / summary
│   ├── assets/audio/          # 答题音效（连击音高递增）
│   └── scripts/test-skin.js   # 皮肤相关逻辑的 Node 冒烟测试
│
└── python-learning-backend/   ← FastAPI 后端服务
    ├── app/
    │   ├── main.py            # FastAPI 入口（启动时自动补齐表字段）
    │   ├── core/              # 配置 / 数据库 / JWT / 星级 / 等级 / 皮肤
    │   ├── models/            # ORM 模型
    │   ├── routers/           # auth / courses / levels / answers / progress / profile / leaderboard
    │   ├── schemas/           # Pydantic 出入参
    │   ├── init_db.py         # 建表 + 轻量迁移（幂等）
    │   ├── seed.py            # 题库数据（CH1/CH2/CH4，共 69 题）
    │   └── seed_leaderboard.py# 排行榜演示同学
    ├── requirements.txt
    └── README.md              # 后端详细说明
```

---

## 功能一览

### 学习链路
- **关卡地图**：课程 → 单元 → 关卡，蛇形排列，显示三态（已通关 / 进行中 / 未开始）与历史最佳星级
- **答题**：逐题作答，立即判分并展示解析；支持单选、判断、填空、代码补全（多空）四种题型
- **结算**：得分、星级、正确率、逐题回顾；答完全部题目才能触发首次闯关奖励

### 成长体系
- **星级**：全对 3 星，正确率 ≥ 2/3 两星，≥ 1/3 一星；历史最佳只升不降
- **经验**：只在**首次完整闯关**发放 = 通关奖励（50 + 星级 × 30）+ 探索奖励（答对题数 × 15），重复挑战不刷分
- **等级 / 段位**：上限 Lv30；每 5 级一个段位（黑铁 → 青铜 → 白银 → 黄金 → 钻石 → 王者），跨段叫「晋级」
- **头像框**：8 款，按等级解锁，佩戴校验在后端
- **皮肤**：7 套配色（含 2 套深色 + 1 套满星限定），后端下发色板令牌，前端转 CSS 变量，全站跟随

### 辅助功能
- **错题本**：只收录「最新一次作答仍答错」的题，原地重做，答对自动移出
- **排行榜**：闯关进度 / 每日打卡 / 学习小组三张榜，一次请求全量返回
- **个人主页**：通关进度、正确率、平均分、学习天数、答题次数、头像框与皮肤收藏
- **答题体验**：连击计数与分档文案、连击音效、震动反馈、静音开关、结算分数滚动与星级动画

### 题库内容

按头歌课程整理，共 **3 章 11 关 69 题**：

- **CH1-Python基础**（4 关）：行与缩进 / 标识符与保留字 / 注释 / 输入输出
- **CH2-Python序列之列表**（4 关）：增删改 / 排序 / 数值列表 / 切片
- **CH4-Python控制结构与字符串**（3 关）：字符串拼接 / 字符转换 / 查找替换

---

## 快速开始

### 1. 启动后端（必须先启动，前端才能跑）

```powershell
cd python-learning-backend

# 创建虚拟环境（Windows / Python 3.12+）
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 创建 .env（首次运行必做）
# Windows PowerShell:
@"
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-me-to-a-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=10080
WX_APPID=
WX_SECRET=
"@ | Out-File -Encoding utf8 .env

# 建表 + 导入课程数据 + 导入排行榜演示同学
python -m app.init_db
python -m app.seed
python -m app.seed_leaderboard

# 启动服务（端口 8001）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

看到 `Uvicorn running on http://0.0.0.0:8001` 即成功。浏览器访问 `http://127.0.0.1:8001/docs` 可在线调试所有接口。

> 已有旧版数据库时，新增字段会自动补齐；但题库内容需要用 `python -m app.seed` 重新导入（新版本为 3 章 11 关 69 题）。

### 2. 启动前端（微信小程序）

1. 打开微信开发者工具，点击 **「导入项目」**
2. **项目目录**选择 `python-learning-miniapp/`（⚠️ 注意是这个子目录，不是仓库根目录）
3. **AppID**：填你们自己的小程序 AppID，或点「测试号」
4. 检查 `python-learning-miniapp/utils/config.js` 里的 `BASE_URL`：

| 场景 | BASE_URL 填什么 |
|------|----------------|
| 开发者工具模拟器里跑 | `http://127.0.0.1:8001` |
| 手机真机调试（手机和电脑连同一个 WiFi） | `http://电脑的局域网IP:8001` |

5. 右上角 **「详情 → 本地设置」**，勾选 **「不校验合法域名」**
6. 点击 **编译**

> 本地开发默认走 mock 登录（`USE_MOCK_LOGIN = true` + 后端未配 `WX_APPID`），不需要真实 AppID 也能跑通全流程。要接真实微信登录时，把 `WX_APPID`/`WX_SECRET` 填进后端 `.env`，并把 `USE_MOCK_LOGIN` 改成 `false`。

---

## 已有旧版本？更新到 1.1.1

```powershell
# 1. 拉取最新代码（有本地改动先 git stash）
git checkout main
git pull origin main

# 2. 更新依赖
cd python-learning-backend
venv\Scripts\activate
pip install -r requirements.txt

# 3. 重新导入题库（由 6 题变为 69 题）
python -m app.seed

# 4. 重启后端
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

- `.env`、`venv`、`app.db` 都在 `.gitignore` 里，更新不会覆盖。
- 想清空旧进度重新开始：删除 `app.db` 后依次执行 `python -m app.init_db`、`python -m app.seed`、`python -m app.seed_leaderboard`。
- 小程序端重新「编译」即可，`utils/config.js` 的 `BASE_URL` 保持你自己的地址。

---

## 演示流程（首次打开会经历什么）

1. **首次启动** → `app.js` 自动调 `/auth/wx-login` 登录（未配密钥时自动 mock）
2. **学习页** → 拉课程树 + 各关进度 + 个人统计，渲染关卡地图、段位经验条
3. **点击关卡** → 逐题作答，立即判分；答对累计连击并播放对应音高的音效
4. **答完全部题目** → 结算：得分滚动、星级弹出、经验条推进、升级/晋级提示、错题回顾
5. **排行 / 错题 / 我的** → 三张榜单切换、错题原地重做、头像框与皮肤切换

---

## 后端接口一览

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/auth/wx-login` | 登录，返回 JWT | ❌ |
| POST | `/auth/mock-login` | 调试用假登录 | ❌ |
| GET  | `/health` | 健康检查 | ❌ |
| GET  | `/courses` | 课程/单元/关卡树 | ✅ |
| GET  | `/levels/{id}/questions` | 关卡题目（不含答案） | ✅ |
| POST | `/answers` | 单题作答，返回判分+解析 | ✅ |
| POST | `/progress/levels/{id}/complete` | 结算本关，返回星级/经验/等级 | ✅ |
| GET  | `/progress/levels/{id}` | 查询本关进度 | ✅ |
| GET  | `/profile/stats` | 个人统计 + 等级经验 + 头像框/皮肤 | ✅ |
| GET  | `/profile/wrong-questions` | 错题列表 | ✅ |
| GET  | `/profile/frames` | 头像框列表与解锁状态 | ✅ |
| POST | `/profile/frame` | 佩戴头像框（校验等级） | ✅ |
| GET  | `/profile/skins` | 皮肤列表与解锁状态 | ✅ |
| POST | `/profile/skin` | 换皮肤（校验等级或满星） | ✅ |
| GET  | `/leaderboard` | 三张排行榜 + 我的排名 | ✅ |

完整接口文档见 [python-learning-backend/API.md](python-learning-backend/API.md)。

---

## 关键规则（全站唯一口径）

| 规则 | 说明 | 代码位置 |
|------|------|----------|
| 星级 | 3 / 2 / 1 / 0，全对为 3 星 | `app/core/scoring.py` |
| 经验 | 首次闯关才发，重复挑战为 0 | `app/core/leveling.py` |
| 等级 | `need(lv) = 120 + 100×(lv-1) + 12×(lv-1)²`，上限 Lv30 | `app/core/leveling.py` |
| 皮肤解锁 | 等级解锁 或 全部关卡 3 星 | `app/core/skins.py` |

---

## 常见问题

**Q: 前端打开后一直"网络请求失败"？**
A: 检查 3 件事：① 后端是否已在 8001 端口启动；② `config.js` 的 `BASE_URL` 是否正确；③ 微信开发者工具是否勾选了"不校验合法域名"。

**Q: 手机真机调试请求不到后端？**
A: 手机和电脑必须连**同一个 WiFi**，`config.js` 里的 IP 改成电脑的局域网 IP（`ipconfig` 查 IPv4），并放行防火墙 8001 端口。

**Q: 每次打开都新建用户，进度丢了？**
A: 保持 `config.js` 里 `USE_MOCK_LOGIN = true`，`MOCK_CODE` 用一个固定字符串（比如你的学号）。后端未配 `WX_APPID` 时会用它当 openid，保证每次都是同一个用户。

**Q: 排行榜里没有别人？**
A: 在后端目录执行 `python -m app.seed_leaderboard` 生成 12 位演示同学（可重复运行，不会动真实用户）。

**Q: 怎么导入新的课程/题目？**
A: 改 `python-learning-backend/app/seed.py` 里的演示数据，然后重新运行 `python -m app.seed`。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | 微信原生小程序（无框架）+ 自定义组件 / CSS 变量换肤 |
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 鉴权 | JWT (python-jose) |
| 数据库 | SQLite（后续可平滑切换 MySQL） |
