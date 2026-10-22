Page({
  data: {
    levelId: 1,
    scoreText: '0',
    isCompleted: false,
    correctCount: 0,
    totalCount: 0,
    attempts: 0,
  },

  onLoad(options) {
    let summary = {}
    try {
      summary = JSON.parse(decodeURIComponent(options.data || '{}'))
    } catch (e) {
      summary = {}
    }

    const score = Number(summary.score || 0)
    this.setData({
      levelId: summary.level_id || 1,
      scoreText: score % 1 === 0 ? String(score) : score.toFixed(2),
      isCompleted: !!summary.is_completed,
      correctCount: summary.correct_count || 0,
      totalCount: summary.total_count || 0,
      attempts: summary.attempts || 0,
    })
  },

  onBackHome() {
    wx.reLaunch({ url: '/pages/index/index' })
  },

  onRetryLevel() {
    wx.redirectTo({
      url: '/pages/level/level?id=' + this.data.levelId,
    })
  },
})
