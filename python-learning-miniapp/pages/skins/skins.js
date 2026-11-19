const { request } = require('../../utils/request')
const { ensureLogin } = require('../../utils/auth')
const skin = require('../../utils/skin')

Page({
  data: {
    loading: true,
    error: '',
    skins: [],
    unlocked: 0,
    total: 0,
    skinId: 'classic',
    skinName: '',
    skinEmoji: '',
    skinDark: false,
    skinStyle: '',
    skinClass: '',
    // 未解锁的皮肤：点一下弹出说明，而不是干瞪眼
    detail: null,
    showDetail: false,
    equipping: false,
  },

  onLoad() {
    // 标题栏和页面底色先按当前皮肤走，不用等接口
    this.setData(skin.apply(skin.getSkin()))
  },

  onShow() {
    this.loadSkins()
  },

  onPullDownRefresh() {
    const stop = () => wx.stopPullDownRefresh()
    this.loadSkins().then(stop, stop)
  },

  onRetry() {
    this.loadSkins()
  },

  loadSkins() {
    const task = ensureLogin()
      .then(() => request({ url: '/profile/skins' }))
      .then((list) => this.applyList(list))
      .catch((err) => {
        this.setData({
          loading: false,
          error: (err && err.message) || '加载失败',
        })
      })
    return task
  },

  applyList(list) {
    const skins = Array.isArray(list) ? list : []
    const equipped = skins.filter((item) => item.equipped)[0] || null

    const patch = {
      loading: false,
      error: '',
      skins,
      unlocked: skins.filter((item) => item.unlocked).length,
      total: skins.length,
    }

    // 以服务端为准刷新配色缓存：换完皮肤回到任何页面都是新配色
    if (equipped) {
      const theme = skin.saveSkin({
        id: equipped.id,
        name: equipped.name,
        emoji: equipped.emoji,
        dark: equipped.dark,
        tokens: equipped.tokens,
      })
      Object.assign(patch, skin.apply(theme))
    }

    this.setData(patch)
  },

  onPick(e) {
    if (this.data.equipping) {
      return
    }
    const id = e.currentTarget.dataset.id
    const item = this.data.skins.filter((s) => s.id === id)[0]
    if (!item) {
      return
    }

    if (item.equipped) {
      wx.showToast({ title: '正在使用中', icon: 'none' })
      return
    }
    if (!item.unlocked) {
      // 没解锁：弹出说明，告诉他差多少
      this.setData({ detail: item, showDetail: true })
      return
    }

    this.equip(item)
  },

  equip(item) {
    this.setData({ equipping: true })
    request({
      url: '/profile/skin',
      method: 'POST',
      data: { skin_id: item.id },
    })
      .then((list) => {
        this.setData({ equipping: false })
        this.applyList(list)
        wx.showToast({ title: '已换上「' + item.name + '」', icon: 'none' })
      })
      .catch((err) => {
        this.setData({ equipping: false })
        wx.showToast({ title: (err && err.message) || '切换失败', icon: 'none' })
      })
  },

  closeDetail() {
    this.setData({ showDetail: false })
  },

  // 弹层里点「去解锁」：等级款回首页闯关，成就款去看错题复习
  onGoUnlock() {
    this.setData({ showDetail: false })
    wx.reLaunch({ url: '/pages/index/index' })
  },

  noop() {},
})
