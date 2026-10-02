const api = require('../../utils/request');
Page({
  data: { seg: 'rank', board: [], games: [], users: [], isOwner: false,
          form: { aIdx: -1, bIdx: -1, sa: 2, sb: 1, detail: '' } },
  onShow() {
    getApp().ready(() => {
      this.setData({ isOwner: getApp().globalData.user.role === 'owner' });
      this.load();
    });
  },
  load() {
    api.get('/api/league/standings').then(b => { b.forEach((x, i) => { x.rank = i + 1; x.initial = (x.nickname || '?').substring(0, 1); }); this.setData({ board: b }); });
    api.get('/api/league/matches').then(g => this.setData({ games: g }));
    api.get('/api/users').then(u => this.setData({ users: u }));
  },
  setSeg(e) { this.setData({ seg: e.currentTarget.dataset.k }); },
  onPick(e) {
    const k = e.currentTarget.dataset.k;
    this.setData({ ['form.' + k]: +e.detail.value });
  },
  onInput(e) {
    const k = e.currentTarget.dataset.k;
    this.setData({ ['form.' + k]: e.detail.value });
  },
  submit() {
    const f = this.data.form, u = this.data.users;
    if (f.aIdx < 0 || f.bIdx < 0 || f.aIdx === f.bIdx) return wx.showToast({ title: '请选择两名不同选手', icon: 'none' });
    api.post('/api/league/matches', {
      player_a_id: u[f.aIdx].id, player_b_id: u[f.bIdx].id,
      score_a: +f.sa, score_b: +f.sb, detail: f.detail,
      played_at: new Date().toISOString().slice(0, 10)
    }).then(() => {
      wx.showToast({ title: '已结算', icon: 'success' });
      this.setData({ seg: 'rank', 'form.detail': '' });
      this.load();
    }).catch(() => {});
  }
});
