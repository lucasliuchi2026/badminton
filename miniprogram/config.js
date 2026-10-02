// 环境配置：本地联调 / Render 部署后切换
module.exports = {
  // 本地跑 uvicorn 时用这个；部署后改成 https://badminton-api.onrender.com
  BASE_URL: 'http://127.0.0.1:8000',
  // dev 模式（后端未配 WECHAT_APPID）下 wx.login 的 code 会被当作稳定身份后缀；
  // 为了真机测试时同一人多设备身份一致，正式接测试号后此配置自动失效
  DEV_FIXTURE: false
};
