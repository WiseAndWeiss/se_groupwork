// app.js
App({
    globalData: {
      petPosition: null
    },
    onLaunch() {
      // 启动后立即隐藏 tabBar，animation: true 可选（是否带隐藏动画）
      wx.hideTabBar({
        animation: false,
        success: () => {
          console.log("tabBar 全局隐藏成功");
        },
        fail: (err) => {
          console.log("tabBar 隐藏失败", err);
        }
      });
    }
  });