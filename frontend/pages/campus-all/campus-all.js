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
        wx.navigateBack({
          delta: 1 // 返回1级页面栈
        });
      },
  
      // 底部导航跳转方法（和校内页面一致）
      goToHome() {
        wx.redirectTo({ 
            url: '/pages/home/home' });
      },
      goToSelection() {
        wx.redirectTo({ url: '/pages/selection/selection' });
      },
      goToUser() {
        wx.redirectTo({ url: '/pages/user/user' });
      }
    }
  });