const request = require('../../../utils/request');

Page({
  data: {
    userInfo: {}
  },

  onShow() {
    this.getProfile();
  },

  async getProfile() {
    console.log('===== profile页面 onShow，强制刷新用户信息 =====');
    try {
      const data = await request.getProfile();
      console.log('获取到的最新数据：', data);
      this.setData({ userInfo: data }, () => {
        console.log('页面数据已更新：', this.data.userInfo);
      });
    } catch (err) {
      console.error('获取资料失败：', err);
      wx.showToast({ title: '获取资料失败', icon: 'none' });
    }
  },

  goBack() {
    wx.navigateBack({ delta: 1 });
  },

  goToUpdateUserInfo() {
    wx.navigateTo({
      url: '/packageA/user/profile/update-userinfo/update-userinfo',
      success: (res) => {
        res.eventChannel.emit('passUserInfo', {
          userInfo: this.data.userInfo
        });
        console.log('传递给修改页面的数据：', this.data.userInfo);
      }
    });
  }
});