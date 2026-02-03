// app.js
App({
  onLaunch() {
    // 小程序启动时执行
    console.log('今乐福小程序启动');
  },

  globalData: {
    // 生产环境：使用 HTTPS 域名 + 子路径
    apiBase: 'https://luoshui.top/happy-lof/api',

    // 开发环境：开发调试时使用
    // apiBase: 'https://luoshui.top/happy-lof/api',

    // 本地开发环境：使用本地 Flask 服务（需在开发者工具中勾选"不校验合法域名"）
    // apiBase: 'http://127.0.0.1:5000/api',
  }
})