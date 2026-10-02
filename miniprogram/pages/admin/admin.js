const api = require('../../utils/request');
Page({
  data: {
    users: [], acts: [],
    showCardForm: false, cardUserIdx: 0, cardDelta: 10, cardMemo: '',
    showCfg: false, cfg: {}
  },
  onShow() {
    getApp().ready(() => {
      if (getApp().globalData.user.role !== 'owner') {
        wx.showToast({ title: '仅群主可访问', icon: 'none' });
        setTimeout(() => wx.navigateBack(), 800);
        return;
      }
      this.load();
    });
  },
  load() {
    api.get('/api/cards/users').then(users => {
      users.forEach(u => u.initial = (u.nickname || '?').substring(0, 1));
      this.setData({ users });
    });
    api.get('/api/activities?scope=active').then(acts => this.setData({ acts }));
    api.get('/api/group').then(cfg => this.setData({ cfg }));
  },
  createAct() { wx.navigateTo({ url: '/pages/activity-edit/activity-edit' }); },
  editAct(e) { wx.navigateTo({ url: '/pages/activity-edit/activity-edit?id=' + e.currentTarget.dataset.id }); },
  openCardForm(e) {
    this.setData({ showCardForm: true, cardUserIdx: +e.currentTarget.dataset.idx });
  },
  onCardUser(e) { this.setData({ cardUserIdx: +e.detail.value }); },
  onCardDelta(e) { this.setData({ cardDelta: e.detail.value }); },
  onCardMemo(e) { this.setData({ cardMemo: e.detail.value }); },
  closeCardForm() { this.setData({ showCardForm: false }); },
  plusCard() { this.submitCard(Math.abs(+this.data.cardDelta || 0)); },
  minusCard() { this.submitCard(-Math.abs(+this.data.cardDelta || 0)); },
  submitCard(delta) {
    if (!delta) return wx.showToast({ title: '数额无效', icon: 'none' });
    const u = this.data.users[this.data.cardUserIdx];
    api.post('/api/cards/adjust', { user_id: u.id, delta, memo: this.data.cardMemo || '群主调整' })
      .then(() => {
        wx.showToast({ title: '已记流水', icon: 'success' });
        this.setData({ showCardForm: false });
        this.load();
      }).catch(() => {});
  },
  toggleCfg() { this.setData({ showCfg: !this.data.showCfg }); },
  onCfg(e) { const k = e.currentTarget.dataset.k; this.setData({ ['cfg.' + k]: e.detail.value }); },
  saveCfg() {
    api.put('/api/group', { club_name: this.data.cfg.club_name, slogan: this.data.cfg.slogan, intro: this.data.cfg.intro })
      .then(() => wx.showToast({ title: '群介绍已更新', icon: 'success' }));
  },
  viewLogs(e) {
    api.get('/api/cards/logs?user_id=' + e.currentTarget.dataset.uid).then(r => {
      const text = r.logs.map(l => l.created_at.slice(0, 10) + ' ' + (l.delta > 0 ? '+' : '') + l.delta + ' ' + l.memo).join('\n') || '暂无流水';
      wx.showModal({ title: '成员流水（余额 ' + this.data.users[e.currentTarget.dataset.idx].card_balance + '）', content: text, showCancel: false });
    });
  }
});
