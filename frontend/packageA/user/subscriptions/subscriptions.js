const request = require('../../../utils/request');

Component({
  data: {
    subscriptionList: [], // 存储订阅列表
    showLoadingAnimation: false
  },

  methods: {
    // 页面显示时刷新（确保订阅状态实时同步）
    onShow() {
      this.getSubscriptionList();
    },

    // 获取订阅列表（对接 GET /api/user/subscriptions/）
    async getSubscriptionList() {
        this.setData({ 
            showLoadingAnimation: true // 显示加载动画
          });
        try {
          const list = await request.getSubscriptionList();
          this.setData({ subscriptionList: list });
          console.log('订阅列表数据（含 id）：', list); // 关键日志：看每个 item 是否有 id
          // 额外校验：打印第一个 item 的 id
          if (list.length > 0) console.log('第一个订阅的 id：', list[0].id);
        } catch (err) {
          wx.showToast({ title: '获取订阅列表失败', icon: 'none' });
          console.error('获取订阅失败：', err);
        }
        this.setData({ 
            showLoadingAnimation: false// 显示加载动画
          });
      },

    // 删除单条订阅（对接 DELETE /api/user/subscriptions/{id}/）
    async deleteSubscription(e) {
      const id = e.currentTarget.dataset.id;
      try {
        await request.deleteSubscription(id);
        wx.showToast({ title: '删除订阅成功' });
        this.getSubscriptionList(); // 刷新列表
      } catch (err) {
        wx.showToast({ title: err || '删除失败', icon: 'none' });
        console.error('删除单条订阅失败：', err);
      }
    },

    // 删除所有订阅（对接 DELETE /api/user/subscriptions/）
    deleteAllSubscriptions() {
      const that = this; // 固定 this 指向，避免小程序兼容问题
      wx.showModal({
        title: '确认删除',
        content: '是否删除所有订阅？删除后不可恢复',
        cancelText: '取消',
        confirmText: '删除',
        confirmColor: '#ff4d4f',
        success: async function(res) {
          if (res.confirm) {
            try {
              wx.showLoading({ title: '删除中...' });
              await request.deleteAllSubscriptions(); // 调用批量删除接口
              wx.hideLoading();
              wx.showToast({ title: '全部删除成功' });
              that.getSubscriptionList(); // 刷新列表（显示空状态）
            } catch (err) {
              wx.hideLoading();
              wx.showToast({ title: err || '删除失败', icon: 'none' });
            }
          }
        }
      });
    },

    // 返回上一页（个人中心）
    goBack() {
      wx.navigateBack({ delta: 1 });
    },

    // 初始化卡片展开状态
    initCardExpand(e) {
      const index = e.currentTarget.dataset.index;
      this.selectComponent(`.card-component-${index}`).setData({ isExpanded: true });
    }
  }
});