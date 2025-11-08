Page({
  
    // 页面加载时执行
    onLoad: function(options) {
      console.log('加载完成');
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
    goToUser: function() {
      wx.showToast({
        title: '跳转到我的页面',
        icon: 'none'
      });
      // 后续添加具体跳转逻辑
      wx.navigateTo({
        url: '/pages/user/user'
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