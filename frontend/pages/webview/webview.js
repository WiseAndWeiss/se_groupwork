// pages/webview/webview.js
Page({
  data: {
    url: ''
  },
  
  onLoad(options) {
    // 专门渲染顶部导航栏，白底黑字
    wx.setNavigationBarColor({
        frontColor: '#000000', 
        backgroundColor: '#ffffff',
      });
    if (options.url) {
      this.setData({
        url: decodeURIComponent(options.url)
      });
    }
  }
});