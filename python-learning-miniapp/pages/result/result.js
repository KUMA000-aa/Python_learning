const { request } = require('../../utils/request')
const { ensureLogin } = require('../../utils/auth')
const summaryStore = require('../../utils/summary')
const comboText = require('../../utils/combo-copy')
const audio = require('../../utils/audio')
const skin = require('../../utils/skin')

function fmtScore(value) {
  const n = Number(value || 0)
  return n % 1 === 0 ? String(n) : n.toFixed(2)
}

// 得分滚动：0 → 最终分。900ms、约 30fps，
// 再快看不清数字变化，再慢会让"看结果"变得着急。
const ROLL_MS = 900
const ROLL_TICK = 33
// 星星在分数滚完之后才开始逐颗弹出
const STAR_DELAY_BASE = 0.95

// 星级对应的一句话评价
function starTextOf(stars) {
  if (stars >= 3) return '三星通关，漂亮！'
  if (stars === 2) return '两颗星，就差一点'
  if (stars === 1) return '一颗星，继续加油'
  return '这次没拿到星'
}

// 后端没给 stars_hint 时的兜底提示（比如从进度接口兜底加载的旧数据）
function starHintOf(stars, hasCounts) {
  if (!hasCounts) return ''
  if (stars >= 3) return ''
  return '全部答对就能拿满 3 颗星'
}

