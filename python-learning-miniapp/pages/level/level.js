const { request } = require('../../utils/request')
const { ensureLogin } = require('../../utils/auth')
const summaryStore = require('../../utils/summary')
const audio = require('../../utils/audio')
const comboText = require('../../utils/combo-copy')
const skin = require('../../utils/skin')

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

// 后端 question_type 目前只有 single_choice，这里把历史值 choice 也兼容掉
const TYPE_TEXT = {
  single_choice: '单选题',
  choice: '单选题',
  multi_choice: '多选题',
  fill_blank: '填空题',
}

Page({
  data: {
    // ===== 皮肤 =====
    skinStyle: '',
    skinClass: '',
    loading: true,
    error: '',
    levelId: null,
    levelTitle: '',
    nextId: '',
    questions: [],
    total: 0,
    index: 0,
    percent: 0,
    stem: '',
    questionType: '单选题',
    currentOptions: [],
    selectedLetter: '',
    answered: false,
    isCorrect: false,
    correctAnswer: '',
    explanation: '',
    isLast: false,
    submitting: false,
    // 逐题回顾：{ index, isCorrect, correctAnswer }，结算后带去结果页
    review: [],
    // ===== 连击 =====
    combo: 0, // 当前连续答对数，答错清零
    bestCombo: 0, // 本次答到过的最高连击，结算时带给结果页
    comboShow: false, // 居中爆发提示是否显示
    comboPop: 'a', // pop-a / pop-b 交替，用来强制重播动画
    comboTag: '',
    comboTip: '',
    comboEmoji: '🔥',
    comboTier: 1,
    comboMilestone: false, // 是否踩中里程碑（3/5/8/10…），用来加一层金光
    comboToNext: 0, // 距下一档还差几连
    comboNextName: '',
    brokenCombo: 0, // 刚被中断的连击数，用于"连击中断"提示
    breakText: '', // 断连专属安慰文案
    // ===== 音效 =====
    soundOn: true,
  },

  onLoad(options) {
    // 皮肤：先把缓存的色板套上，页面底色/主色立刻到位
    this.setData(skin.apply(skin.getSkin()))

    const levelId = Number(options.id)
    const levelTitle = options.title ? decodeURIComponent(options.title) : ''
    const nextId = options.next || ''

    this.setData({ levelId, levelTitle, nextId, soundOn: audio.isEnabled() })
    // 预热常用音效，避免第一题答对时才有 100ms 级的延迟
    audio.warmup()

    if (levelTitle) {
      wx.setNavigationBarTitle({ title: levelTitle })
    }

    if (!levelId) {
      this.setData({ loading: false, error: '缺少关卡 ID' })
      return
    }
    this.loadQuestions(levelId)
  },

  loadQuestions(levelId) {
    this.setData({ loading: true, error: '' })

    ensureLogin()
      .then(() => request({ url: '/levels/' + levelId + '/questions' }))
      .then((questions) => {
        if (!questions || !questions.length) {
          throw new Error('本关还没有题目')
        }
        this.setData({
          loading: false,
          questions,
          total: questions.length,
          review: [],
          // 重练时连击从头算
          combo: 0,
          bestCombo: 0,
          comboShow: false,
          brokenCombo: 0,
          breakText: '',
        })
        this.buildView(0)
      })
      .catch((err) => {
        this.setData({ loading: false, error: err.message || '加载失败' })
      })
  },

  // 把当前题渲染成视图数据
  buildView(index) {
    const questions = this.data.questions
    const question = questions[index]
    if (!question) {
      return
    }

    const options = (question.options || []).map((text, i) => ({
      letter: LETTERS[i],
      text,
    }))

    this.startedAt = Date.now()
    // 换题时收起上一题的连击爆发，避免停在新题画面上
    this.clearComboHide()
    this.setData({
      index,
      stem: question.stem,
      questionType: TYPE_TEXT[question.question_type] || '题目',
      currentOptions: options,
      isLast: index === questions.length - 1,
      selectedLetter: '',
      answered: false,
      isCorrect: false,
      correctAnswer: '',
      explanation: '',
      comboShow: false,
      brokenCombo: 0,
      breakText: '',
    })
    this.refreshPercent()
  },

  // 进度条按「已作答题目数」增长：答完当前题后前进一格
  refreshPercent() {
    const { index, answered, total } = this.data
    const done = index + (answered ? 1 : 0)
    this.setData({ percent: total ? Math.round((done / total) * 100) : 0 })
  },

  // ===== 连击 =====
  // 答对：连击 +1，返回需要合并进 setData 的字段
  bumpCombo() {
    const combo = this.data.combo + 1
    const copy = comboText.comboCopy(combo)
    const patch = {
      combo,
      bestCombo: Math.max(combo, this.data.bestCombo),
      brokenCombo: 0,
      breakText: '',
      // 文案在答对时就先算好，底部反馈条与爆发浮层共用同一句，避免两处不一致
      comboTag: copy.tag,
      comboTier: copy.tier,
      comboEmoji: copy.emoji,
      comboMilestone: copy.isMilestone,
      comboToNext: copy.toNext,
      comboNextName: copy.nextName,
    }

    // 首答（combo=1）不弹，避免每题都闪一下；2 连起才有意义
    if (combo >= 2) {
      patch.comboShow = true
      patch.comboTip = copy.tip
      // 同一元素上重复设置相同动画不会重播，所以用两个同名关键帧交替触发
      patch.comboPop = this.data.comboPop === 'a' ? 'b' : 'a'
      this.scheduleComboHide()
    }
    return patch
  },

  // 答错：连击清零，并记下断掉的连击数用于提示
  breakCombo() {
    const broken = this.data.combo
    this.clearComboHide()
    return {
      combo: 0,
      comboShow: false,
      brokenCombo: broken >= 2 ? broken : 0,
      breakText: comboText.breakCopy(broken),
      comboTag: '',
      comboTip: '',
      comboMilestone: false,
    }
  },

  scheduleComboHide() {
    this.clearComboHide()
    this.comboTimer = setTimeout(() => {
      this.comboTimer = null
      this.setData({ comboShow: false })
    }, 1300)
  },

  clearComboHide() {
    if (this.comboTimer) {
      clearTimeout(this.comboTimer)
      this.comboTimer = null
    }
  },

  // 震动：部分机型/基础库不支持，失败即忽略
  buzz(type) {
    try {
      wx.vibrateShort({ type })
    } catch (err) {
      // 忽略
    }
  },

  // 音效开关：关掉后立刻静音，打开时放一声作为试听
  onToggleSound() {
    const on = audio.toggle()
    this.setData({ soundOn: on })
    if (on) {
      audio.playCorrect(1)
    }
    this.buzz('light')
  },

  onSelect(e) {
    if (this.data.answered || this.data.submitting) {
      return
    }

    const letter = e.currentTarget.dataset.letter
    const question = this.data.questions[this.data.index]
    const duration = Date.now() - (this.startedAt || Date.now())

    this.setData({ selectedLetter: letter, submitting: true })

    request({
      url: '/answers',
      method: 'POST',
      data: {
        question_id: question.id,
        user_answer: letter,
        duration_ms: duration,
      },
    })
      .then((res) => {
        const correct = !!res.is_correct
        const review = this.data.review.concat([
          {
            index: this.data.index,
            isCorrect: correct,
            correctAnswer: res.correct_answer || '',
          },
        ])

        const patch = {
          submitting: false,
          answered: true,
          isCorrect: correct,
          correctAnswer: res.correct_answer || '',
          explanation: res.explanation || '',
          review,
        }

        // 连击与音效：先算出新状态，再一次性 setData
        const comboPatch = correct ? this.bumpCombo() : this.breakCombo()
        Object.assign(patch, comboPatch)

        this.setData(patch)
        this.refreshPercent()

        if (correct) {
          // 音高随连击上行，听感上"越答越往上走"
          audio.playCorrect(patch.combo)
          // 每 5 连击来一段铃声，给个阶段性反馈
          if (patch.combo % 5 === 0) {
            audio.playMilestone()
            this.buzz('light')
          }
        } else {
          audio.playWrong()
          this.buzz('heavy')
        }
      })
      .catch((err) => {
        this.setData({ submitting: false, selectedLetter: '' })
        wx.showToast({ title: (err && err.message) || '提交失败', icon: 'none' })
      })
  },

  onNext() {
    if (!this.data.answered || this.data.submitting) {
      return
    }
    if (this.data.index + 1 < this.data.total) {
      this.buildView(this.data.index + 1)
      return
    }
    this.completeLevel()
  },

  // 全部答完：调结算接口，再跳结果页
  completeLevel() {
    if (this.data.submitting) {
      return
    }
    this.setData({ submitting: true })
    wx.showLoading({ title: '结算中', mask: true })

    request({
      url: '/progress/levels/' + this.data.levelId + '/complete',
      method: 'POST',
    })
      .then((summary) => {
        wx.hideLoading()
        // 结果数据走内存缓存，避免把整段 JSON 塞进 URL（有长度限制且易出转义问题）
        summaryStore.set({
          summary,
          title: this.data.levelTitle,
          nextId: this.data.nextId,
          review: this.data.review,
          maxCombo: this.data.bestCombo,
        })
        wx.redirectTo({
          url: '/pages/result/result?levelId=' + (summary.level_id || this.data.levelId),
        })
      })
      .catch((err) => {
        wx.hideLoading()
        this.setData({ submitting: false })
        wx.showToast({ title: (err && err.message) || '结算失败', icon: 'none' })
      })
  },

  goBack() {
    wx.navigateBack({
      fail() {
        wx.reLaunch({ url: '/pages/index/index' })
      },
    })
  },

  // 中途退出会丢作答进度，给个二次确认
  onExit() {
    const started = this.data.index > 0 || this.data.answered
    if (!started) {
      this.goBack()
      return
    }
    wx.showModal({
      title: '退出本关？',
      content: '当前作答不会保存，下次要重新开始',
      confirmText: '退出',
      cancelText: '继续答题',
      confirmColor: '#FF4B4B',
      success: (res) => {
        if (res.confirm) {
          this.goBack()
        }
      },
    })
  },

  onRetry() {
    this.loadQuestions(this.data.levelId)
  },

  // 切后台或离开页面时把声音收干净，避免"退出后还有声音在飘"
  onHide() {
    audio.stopAll()
    this.clearComboHide()
  },

  onUnload() {
    audio.stopAll()
    this.clearComboHide()
  },
})
