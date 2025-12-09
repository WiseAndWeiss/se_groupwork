const request = require('../../../utils/request');


Component({
  data: {
    userInfo: {}
  },
  methods: {
    goBack() {
      wx.navigateBack({ delta: 1 });
    },

    // 刷新用户信息
    async getProfile() {
      console.log('===== 开始获取用户信息 =====');
      try {
        const data = await request.getProfile();
        console.log('获取到的最新数据：', data); // 确认数据是否更新
        this.setData({ userInfo: data }, () => {
          console.log('页面数据已更新：', this.data.userInfo); // 确认 setData 生效
        });
      } catch (err) {
        console.error('获取资料失败：', err);
        wx.showToast({ title: '获取资料失败', icon: 'none' });
      }
    },

    // 跳转到修改页面（确保传递数据正确）
    goToUpdateUserInfo() {
      wx.navigateTo({
        url: '/packageA/user/profile/update-userinfo/update-userinfo',
        success: (res) => {
          res.eventChannel.emit('passUserInfo', {
            userInfo: this.data.userInfo
          });
          console.log('传递给修改页面的数据：', this.data.userInfo);
        }
      });
    }
  },

  // 组件挂载时获取
  lifetimes: {
    attached() {
      this.getProfile();
    }
  },

  // 页面显示时强制刷新（不管是首次进入还是返回）
  pageLifetimes: {
    show() {
      console.log('===== profile 页面显示，强制刷新 =====');
      this.getProfile();
    }
  },

  //监听页面的 show 事件
  attached() {
    this.getProfile();
    const currentPage = getCurrentPages().pop();
    if (currentPage) {
      const originalOnShow = currentPage.onShow;
      currentPage.onShow = () => {
        originalOnShow && originalOnShow();
        console.log('===== 页面 onShow 触发刷新 =====');
        this.getProfile();
      };
    }
  }
});