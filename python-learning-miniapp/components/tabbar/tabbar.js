const { request } = require('../../utils/request')
const skin = require('../../utils/skin')

Component({
  properties: {
    // 当前所在页：index / rank / review / profile
    current: {
      type: String,
      value: 'index',
    },
  },

  data: {
    tabs: [
      { key: 'index', text: '学习', icon: '📚', path: '/pages/index/index' },
      { key: 'rank', text: '排行', icon: '🏆', path: '/pages/rank/rank' },
      { key: 'review', text: '错题', icon: '📝', path: '/pages/review/review' },
      { key: 'profile', text: '我的', icon: '🐍', path: '/pages/profile/profile' },
    ],
    // 错题数量角标
    badge: 0,
    // 皮肤色板（挂在 tabbar 根节点上，子节点用 var(--sk-*) 取值）
    skinStyle: '',
  },

  attached() {
    // tabbar 是自定义组件，拿不到页面根节点的变量，自己读一份缓存挂上
    this.setData({ skinStyle: skin.styleOf(skin.getSkin()) })
    this.loadBadge()
  },

  methods: {
    // 角标用真实的错题数，拉不到就静默不显示（比如还没登录）
    loadBadge() {
      request({ url: '/profile/stats' })
        .then((stats) => {
          this.setData({ badge: Number(stats.wrong_count || 0) })
        })
        .catch(() => {})
    },

    onTap(e) {
      const key = e.currentTarget.dataset.key
      if (key === this.data.current) {
        return
      }
      const tab = this.data.tabs.filter((t) => t.key === key)[0]
      if (!tab) {
        return
      }
      // 三个主页面平级切换，用 reLaunch 清栈，避免来回切把页面栈堆满
      wx.reLaunch({ url: tab.path })
    },
  },
})
