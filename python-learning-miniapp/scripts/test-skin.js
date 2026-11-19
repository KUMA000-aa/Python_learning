/**
 * Node 端冒烟测试：用假的 wx / Page 跑一遍「皮肤」相关页面逻辑。
 * 只验证数据流（setData 出什么、请求怎么发），不渲染 WXML。
 *
 * 用法：node scripts/test-skin.js
 */
const path = require('path')
const ROOT = path.join(__dirname, '..')

// ---------- 假 wx ----------
const storage = {}
const toasts = []
const navColors = []
let lastRequest = null
let nextResponse = null

global.wx = {
  getStorageSync: (k) => storage[k],
  setStorageSync: (k, v) => { storage[k] = v },
  removeStorageSync: (k) => { delete storage[k] },
  showToast: (o) => toasts.push(o.title),
  setNavigationBarColor: (o) => navColors.push(o),
  stopPullDownRefresh: () => {},
  reLaunch: () => {},
  navigateTo: () => {},
  login: (o) => o.success && o.success({ code: 'mock' }),
  request(o) {
    lastRequest = o
    const res = nextResponse || { statusCode: 200, data: {} }
    setTimeout(() => {
      if (res.statusCode >= 200 && res.statusCode < 300) o.success(res)
      else o.success(res)
    }, 0)
  },
}

// ---------- 假 Page ----------
let captured = null
global.Page = (opts) => { captured = opts }
global.Component = (opts) => { captured = opts }
global.getApp = () => ({ globalData: {} })

function loadPage(rel) {
  delete require.cache[require.resolve(path.join(ROOT, rel))]
  captured = null
  require(path.join(ROOT, rel))
  const page = captured
  page.data = JSON.parse(JSON.stringify(page.data || {}))
  page.setData = function (patch) {
    Object.assign(this.data, patch)
  }
  return page
}

function assert(cond, msg) {
  if (!cond) {
    console.error('  ✗ ' + msg)
    process.exitCode = 1
  } else {
    console.log('  ✓ ' + msg)
  }
}

const skin = require(path.join(ROOT, 'utils/skin'))

// 造一份和服务端一致的皮肤数据
const TOKENS = {
  bg: '#0D0F16', glow: 'rgba(0,229,255,.10)', card: '#161A25', border: '#242A3A',
  text: '#E9EFFA', sub: '#9AA6C0', muted: '#6D7896', line: '#232938', track: '#1E2431',
  primary: '#4C6FFF', primary_dark: '#2F4EDC', primary_soft: '#1A2340', accent: '#00E5FF',
  on_primary: '#FFFFFF', hero_from: '#2A2168', hero_to: '#0B0E18', hero_text: '#EAF6FF',
  hero_border: 'rgba(0,229,255,.35)', nav: '#10141F', nav_text: '#ffffff',
}
function skinItem(over) {
  return Object.assign({
    id: 'classic', name: '原野绿', subtitle: '', desc: '', emoji: '🌿', dark: false,
    tags: [], unlock_type: 'level', min_level: 1, rarity: 'normal', rarity_name: '普通',
    rarity_color: '#8A94A6', rarity_light: '#F2F4F7',
    tokens: Object.assign({}, TOKENS), unlocked: true, equipped: false,
    unlock_hint: '已解锁', levels_left: 0,
  }, over)
}

console.log('\n[1] utils/skin.js')
{
  const s = skin.saveSkin({ id: 'cyber', name: '赛博夜', emoji: '🌃', dark: true, tokens: TOKENS })
  const style = skin.styleOf(s)
  assert(style.includes('--sk-primary:#4C6FFF'), '主色转成 CSS 变量')
  assert(style.includes('--sk-bg:#0D0F16'), '底色转成 CSS 变量')
  assert(style.split(';').length >= 18, '至少 18 个变量（令牌全覆盖）')
  const chrome = skin.apply(s)
  assert(chrome.skinClass === 'sk-dark', '深色皮肤带 sk-dark class')
  assert(navColors.length === 1 && navColors[0].backgroundColor === '#10141F', '导航栏跟随皮肤')
  const cached = skin.getSkin()
  assert(cached.id === 'cyber' && cached.tokens.primary === '#4C6FFF', '缓存可读回')
  // 兜底：没缓存时也能拿到默认色板
  delete storage.skin
  assert(skin.getSkin().id === 'classic', '无缓存回落到默认皮肤')
}

