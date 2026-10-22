// 后端地址
// 开发者工具模拟器里跑：保持 127.0.0.1 即可
// 手机真机调试（手机和电脑连同一个 WiFi）：改成电脑的局域网 IP（cmd 跑 ipconfig 查）
const BASE_URL = 'http://127.0.0.1:8001'

// 登录方式开关
// true  -> 不调 wx.login，用固定的 code 登录。后端未配 WX_APPID 时会进入 mock 模式，
//          固定 code 能保证每次都是同一个用户（否则每次都新建用户，进度会丢）
// false -> 调 wx.login() 拿真实 code，后端配好 WX_APPID/WX_SECRET 后必须改成 false
const USE_MOCK_LOGIN = false
const MOCK_CODE = 'dev_demo_user_001'

module.exports = {
  BASE_URL,
  USE_MOCK_LOGIN,
  MOCK_CODE,
}
