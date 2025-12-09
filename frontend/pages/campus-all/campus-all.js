const request = require('../../utils/request');

Component({
    data: {
        campusAccountList:[], //存储校内公众号
        showLoadingAnimation: false,
    },
  
    methods: { 
      // 页面显示时刷新（确保订阅状态实时同步）
      onShow() {
          this.getCampusAccountList()
      },

      // 获取订阅列表（对接 GET /api/campus-accounts/）
      async getCampusAccountList() {
        this.setData({ 
            showLoadingAnimation: true // 显示加载动画
          });
        try {
          const list = await request.getCampusAccountList();
          this.setData({ campusAccountList: list });
          console.log('订阅列表数据（含 id）：', list); 
        } catch (err) {
          wx.showToast({ title: '获取订阅列表失败', icon: 'none' });
          console.error('获取订阅失败：', err);
        }
        this.setData({ 
            showLoadingAnimation: false // 显示加载动画
          });
      },

      goBack() {
        wx.switchTab({ url: '/pages/campus/campus' }); // 替换为 switchTab
      },
  
      // 跳转到首页（Tab 切换）
      goToHome() {
        wx.switchTab({ url: '/pages/home/home' }); // 替换为 switchTab
      },
      
      // 跳转到自选页面（Tab 切换）
      goToSelection() {
        wx.switchTab({ url: '/pages/selection/selection' }); // 替换为 switchTab
      },
      
      // 跳转到我的页面（Tab 切换）
      goToUser() {
        wx.switchTab({ url: '/pages/user/user' }); // 替换为 switchTab
      }
    }
  });