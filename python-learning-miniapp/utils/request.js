const { BASE_URL } = require('./config')

const TOKEN_KEY = 'token'

// 由 utils/auth.js 注入，避免 request.js 与 auth.js 循环依赖
let reloginHandler = null

function setReloginHandler(handler) {
  reloginHandler = handler
}

function getToken() {
  return wx.getStorageSync(TOKEN_KEY) || ''
}

function setToken(token) {
  wx.setStorageSync(TOKEN_KEY, token)
}

function clearToken() {
  wx.removeStorageSync(TOKEN_KEY)
}

// 把后端错误响应转成中文提示（FastAPI 的 detail 可能是字符串，也可能是 422 的校验数组）
function pickMessage(res) {
  const detail = res.data && res.data.detail
  if (typeof detail === 'string' && detail) {
    return detail
  }
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0] || {}
    const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : ''
    return (field ? field + ' ' : '') + (first.msg || '参数有误')
  }
  return '请求失败（' + res.statusCode + '）'
}

/**
 * 统一请求封装
 * @param {Object} options
 * @param {string} options.url      接口路径，如 '/courses'
 * @param {string} [options.method] GET / POST
 * @param {Object} [options.data]   请求体
 * @param {boolean} [options.auth]  是否带 token，默认 true
 * @param {boolean} [options.retry] 401 时是否自动重新登录后重放请求，默认 true（递归时关闭）
 */
function request(options) {
  const { url, method = 'GET', data = {}, auth = true, retry = true } = options

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

        // token 失效：静默重新登录一次再重放请求，用户无感知
        if (res.statusCode === 401 && retry && reloginHandler) {
          clearToken()
          reloginHandler()
            .then(() => request({ url, method, data, auth, retry: false }).then(resolve, reject))
            .catch(() => reject(new Error('登录已失效，请下拉刷新重试')))
          return
        }

        if (res.statusCode === 401) {
          // 没带 token 或重放仍失败，清掉，下次进页面会重新登录
          clearToken()
        }
        reject(new Error(pickMessage(res)))
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
  setReloginHandler,
}
