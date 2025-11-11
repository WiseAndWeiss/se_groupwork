// 引入全局测试数据
const testData = require('../../data/testData.js');

Component({
  data: {
    current: 0,
    autoplay: false, // 开启自动轮播（可改为false关闭）
    duration: 500,
    interval: 5000,
    // 轮播图数据
    swiperList: [
      {
        image: '/assets/images/banner1.jpg', 
      },
      {
        image: '/assets/images/banner2.jpg', 
      },
      {
        image: '/assets/images/banner3.jpg',
      }
    ],
    // 卡片数据
    selectionList: testData.sharedNewsList,
  },

  // 页面生命周期（修正位置）
  pageLifetimes: {
    onLoad() {
      console.log('页面加载完成');
    },
    onPullDownRefresh() {
      console.log('下拉刷新');
      setTimeout(() => {
        wx.stopPullDownRefresh();
        wx.showToast({ title: '刷新成功', icon: 'success' });
      }, 1000);
    }
  },

  methods: {
    onTap(e) {
      const { index } = e.detail;
      console.log('轮播图点击索引：', index);
    },
    onChange(e) {
      const { current, source } = e.detail;
      this.setData({ current });
      console.log('轮播图切换到：', current, source);
    },
    onImageLoad(e) {
      console.log('轮播图图片加载完成：', e.currentTarget.dataset.index);
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
  
  // 跳转到我的页面（Tab 切换）
  goToUser() {
    wx.showToast({ title: '跳转到我的页面', icon: 'none' });
    wx.switchTab({ url: '/pages/user/user' }); // 替换为 switchTab
  }
  },
});