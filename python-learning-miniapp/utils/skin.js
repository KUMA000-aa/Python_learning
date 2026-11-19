/**
 * 皮肤工具
 *
 * 后端只下发「色板令牌」（tokens），这里把令牌转成一串 CSS 变量，
 * 页面根节点挂上 style 之后，WXSS 里 var(--sk-primary) 这些就能取到值。
 * 好处：加皮肤完全不用改页面，改后端 skins.py 即可。
 *
 * 变量命名统一加 --sk- 前缀，避免和页面自己的变量撞车。
 */

const STORAGE_KEY = 'skin'

// 首屏兜底：还没拉到皮肤（或接口挂了）时用默认绿，保证页面永远有颜色可用
const FALLBACK = {
  id: 'classic',
  name: '原野绿',
  emoji: '🌿',
  dark: false,
  rarity: 'normal',
  tokens: {
    bg: '#F7F7F9',
    glow: 'rgba(88, 204, 2, 0.10)',
    card: '#FFFFFF',
    border: '#EFF1F3',
    text: '#3C3C3C',
    sub: '#6E6E6E',
    muted: '#A8A8A8',
    line: '#F0F0F0',
    track: '#EFEFEF',
    primary: '#58CC02',
    primary_dark: '#46A302',
    primary_soft: '#EFF9E6',
    accent: '#FFC800',
    on_primary: '#FFFFFF',
    hero_from: '#58CC02',
    hero_to: '#37A000',
    hero_text: '#FFFFFF',
    hero_border: 'rgba(255, 255, 255, 0.22)',
    nav: '#4BB802',
    nav_text: '#ffffff',
  },
}

// 令牌字段 -> CSS 变量名（顺序固定，方便调试时对照）
const VAR_MAP = {
  bg: '--sk-bg',
  glow: '--sk-glow',
  card: '--sk-card',
  border: '--sk-border',
  text: '--sk-text',
  sub: '--sk-sub',
  muted: '--sk-muted',
  line: '--sk-line',
  track: '--sk-track',
  primary: '--sk-primary',
  primary_dark: '--sk-primary-dark',
  primary_soft: '--sk-primary-soft',
  accent: '--sk-accent',
  on_primary: '--sk-on-primary',
  hero_from: '--sk-hero-from',
  hero_to: '--sk-hero-to',
  hero_text: '--sk-hero-text',
  hero_border: '--sk-hero-border',
  nav: '--sk-nav',
}

function normalize(skin) {
  if (!skin || !skin.tokens) {
    return FALLBACK
  }
  return {
    id: skin.id || FALLBACK.id,
    name: skin.name || FALLBACK.name,
    emoji: skin.emoji || FALLBACK.emoji,
    dark: !!skin.dark,
    rarity: skin.rarity || 'normal',
    tokens: Object.assign({}, FALLBACK.tokens, skin.tokens),
  }
}

/** 读本地缓存的皮肤（同步，页面 onShow 里直接用） */
function getSkin() {
  try {
    return normalize(wx.getStorageSync(STORAGE_KEY))
  } catch (e) {
    return FALLBACK
  }
}

/** 存皮肤，下次进任何页面都能立刻套上，不会先闪一下默认绿 */
function saveSkin(skin) {
  const normalized = normalize(skin)
  try {
    wx.setStorageSync(STORAGE_KEY, normalized)
  } catch (e) {
    /* 存储满了也不影响当前页面显示 */
  }
  return normalized
}

/** 从 /profile/stats 的回包里取皮肤（顺便写缓存） */
function fromStats(stats) {
  if (!stats || !stats.skin_tokens) {
    return null
  }
  return saveSkin({
    id: stats.skin,
    name: stats.skin_name,
    emoji: stats.skin_emoji,
    dark: stats.skin_dark,
    tokens: stats.skin_tokens,
  })
}

/** 令牌 -> "内联 style" 字符串 */
function styleOf(skin) {
  const tokens = (skin && skin.tokens) || FALLBACK.tokens
  return Object.keys(VAR_MAP)
    .filter((key) => !!tokens[key])
    .map((key) => VAR_MAP[key] + ':' + tokens[key])
    .join(';')
}

/** 页面要 setData 的那一坨：样式、深色类、皮肤名 */
function chrome(skin) {
  const current = normalize(skin)
  return {
    skinId: current.id,
    skinName: current.name,
    skinEmoji: current.emoji,
    skinDark: current.dark,
    skinStyle: styleOf(current),
    skinClass: current.dark ? 'sk-dark' : '',
  }
}

/**
 * 导航栏跟着皮肤走。
 * 微信只接受 frontColor 为 #ffffff / #000000，所以后端令牌里的 nav_text 也只有这两个值。
 */
function applyNavBar(skin) {
  const tokens = normalize(skin).tokens
  const front = tokens.nav_text === '#000000' ? '#000000' : '#ffffff'
  try {
    wx.setNavigationBarColor({
      frontColor: front,
      backgroundColor: tokens.nav,
      fail() {},
    })
  } catch (e) {
    /* 某些基础库版本不支持，忽略即可，页面配色不受影响 */
  }

  // 下拉回弹露出的那一截也染成皮肤底色，深色皮肤下不会露出白边
  try {
    wx.setBackgroundColor({
      backgroundColor: tokens.bg,
      backgroundColorTop: tokens.bg,
      backgroundColorBottom: tokens.bg,
      fail() {},
    })
  } catch (e) {
    /* 同上，低版本忽略 */
  }
}

/** 一次搞定：套色 + 导航栏，返回可直接 setData 的对象 */
function apply(skin) {
  const current = normalize(skin)
  applyNavBar(current)
  return chrome(current)
}

module.exports = {
  FALLBACK,
  getSkin,
  saveSkin,
  fromStats,
  styleOf,
  chrome,
  applyNavBar,
  apply,
}