console.log('\n[2] pages/skins 皮肤图鉴')
{
  const page = loadPage('pages/skins/skins.js')
  page.onLoad()
  assert(!!page.data.skinStyle, 'onLoad 先套缓存色板')

  page.applyList([
    skinItem({ id: 'classic', name: '原野绿', equipped: true }),
    skinItem({ id: 'ocean', name: '深海蓝', min_level: 2 }),
    skinItem({ id: 'sakura', name: '樱花粉', min_level: 4, unlocked: false, unlocked2: 0, unlock_hint: 'Lv4 解锁 · 还差 1 级' }),
  ])
  assert(page.data.total === 3 && page.data.unlocked === 2, '统计已解锁数量')
  assert(page.data.skinId === 'classic', '当前皮肤同步到页面')

  // 点未解锁的：弹说明，不发请求
  lastRequest = null
  page.onPick({ currentTarget: { dataset: { id: 'sakura' } } })
  assert(page.data.showDetail === true, '点未解锁弹说明层')
  assert(lastRequest === null, '未解锁不发请求')
  page.closeDetail()

  // 点已解锁的：POST /profile/skin
  nextResponse = {
    statusCode: 200,
    data: [
      skinItem({ id: 'classic', name: '原野绿' }),
      skinItem({ id: 'ocean', name: '深海蓝', min_level: 2, equipped: true }),
      skinItem({ id: 'sakura', name: '樱花粉', min_level: 4, unlocked: false, unlock_hint: 'Lv4 解锁 · 还差 1 级' }),
    ],
  }
  page.onPick({ currentTarget: { dataset: { id: 'ocean' } } })
  setTimeout(() => {
    assert(lastRequest.method === 'POST' && lastRequest.url.endsWith('/profile/skin'), '佩戴走 POST /profile/skin')
    assert(lastRequest.data.skin_id === 'ocean', '请求体带 skin_id')
    assert(page.data.skinId === 'ocean', '佩戴后页面皮肤更新')
    assert(storage.skin.id === 'ocean', '佩戴后写入缓存')
    assert(toasts.some((t) => t.includes('深海蓝')), '佩戴成功有提示')
    runProfile()
  }, 10)
}

console.log('\n[3] pages/profile 我的页面')
function runProfile() {
  nextResponse = {
    statusCode: 200,
    data: {
      user_id: 1, nickname: 'Python 学习者',
      total_levels: 2, completed_levels: 2, progress_percent: 100, avg_score: 100,
      total_stars: 6, max_stars: 6, total_questions: 6, answered_count: 6,
      correct_count: 6, wrong_count: 0, accuracy: 100, total_answer_times: 8,
      level_attempts: 6, study_days: 2, exp: 370, level: 3, level_title: '黑铁 Ⅲ',
      exp_in_level: 250, exp_need: 368, exp_percent: 67.9, exp_to_next: 118,
      next_level_title: '黑铁 Ⅱ', max_level: 30, is_max_level: false,
      tier: 'iron', tier_name: '黑铁', tier_color: '#6E7B8B', tier_light: '#EFF2F5',
      tier_desc: '', tier_index: 3, tier_roman: 'Ⅲ', tier_levels_left: 2,
      next_tier_name: '青铜', avatar_frame: 'f2', avatar_frame_name: '银纹环',
      avatar_frame_accent: '#9AA7B8', avatar_frame_emoji: '🥈', frames: [],
      skin: 'cyber', skin_name: '赛博夜', skin_emoji: '🌃', skin_dark: true, skin_tokens: TOKENS,
      skins: [skinItem({ id: 'cyber', name: '赛博夜', dark: true, equipped: true }), skinItem()],
    },
  }
  const page = loadPage('pages/profile/profile.js')
  page.applyStats(nextResponse.data)
  assert(page.data.skinId === 'cyber' && page.data.skinDark === true, '我的页套深色皮肤')
  assert(page.data.skinClass === 'sk-dark', '我的页带 sk-dark')
  assert(page.data.skins.length === 2 && page.data.unlockedSkins === 2, '我的页拿到皮肤列表')
  assert(page.data.level === 3 && page.data.frames.length === 0, '等级/头像框数据不受影响')
  page.onGoSkins && page.onGoSkins()
  console.log('\n完成' + (process.exitCode ? '（有失败项）' : '（全部通过）'))
}
