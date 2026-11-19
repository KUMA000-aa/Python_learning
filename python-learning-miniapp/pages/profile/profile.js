const { request, clearToken } = require('../../utils/request')
const { ensureLogin, getCachedUser } = require('../../utils/auth')
const { BASE_URL } = require('../../utils/config')
const skin = require('../../utils/skin')

function fmtScore(value) {
  const n = Number(value || 0)
  return n % 1 === 0 ? String(n) : n.toFixed(1)
}

Page({
  data: {
    loading: true,
    error: '',
    displayName: 'Python 学习者',
    avatar: '🐍',
    userId: null,
    completedLevels: 0,
    totalLevels: 0,
    percent: 0,
    wrongCount: 0,
    statItems: [],
    // ===== 等级与经验 =====
    level: 1,
    levelTitle: '',
    tierName: '',
    tierRoman: '',
    tierColor: '#6E7B8B',
    tierLight: '#EFF2F5',
    tierDesc: '',
    tierLevelsLeft: 0,
    nextTierName: '',
    exp: 0,
    expInLevel: 0,
    expNeed: 0,
    expPercent: 0,
    expToNext: 0,
    nextLevelTitle: '',
    maxLevel: 30,
    isMaxLevel: false,
    // ===== 头像框 =====
    avatarFrame: 'f1',
    frameName: '',
    frameAccent: '#B87333',
    frameEmoji: '🥉',
    frames: [],
    unlockedFrames: 0,
    pickingFrame: false,
    // ===== 皮肤 =====
    skinId: 'classic',
    skinName: '',
    skinEmoji: '',
    skinDark: false,
    skinStyle: '',
    skinClass: '',
    skins: [],
    unlockedSkins: 0,
    apiBase: BASE_URL,
    relogging: false,
  },

  onShow() {
    // 先套本地缓存的皮肤，再拉最新数据（换完皮肤从皮肤页回来立刻变）
    this.setData(skin.apply(skin.getSkin()))
    this.loadData()
  },

  onPullDownRefresh() {
    const stop = () => wx.stopPullDownRefresh()
    this.loadData().then(stop, stop)
  },

  onRetry() {
    this.loadData()
  },

  loadData() {
    this.setData({ loading: true, error: '' })

    const cached = getCachedUser()
    if (cached && cached.nickname) {
      this.setData({ displayName: cached.nickname })
    }

    const task = ensureLogin()
      .then(() => request({ url: '/profile/stats' }))
      .then((stats) => this.applyStats(stats))
      .catch((err) => {
        this.setData({ loading: false, error: (err && err.message) || '加载失败' })
      })

    return task
  },

  applyStats(stats) {
    const totalLevels = Number(stats.total_levels || 0)
    const completedLevels = Number(stats.completed_levels || 0)
    const accuracy = Number(stats.accuracy || 0)
    const correct = Number(stats.correct_count || 0)
    const answered = Number(stats.answered_count || 0)

    const frames = Array.isArray(stats.frames) ? stats.frames : []
    const skins = Array.isArray(stats.skins) ? stats.skins : []

    const patch = {
      loading: false,
      error: '',
      displayName: stats.nickname || this.data.displayName,
      userId: stats.user_id,
      level: Number(stats.level || 1),
      levelTitle: stats.level_title || '',
      tierName: stats.tier_name || '',
      tierRoman: stats.tier_roman || '',
      tierColor: stats.tier_color || '#6E7B8B',
      tierLight: stats.tier_light || '#EFF2F5',
      tierDesc: stats.tier_desc || '',
      tierLevelsLeft: Number(stats.tier_levels_left || 0),
      nextTierName: stats.next_tier_name || '',
      exp: Number(stats.exp || 0),
      expInLevel: Number(stats.exp_in_level || 0),
      expNeed: Number(stats.exp_need || 0),
      expPercent: Number(stats.exp_percent || 0),
      expToNext: Number(stats.exp_to_next || 0),
      nextLevelTitle: stats.next_level_title || '',
      maxLevel: Number(stats.max_level || 30),
      isMaxLevel: !!stats.is_max_level,
      avatarFrame: stats.avatar_frame || 'f1',
      frameName: stats.avatar_frame_name || '',
      frameAccent: stats.avatar_frame_accent || '#B87333',
      frameEmoji: stats.avatar_frame_emoji || '🥉',
      frames,
      unlockedFrames: frames.filter((f) => f.unlocked).length,
      skins,
      unlockedSkins: skins.filter((s) => s.unlocked).length,
      completedLevels,
      totalLevels,
      percent: totalLevels ? Math.round((completedLevels / totalLevels) * 100) : 0,
      wrongCount: Number(stats.wrong_count || 0),
      statItems: [
        { label: '正确率', value: answered ? accuracy.toFixed(0) + '%' : '—', accent: true },
        {
          label: '获得星星',
          value: Number(stats.total_stars || 0) + '/' + Number(stats.max_stars || 0),
          gold: true,
        },
        { label: '答对题数', value: correct + '/' + answered },
        { label: '平均分', value: fmtScore(stats.avg_score) },
        { label: '学习天数', value: String(stats.study_days || 0) },
        { label: '答题次数', value: String(stats.total_answer_times || 0) },
      ],
    }

    // 皮肤：接口里带着当前色板，顺手写缓存 + 套色
    const theme = skin.fromStats(stats)
    if (theme) {
      Object.assign(patch, skin.apply(theme))
    }

    this.setData(patch)
  },

  // 点头像框：已解锁就戴上，没解锁就告诉他还差几级
  onPickFrame(e) {
    if (this.data.pickingFrame) {
      return
    }
    const id = e.currentTarget.dataset.id
    const frame = this.data.frames.find((f) => f.id === id)
    if (!frame) {
      return
    }

    if (!frame.unlocked) {
      const left = Number(frame.levels_left || 0)
      wx.showToast({
        title: 'Lv' + frame.min_level + ' 解锁，还差 ' + left + ' 级',
        icon: 'none',
      })
      return
    }
    if (frame.equipped) {
      wx.showToast({ title: '正在使用中', icon: 'none' })
      return
    }

    this.setData({ pickingFrame: true })
    request({
      url: '/profile/frame',
      method: 'POST',
      data: { frame_id: id },
    })
      .then((frames) => {
        const list = Array.isArray(frames) ? frames : []
        const worn = list.find((f) => f.equipped) || frame
        this.setData({
          pickingFrame: false,
          frames: list,
          unlockedFrames: list.filter((f) => f.unlocked).length,
          avatarFrame: worn.id,
          frameName: worn.name,
          frameAccent: worn.accent,
          frameEmoji: worn.emoji,
        })
        wx.showToast({ title: '已佩戴「' + worn.name + '」', icon: 'none' })
      })
      .catch((err) => {
        this.setData({ pickingFrame: false })
        wx.showToast({ title: (err && err.message) || '切换失败', icon: 'none' })
      })
  },

  onGoReview() {
    wx.reLaunch({ url: '/pages/review/review' })
  },

  onGoSkins() {
    wx.navigateTo({ url: '/pages/skins/skins' })
  },

  onGoStudy() {
    wx.reLaunch({ url: '/pages/index/index' })
  },

  // 清掉本地登录态后重新登录，便于换一个 mock code 重新开始
  onRelogin() {
    if (this.data.relogging) {
      return
    }
    wx.showModal({
      title: '重新登录？',
      content: '会清空本地登录态并重新登录，进度仍按同一个用户标识保留',
      confirmText: '重新登录',
      confirmColor: '#58CC02',
      success: (res) => {
        if (!res.confirm) {
          return
        }
        this.setData({ relogging: true })
        clearToken()
        wx.removeStorageSync('user')
        ensureLogin(true)
          .then(() => {
            this.setData({ relogging: false })
            wx.showToast({ title: '已重新登录', icon: 'success' })
            this.loadData()
          })
          .catch((err) => {
            this.setData({ relogging: false })
            wx.showToast({ title: (err && err.message) || '登录失败', icon: 'none' })
          })
      },
    })
  },
})
