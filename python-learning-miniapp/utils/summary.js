// 答题页 → 结果页的数据中转。
//
// 为什么不用 URL 传参：结算结果里含解析等文本，拼进 URL 既受长度限制、
// 又要反复 encode/decode，容易出转义 bug。小程序里 require 的模块是单例，
// 页面间共享同一份缓存，因此直接用内存缓存最稳。
//
// 仍然保留 URL 传参作为兜底：结果页优先读缓存，读不到再解析 options.data。

let cache = null

function set(payload) {
  cache = payload || null
}

function get() {
  return cache
}

function clear() {
  cache = null
}

module.exports = { set, get, clear }
