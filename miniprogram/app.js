const api = require('./utils/request');
const config = require('./config');

// 微信/后端的登录报错翻译成人话，省得每次翻 Network 面板
function explain(msg) {
  const s = String(msg || '');
  if (/40029/.test(s)) return '微信拒绝了 code（40029）：通常是项目 AppID 与后端不一致，请关闭项目重新打开';
  if (/40125|40013/.test(s)) return 'AppID/AppSecret 不匹配（' + (s.match(/\d{5}/) || ['40125'])[0] + '）：测试号重置过密钥，需更新后端环境变量';
  if (/40164/.test(s)) return '后端出口 IP 不在微信白名单（40164）：到测试号后台清空 IP 白名单限制';
  if (/45009/.test(s)) return '登录接口调用超限（45009），稍后再试';
  return s || '请检查后端与 AppID';
}

App({
  globalData: { user: null, group: null },
  onLaunch() {
    this.loginReady = this.login();
  },
  login(force) {
    if (!force && wx.getStorageSync('token')) {
      return api.get('/api/group')
        .then(group => { this.globalData.group = group; return api.get('/api/auth/me'); })
        .then(user => { this.globalData.user = user; this.checkProfile(user); return user; })
        .catch(() => this._wxLogin());
    }
    return this._wxLogin();
  },
  _wxLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: res => {
          // AppID 自检：改了 project.config.json 但没重开项目时，wx.login 仍走旧 AppID，
          // 后端会回 400（微信 40029），这里提前拦下并给出可操作提示
          let running = '';
          try { running = (wx.getAccountInfoSync().miniProgram || {}).appId || ''; } catch (e) {}
          if (config.EXPECTED_APPID && running && running !== config.EXPECTED_APPID) {
            reject(new Error('当前项目 AppID 是 ' + running + '，后端配的是 ' + config.EXPECTED_APPID + '。请关闭项目后重新打开（改 project.config.json 不会热生效）。'));
            return;
          }
          api.post('/api/auth/login', { code: res.code })
            .then(r => {
              wx.setStorageSync('token', r.token);
              this.globalData.user = r.user;
              this.checkProfile(r.user);
              return api.get('/api/group');
            })
            .then(g => { this.globalData.group = g; resolve(this.globalData.user); })
            .catch(reject);
        },
        fail: reject
      });
    });
  },
  // 首次登录（后端默认昵称）引导完善资料；本机保存过则跳过
  checkProfile(user) {
    if (!user) return;
    const onSetup = getCurrentPages().some(p => p.route === 'pages/profile-setup/profile-setup');
    if (onSetup) return;
    if (wx.getStorageSync('profileSaved') === user.id) return;
    if (user.nickname === '球友' || user.nickname === '群主') {
      wx.reLaunch({ url: '/pages/profile-setup/profile-setup' });
    }
  },
  // 页面统一入口：等登录完成再取数
  ready(cb) {
    const p = this.loginReady || this.login();
    this.loginReady = p;
    p.then(cb).catch(e => {
      this.loginReady = null;   // 允许下次 onShow 重试（后端冷启动/清库时不至于卡死）
      if (this._loginErrorShown) return;
      this._loginErrorShown = true;
      const msg = explain(e && e.message);
      console.error('[login] failed:', (e && e.message) || e);
      // 用弹窗而不是 toast：长错误 toast 会被截断，看不清 errcode
      wx.showModal({ title: '登录失败', content: msg, showCancel: false });
    });
  }
});
