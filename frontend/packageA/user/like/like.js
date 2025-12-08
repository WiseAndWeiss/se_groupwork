const request = require('../../../utils/request');

Component({
  data: {
    favouriteList: [] ,// 存储从 Mock 接口获取的收藏列表
    showLoadingAnimation: false
  },

  methods: {
    // 页面显示时刷新（确保收藏状态实时同步）
    onShow() {
      this.getFavouriteList();
    },

    // 页面卸载时清理（比如跳转到其他Tab页面、关闭页面）
    onHide() {
      console.log('页面卸载，彻底清理数据');
      this.clearPageData();
    },

    clearPageData() {
      this.setData({
          favouriteList: []
      });
    },

    // 从 Mock 接口获取收藏列表（对接 GET /user/favorites/）
    async getFavouriteList() {
      this.setData({ 
        showLoadingAnimation: true // 显示加载动画
      });
      try {
        const list = await request.getFavouriteList();
        console.log(list)
        // 按收藏时间倒序排列（最新收藏在前）
        this.setData({ favouriteList: list });
        console.log('Mock 收藏列表：', list);
      } catch (err) {
        wx.showToast({ title: '获取收藏列表失败', icon: 'none' });
        console.error('获取收藏失败：', err);
      }
      this.setData({ 
        showLoadingAnimation: false // 显示加载动画
      });
    },

    // 删除所有收藏
    deleteAllFavourite() {
      const that = this; 

      wx.showModal({
        title: '确认删除',
        content: '是否删除所有收藏？删除后不可恢复',
        cancelText: '取消',
        confirmText: '删除',
        confirmColor: '#ff4d4f',
        // 普通函数回调，用 that 调用方法
        success: async function(res) {
          if (res.confirm) {
            try {
              wx.showLoading({ title: '删除中...' });
              await request.deleteAllFavourite(); // 调用 Mock 批量删除接口
              wx.hideLoading();
              wx.showToast({ title: '全部删除成功' });
              that.getFavouriteList(); // 刷新列表（显示空状态）
            } catch (err) {
              wx.hideLoading();
              wx.showToast({ title: err || '删除失败', icon: 'none' });
              console.error('删除所有收藏失败：', err);
            }
          }
        }
      });
    },

    // 返回上一页（个人中心）
    goBack() {
      wx.navigateBack({ delta: 1 });
    },

    initCardExpand(e) {
      const index = e.currentTarget.dataset.index;
      this.selectComponent(`.card-component-${index}`).setData({ isExpanded: true });
    }
  }
});