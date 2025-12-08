const request = require('../../utils/request');

Component({
  properties: {
    accountId: String,       // 公众号唯一ID
    name: String,            // 公众号名称
    avatar: String,          // 公众号头像
    isSubscribed: {
      type: Number,
      value: false
    },
    showSubscribeBtn: {
      type: Boolean,
      value: true
    }
  },

  methods: {
    navigateToAccountDetail() {
        const accountId = String(this.properties.accountId || '').trim();
        const accountName = this.properties.name || ''; // 获取公众号名称，在wxml中使用（导航栏公众号名称）
        console.log('当前组件：accountId=', accountId, 'name=', accountName); 
        
        if (!accountId) {
          wx.showToast({ title: '公众号ID无效', icon: 'none' });
          return;
        }
  
        // URL 拼接 accountid + name，携带传递
        wx.navigateTo({
          url: `/packageA/account/detail/detail?accountid=${encodeURIComponent(accountId)}&name=${encodeURIComponent(accountName)}`
        });
      },
    /**
     订阅/取消订阅切换逻辑
     */
    async toggleSubscribe(e) {
        const { accountId, isSubscribed } = this.properties;
        
        // 校验公众号ID
        if (!accountId) {
          wx.showToast({ title: '公众号ID无效，无法订阅', icon: 'none' });
          return;
        }
  
        try {
          if (!isSubscribed) {
            // 未订阅->订阅
            const response = await request.addSubscription({public_account_id: accountId});
            wx.showToast({ title: '订阅成功' });
            // 更新组件状态为“已订阅”
            this.setData({ isSubscribed: response.id });
          } else {
            // 已订阅->取消
            const response = await request.deleteSubscription(isSubscribed);
            wx.showToast({ title: '取消订阅成功' });
            this.setData({ isSubscribed: response.id });
          }
        } catch (error) {
          console.error('订阅操作失败：', error);
        }
      }
  },

  lifetimes: {
    attached() {
      console.log('组件加载时 accountid：', this.properties.accountId);
    }
  },
});