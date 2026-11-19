const { ensureLogin, getCachedUser } = require('./utils/auth')

App({
  globalData: {
    user: null,
  },

  onLaunch() {
    // 已有 token 时 ensureLogin 返回 null，这里先用上次缓存的用户信息兜底
    this.globalData.user = getCachedUser()

    // 静默登录：拿到 token 存本地，后续所有请求自动带上
    // 登录失败不阻塞页面，页面里会展示错误并提供重试
    ensureLogin()
      .then((user) => {
        if (user) {
          this.globalData.user = user
        }
      })
      .catch((err) => {
        console.error('[app] 登录失败：', err.message)
      })
  },
})
