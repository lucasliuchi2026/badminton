// 环境配置：本地联调 / Render 部署后切换
module.exports = {
  // 本地跑 uvicorn 时改成 http://127.0.0.1:8000
  BASE_URL: 'https://badminton-api-5k6c.onrender.com',
  // dev 模式（后端未配 WECHAT_APPID）下 wx.login 的 code 会被当作稳定身份后缀；
  // 为了真机测试时同一人多设备身份一致，正式接测试号后此配置自动失效
  DEV_FIXTURE: false,
  // 后端 WECHAT_APPID 的值（AppID 是公开信息，不是密钥）。
  // 用途：启动时和当前项目的 AppID 比对，不一致直接提示「关项目重开」，免得只看到一个 400。
  // 换正式号 / 重置测试号时，这里和后端环境变量要一起改。
  EXPECTED_APPID: 'wx1a05a4e7883eea18'
};
