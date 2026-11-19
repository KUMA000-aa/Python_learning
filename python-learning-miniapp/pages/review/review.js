const { request } = require('../../utils/request')
const { ensureLogin } = require('../../utils/auth')
const skin = require('../../utils/skin')

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

Page({
  data: {
    // ===== 皮肤 =====
    skinStyle: '',
    skinClass: '',
    loading: true,
    error: '',
    list: [],
    total: 0,
    corrected: 0,
  },

  onShow() {
    // 皮肤：先用缓存上色，再拉错题
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

  // 错题 = 每题「最新一次作答」仍为错的题；答对后下次加载就自动消失
  loadData() {
    this.setData({ loading: true, error: '' })

    const task = ensureLogin()
      .then(() => request({ url: '/profile/wrong-questions' }))
      .then((rows) => {
        const list = (rows || []).map((row) => ({
          qid: row.question_id,
          levelId: row.level_id,
          levelTitle: row.level_title,
          stem: row.stem,
          correctAnswer: row.correct_answer,
          userAnswer: row.user_answer,
          explanation: row.explanation || '',
          options: (row.options || []).map((text, i) => ({
            letter: LETTERS[i],
            text,
          })),
          showExp: false,
          selected: '',
          answered: false,
          ok: false,
          busy: false,
        }))

        this.setData({
          loading: false,
          error: '',
          list,
          total: list.length,
          corrected: 0,
        })
      })
      .catch((err) => {
        this.setData({
          loading: false,
          error: (err && err.message) || '加载失败',
        })
      })

    return task
  },

  // 原地重新作答：走和答题页同一个上报接口
  onAnswer(e) {
    const qi = Number(e.currentTarget.dataset.qindex)
    const letter = e.currentTarget.dataset.letter
    const item = this.data.list[qi]

    if (!item || item.answered || item.busy) {
      return
    }

    const p = (field) => 'list[' + qi + '].' + field

    this.setData({
      [p('busy')]: true,
      [p('selected')]: letter,
    })

    request({
      url: '/answers',
      method: 'POST',
      data: { question_id: item.qid, user_answer: letter },
    })
      .then((res) => {
        const ok = !!res.is_correct
        this.setData({
          [p('busy')]: false,
          [p('answered')]: true,
          [p('ok')]: ok,
          [p('showExp')]: true,
        })

        if (ok) {
          this.setData({ corrected: this.data.corrected + 1 })
          // 订正成功后同步角标数量
          const tabbar = this.selectComponent('#tabbar')
          if (tabbar && tabbar.loadBadge) {
            tabbar.loadBadge()
          }
        }
      })
      .catch((err) => {
        this.setData({
          [p('busy')]: false,
          [p('selected')]: '',
        })
        wx.showToast({ title: (err && err.message) || '提交失败', icon: 'none' })
      })
  },

  toggleExp(e) {
    const qi = Number(e.currentTarget.dataset.qindex)
    this.setData({ ['list[' + qi + '].showExp']: !this.data.list[qi].showExp })
  },

  onGoLevel(e) {
    const levelId = e.currentTarget.dataset.level
    wx.navigateTo({ url: '/pages/level/level?id=' + levelId })
  },
})
