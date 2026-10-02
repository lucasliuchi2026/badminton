const api = require('./utils/request');

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
      if (this._loginToastShown) return;
      this._loginToastShown = true;
      // 把后端原话摊出来，方便区分「AppID 不匹配 / 网络不通 / 后端挂了」
      wx.showToast({ title: '登录失败：' + ((e && e.message) || '请检查后端与 AppID'), icon: 'none', duration: 3000 });
    });
  }
});
