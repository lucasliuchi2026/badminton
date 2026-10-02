const api = require('../../utils/request');
Page({
  data: { nickname: '', gender: 'M', avatarTemp: '', avatarPreview: '', saving: false },
  onLoad() {
    const u = getApp().globalData.user;
    if (u && u.nickname !== '球友' && u.nickname !== '群主') this.setData({ nickname: u.nickname, gender: u.gender });
  },
  onNick(e) { this.setData({ nickname: e.detail.value }); },
  onGender(e) { this.setData({ gender: e.currentTarget.dataset.g }); },
  chooseAvatar(e) {
    const temp = e.detail.avatarUrl;
    this.setData({ avatarTemp: temp, avatarPreview: temp });
  },
  save() {
    const nick = (this.data.nickname || '').trim();
    if (!nick) return wx.showToast({ title: '请填写昵称', icon: 'none' });
    this.setData({ saving: true });
    api.post('/api/auth/profile', { nickname: nick, gender: this.data.gender })
      .then(u => this.data.avatarTemp ? api.upload('/api/auth/avatar', this.data.avatarTemp, 'avatar') : u)
      .then(u => {
        getApp().globalData.user = u;
        wx.setStorageSync('profileSaved', u.id);
        wx.reLaunch({ url: '/pages/square/square' });
      })
      .catch(() => this.setData({ saving: false }));
  }
});
