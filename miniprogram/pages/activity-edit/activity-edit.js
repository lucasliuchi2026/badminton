const api = require('../../utils/request');
Page({
  data: {
    id: null,
    f: { name: '', venue: '', date: '2026-10-04', time_start: '19:00', time_end: '21:00',
         type: 'paid', cost_m: 30, cost_f: 20, cap_m: 6, cap_f: 4 }
  },
  onLoad(q) {
    if (q.id) {
      this.setData({ id: +q.id });
      wx.setNavigationBarTitle({ title: '编辑活动' });
      api.get('/api/activities/' + q.id).then(a => {
        this.setData({ f: { name: a.name, venue: a.venue, date: a.date, time_start: a.time_start,
                            time_end: a.time_end, type: a.type, cost_m: a.cost_m, cost_f: a.cost_f,
                            cap_m: a.cap_m, cap_f: a.cap_f } });
      });
    }
  },
  onField(e) { this.setData({ ['f.' + e.currentTarget.dataset.k]: e.detail.value }); },
  onDate(e) { this.setData({ 'f.date': e.detail.value }); },
  onStart(e) { this.setData({ 'f.time_start': e.detail.value }); },
  onEnd(e) { this.setData({ 'f.time_end': e.detail.value }); },
  setType(e) { this.setData({ 'f.type': e.currentTarget.dataset.t }); },
  submit() {
    const f = this.data.f;
    const body = {
      name: f.name, venue: f.venue, date: f.date,
      time_start: f.time_start, time_end: f.time_end, type: f.type,
      cost_m: +f.cost_m || 0, cost_f: +f.cost_f || 0,
      cap_m: +f.cap_m || 0, cap_f: +f.cap_f || 0
    };
    const p = this.data.id ? api.put('/api/activities/' + this.data.id, body) : api.post('/api/activities', body);
    p.then(() => { wx.showToast({ title: '已保存', icon: 'success' }); setTimeout(() => wx.navigateBack(), 600); })
      .catch(() => {});
  }
});
