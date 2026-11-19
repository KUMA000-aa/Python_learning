const { request } = require('../../utils/request')
const { ensureLogin } = require('../../utils/auth')
const skin = require('../../utils/skin')

// 三张榜单的元信息，切 tab 只换数据，不重新请求
const BOARDS = [
  { key: 'progress', name: '闯关进度', icon: '🏁', tip: '按通关关卡数排名，同分看星星' },
  { key: 'checkin', name: '每日打卡', icon: '📅', tip: '按有学习记录的天数排名' },
  { key: 'groups', name: '学习小组', icon: '👥', tip: '按小组成员的总积分排名' },
]

const MEDALS = ['🥇', '🥈', '🥉']

function fmtScore(value) {
  const n = Number(value || 0)
  return n % 1 === 0 ? String(n) : n.toFixed(1)
}

// 把三种不同结构的榜单项，统一成一套渲染用的字段
function normalize(key, item) {
  const name =
    key === 'groups' ? item.group_name : item.nickname || '匿名学习者'
  let main = ''
  let sub = ''

  if (key === 'progress') {
    main = item.completed_levels + '/' + item.total_levels + ' 关'
    sub = item.stars + ' 颗星 · ' + fmtScore(item.score_sum) + ' 分'
  } else if (key === 'checkin') {
    main = item.study_days + ' 天'
    sub = '累计作答 ' + item.answer_times + ' 次'
  } else {
    main = Math.round(Number(item.total_score || 0)) + ' 分'
    sub = item.member_count + ' 人 · ' + item.total_stars + ' 颗星'
  }

  return {
    rank: item.rank,
    name,
    avatar: (name || '?').slice(0, 1),
    main,
    sub,
    isMe: !!item.is_me,
    medal: MEDALS[item.rank - 1] || '',
    // 头像配色按名次循环，保证同一个人在不同榜单颜色一致
    ci: (item.rank - 1) % 5,
  }
}

Page({
  data: {
    // ===== 皮肤 =====
    skinStyle: '',
    skinClass: '',
    loading: true,
    error: '',
    boards: BOARDS,
    tabIndex: 0,
    tip: BOARDS[0].tip,
    totalText: '',
    podium: [],
    rest: [],
    me: null,
    showMine: false,
    isEmpty: false,
  },

  onShow() {
    // 皮肤：先用缓存上色，再拉榜单数据
    this.setData(skin.apply(skin.getSkin()))

    this.loadData()
  },

  onPullDownRefresh() {
    const stop = () => wx.stopPullDownRefresh()
    this.loadData().then(stop, stop)
  },

  loadData() {
    this.setData({ loading: true, error: '' })

    const task = ensureLogin()
      .then(() => request({ url: '/leaderboard?limit=20' }))
      .then((res) => {
        this.raw = res || {}
        this.applyBoard(this.data.tabIndex)
      })
      .catch((err) => {
        this.setData({ loading: false, error: (err && err.message) || '加载失败' })
      })

    return task
  },

  onTab(e) {
    const index = Number(e.currentTarget.dataset.index)
    if (Number.isNaN(index) || index === this.data.tabIndex) {
      return
    }
    this.applyBoard(index)
  },

  // 三张榜单已在同一次请求里拿全，切 tab 只是重新装配视图
  applyBoard(index) {
    const raw = this.raw || {}
    const board = BOARDS[index]
    if (!board) {
      return
    }

    let list = []
    let me = null
    if (board.key === 'progress') {
      list = raw.progress || []
      me = raw.progress_me
    } else if (board.key === 'checkin') {
      list = raw.checkin || []
      me = raw.checkin_me
    } else {
      list = raw.groups || []
      me = raw.groups_me
    }

    const view = list.map((item) => normalize(board.key, item))
    const meView = me ? normalize(board.key, me) : null

    // 领奖台顺序：第二名、第一名、第三名（视觉上中间最高）
    const podium = []
    if (view[1]) podium.push(view[1])
    if (view[0]) podium.push(view[0])
    if (view[2]) podium.push(view[2])

    const totalText =
      board.key === 'groups'
        ? '共 ' + (raw.total_groups || 0) + ' 个小组'
        : '共 ' + (raw.total_users || 0) + ' 位学习者'

    this.setData({
      loading: false,
      error: '',
      tabIndex: index,
      tip: board.tip,
      totalText,
      podium,
      rest: view.slice(3),
      me: meView,
      showMine: !!meView && meView.rank > 3,
      isEmpty: view.length === 0,
    })
  },

  onRetry() {
    this.loadData()
  },

  goStudy() {
    wx.reLaunch({ url: '/pages/index/index' })
  },
})
