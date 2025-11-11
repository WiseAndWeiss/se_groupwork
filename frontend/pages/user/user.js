Page({
    data: {
        userInfo: {
          avatarUrl: '', // 用户头像URL，根据用户上传选取
          nickName: ''   // 用户名，根据用户设置选取
        }
      },
  
    // 页面加载时执行
    onLoad: function(options) {
    this.getUserInfo();
      // 这里可以添加从服务器获取数据的逻辑
    },
  
    // 跳转到首页（Tab 切换）
  goToHome() {
    wx.showToast({ title: '跳转到首页页面', icon: 'none' });
    wx.switchTab({ url: '/pages/home/home' }); // 替换为 switchTab
  },
  
  // 跳转到校内页面（Tab 切换）
  goToCampus() {
    wx.showToast({ title: '跳转到校内页面', icon: 'none' });
    wx.switchTab({ url: '/pages/campus/campus' }); // 替换为 switchTab
  },
  
  // 跳转到自选页面（Tab 切换）
  goToSelection() {
    wx.showToast({ title: '跳转到自选页面', icon: 'none' });
    wx.switchTab({ url: '/pages/selection/selection' }); // 替换为 switchTab
  },
  
    // 下拉刷新
    onPullDownRefresh: function() {
      console.log('下拉刷新');
      // 模拟刷新数据
      setTimeout(() => {
        wx.stopPullDownRefresh();
        wx.showToast({
          title: '刷新成功',
          icon: 'success'
        });
      }, 1000);
    }
  })