const request = require('../../utils/request');

Component({
  data: {
    searchContent: '',
    campusAccountList: [],
    showLoadingAnimation: false,
    showNoResults: false,
    showNoResults: false,
  },

  pageLifetimes: {
    onLoad() {
      console.log('校内公众号一览页面加载完成');
    }
  },

  methods: {
    goBack() {
      wx.navigateBack({
        delta: 1 // 返回1级页面栈
      });
    },

    // 输入框内容变化时触发
    onSearchInput(e) {
      this.setData({
        searchContent: e.detail.value,
        // 输入时隐藏无结果提示
        showNoResults: false,
        showNoResults: false
      });
    },

    async searchMoreAccounts() {
      const searchContent = this.data.searchContent.trim();
      this.setData({
        showLoadingAnimation: true
      });

      if (!searchContent) {
        wx.showToast({
          title: '请输入搜索关键词',
          icon: 'none'
        });
        return;
      }

      try {
        const list = await request.getMoreAccountsByName(searchContent);
        const dataList = list?.public_accounts || list || [];

        this.setData({
          campusAccountList: dataList,
          showNoResults: dataList.length === 0
        });

        if (dataList.length === 0) {
          console.log('no results')
        }
      } catch (err) {
        wx.showToast({
          title: '获取订阅列表失败',
          icon: 'none'
        });
        console.error('获取订阅失败：', err);
        this.setData({
          showNoResults: true
        });
      } finally {
        console.log(this.data.campusAccountList);
        this.setData({
          showLoadingAnimation: false
        });
      }
    },

    async searchAccount() {
      const searchContent = this.data.searchContent.trim();
      this.setData({
        showLoadingAnimation: true
      });
      console.log('test', searchContent);

      if (!searchContent) {
        wx.showToast({
          title: '请输入搜索关键词',
          icon: 'none'
        });
        this.setData({
          showLoadingAnimation: false
        });
        return;
      }

      try {
        const list = await request.getAccountsByName(searchContent);
        const dataList = list?.public_accounts || [];

        this.setData({
          campusAccountList: dataList,
          showNoResults: dataList.length === 0
        });

        if (dataList.length === 0) {
          console.log('no results')
        }
      } catch (err) {
        wx.showToast({
          title: '获取订阅列表失败',
          icon: 'none'
        });
        console.error('获取订阅失败：', err);
        this.setData({
          showNoResults: true
        });
      } finally {
        console.log(this.data.campusAccountList);
        this.setData({
          showLoadingAnimation: false
        });
      }
    }
  }
});