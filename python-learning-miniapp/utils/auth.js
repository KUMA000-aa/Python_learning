const { USE_MOCK_LOGIN, MOCK_CODE } = require('./config')
const { request, getToken, setToken } = require('./request')

// 防止多个页面同时触发登录，复用同一个请求
let loginTask = null

function getWxCode() {
  return new Promise((resolve, reject) => {
    if (USE_MOCK_LOGIN) {
      resolve(MOCK_CODE)
      return
    }
    wx.login({
      success(res) {
        if (res.code) {
          resolve(res.code)
        } else {
          reject(new Error('wx.login 未返回 code'))
        }
      },
      fail() {
        reject(new Error('wx.login 调用失败'))
      },
    })
  })
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

module.exports = {
  ensureLogin,
}
