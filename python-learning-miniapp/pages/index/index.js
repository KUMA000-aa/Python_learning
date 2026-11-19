const { request } = require('../../utils/request')
const { ensureLogin } = require('../../utils/auth')
const skin = require('../../utils/skin')

// 关卡节点在路径上的左右摆动顺序，做出多邻国那种蛇形地图
const ALIGN_CYCLE = ['flex-start', 'center', 'flex-end', 'center']

// 单元配色（主色 / 深色，深色用于立体投影与文字）
const UNIT_COLORS = [
  { main: '#58CC02', dark: '#46A302' },
  { main: '#1CB0F6', dark: '#1899D6' },
  { main: '#CE82FF', dark: '#A855F7' },
  { main: '#FF9600', dark: '#E08600' },
  { main: '#FF4B4B', dark: '#E03A3A' },
]

function fmtScore(value) {
  const n = Number(value || 0)
  return n % 1 === 0 ? String(n) : n.toFixed(2)
}

Page({
  data: {
    loading: true,
    error: '',
    errorHint: '',
    courses: [],
    // 顶部统计
    percent: 0,
    completedCount: 0,
    totalCount: 0,
    attemptedCount: 0,
    avgScore: 0,
    totalAttempts: 0,
    totalStars: 0,
    maxStars: 0,
    // 等级条（来自 /profile/stats，拿不到就整条隐藏，不影响主流程）
    level: 0,
    levelTitle: '',
    // 段位（每段 5 级：黑铁/青铜/白银/黄金/钻石/王者）
    tierName: '',
    tierRoman: '',
    tierColor: '#6E7B8B',
    expInLevel: 0,
    expNeed: 0,
    expPercent: 0,
    expToNext: 0,
    frameAccent: '#58CC02',
    frameEmoji: '',
    heroSub: '每天一小关，离独立写代码更近一步',
    // 下一个推荐关卡（第一个未通关的）
    nextLevel: null,
    isEmpty: false,
    // ===== 皮肤 =====
    skinId: 'classic',
    skinName: '',
    skinEmoji: '',
    skinDark: false,
    skinStyle: '',
    skinClass: '',
  },

  onShow() {
    // 先用本地缓存的皮肤上色，避免先闪一下默认绿再跳色
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

  // 拉课程树 + 每个关卡的进度，合并成页面展示用的结构
  loadData() {
    this.setData({ loading: true, error: '', errorHint: '' })

    const task = ensureLogin()
      .then(() =>
        Promise.all([
          request({ url: '/courses' }),
          // 等级条是增项：失败就静默跳过，别把整页拖进错误态
          request({ url: '/profile/stats' }).catch(() => null),
        ])
      )
      .then(([courses, stats]) => {
        if (stats) {
          this.applyProfile(stats)
        }
        const list = Array.isArray(courses) ? courses : []

        // 摊平成一维关卡列表：既用来并发拉进度，也用来算「下一关」
        const flat = []
        list.forEach((course) => {
          (course.units || []).forEach((unit) => {
            (unit.levels || []).forEach((level) => {
              flat.push({ id: level.id, title: level.title })
            })
          })
        })

        // 进度接口按关卡查询，并发拉取；单个失败不影响整体
        const tasks = flat.map((item) =>
          request({ url: '/progress/levels/' + item.id }).catch(() => null)
        )

        return Promise.all(tasks).then((progressList) => {
          this.applyData(list, flat, progressList)
        })
      })
      .catch((err) => this.handleError(err))

    return task
  },

  // 等级/经验条：单独渲染，和课程数据互不阻塞
  applyProfile(stats) {
    const patch = {
      level: Number(stats.level || 0),
      levelTitle: stats.level_title || '',
      tierName: stats.tier_name || '',
      tierRoman: stats.tier_roman || '',
      tierColor: stats.tier_color || '#6E7B8B',
      expInLevel: Number(stats.exp_in_level || 0),
      expNeed: Number(stats.exp_need || 0),
      expPercent: Number(stats.exp_percent || 0),
      expToNext: Number(stats.exp_to_next || 0),
      frameAccent: stats.avatar_frame_accent || '#58CC02',
      frameEmoji: stats.avatar_frame_emoji || '',
    }

    // 皮肤跟着 stats 一起回来，顺手刷新缓存（换完皮肤回首页立刻生效）
    const theme = skin.fromStats(stats)
    if (theme) {
      Object.assign(patch, skin.apply(theme))
    }

    this.setData(patch)
  },

  applyData(courses, flat, progressList) {
    const progressMap = {}
    flat.forEach((item, i) => {
      progressMap[item.id] = progressList[i] || {}
    })

    // 关卡 id -> 下一关 id（跨单元/跨课程连续）
    const nextMap = {}
    flat.forEach((item, i) => {
      nextMap[item.id] = flat[i + 1] ? flat[i + 1].id : ''
    })

    let total = 0
    let completed = 0
    let attempted = 0
    let attemptsSum = 0
    let scoreSum = 0
    let starsSum = 0
    let nextLevel = null
    let colorIndex = 0

    const viewCourses = courses.map((course) => ({
      id: course.id,
      title: course.title,
      description: course.description || '',
      units: (course.units || []).map((unit) => {
        const color = UNIT_COLORS[colorIndex % UNIT_COLORS.length]
        const ci = colorIndex % UNIT_COLORS.length
        colorIndex += 1

        const levels = (unit.levels || []).map((level, idx) => {
          const progress = progressMap[level.id] || {}
          const done = !!progress.is_completed
          const score = Number(progress.score || 0)
          // 星级与最高分都以「历史最佳」为准，重玩答差了不会掉星
          const stars = Number(progress.stars || 0)
          const bestScore = Number(
            typeof progress.best_score === 'number' ? progress.best_score : score
          )
          const attempts = Number(progress.attempts || 0)

          total += 1
          starsSum += stars
          if (done) completed += 1
          if (attempts > 0) {
            attempted += 1
            scoreSum += bestScore
          }
          attemptsSum += attempts

          // 三态：已通关 / 进行中（挑战过但没通关）/ 未开始
          const state = done ? 'done' : (attempts > 0 || score > 0 ? 'doing' : 'todo')

          if (!done && !nextLevel) {
            nextLevel = {
              id: level.id,
              title: level.title,
              nextId: nextMap[level.id] || '',
            }
          }

          return {
            id: level.id,
            title: level.title,
            badge: idx + 1,
            align: ALIGN_CYCLE[idx % ALIGN_CYCLE.length],
            state,
            stars,
            bestScoreText: fmtScore(bestScore),
            scoreText: fmtScore(score),
            nextId: nextMap[level.id] || '',
            isNext: false, // 稍后统一标记
          }
        })

        const doneCount = levels.filter((l) => l.state === 'done').length
        return {
          id: unit.id,
          title: unit.title,
          color: color.main,
          colorDark: color.dark,
          ci,
          levelCount: levels.length,
          doneCount,
          percent: levels.length ? Math.round((doneCount / levels.length) * 100) : 0,
          levels,
        }
      }),
    }))

    // 标记推荐关卡（用于在地图上高亮 + 显示「开始」气泡）
    if (nextLevel) {
      viewCourses.forEach((course) => {
        course.units.forEach((unit) => {
          unit.levels.forEach((level) => {
            if (level.id === nextLevel.id) level.isNext = true
          })
        })
      })
    }

    const percent = total ? Math.round((completed / total) * 100) : 0
    let heroSub = '每天一小关，离独立写代码更近一步'
    if (total === 0) {
      heroSub = '课程空空如也，先在后端导入演示数据吧'
    } else if (percent === 100) {
      heroSub = '全部通关！你已经把这门课吃透了 🎉'
    } else if (completed === 0) {
      heroSub = '从第一关开始，今天就通关一个'
    }

    this.setData({
      loading: false,
      error: '',
      errorHint: '',
      courses: viewCourses,
      completedCount: completed,
      totalCount: total,
      attemptedCount: attempted,
      avgScore: attempted ? Math.round(scoreSum / attempted) : 0,
      totalAttempts: attemptsSum,
      totalStars: starsSum,
      maxStars: total * 3,
      percent,
      heroSub,
      nextLevel,
      isEmpty: total === 0,
    })
  },

  // 出错时用 /health（无需鉴权）区分「后端没启动」和「接口报错」，给出更准确的提示
  handleError(err) {
    const message = (err && err.message) || '加载失败'
    request({ url: '/health', auth: false })
      .then(() => {
        this.setData({
          loading: false,
          error: message,
          errorHint: '后端能连上，可能是登录态或数据问题，下拉刷新重试',
        })
      })
      .catch(() => {
        this.setData({
          loading: false,
          error: '连不上后端服务',
          errorHint:
            '请确认已启动后端：python -m uvicorn app.main:app --port 8001，并勾选「不校验合法域名」',
        })
      })
  },

  goLevel(id, title, nextId) {
    const url =
      '/pages/level/level?id=' +
      id +
      '&next=' +
      (nextId || '') +
      '&title=' +
      encodeURIComponent(title || '')
    wx.navigateTo({
      url,
      fail() {
        // 页面栈超过 10 层时 navigateTo 会失败，降级为重定向
        wx.redirectTo({ url })
      },
    })
  },

  onLevelTap(e) {
    const { id, title, next } = e.currentTarget.dataset
    this.goLevel(id, title, next)
  },

  onContinue() {
    const next = this.data.nextLevel
    if (!next) return
    this.goLevel(next.id, next.title, next.nextId)
  },
})
