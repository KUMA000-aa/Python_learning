# python-learning-miniapp

Python 学习小程序 —— **微信原生小程序前端**。

## 技术栈

- 微信原生小程序（无框架，直接 JS + WXML + WXSS）
- 与后端通过 HTTP + JWT 鉴权通信
- 接口请求统一封装在 `utils/request.js`

## 目录结构

```
python-learning-miniapp/
├── app.js                      # 小程序入口，启动时自动登录
├── app.json                    # 全局配置（页面路径、导航栏样式等）
├── app.wxss                    # 全局样式
├── sitemap.json                # 搜索引擎收录配置
├── project.config.json         # 微信开发者工具项目配置
│
├── pages/
│   ├── index/                  # 首页：课程关卡地图 + 进度条
│   │   ├── index.js            # 拉课程树 + 每个关卡的进度，合并展示
│   │   ├── index.wxml
│   │   ├── index.wxss
│   │   └── index.json
│   ├── level/                  # 答题页：逐题作答 + 立即判分
│   │   ├── level.js            # 拉题目 → 提交答案 → 结算通关
│   │   ├── level.wxml
│   │   ├── level.wxss
│   │   └── level.json
│   └── result/                 # 结果页：本关得分 + 通关状态
│       ├── result.js
│       ├── result.wxml
│       ├── result.wxss
│       └── result.json
│
└── utils/
    ├── config.js               # ⚠️ 必须配置：后端地址 + 登录开关
    ├── request.js              # 统一请求封装（自动带 token）
    └── auth.js                 # 登录：wx.login → 后端换 JWT
```

## 配置（首次使用必做）

打开 `utils/config.js`，改两个东西：

```javascript
// 后端地址：开发者工具里跑填 127.0.0.1，真机调试填电脑的局域网 IP
const BASE_URL = 'http://127.0.0.1:8001'

// 登录方式：没配 WX_APPID 时建议 true，保证每次都是同一个用户（进度不丢）
const USE_MOCK_LOGIN = true
const MOCK_CODE = 'dev_demo_user_001'  // 改成你自己的固定标识
```

**三种常见场景的 BASE_URL：**

| 场景 | BASE_URL |
|------|----------|
| 开发者工具模拟器 | `http://127.0.0.1:8001` |
| 手机真机调试（同 WiFi） | `http://192.168.x.x:8001`（cmd 跑 `ipconfig` 查） |
| 部署到服务器后 | `http://你的服务器IP:8001` 或 `https://你的域名` |

## 启动步骤

### 0. 先确保后端已经启动
详见 [项目根目录 README](../README.md)，后端启动在 `8001` 端口。

### 1. 导入微信开发者工具

1. 下载并安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 打开 → **导入项目**
3. **目录** → 选择本文件夹 `python-learning-miniapp/`（⚠️ 不是仓库根目录）
4. **AppID** → 填你们自己的小程序 AppID，或点「测试号」
5. 导入成功后，在开发者工具里：
   - 点击右上角 **详情 → 本地设置**
   - ✅ 勾选 **「不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书」**（开发阶段必勾，否则无法请求本地后端）

### 2. 编译运行

点击工具栏的 **编译** 按钮，左侧模拟器会显示首页。

## 页面流程

```
首页 (pages/index)           答题页 (pages/level)         结果页 (pages/result)
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│ 📈 整体进度条     │        │ 进度条 N/总题     │        │ 🏆 通过 / 💪 加油 │
│ 📚 课程关卡列表   │  点击  │ 题干 + 选项       │  答完  │ 分数 / 正确率    │
│ 🟢 已通关 · 分数   │──────▶│ 选完立即判分+解析  │──────▶│ 再练一次 / 返回   │
│ ⚪ 未开始         │        │ 下一题            │        │                  │
└──────────────────┘        └──────────────────┘        └──────────────────┘
```

## 鉴权机制

```
小程序启动 → wx.login() 拿 code → POST /auth/wx-login → 拿到 JWT token
    → 存本地（wx.setStorageSync）→ 所有请求自动带 Authorization: Bearer <token>
    → 401 时自动清 token，下次启动重新登录
```

- 没配 WX_APPID/WX_SECRET 时，后端自动走 mock 模式（用 code 当 openid）
- `USE_MOCK_LOGIN = true` 时不走 wx.login，直接用固定的 `MOCK_CODE`，保证每次都是同一个用户
- token 默认有效期 7 天

## 常见问题

**Q: 请求一直失败？**
A: 检查：① 后端是否在 8001 端口跑着；② `config.js` 的 BASE_URL 是否对；③ 本地设置里是否勾了"不校验合法域名"。

**Q: 每次打开都变成新用户，进度丢了？**
A: 把 `config.js` 的 `USE_MOCK_LOGIN` 改成 `true`，`MOCK_CODE` 设成你的学号或固定字符串，后端会用它当 openid，每次都是你。

**Q: 手机真机调试连不上后端？**
A: ① 手机和电脑必须连**同一个 WiFi**；② BASE_URL 改成电脑的局域网 IP（`ipconfig` 查 IPv4）；③ Windows 防火墙要放行 8001 端口（"Windows Defender 防火墙 → 高级设置 → 入站规则 → 新建 TCP 规则，端口 8001，允许连接"）。

**Q: 想加新页面？**
A: 1. 在 `pages/` 下新建文件夹；2. 在 `app.json` 的 `pages` 数组里加路径；3. 微信开发者工具会自动识别。

## 后端 API

详见 [python-learning-backend/API.md](../python-learning-backend/API.md)。