Page({
  data: {
    // ===== 皮肤 =====
    skinStyle: '',
    skinClass: '',
    hasData: false,
    hasCounts: false,
    levelId: null,
    levelTitle: '',
    nextId: '',
    scoreText: '0',
    scoreRolling: false, // 滚动中：数字在跳
    scoreDone: false, // 滚完了：触发一次放大回弹
    isCompleted: false,
    levelCompleted: false,
    correctCount: 0,
    totalCount: 0,
    attempts: 0,
    accuracy: 0,
    // 星级
    stars: 0,
    bestStars: 0,
    starTitle: '',
    starHint: '',
    starList: [],
    // 本次最高连击（由答题页写入缓存，兜底加载时为 0）
    maxCombo: 0,
    comboTier: 0, // 最高连击所属档位，决定评语气质
    comboTag: '', // 结算页专属评语标题
    comboTip: '', // 评语的补充一句
    // ===== 经验与等级 =====
    hasExp: false,       // 兜底加载（无缓存）时没有经验数据，整块隐藏
    expGained: 0,        // 本次获得的经验
    expTotal: 0,
    expInLevel: 0,
    expNeed: 0,
    expPercent: 0,       // 经验条宽度（延迟到入场后再赋，触发过渡动画）
    expBarWidth: 0,
    expNote: '',         // 「首次闯关 +140」「重复闯关不再获得」这类说明
    expFirstClear: false,
    level: 1,
    levelTitle: '',
    prevLevel: 1,
    levelUp: false,
    // 段位：跨段时要换成「晋级」而不是「升级」
    tierName: '',
    tierRoman: '',
    tierColor: '#6E7B8B',
    tierUp: false,
    prevTierName: '',
    framesUnlocked: [],  // 本次升级解锁的头像框
    skinsUnlocked: [],   // 本次升级解锁的皮肤（等级解锁款）
    review: [],
  },

  onLoad(options) {
    // 皮肤：结算页也要跟当前皮肤一致，不要从答题页跳过来变了色
    this.setData(skin.apply(skin.getSkin()))

    // 优先读内存缓存（答题页写入），读不到再用进度接口兜底
    const cached = summaryStore.get() || {}
    const summary = cached.summary || null
    const levelId = Number(options.levelId) || (summary && summary.level_id) || 0

    this.setData({
      levelId,
      levelTitle: cached.title || '',
      nextId: cached.nextId || '',
    })

    if (summary && typeof summary.total_count !== 'undefined') {
      this.applySummary(summary, cached.review || [], true, cached.maxCombo || 0)
      summaryStore.clear()
      return
    }

    if (levelId) {
      // 兜底：缓存失效时至少展示得分与通关状态（进度接口不返回题目数）
      ensureLogin()
        .then(() => request({ url: '/progress/levels/' + levelId }))
        .then((progress) => {
          this.applySummary(
            {
              level_id: levelId,
              score: progress.score || 0,
              is_completed: !!progress.is_completed,
              level_completed: !!progress.is_completed,
              correct_count: 0,
              total_count: 0,
              attempts: progress.attempts || 0,
              // 兜底时拿不到本次成绩，只能用历史最佳星级，提示里也说明一下
              stars: Number(progress.stars || 0),
              best_stars: Number(progress.stars || 0),
            },
            [],
            false
          )
        })
        .catch(() => this.setData({ hasData: false }))
    }

    summaryStore.clear()
  },

  applySummary(summary, review, hasCounts, maxCombo) {
    const score = Number(summary.score || 0)
    const totalCount = Number(summary.total_count || 0)
    const correctCount = Number(summary.correct_count || 0)
    const stars = Number(summary.stars || 0)
    // 历史最佳星级：老接口没有时退回本次星级
    const bestStars = Number(
      typeof summary.best_stars === 'number' ? summary.best_stars : stars
    )
    // 最高连击评语：一句话总结这局的连击表现
    const comboMax = Number(maxCombo) || 0
    const comboBest = comboText.bestComboCopy(comboMax)

    // ===== 经验 =====
    const expGained = Number(summary.exp_gained || 0)
    const expFirstClear = !!summary.exp_first_clear
    const level = Number(summary.level || 1)
    const prevLevel = Number(summary.prev_level || level)
    const framesUnlocked = Array.isArray(summary.frames_unlocked)
      ? summary.frames_unlocked
      : []
    const skinsUnlocked = Array.isArray(summary.skins_unlocked)
      ? summary.skins_unlocked
      : []
    const expInLevel = Number(summary.exp_in_level || 0)
    const expNeed = Number(summary.exp_need || 0)
    const expPercent = Number(summary.exp_percent || 0)

    // 说明文案：分清「首次拿到」「重复刷」「一分没拿」三种情况，别让人误会经验丢了
    const expClearBonus = Number(summary.exp_clear_bonus || 0)
    const expExploreBonus = Number(summary.exp_explore_bonus || 0)

    let expNote = ''
    if (expFirstClear) {
      // 把经验来源写清楚：星级拿多少、答对题数拿多少，避免「这 185 怎么来的」
      expNote =
        '通关 ' +
        expClearBonus +
        ' + 探索 ' +
        expExploreBonus +
        '（答对 ' +
        Number(summary.correct_count || 0) +
        ' 题）· 本关经验只能领一次'
    } else if (expGained === 0 && Number(summary.attempts || 0) <= 1) {
      expNote = '答完全部题目且至少答对 1 题，才算首次闯关成功'
    } else if (expGained === 0) {
      expNote = '本关经验已领取，重复闯关不再增加'
    }

    this.setData({
      hasData: true,
      hasCounts,
      levelId: summary.level_id || this.data.levelId,
      // 分数从 0 开始，马上交给 rollScore 往上滚
      scoreText: '0',
      scoreRolling: false,
      scoreDone: false,
      isCompleted: !!summary.is_completed,
      levelCompleted: !!(summary.level_completed || summary.is_completed),
      correctCount,
      totalCount,
      attempts: Number(summary.attempts || 0),
      accuracy: totalCount ? Math.round((correctCount / totalCount) * 100) : 0,
      hasExp: typeof summary.exp_total !== 'undefined',
      expGained,
      expFirstClear,
      expTotal: Number(summary.exp_total || 0),
      expInLevel,
      expNeed,
      expPercent,
      expNote,
      level,
      levelTitle: summary.level_title || '',
      prevLevel,
      levelUp: !!summary.level_up,
      tierName: summary.tier_name || '',
      tierRoman: summary.tier_roman || '',
      tierColor: summary.tier_color || '#6E7B8B',
      tierUp: !!summary.tier_up,
      prevTierName: summary.prev_tier_name || '',
      framesUnlocked,
      skinsUnlocked,
      maxCombo: comboMax,
      comboTier: comboBest.tier,
      comboTag: comboBest.tag,
      comboTip: comboBest.tip,
      stars,
      bestStars,
      starTitle: starTextOf(stars),
      starHint: summary.stars_hint || starHintOf(stars, hasCounts),
      starList: [0, 1, 2].map((i) => ({
        k: i,
        on: i < stars,
        // 等分数滚完再逐颗弹出，延迟用内联 style 传给动画
        delay: (STAR_DELAY_BASE + i * 0.16).toFixed(2),
      })),
      review: (review || []).map((item, i) => ({
        no: i + 1,
        ok: !!item.isCorrect,
        correctAnswer: item.correctAnswer || '',
      })),
    })

    this.rollScore(score)
    this.startExpBar(expPercent)

    // 升级给一声铃声，和答题页的里程碑音效同一套，静音开关同样生效
    if (summary.level_up) {
      audio.playMilestone()
    }
  },

  // 经验条：等星星弹完再推进，避免三处动画同时抢注意力
  startExpBar(percent) {
    if (this.expTimer) {
      clearTimeout(this.expTimer)
      this.expTimer = null
    }
    if (!percent) {
      this.setData({ expBarWidth: 0 })
      return
    }
    this.expTimer = setTimeout(() => {
      this.expTimer = null
      this.setData({ expBarWidth: percent })
    }, 1450)
  },

  // 分数滚动：easeOutCubic，先快后慢，最后几位数字"咬住"更耐看
  rollScore(target) {
    this.clearRoll()
    const to = Number(target) || 0

    if (!to) {
      this.setData({ scoreText: '0', scoreRolling: false, scoreDone: false })
      return
    }

    const startedAt = Date.now()
    this.rollTarget = to
    this.setData({ scoreRolling: true, scoreDone: false })

    const step = () => {
      const p = Math.min(1, (Date.now() - startedAt) / ROLL_MS)
      if (p >= 1) {
        this.scoreTimer = null
        // 结束时写精确值，避免 83 停在 83 而不是 83.33
        this.setData({ scoreText: fmtScore(to), scoreRolling: false, scoreDone: true })
        return
      }
      const eased = 1 - Math.pow(1 - p, 3)
      this.setData({ scoreText: String(Math.round(to * eased)) })
      this.scoreTimer = setTimeout(step, ROLL_TICK)
    }

    this.scoreTimer = setTimeout(step, ROLL_TICK)
  },

  clearRoll() {
    if (this.scoreTimer) {
      clearTimeout(this.scoreTimer)
      this.scoreTimer = null
    }
  },

  clearExpTimer() {
    if (this.expTimer) {
      clearTimeout(this.expTimer)
      this.expTimer = null
    }
  },

  // 页面被切走或关闭时收尾，别让数字停在半路
  finishRoll() {
    this.clearRoll()
    this.clearExpTimer()
    if (!this.data.scoreRolling) {
      return
    }
    this.setData({
      scoreText: fmtScore(this.rollTarget || 0),
      scoreRolling: false,
      scoreDone: true,
    })
  },

  onNextLevel() {
    const nextId = this.data.nextId
    if (!nextId) return
    wx.redirectTo({ url: '/pages/level/level?id=' + nextId })
  },

  onRetryLevel() {
    const { levelId, levelTitle, nextId } = this.data
    wx.redirectTo({
      url:
        '/pages/level/level?id=' +
        levelId +
        '&next=' +
        (nextId || '') +
        '&title=' +
        encodeURIComponent(levelTitle || ''),
    })
  },

  onBackHome() {
    wx.reLaunch({ url: '/pages/index/index' })
  },

  onHide() {
    this.finishRoll()
  },

  onUnload() {
    this.finishRoll()
  },
})
