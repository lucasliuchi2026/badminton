const api = require('../../utils/request');
Page({
  data: { group: null, list: [], totalSigned: 0 },
  onShow() { getApp().ready(() => this.load()); },
  load() {
    api.get('/api/group').then(g => this.setData({ group: g })).catch(() => {});
    api.get('/api/activities?scope=active').then(list => {
      list.forEach(a => {
        a.pctM = Math.min(100, Math.round(a.signed_m / a.cap_m * 100) || 0);
        a.pctF = Math.min(100, Math.round(a.signed_f / a.cap_f * 100) || 0);
        a.statusText = { ongoing: '进行中', upcoming: '未开始' }[a.status];
        a.statusCls = a.status === 'ongoing' ? 'badge-dark' : 'badge-blue';
        a.typeText = a.type === 'paid'
          ? (a.cost_m === a.cost_f ? '⚡积分局·' + a.cost_m + '分/人' : '⚡积分局·♂' + a.cost_m + ' ♀' + a.cost_f + '分/人')
          : '🆓免费局';
        a.typeCls = a.type === 'paid' ? 'badge-dark' : 'badge-green';
      });
      this.setData({ list, totalSigned: list.reduce((s, a) => s + a.signed_total, 0) });
    });
  },
  openDetail(e) {
    wx.navigateTo({ url: '/pages/detail/detail?id=' + e.currentTarget.dataset.id });
  }
});
