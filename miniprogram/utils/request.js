const config = require('../config');

function request(path, method, data, silent, retried) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: config.BASE_URL + path,
      method: method || 'GET',
      data: data || {},
      header: { Authorization: 'Bearer ' + (wx.getStorageSync('token') || '') },
      success(res) {
        if (res.statusCode === 401) {
          if (retried) {
            reject(new Error('登录态无效(' + path + ')'));
            return;
          }
          // token 失效（后端重部署清库后旧 token 必然 401）：丢掉旧 token，静默重新登录后重试一次
          wx.removeStorageSync('token');
          getApp().login(true).then(() => request(path, method, data, silent, true)).then(resolve).catch(reject);
          return;
        }
        if (res.statusCode >= 200 && res.statusCode < 300) return resolve(res.data);
        const msg = (res.data && res.data.detail) || '请求失败(' + res.statusCode + ')';
        if (!silent) wx.showToast({ title: msg, icon: 'none' });
        reject(new Error(msg));
      },
      fail(err) {
        if (!silent) wx.showToast({ title: '网络错误，检查后端是否启动', icon: 'none' });
        reject(err);
      }
    });
  });
}

module.exports = {
  get: (p, d) => request(p, 'GET', d),
  post: (p, d) => request(p, 'POST', d),
  put: (p, d) => request(p, 'PUT', d),
  // 素材上传：multipart，返回后端 json
  upload(path, filePath, kind) {
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: config.BASE_URL + path,
        filePath,
        name: 'file',
        formData: { kind },
        header: { Authorization: 'Bearer ' + (wx.getStorageSync('token') || '') },
        success(res) {
          try { resolve(JSON.parse(res.data)); } catch (e) { reject(e); }
        },
        fail: reject
      });
    });
  }
};
