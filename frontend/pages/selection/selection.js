// 引入全局测试数据
const testData = require('../../data/testData.js');

Component({
  data: {
    currentSort: 'time',
    selectionList: testData.sharedNewsList,
    officialList: testData.campusOfficialTestList,
  },

  // 页面生命周期
  pageLifetimes: {
    onLoad(options) {
      console.log('自选页面加载完成');
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
    // 切换排序方式
    switchSort(e) {
      const sortType = e.currentTarget.dataset.type;
      this.setData({ currentSort: sortType });
    },

    // 跳转到添加自选页面
    goToAdd() {
        wx.showToast({ title: '跳转到添加自选页面', icon: 'none' });
        wx.navigateTo({ url: '/pages/add/add' });
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
        
        // 跳转到我的页面（Tab 切换）
        goToUser() {
          wx.showToast({ title: '跳转到我的页面', icon: 'none' });
          wx.switchTab({ url: '/pages/user/user' }); // 替换为 switchTab
        }
      
  }
});