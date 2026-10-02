const api = require('./utils/request');

// 微信/后端的登录报错翻译成人话，省得每次翻 Network 面板
function explain(msg) {
  const s = String(msg || '');
  if (/AppID 不一致/.test(s)) return s + '。处理：开发者工具「详情 → 基本信息」确认 AppID，或关项目重开（改 project.config.json 不会热生效）';
  if (/40029/.test(s)) return '微信拒绝了 code（40029）：AppID 与 code 不匹配（多半是复制了公众号测试号的 AppID，而不是「小程序」那一栏的），或 code 已被用过';
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
          // 把自己的 AppID 一起上报：与后端 WECHAT_APPID 不一致时，后端会明确回「AppID 不一致：...」
          // （改了 project.config.json 但没关项目重开时，wx.login 仍走旧 AppID，只表现为一个 400）
          let running = '';
          try { running = (wx.getAccountInfoSync().miniProgram || {}).appId || ''; } catch (e) {}
          api.post('/api/auth/login', { code: res.code, appid: running })
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
