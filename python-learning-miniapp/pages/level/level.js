const { request } = require('../../utils/request')
const { ensureLogin } = require('../../utils/auth')

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

Page({
  data: {
    loading: true,
    error: '',
    levelId: null,
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
  },

  onLoad(options) {
    const levelId = Number(options.id)
    this.startedAt = Date.now()
    this.setData({ levelId })
    this.loadQuestions(levelId)
  },

  loadQuestions(levelId) {
    ensureLogin()
      .then(() => request({ url: '/levels/' + levelId + '/questions' }))
      .then((questions) => {
        if (!questions || !questions.length) {
          throw new Error('本关还没有题目')
        }
        this.setData({ loading: false, questions, total: questions.length })
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
    this.setData({
      index,
      stem: question.stem,
      questionType: question.question_type === 'single_choice' ? '单选题' : '题目',
      currentOptions: options,
      percent: Math.round((index / questions.length) * 100),
      isLast: index === questions.length - 1,
      selectedLetter: '',
      answered: false,
      isCorrect: false,
      correctAnswer: '',
      explanation: '',
    })
  },

  onSelect(e) {
    if (this.data.answered || this.data.submitting) {
      return
    }

    const letter = e.currentTarget.dataset.letter
    const question = this.data.questions[this.data.index]
    const duration = Date.now() - this.startedAt

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
        this.setData({
          submitting: false,
          answered: true,
          isCorrect: res.is_correct,
          correctAnswer: res.correct_answer || '',
          explanation: res.explanation || '',
        })
      })
      .catch((err) => {
        this.setData({ submitting: false, selectedLetter: '' })
        wx.showToast({ title: err.message, icon: 'none' })
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
        const payload = encodeURIComponent(JSON.stringify(summary))
        wx.redirectTo({
          url: '/pages/result/result?data=' + payload,
        })
      })
      .catch((err) => {
        wx.hideLoading()
        this.setData({ submitting: false })
        wx.showToast({ title: err.message, icon: 'none' })
      })
  },

  onExit() {
    wx.navigateBack({
      fail() {
        wx.reLaunch({ url: '/pages/index/index' })
      },
    })
  },

  onRetry() {
    this.setData({ loading: true, error: '' })
    this.loadQuestions(this.data.levelId)
  },
})
