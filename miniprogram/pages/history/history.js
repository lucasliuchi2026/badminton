const api = require('../../utils/request');
Page({
  data: { kw: '', list: [] },
  onShow() { getApp().ready(() => this.load()); },
  load() {
    api.get('/api/activities?scope=history&keyword=' + encodeURIComponent(this.data.kw)).then(list => {
      list.forEach(a => {
        a.typeText = a.type === 'paid' ? '⚡积分局' : '🆓免费局';
        a.typeCls = a.type === 'paid' ? 'badge-dark' : 'badge-green';
      });
      this.setData({ list });
    });
  },
  onSearch(e) { this.setData({ kw: e.detail.value }); this.load(); },
  openDetail(e) { wx.navigateTo({ url: '/pages/detail/detail?id=' + e.currentTarget.dataset.id }); }
});
