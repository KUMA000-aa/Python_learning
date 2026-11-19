const { USE_MOCK_LOGIN, MOCK_CODE } = require('./config')
const { request, getToken, setToken, setReloginHandler } = require('./request')

const USER_KEY = 'user'

// 防止多个页面同时触发登录，复用同一个请求
let loginTask = null

function getWxCode() {
  if (USE_MOCK_LOGIN) {
    return Promise.resolve(MOCK_CODE)
  }
  return new Promise((resolve) => {
    wx.login({
      success(res) {
        // 模拟器 / 测试号 / 未配 AppID 时拿不到 code，降级到固定 mock code，保证仍可用
        resolve(res.code || MOCK_CODE)
      },
      fail() {
        resolve(MOCK_CODE)
      },
    })
  })
}

function saveUser(res) {
  if (res) {
    wx.setStorageSync(USER_KEY, res)
  }
}

function getCachedUser() {
  return wx.getStorageSync(USER_KEY) || null
}

function doLogin() {
  return getWxCode()
    .then((code) =>
      request({
        url: '/auth/wx-login',
        method: 'POST',
        data: { code },
        auth: false,
      })
    )
    .then((res) => {
      setToken(res.token)
      saveUser(res)
      return res
    })
}

/**
 * 确保已登录。已有 token 时直接返回 null（不重复登录）。
 * @param {boolean} force 强制重新登录
 */
function ensureLogin(force) {
  if (!force && getToken()) {
    return Promise.resolve(null)
  }
  if (loginTask) {
    return loginTask
  }
  loginTask = doLogin().then(
    (res) => {
      loginTask = null
      return res
    },
    (err) => {
      loginTask = null
      throw err
    }
  )
  return loginTask
}

// 注入给 request.js：遇到 401 时自动重新登录并重放请求
setReloginHandler(() => doLogin())

module.exports = {
  ensureLogin,
  doLogin,
  getCachedUser,
}
