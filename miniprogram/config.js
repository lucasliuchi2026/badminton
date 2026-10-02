// 环境配置：本地联调 / Render 部署后切换
module.exports = {
  // 本地跑 uvicorn 时改成 http://127.0.0.1:8000
  BASE_URL: 'https://badminton-api-5k6c.onrender.com',
  // dev 模式（后端未配 WECHAT_APPID）用 code 当身份，方便无微信环境联调；
  // 注意每次 wx.login 的 code 都不同，所以每次编译都会是一个新账号，不能用来验证点卡记账的连续性
  DEV_FIXTURE: false
};
