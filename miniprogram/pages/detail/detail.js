const api = require('../../utils/request');
Page({
  data: {
    id: null, a: null, me: null, isOwner: false,
    showSignup: false, sgGender: 'M', slots: 1, names: '', pay: 0, unit: 0, canCancelId: null
  },
  onLoad(q) { this.setData({ id: +q.id }); },
  onShow() { getApp().ready(() => { this.setData({ me: getApp().globalData.user }); this.load(); }); },
  load() {
    api.get('/api/activities/' + this.data.id).then(a => {
      const me = this.data.me;
      a.media.forEach(m => { if (m.url && m.url[0] === '/') m.url = require('../../config').BASE_URL + m.url; });
      a.registrations_m.forEach(r => r.initial = (r.member_name || '?').substring(0, 1));
      a.registrations_f.forEach(r => r.initial = (r.member_name || '?').substring(0, 1));
      a.typeText = a.type === 'paid'
        ? (a.cost_m === a.cost_f ? '⚡积分局·' + a.cost_m + '分/人' : '⚡积分局·♂' + a.cost_m + ' ♀' + a.cost_f + '分/人')
        : '🆓免费局';
      a.signupBtn = a.type === 'paid'
        ? '⚡ 预付积分报名（♂' + a.cost_m + ' / ♀' + a.cost_f + '）'
        : '🙋 免费报名 / 代报名';
      this.setData({ a, isOwner: me && me.role === 'owner' });
      this.calcPay();
    });
  },
  toggleSignup() { this.setData({ showSignup: !this.data.showSignup }); },
  setGender(e) { this.setData({ sgGender: e.currentTarget.dataset.g }); this.calcPay(); },
  onSlots(e) { this.setData({ slots: +e.detail.value || 1 }); this.calcPay(); },
  onNames(e) { this.setData({ names: e.detail.value }); },
  calcPay() {
    const a = this.data.a; if (!a) return;
    const unit = a.type === 'paid' ? (this.data.sgGender === 'M' ? a.cost_m : a.cost_f) : 0;
    this.setData({ unit, pay: unit * this.data.slots });
  },
  parseNames() {
    return this.data.names.split(/[,，]/).map(s => s.trim()).filter(Boolean);
  },
  doSignup() {
    const names = this.parseNames();
    if (names.length + 1 !== this.data.slots) {
      return wx.showToast({ title: '代报昵称数应为名额数-1', icon: 'none' });
    }
    api.post('/api/activities/' + this.data.id + '/signup', { gender: this.data.sgGender, slots: this.data.slots, names })
      .then(() => {
        this.setData({ showSignup: false, slots: 1, names: '' });
        wx.showToast({ title: '报名成功' + (this.data.pay ? '，已扣' + this.data.pay + '点卡' : ''), icon: 'success' });
        this.load();
      }).catch(() => {});
  },
  previewImg(e) {
    const urls = (this.data.a.media || []).filter(m => m.kind === 'photo').map(m => m.url);
    wx.previewImage({ urls, current: e.currentTarget.dataset.url });
  },
  cancelReg(e) {
    const rid = e.currentTarget.dataset.rid;
    wx.showModal({ title: '取消报名', content: '确认取消该名额？活动开始前积分原路退还', success: r => {
      if (r.confirm) api.post('/api/activities/registrations/' + rid + '/cancel').then(() => { this.load(); });
    }});
  },
  chooseMedia(e) {
    const kind = e.currentTarget.dataset.kind;
    wx.chooseMedia({ count: 1, mediaType: kind === 'photo' ? ['image'] : ['video'], maxDuration: 30,
      success: res => {
        wx.showLoading({ title: '上传中' });
        api.upload('/api/activities/' + this.data.id + '/media', res.tempFiles[0].tempFilePath, kind)
          .then(() => { wx.hideLoading(); wx.showToast({ title: '已上传', icon: 'success' }); this.load(); })
          .catch(err => { wx.hideLoading(); wx.showToast({ title: '上传失败', icon: 'none' }); });
      }});
  },
  genReview() {
    api.get('/api/activities/' + this.data.id + '/review').then(r => {
      wx.showModal({ title: '活动回顾（' + r.engine + '）', content: r.text, showCancel: false });
    });
  },
  editAct() { wx.navigateTo({ url: '/pages/activity-edit/activity-edit?id=' + this.data.id }); },
  endAct() {
    wx.showModal({ title: '结束活动', content: '结束后不可再报名，确认？', success: r => {
      if (r.confirm) api.post('/api/activities/' + this.data.id + '/status', { status: 'ended' }).then(() => this.load());
    }});
  }
});
