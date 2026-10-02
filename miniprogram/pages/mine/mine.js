const api = require('../../utils/request');
Page({
  data: { me: null, logs: [], mine: [], editing: false, nickname: '' },
  onShow() {
    getApp().ready(() => {
      this.setData({ me: getApp().globalData.user });
      this.load();
    });
  },
  load() {
    api.get('/api/cards/mine').then(r => this.setData({ logs: r.logs }));
    api.get('/api/activities/mine/registrations').then(mine => this.setData({ mine }));
  },
  onNick(e) { this.setData({ nickname: e.detail.value }); },
  saveNick() {
    api.post('/api/auth/profile', { nickname: this.data.nickname }).then(u => {
      getApp().globalData.user = u;
      this.setData({ me: u, editing: false });
      wx.showToast({ title: '已保存', icon: 'success' });
    });
  },
  toggleEdit() { this.setData({ editing: !this.data.editing, nickname: this.data.me.nickname }); },
  goAdmin() { wx.navigateTo({ url: '/pages/admin/admin' }); }
});
