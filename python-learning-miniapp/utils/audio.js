// 音效管理：统一收口 InnerAudioContext 的创建、复用与静音开关。
//
// 几个关键取舍：
// 1) 音频文件放在包内 assets/audio/，不走网络 —— 答题是高频操作，
//    网络音效会有一两百毫秒延迟，连击听起来就会"慢半拍"。
// 2) 每个文件复用一个 InnerAudioContext（而不是每次 new），
//    否则连续作答会在部分机型上触发"音频实例过多"的报错。
// 3) 重播前先 stop() 再 play()，保证同一音效连续触发时能立刻重头播。
// 4) obeyMuteSwitch 保持默认 true —— 尊重系统静音键，
//    学生在自习室/课堂上不会被强制外放。
// 5) 所有调用都 try/catch 并静默失败：音效永远不能影响答题主流程。

const STORAGE_KEY = 'sound_enabled'
const DIR = '/assets/audio/'

const SRC = {
  correct: [
    DIR + 'correct_1.wav',
    DIR + 'correct_2.wav',
    DIR + 'correct_3.wav',
    DIR + 'correct_4.wav',
    DIR + 'correct_5.wav',
    DIR + 'correct_6.wav',
  ],
  wrong: DIR + 'wrong.wav',
  milestone: DIR + 'milestone.wav',
}

const pool = {}
let enabled = null
let milestoneTimer = null

function readPref() {
  try {
    const v = wx.getStorageSync(STORAGE_KEY)
    // 没存过（'' / undefined）默认开启
    return v === '' || v === undefined || v === null ? true : !!v
  } catch (e) {
    return true
  }
}

function isEnabled() {
  if (enabled === null) {
    enabled = readPref()
  }
  return enabled
}

function setEnabled(on) {
  enabled = !!on
  try {
    wx.setStorageSync(STORAGE_KEY, enabled)
  } catch (e) {
    // 存储失败不影响本次会话内的开关状态
  }
  if (!enabled) {
    stopAll()
  }
  return enabled
}

function toggle() {
  return setEnabled(!isEnabled())
}

// 懒创建 + 复用
function context(src) {
  let ctx = pool[src]
  if (ctx) {
    return ctx
  }
  if (typeof wx.createInnerAudioContext !== 'function') {
    return null
  }
  ctx = wx.createInnerAudioContext()
  ctx.src = src
  ctx.onError(function () {
    // 1) 包内路径兜底：个别机型对「以 / 开头」的包内路径解析失败，
    //    这里退回相对路径重试一次（只试一次，避免死循环）。
    // 2) 其它错误（格式不支持 / 音频通道被占用）直接放弃，不影响答题。
    if (!ctx.__retried && String(ctx.src).charAt(0) === '/') {
      ctx.__retried = true
      ctx.src = String(ctx.src).slice(1)
      try {
        ctx.play()
      } catch (e) {
        // 忽略
      }
    }
  })
  pool[src] = ctx
  return ctx
}

// 预热：提前建好前两个连击音与错误音，减少首答的播放延迟
function warmup() {
  if (!isEnabled() || typeof wx.createInnerAudioContext !== 'function') {
    return
  }
  context(SRC.correct[0])
  context(SRC.correct[1])
  context(SRC.wrong)
}

function play(src, volume) {
  if (!isEnabled() || !src) {
    return
  }
  try {
    const ctx = context(src)
    if (!ctx) {
      return
    }
    ctx.volume = typeof volume === 'number' ? volume : 0.9
    ctx.stop()
    ctx.play()
  } catch (e) {
    // 忽略
  }
}

// 连击音高随连击数上行：1→C5 … 6→C6，之后统一用最高音
function comboIndex(combo) {
  const n = Number(combo) || 1
  if (n < 1) return 1
  if (n > SRC.correct.length) return SRC.correct.length
  return n
}

function playCorrect(combo) {
  const idx = comboIndex(combo)
  // 连击越高音量略增，配合音高一起制造"往上走"的感觉
  const volume = Math.min(0.98, 0.82 + idx * 0.025)
  play(SRC.correct[idx - 1], volume)
}

function playWrong() {
  play(SRC.wrong, 0.85)
}

// 里程碑铃声：错开 70ms 叠在判对音之后，听感是"叮——哒啷"
function playMilestone() {
  if (!isEnabled()) {
    return
  }
  clearMilestone()
  milestoneTimer = setTimeout(function () {
    milestoneTimer = null
    play(SRC.milestone, 0.62)
  }, 70)
}

function clearMilestone() {
  if (milestoneTimer) {
    clearTimeout(milestoneTimer)
    milestoneTimer = null
  }
}

function stopAll() {
  clearMilestone()
  Object.keys(pool).forEach(function (k) {
    try {
      pool[k].stop()
    } catch (e) {
      // 忽略
    }
  })
}

// 页面隐藏/卸载时调用，避免切后台后还有声音在飘
function release() {
  stopAll()
  Object.keys(pool).forEach(function (k) {
    try {
      pool[k].destroy()
    } catch (e) {
      // 忽略
    }
    delete pool[k]
  })
}

module.exports = {
  isEnabled,
  setEnabled,
  toggle,
  warmup,
  playCorrect,
  playWrong,
  playMilestone,
  stopAll,
  release,
}
