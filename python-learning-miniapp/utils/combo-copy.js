// ===== 连击专属文案库 =====
// 设计思路：
// 1) 档位只决定配色和"口气等级"，同档内准备多条文案轮换，避免每局都看到同一句；
// 2) 特定连击数（3/5/8/10/15/20）有里程碑专属句子，给玩家"打到点了"的确定感；
// 3) 断连也有专属安慰文案，降挫败感；结算页再给一句总结评语，形成完整叙事。
// 文案尽量往 Python 梗上靠，让提示本身也带一点学科气质。

// ---------- 内部工具 ----------
// 用"洗牌牌堆"而不是纯随机：每轮把所有文案打乱后依次抽，
// 抽完再洗一轮，既不连续重复，也不会出现某句一直被抽中的情况。
const bags = {}
const lastPicked = {}

function shuffle(arr) {
  const a = arr.slice()
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    const t = a[i]
    a[i] = a[j]
    a[j] = t
  }
  return a
}

function pick(list, key) {
  if (!list || !list.length) {
    return ''
  }
  if (list.length === 1) {
    return list[0]
  }
  let bag = bags[key]
  if (!bag || !bag.length) {
    bag = shuffle(list)
    // 新一轮的第一条避开上一轮的结尾，避免跨轮撞句
    if (bag[0] === lastPicked[key]) {
      const t = bag[0]
      bag[0] = bag[1]
      bag[1] = t
    }
    bags[key] = bag
  }
  const item = bag.shift()
  lastPicked[key] = item
  return item
}

function fill(template, n) {
  return String(template).replace(/\{n\}/g, String(n))
}

// ---------- 档位定义 ----------
// min 表示"达到该档所需的最小连击数"，从高到低匹配
const TIERS = [
  {
    tier: 4,
    min: 10,
    name: '无人能挡',
    emoji: '👑',
    tags: ['无人能挡', '出题人已退群', '这关我收了', '手感封神', '建议直接发证书', 'bug 都绕着你走'],
    tips: [
      '十连之后，题目开始怀疑自己',
      '这已经不是运气，是肌肉记忆',
      '你答得比解释器还快',
      '再打下去，题库要不够用了',
    ],
  },
  {
    tier: 3,
    min: 6,
    name: '手感火热',
    emoji: '🔥',
    tags: ['手感火热', '根本停不下来', '全对预警', '这题我熟', '缩进都没错'],
    tips: [
      '节奏稳得像 while True',
      '思路一遍过，没有 debug',
      '连着答对，错题都没机会出现',
      '脑子比编译器还快',
    ],
  },
  {
    tier: 2,
    min: 4,
    name: '状态很好',
    emoji: '⚡',
    tags: ['状态很好', '越答越顺', '进入状态', '开始起飞', '稳得一批'],
    tips: [
      '错题本今天可以休息了',
      '保持这个节奏，别停',
      '连击还能再往上冲',
      '手感正在热机',
    ],
  },
  {
    tier: 1,
    min: 2,
    name: '连击开始',
    emoji: '✨',
    tags: ['连击开始', '连上了', '有点东西', '稳住能赢', '开张了'],
    tips: [
      '先把两条连起来，节奏就来了',
      '再接一题，手感会更顺',
      '连击计数已启动',
      '不错，继续加码',
    ],
  },
]

// ---------- 里程碑专属文案 ----------
// 只在"恰好打到这个数"时出现，给一个明确的阶段性高光
const MILESTONES = {
  3: { tag: '三连达成', text: '手感正在上线' },
  5: { tag: '五连达成', text: '这种状态，考试也就这样了' },
  8: { tag: '八连达成', text: '八题没错一个，稳得可怕' },
  10: { tag: '十连达成', text: '出题人已退群，建议截图' },
  15: { tag: '十五连', text: '这已经不是运气了' },
  20: { tag: '二十连', text: '建议直接来当助教' },
}

// ---------- 断连文案 ----------
const BREAK_COPIES = [
  '×{n} 断在这一题，思路还在，接着来',
  '连击停在 ×{n}，喘口气再冲一次',
  '×{n} 没了，但手感不会跑',
  '差一点就 ×{n}+1，下一题补回来',
]

// ---------- 结算页评语 ----------
function bestComboCopy(maxCombo) {
  const n = Number(maxCombo) || 0
  if (n >= 10) {
    return { tier: 4, tag: '连击封神', tip: '这局连击拉满，值得截图留念' }
  }
  if (n >= 6) {
    return { tier: 3, tag: '手感火热', tip: '离满星只差一点稳定度' }
  }
  if (n >= 4) {
    return { tier: 2, tag: '状态不错', tip: '再稳一点就能上十连' }
  }
  if (n >= 2) {
    return { tier: 1, tag: '连击开张', tip: '下次试试冲五连' }
  }
  return { tier: 0, tag: '', tip: '' }
}

// ---------- 对外接口 ----------

// 取档位：从高到低找第一个满足 min 的
function tierOf(combo) {
  const n = Number(combo) || 0
  for (let i = 0; i < TIERS.length; i++) {
    if (n >= TIERS[i].min) {
      return TIERS[i]
    }
  }
  return null
}

// 距下一档还差几连；已到顶则返回 0
// TIERS 是「高 → 低」排序，所以"下一档"是数组里更靠前的那一个
function gapToNext(combo) {
  const n = Number(combo) || 0
  const tier = tierOf(n)
  if (!tier) {
    // 还没进第一档（n = 0 或 1）
    const first = TIERS[TIERS.length - 1]
    return { toNext: first.min - n, nextName: first.name }
  }
  const idx = TIERS.indexOf(tier)
  if (idx <= 0) {
    // 已经在最高档，没有"下一档"了
    return { toNext: 0, nextName: '' }
  }
  const next = TIERS[idx - 1]
  return { toNext: next.min - n, nextName: next.name }
}

// 主入口：连击数 -> 一整套展示文案
function comboCopy(combo) {
  const n = Number(combo) || 0
  const tier = tierOf(n) || TIERS[TIERS.length - 1]
  const milestone = MILESTONES[n] || null

  let tag
  let tip
  if (milestone) {
    tag = milestone.tag
    tip = milestone.text
  } else {
    tag = pick(tier.tags, 'tag-' + tier.tier)
    tip = pick(tier.tips, 'tip-' + tier.tier)
  }

  const gap = gapToNext(n)

  return {
    tier: tier.tier,
    tierName: tier.name,
    emoji: tier.emoji,
    tag,
    tip,
    isMilestone: !!milestone,
    toNext: gap.toNext,
    nextName: gap.nextName,
  }
}

// 断连文案：broken 为被中断的连击数
function breakCopy(broken) {
  const n = Number(broken) || 0
  if (n < 2) {
    return ''
  }
  return fill(pick(BREAK_COPIES, 'break'), n)
}

module.exports = {
  comboCopy,
  breakCopy,
  bestComboCopy,
  tierOf,
  gapToNext,
  MILESTONES,
  // 便于自测/调试
  _TIERS: TIERS,
}
