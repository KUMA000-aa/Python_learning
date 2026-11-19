// ============================================================
// 后端地址
// ============================================================
// 开发者工具模拟器里跑：保持 127.0.0.1 即可
// 手机真机调试（手机和电脑连同一个 WiFi）：改成电脑的局域网 IP（cmd 跑 ipconfig 查）
const BASE_URL = 'http://127.0.0.1:8001'

// ============================================================
// 登录方式开关
// ============================================================
// true  -> 不调 wx.login，用固定的 code 登录。后端未配 WX_APPID 时会进入 mock 模式，
//          固定 code 能保证每次都是同一个用户（否则每次都新建用户，进度会丢）
// false -> 调 wx.login() 拿真实 code，后端配好 WX_APPID/WX_SECRET 后必须改成 false
//
// ⚠️ 默认为 true：后端 .env 里 WX_APPID 默认是空的（mock 模式），
//    此时 wx.login() 每次返回的 code 都不一样，后端会把每个 code 当成新的 openid，
//    导致「每次打开都是新用户、进度全丢」。配好真实 AppID 后再改成 false。
//
// 兜底：即使设为 false，只要 wx.login() 调用失败（模拟器 / 测试号 / 无 AppID），
//      utils/auth.js 也会自动降级到 MOCK_CODE，不会卡在登录失败。
const USE_MOCK_LOGIN = true

// 固定登录标识，建议改成你自己的学号等唯一字符串
const MOCK_CODE = 'dev_demo_user_001'

module.exports = {
  BASE_URL,
  USE_MOCK_LOGIN,
  MOCK_CODE,
}
