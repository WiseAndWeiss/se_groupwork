const testData = require('../../data/testData.js');

Component({
    data: {
        officialList: testData.campusOfficialTestList,
    },
  
    pageLifetimes: {
      onLoad(options) {
        console.log('校内公众号一览页面加载完成');
      }
    },
  
    methods: {
      // 点击公众号，可跳转公众号详情（后续可扩展）
      goToOfficialDetail(e) {
        const officialId = e.currentTarget.dataset.id;
        wx.showToast({ title: `查看${e.currentTarget.dataset.name}详情`, icon: 'none' });
        // 后续可添加跳转详情页逻辑：wx.navigateTo({ url: `/pages/official-detail/official-detail?id=${officialId}` });
      },

      goBack() {
        wx.showToast({ title: '跳转到校内页面', icon: 'none' });
        wx.switchTab({ url: '/pages/campus/campus' }); // 替换为 switchTab
      },
  
      // 跳转到首页（Tab 切换）
      goToHome() {
        wx.showToast({ title: '跳转到首页页面', icon: 'none' });
        wx.switchTab({ url: '/pages/home/home' }); // 替换为 switchTab
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
    }
  });