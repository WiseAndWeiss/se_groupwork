Component({
    options: {
        addGlobalClass: true, 
      },
    properties: {
      avatar: {
        type: String,
      },
      name: {
        type: String,
      },
      accountId: {
        type: String,
      },
      subscriptionId: {
        type: String,
      },
      disabled: {
        type: Boolean,
        value: false, // 默认不禁用
        observer(newVal) {
          this.setData({ isDisabled: newVal });
        }
      }
    },
  
    data: { 
        isDisabled: false
    },

    methods: {
        // 添加点击卡片事件
      handleCardClick() {
        // 禁用状态下不执行任何操作
        if (this.data.isDisabled) return;
        
        this.navigateToAccountDetail();
        this.triggerEvent('click', { name: this.data.name }); 
      },
      navigateToAccountDetail() {
        if (this.data.isDisabled) return;
        const accountId = String(this.properties.accountId || '').trim();
        const accountName = this.properties.name || ''; // 获取公众号名称，在wxml中使用（导航栏公众号名称）
        
        if (!accountId) {
          wx.showToast({ title: '公众号ID无效', icon: 'none' });
          return;
        }
  
        // URL 拼接 accountid + name，携带传递
        wx.navigateTo({
          url: `/packageA/account/detail/detail?accountid=${encodeURIComponent(accountId)}&name=${encodeURIComponent(accountName)}`
        });
      },
    }
  });