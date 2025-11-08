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
  
    // 跳转到校内页面
    goToCampus: function() {
      wx.showToast({
        title: '跳转到校内页面',
        icon: 'none'
      });
      // 后续添加具体跳转逻辑
      wx.navigateTo({
        url: '/pages/campus/campus'
       });
    },
  
    // 跳转到自选页面
    goToSelection: function() {
      wx.showToast({
        title: '跳转到自选页面',
        icon: 'none'
      });
      // 后续添加具体跳转逻辑
      wx.navigateTo({
        url: '/pages/selection/selection'
       });
    },
  
    // 跳转到我的页面
    goToHome: function() {
      wx.showToast({
        title: '跳转到主页',
        icon: 'none'
      });
      // 后续添加具体跳转逻辑
      wx.navigateTo({
        url: '/pages/home/home'
        });
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