const request = require('../../utils/request'); // 引入 request 模块

Page({
  data: {
    userInfo: {
      avatarUrl: '/assets/icons/default-avatar.png', // 默认头像
      nickName: '未登录用户'                          // 默认昵称
    }
  },
  
  onReady() {
    // 此时页面已渲染完成，tabBar 存在，调用不会报错
    wx.hideTabBar({
      animation: false,
      success: () => console.log("tabBar 隐藏成功"),
      fail: (err) => console.log("隐藏失败", err)
    });
  },

  // 页面加载时获取 Mock 用户信息
  onLoad: function(options) {
    this.getUserInfo();
  },

  // 下拉刷新时同步最新 Mock 用户信息
  onPullDownRefresh: function() {
    console.log('下拉刷新：同步用户信息');
    this.getUserInfo(true); // 传 true 表示刷新场景
  },

   // 页面显示时获取（返回页面时触发）
   onShow: function() {
    this.getUserInfo(); 
  },


  //从 Mock 接口获取用户信息（对接 GET /user/auth/profile/）
  async getUserInfo(isRefresh = false) {
    try {
      const mockUserInfo = await request.getProfile();
      // 更新页面数据
      this.setData({
        userInfo: {
          avatarUrl: (mockUserInfo.avatar) || '/assets/icons/default-avatar.png',
          nickName: mockUserInfo.username || '默认用户名'
        }
      });
      console.log('Mock 用户信息获取成功：', mockUserInfo);

      // 如果是下拉刷新，停止刷新动画并提示
      if (isRefresh) {
        wx.stopPullDownRefresh();
        wx.showToast({ title: '刷新成功', icon: 'success' });
      }
    } catch (err) {
      console.error('获取 Mock 用户信息失败：', err);
      wx.showToast({ title: '获取用户信息失败', icon: 'none' });

      // 刷新场景下也要停止动画
      if (isRefresh) wx.stopPullDownRefresh();
    }
  },

  // 跳转到个人资料
  goToProfile() {
    wx.navigateTo({ url: '/packageA/user/profile/profile' });
  },

  // 跳转历史记录
  goToHistory() {
    wx.navigateTo({ url: '/packageA/user/history/history' });
  },

  // 跳转收藏页面
  goToFavorites() {
    wx.navigateTo({ url: '/packageA/user/like/like' }); 
  },

  // 跳转收藏夹页面
  goToFavorites_() {
    wx.navigateTo({ url: '/packageA/user/favorites/favorites' }); 
  },

  // 跳转到帮助中心
  goToHelp() {
    wx.navigateTo({ url: '/packageA/user/help/help' });
  },

  // 跳转到反馈建议
  goToSuggestion() {
    wx.navigateTo({ url: '/packageA/user/suggestion/suggestion' }); 
  },

  // 跳转到我的订阅
  goToSubscriptions() {
    wx.navigateTo({ url: '/packageA/user/subscriptions/subscriptions' });
  },

  // 跳转到我的待办
  goToCalendar() {
    wx.navigateTo({ url: '/packageA/user/calendar/calendar' });
  },

  // 底部 Tab 切换（保持不变）
  goToHome() {
    wx.switchTab({ url: '/pages/home/home' });
  },
  goToCampus() {
    wx.switchTab({ url: '/pages/campus/campus' });
  },
  goToSelection() {
    wx.switchTab({ url: '/pages/selection/selection' });
  }
});