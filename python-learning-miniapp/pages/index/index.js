const { request } = require('../../utils/request')
const { ensureLogin } = require('../../utils/auth')

Page({
  data: {
    loading: true,
    error: '',
    courses: [],
    completedCount: 0,
    totalCount: 0,
    percent: 0,
  },

  onShow() {
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onRetry() {
    this.loadData()
  },

  // 拉课程树 + 每个关卡的进度，合并成页面展示用的结构
  loadData() {
    this.setData({ loading: true, error: '' })

    const task = ensureLogin()
      .then(() => request({ url: '/courses' }))
      .then((courses) => {
        const levelIds = []
        courses.forEach((course) => {
          (course.units || []).forEach((unit) => {
            (unit.levels || []).forEach((level) => {
              levelIds.push(level.id)
            })
          })
        })

        // 进度接口是按关卡查询的，这里并发拉取；单个失败不影响整体
        const progressTasks = levelIds.map((id) =>
          request({ url: '/progress/levels/' + id }).catch(() => null)
        )
        return Promise.all(progressTasks).then((progressList) => ({
          courses,
          levelIds,
          progressList,
        }))
      })
      .then(({ courses, levelIds, progressList }) => {
        const progressMap = {}
        levelIds.forEach((id, i) => {
          progressMap[id] = progressList[i] || {}
        })

        let total = 0
        let completed = 0
        const viewCourses = courses.map((course) => ({
          id: course.id,
          title: course.title,
          description: course.description || '',
          units: (course.units || []).map((unit) => ({
            id: unit.id,
            title: unit.title,
            levels: (unit.levels || []).map((level) => {
              const progress = progressMap[level.id]
              total += 1
              if (progress.is_completed) {
                completed += 1
              }
              return {
                id: level.id,
                title: level.title,
                order: level.order_index,
                completed: !!progress.is_completed,
                score: progress.score || 0,
              }
            }),
          })),
        }))

        this.setData({
          loading: false,
          courses: viewCourses,
          completedCount: completed,
          totalCount: total,
          percent: total ? Math.round((completed / total) * 100) : 0,
        })
      })
      .catch((err) => {
        this.setData({
          loading: false,
          error: err.message || '加载失败',
        })
      })

    return task
  },

  onLevelTap(e) {
    const levelId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: '/pages/level/level?id=' + levelId,
    })
  },
})
