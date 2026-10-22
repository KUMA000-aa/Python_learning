const { BASE_URL } = require('./config')

const TOKEN_KEY = 'token'

function getToken() {
  return wx.getStorageSync(TOKEN_KEY) || ''
}

function setToken(token) {
  wx.setStorageSync(TOKEN_KEY, token)
}

function clearToken() {
  wx.removeStorageSync(TOKEN_KEY)
}

/**
 * 统一请求封装
 * @param {Object} options
 * @param {string} options.url      接口路径，如 '/courses'
 * @param {string} [options.method] GET / POST
 * @param {Object} [options.data]   请求体
 * @param {boolean} [options.auth]  是否带 token，默认 true
 */
function request(options) {
  const { url, method = 'GET', data = {}, auth = true } = options

  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json' }
    if (auth) {
      const token = getToken()
      if (token) {
        header.Authorization = 'Bearer ' + token
      }
    }

    wx.request({
      url: BASE_URL + url,
      method,
      data,
      header,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        if (res.statusCode === 401) {
          // token 失效，清掉，下次进页面会重新登录
          clearToken()
        }
        let message = '请求失败（' + res.statusCode + '）'
        if (res.data && res.data.detail) {
          message = typeof res.data.detail === 'string' ? res.data.detail : '参数校验失败'
        }
        reject(new Error(message))
      },
      fail() {
        reject(new Error('网络请求失败，请确认后端已启动：' + BASE_URL))
      },
    })
  })
}

module.exports = {
  request,
  getToken,
  setToken,
  clearToken,
}
